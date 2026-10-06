"""End-to-end tests: island run as a user does, on local git servers."""

from pathlib import Path
import re

from conftest import SERVER, git, make_server_repository, run_island


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


def test_sync_clones_on_the_default_branch_of_the_manifest(workspace: Path) -> None:
    assert git("branch", "--show-current", cwd=workspace / "alpha").strip() == "dev"
    assert git("branch", "--show-current", cwd=workspace / "libs" / "beta").strip() == "dev"


def test_sync_keeps_the_branch_of_the_server_when_the_default_one_is_missing(tmp_path: Path, servers: Path) -> None:
    workspace = tmp_path / "other"
    workspace.mkdir()
    run_island("init", SERVER + ":manifest.git", cwd=workspace)
    result = run_island("sync", cwd=workspace)
    assert "has no branch 'dev': clone its default branch" in result.stdout
    assert git("branch", "--show-current", cwd=workspace / "solo").strip() == "main"


def test_status_shows_each_project_and_an_empty_one(workspace: Path) -> None:
    result = run_island("status", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    lines = status_lines(result.stdout)
    assert lines[".island/manifest"] == "(main -> origin/main)"
    assert lines["alpha"] == "(dev -> origin/dev)"
    assert lines["libs/beta"] == "(dev -> origin/dev)"
    assert lines["solo"] == "(main -> origin/main)"
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
    result = run_island("checkout", "main", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert git("branch", "--show-current", cwd=workspace / "alpha").strip() == "main"
    assert git("branch", "--show-current", cwd=workspace / "libs" / "beta").strip() == "main"


def test_sync_pulls_a_new_commit(workspace: Path, servers: Path) -> None:
    work = servers / "work-alpha.git"
    (work / "NEW.md").write_text("new\n")
    git("add", ".", cwd=work)
    git("commit", "--quiet", "-m", "second", cwd=work)
    git("push", "--quiet", "origin", "HEAD:dev", cwd=work)
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


def test_sync_links_the_files_of_the_manifest(workspace: Path) -> None:
    link = workspace / "manifest.xml"
    assert link.is_symlink()
    assert link.resolve() == (workspace / ".island" / "manifest" / "default.xml").resolve()
    assert run_island("sync", cwd=workspace).returncode == 0
    assert link.is_symlink()


def test_sync_fails_when_a_link_takes_the_place_of_a_file(workspace: Path) -> None:
    (workspace / "manifest.xml").unlink()
    (workspace / "manifest.xml").write_text("a file of the user\n")
    result = run_island("sync", cwd=workspace)
    assert "path already exist" in result.stdout
    assert result.returncode != 0
    assert (workspace / "manifest.xml").read_text() == "a file of the user\n"


def add_project_to_the_manifest(servers: Path) -> None:
    """Add the project 'gamma' to the manifest on the server."""
    make_server_repository(servers, "gamma.git", {"README.md": "gamma\n"})
    work = servers / "work-manifest.git"
    manifest = work / "default.xml"
    manifest.write_text(
        manifest.read_text().replace('<project name="solo.git"', '<project name="gamma.git" path="gamma"/>\n\t<project name="solo.git"')
    )
    git("commit", "--quiet", "-am", "add gamma", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", cwd=work)


def test_sync_takes_the_new_projects_of_the_manifest(workspace: Path, servers: Path) -> None:
    add_project_to_the_manifest(servers)
    run_island("sync", cwd=workspace)
    assert (workspace / "gamma" / "README.md").read_text() == "gamma\n"


def test_sync_without_fetching_the_manifest_keeps_it(workspace: Path, servers: Path) -> None:
    add_project_to_the_manifest(servers)
    result = run_island("--no-fetch-manifest", "sync", cwd=workspace)
    assert "manifest not updated" in result.stdout
    assert (workspace / "gamma").exists() is False


def change_the_manifest(servers: Path, files: dict[str, str], before_solo: str) -> None:
    """Add files next to the manifest on the server, and a line in it before the project 'solo'."""
    work = servers / "work-manifest.git"
    for name, content in files.items():
        (work / name).write_text(content)
    manifest = work / "default.xml"
    manifest.write_text(manifest.read_text().replace('<project name="solo.git"', before_solo + '\n\t<project name="solo.git"'))
    git("add", ".", cwd=work)
    git("commit", "--quiet", "-m", "change the manifest", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", cwd=work)


def test_sync_clones_the_repositories_of_an_imported_vcs_file(workspace: Path, servers: Path) -> None:
    make_server_repository(servers, "delta.git", {"README.md": "delta\n"})
    make_server_repository(servers, "epsilon.git", {"README.md": "epsilon\n"})
    repos = "repositories:\n  delta:\n    type: git\n    url: git@island.test:delta.git\n  epsilon:\n    url: git@island.test:epsilon.git\n    version: dev\n"
    change_the_manifest(servers, {"extra.repos": repos}, '<import name="extra.repos"/>')
    result = run_island("sync", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert (workspace / "delta" / "README.md").read_text() == "delta\n"
    assert "Need to select a specific tag version ... dev" in result.stdout


def test_a_volatile_repository_is_listed_once_with_an_included_manifest(workspace: Path, servers: Path) -> None:
    make_server_repository(servers, "zeta.git", {"README.md": "zeta\n"})
    include = '<?xml version="1.0" encoding="UTF-8"?>\n<manifest>\n\t<project name="zeta.git" path="zeta"/>\n</manifest>\n'
    change_the_manifest(servers, {"more.xml": include}, '<include name="more.xml"/>')
    run_island("sync", cwd=workspace)
    assert (workspace / "zeta" / "README.md").read_text() == "zeta\n"
    run_island("volatile-add", SERVER + ":alpha.git", "volatile-alpha", cwd=workspace)
    lines = run_island("status", cwd=workspace).stdout.split("\n")
    assert len([line for line in lines if " : volatile-alpha" in line]) == 1


def test_sync_local_skips_a_project_without_tracking_branch(workspace: Path) -> None:
    git("checkout", "--quiet", "-b", "local-only", cwd=workspace / "alpha")
    result = run_island("sync-local", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert "no tracking branch" in result.stdout
    assert "local sync partial warning on 2 repository" in result.stdout


def test_sync_clones_a_project_with_its_submodules(workspace: Path, servers: Path) -> None:
    make_server_repository(servers, "eta.git", {"README.md": "eta\n"})
    work = servers / "work-eta.git"
    git("submodule", "--quiet", "add", SERVER + ":alpha.git", "sub/alpha", cwd=work)
    git("commit", "--quiet", "-m", "add a submodule", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", "HEAD:dev", cwd=work)
    change_the_manifest(servers, {}, '<project name="eta.git" path="eta"/>')
    result = run_island("sync", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert "Can not init submodules" not in result.stdout
    assert (workspace / "eta" / "sub" / "alpha" / "README.md").read_text() == "alpha\n"


def test_sync_tells_a_submodule_it_cannot_clone(workspace: Path, servers: Path) -> None:
    make_server_repository(servers, "theta.git", {"README.md": "theta\n"})
    work = servers / "work-theta.git"
    git("submodule", "--quiet", "add", SERVER + ":alpha.git", "sub/alpha", cwd=work)
    git("config", "--file", ".gitmodules", "submodule.sub/alpha.url", SERVER + ":missing.git", cwd=work)
    git("commit", "--quiet", "-am", "add a submodule that does not exist", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", "HEAD:dev", cwd=work)
    change_the_manifest(servers, {}, '<project name="theta.git" path="theta"/>')
    result = run_island("sync", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert "Can not init submodules" in result.stdout


HELLO_ACTION = """def help() -> str:
    return "Say hello"


def execute(_arguments: list) -> None:
    print("hello from the workspace")
"""


def test_an_action_of_the_workspace_runs(workspace: Path) -> None:
    (workspace / "alpha" / "islandAction_hello.py").write_text(HELLO_ACTION)
    assert "hello from the workspace" in run_island("hello", cwd=workspace).stdout


def test_the_user_config_excludes_folders_from_the_search_of_actions(workspace: Path) -> None:
    (workspace / "alpha" / "islandAction_hello.py").write_text(HELLO_ACTION)
    (workspace / "islandConfig.py").write_text('def get_exclude_path() -> list[str]:\n    return [".island", ".git", "alpha"]\n')
    result = run_island("hello", cwd=workspace)
    assert "Traceback" not in result.stderr, result.stderr
    assert "Wrong action type : 'hello'" in result.stdout


def test_checkout_tells_a_branch_it_cannot_take(workspace: Path, servers: Path) -> None:
    work = servers / "work-alpha.git"
    git("checkout", "--quiet", "-b", "feature", cwd=work)
    (work / "NEW.md").write_text("from the feature\n")
    git("add", ".", cwd=work)
    git("commit", "--quiet", "-m", "feature", cwd=work)
    git("push", "--quiet", "origin", "feature", cwd=work)
    git("fetch", "--quiet", "origin", cwd=workspace / "alpha")
    # an untracked file of the user that the branch would overwrite
    (workspace / "alpha" / "NEW.md").write_text("of the user\n")
    result = run_island("checkout", "feature", cwd=workspace)
    assert "Can not checkout to the correct branch" in result.stdout
    assert result.returncode != 0
    assert git("branch", "--show-current", cwd=workspace / "alpha").strip() == "dev"


def test_init_fails_on_a_manifest_it_cannot_clone(tmp_path: Path, servers: Path) -> None:
    workspace = tmp_path / "other"
    workspace.mkdir()
    result = run_island("init", SERVER + ":missing.git", cwd=workspace)
    assert result.returncode != 0
