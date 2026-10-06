"""End-to-end tests: island run as a user does, on local git servers."""

from pathlib import Path
import re

from conftest import git, run_island


def status_lines(output: str) -> dict[str, str]:
    """The status of each project, by path, without the tabulations of the display."""
    lines = {}
    for line in output.split("\n"):  # not splitlines(): the display aligns its columns with a carriage return
        match = re.match(r"\s*\d+/\d+ : (\S+)\s*(.*)$", re.sub(r"\r\t*", " ", line))
        if match:
            lines[match.group(1)] = match.group(2).strip()
    return lines


def test_help_lists_the_actions(tmp_path: Path, isolated_git: Path) -> None:
    result = run_island("--help", cwd=tmp_path)
    for action in ("init", "sync", "status", "checkout", "ssh-key", "user"):
        assert action in result.stdout


def test_sync_clones_every_project_on_the_default_branch(workspace: Path) -> None:
    assert (workspace / "alpha" / "README.md").read_text() == "alpha\n"
    assert (workspace / "libs" / "beta" / "README.md").read_text() == "beta\n"
    assert (workspace / "README.md").exists() is False
    assert (workspace / "empty" / ".git").is_dir()


def test_status_shows_each_project_and_an_empty_one(workspace: Path) -> None:
    result = run_island("status", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    lines = status_lines(result.stdout)
    assert lines[".island/manifest"] == "(main -> origin/main)"
    assert lines["alpha"].endswith("-> origin/main)")
    assert lines["libs/beta"].endswith("-> origin/main)")
    assert lines["empty"] == "(NO COMMIT)"


def test_status_marks_a_modified_project(workspace: Path) -> None:
    (workspace / "alpha" / "README.md").write_text("changed\n")
    lines = status_lines(run_island("status", cwd=workspace).stdout)
    assert "***" in lines["alpha"]
    assert "***" not in lines["libs/beta"]


def test_status_works_from_a_sub_folder(workspace: Path) -> None:
    lines = status_lines(run_island("status", cwd=workspace / "libs" / "beta").stdout)
    assert lines["empty"] == "(NO COMMIT)"


def test_checkout_switches_the_projects_to_a_branch(workspace: Path) -> None:
    result = run_island("checkout", "dev", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert git("branch", "--show-current", cwd=workspace / "alpha").strip() == "dev"
    assert git("branch", "--show-current", cwd=workspace / "libs" / "beta").strip() == "dev"


def test_sync_pulls_a_new_commit(workspace: Path, servers: Path) -> None:
    work = servers / "work-alpha.git"
    (work / "NEW.md").write_text("new\n")
    git("add", ".", cwd=work)
    git("commit", "--quiet", "-m", "second", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", cwd=work)
    result = run_island("sync", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert (workspace / "alpha" / "NEW.md").exists()


def test_user_and_ssh_key_are_set_in_every_repository(workspace: Path, isolated_git: Path) -> None:
    key = isolated_git / "id_test"
    key.write_text("not a real key\n")
    run_island("user", "--name=Somebody", "--email=somebody@island.invalid", cwd=workspace)
    run_island("ssh-key", str(key), cwd=workspace)
    for path in (workspace / "alpha", workspace / "libs" / "beta", workspace / ".island" / "manifest"):
        assert git("config", "user.name", cwd=path).strip() == "Somebody"
        assert git("config", "user.email", cwd=path).strip() == "somebody@island.invalid"
        assert str(key) in git("config", "core.sshCommand", cwd=path)


def test_a_wrong_manifest_root_is_told(workspace: Path) -> None:
    manifest = workspace / ".island" / "manifest" / "default.xml"
    manifest.write_text(manifest.read_text().replace("manifest>", "manifesto>"))
    result = run_island("status", cwd=workspace)
    assert "NameError" not in result.stderr, result.stderr
    assert "have not main xml node='manifest'" in result.stdout


def test_a_wrong_submodule_option_is_told(workspace: Path) -> None:
    manifest = workspace / ".island" / "manifest" / "default.xml"
    manifest.write_text(manifest.read_text().replace(">true</synchronize-submodule>", ">maybe</synchronize-submodule>"))
    result = run_island("status", cwd=workspace)
    assert "NameError" not in result.stderr, result.stderr
    assert "value:'maybe' available:[true,1,yes,false,0,no]" in result.stdout
