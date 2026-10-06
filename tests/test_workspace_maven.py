"""End-to-end tests of the delivery of Maven projects that depend on each other."""

from pathlib import Path

from conftest import SERVER, git, make_server_repository, run_island
import pytest
from test_workspace import result_lines
from test_workspace_deliver import commit, show


def pom(artifact: str, version: str, dependencies: dict[str, str]) -> str:
    """A pom of the workspace, laid out as the poms of jatria_soft."""
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        f"  <modelVersion>4.0.0</modelVersion>\n  <groupId>org.atriasoft</groupId>\n  <artifactId>{artifact}</artifactId>\n"
        f"  <version>{version}</version>\n\t<dependencies>\n"
    )
    for name, dependency_version in dependencies.items():
        text += f"\t\t<dependency>\n\t\t\t<groupId>org.atriasoft</groupId>\n\t\t\t<artifactId>{name}</artifactId>\n"
        text += f"\t\t\t<version>{dependency_version}</version>\n\t\t</dependency>\n"
    return text + "\t</dependencies>\n</project>\n"


# name: (dependencies, branches, private)
PROJECTS = {
    "etk": ({}, ("main", "dev"), False),
    "gale": ({"etk": "0.1.0"}, ("main", "dev"), False),
    "ewol": ({"gale": "0.1.0", "etk": "0.1.0"}, ("main", "dev"), False),
    "secret": ({}, ("main", "dev"), True),
    "game": ({"ewol": "0.1.0", "etk": "0.1.0"}, ("main",), True),
}


@pytest.fixture
def maven_workspace(tmp_path: Path, servers: Path) -> Path:
    """A workspace of Maven projects, all in 0.1.0, as jatria_soft before its first delivery."""
    projects = ""
    for name, (dependencies, branches, private) in PROJECTS.items():
        make_server_repository(servers, f"{name}.git", {"pom.xml": pom(name, "0.1.0", dependencies)}, branches=branches)
        private_attribute = ' private="true"' if private else ""
        projects += f'\t<project name="{name}.git" path="{name}"{private_attribute}/>\n'
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<manifest>\n\t<remote name="origin" fetch="git@island.test"/>\n'
        "\t<option>\n\t\t<branch-release>main</branch-release>\n\t\t<branch-develop>dev</branch-develop>\n"
        "\t\t<default-branch>dev</default-branch>\n\t\t<default-remote>origin</default-remote>\n\t</option>\n"
        f"{projects}</manifest>\n"
    )
    make_server_repository(servers, "maven-manifest.git", {"default.xml": manifest})
    workspace = tmp_path / "maven"
    workspace.mkdir()
    run_island("init", SERVER + ":maven-manifest.git", cwd=workspace)
    assert run_island("sync", cwd=workspace).returncode == 0
    return workspace


def dependency_version(repository: Path, ref: str, artifact: str) -> str:
    text = show(repository, ref, "pom.xml")
    return text.split(f"<artifactId>{artifact}</artifactId>")[1].split("<version>")[1].split("</version>")[0]


def own_version(repository: Path, ref: str) -> str:
    return show(repository, ref, "pom.xml").split("</artifactId>\n  <version>")[1].split("</version>")[0]


def test_deliver_pins_the_releases_and_follows_the_snapshots(maven_workspace: Path) -> None:
    etk, gale, ewol, game = (maven_workspace / name for name in ("etk", "gale", "ewol", "game"))
    commit(etk, "[FEAT] a feature")
    commit(gale, "[FIX] a fix")
    result = run_island("deliver", "--yes", cwd=maven_workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    checks = result_lines(result.stdout.split("Deliver 2 projects:")[0])
    assert checks["ewol"] == "unreleased 0.1.0, never released"
    # never released: the version of the pom is the first release
    assert "    etk   0.1.0 never released -> 0.1.0 (minor), 1 commit" in result.stdout
    assert "    gale  0.1.0 never released -> 0.1.0 (patch), 1 commit, with etk 0.1.0" in result.stdout
    assert "    ewol, game" in result.stdout
    # the releases depend on releases
    assert (own_version(etk, "main"), own_version(gale, "main")) == ("0.1.0", "0.1.0")
    assert dependency_version(gale, "main", "etk") == "0.1.0"
    # the source branches depend on what their dependencies develop
    assert (own_version(etk, "dev"), own_version(gale, "dev")) == ("0.1.1-SNAPSHOT", "0.1.1-SNAPSHOT")
    assert dependency_version(gale, "dev", "etk") == "0.1.1-SNAPSHOT"
    # the projects not delivered follow, on the branch they are developed on
    assert (dependency_version(ewol, "dev", "etk"), dependency_version(ewol, "dev", "gale")) == ("0.1.1-SNAPSHOT", "0.1.1-SNAPSHOT")
    assert git("log", "-1", "--format=%s", "dev", cwd=ewol).strip() == "[DEV] Follow gale 0.1.1-SNAPSHOT, etk 0.1.1-SNAPSHOT"
    assert dependency_version(game, "main", "etk") == "0.1.1-SNAPSHOT"
    assert dependency_version(game, "main", "ewol") == "0.1.0"
    # a Maven project keeps its version in its pom alone
    assert git("ls-tree", "--name-only", "main", cwd=etk).split() == ["CHANGE.md", "pom.xml"]
    # the deliveries and the commits island made are pushed, nothing else
    lines = result_lines(run_island("deliver-push", cwd=maven_workspace).stdout)
    assert lines["etk"] == "pushed     main, dev, v0.1.0"
    assert lines["ewol"] == "pushed     dev"
    assert lines["game"] == "pushed     main"
    # a project that only followed its dependencies has nothing new to deliver
    lines = result_lines(run_island("deliver", "--yes", cwd=maven_workspace).stdout)
    assert lines["ewol"] == "unreleased 0.1.0, never released"
    assert lines["etk"] == "up to date 0.1.1-SNAPSHOT, nothing to deliver"


def test_deliver_adds_the_dependencies_a_project_needs(maven_workspace: Path) -> None:
    run_island("deliver", "--yes", "--unreleased", "--push", cwd=maven_workspace)
    assert git("tag", cwd=maven_workspace / "ewol").strip() == "v0.1.0"
    commit(maven_workspace / "etk", "[FIX] a fix")
    commit(maven_workspace / "gale", "[FIX] a fix")
    result = run_island("--filter=gale", "deliver", "--yes", cwd=maven_workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Added, needed by gale: etk" in result.stdout
    assert "    gale  0.1.1-SNAPSHOT -> 0.1.1 (patch), 1 commit, with etk 0.1.1" in result.stdout
    assert dependency_version(maven_workspace / "gale", "main", "etk") == "0.1.1"
    # skipping a dependency while editing the plan: it comes back
    commit(maven_workspace / "etk", "[FIX] a fix")
    commit(maven_workspace / "gale", "[FIX] a fix")
    result = run_island("deliver", cwd=maven_workspace, answers="e\nskip\n\nn\n")
    assert "Added, needed by gale: etk" in result.stdout.split("version patch")[-1]


def test_a_public_project_can_not_depend_on_a_private_one(maven_workspace: Path) -> None:
    gale = maven_workspace / "gale"
    (gale / "pom.xml").write_text(pom("gale", "0.1.0", {"etk": "0.1.0", "secret": "0.1.0"}))
    git("commit", "--quiet", "-am", "[DEV] use the secret", cwd=gale)
    result = run_island("deliver", "--yes", cwd=maven_workspace)
    assert "Error: gale is public and depends on secret, which is private" in result.stdout
    assert result.returncode != 0


def test_deliver_warns_of_a_dependency_pulled_in_two_versions(maven_workspace: Path) -> None:
    run_island("deliver", "--yes", "--unreleased", "--push", cwd=maven_workspace)
    # etk and ewol move, gale does not: its release still depends on the former etk
    commit(maven_workspace / "etk", "[FEAT] a feature")
    commit(maven_workspace / "ewol", "[FIX] a fix")
    result = run_island("deliver", "--yes", cwd=maven_workspace)
    assert "Warning: ewol 0.1.1 pulls etk in several versions: 0.1.0 through gale, 0.2.0 through ewol" in result.stdout
    assert result.returncode == 0
