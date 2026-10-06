"""End-to-end tests of the deliveries: deliver, deliver-push, manifest-deliver, manifest-deliver-push."""

from pathlib import Path

from conftest import git, make_server_repository, run_island
from test_workspace import change_the_manifest, result_lines


def commit(repository: Path, subject: str, file_name: str = "CHANGE.md") -> None:
    """Commit a change in a repository, on its current branch."""
    path = repository / file_name
    path.write_text((path.read_text() if path.exists() else "") + subject + "\n")
    git("add", ".", cwd=repository)
    git("commit", "--quiet", "-m", subject, cwd=repository)


def show(repository: Path, ref: str, file_name: str) -> str:
    return git("show", f"{ref}:{file_name}", cwd=repository)


def test_deliver_releases_the_projects_with_new_commits(workspace: Path) -> None:
    alpha = workspace / "alpha"
    commit(alpha, "[FEAT] a feature")
    commit(alpha, "[FIX] a fix")
    result = run_island("deliver", "--yes", cwd=workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "    alpha  new version.txt -> 0.1.0 (minor), 2 commits" in result.stdout
    checks = result_lines(result.stdout.split("Deliver 1 project:")[0])
    assert checks["libs/beta"] == "up to date no version.txt, nothing to deliver"
    assert checks["solo"] == "no dev     no branch dev: nothing is developed apart"
    assert checks["empty"] == "empty      no commit"
    assert result_lines(result.stdout.split("Deliver 1 project:")[1])["alpha"] == "delivered  v0.1.0 on main, dev at 0.1.1-dev"
    assert "Push them with: island deliver-push" in result.stdout
    # the release on main, tagged, and the next version on dev that contains it
    assert show(alpha, "main", "version.txt") == "0.1.0\n"
    assert git("describe", "--tags", "main", cwd=alpha).strip() == "v0.1.0"
    assert git("log", "-1", "--format=%s", "main", cwd=alpha).strip() == "[RELEASE] Release v0.1.0"
    assert show(alpha, "dev", "version.txt") == "0.1.1-dev\n"
    assert git("rev-list", "--count", "dev..main", cwd=alpha).strip() == "0"
    # the repository is back on its branch, clean
    assert git("branch", "--show-current", cwd=alpha).strip() == "dev"
    assert git("status", "--porcelain", cwd=alpha) == ""


def test_deliver_push_sends_the_deliveries_only(workspace: Path, servers: Path) -> None:
    commit(workspace / "alpha", "[FIX] a fix")
    run_island("deliver", "--yes", cwd=workspace)
    # work in progress on beta: not a delivery
    commit(workspace / "libs" / "beta", "[DEV] work in progress")
    result = run_island("deliver-push", cwd=workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result_lines(result.stdout)
    assert lines["alpha"] == "pushed     main, dev, v0.0.1"
    assert lines["libs/beta"] == "up to date no delivery to push"
    server = servers / "alpha.git"
    assert git("tag", cwd=server).strip() == "v0.0.1"
    assert git("rev-parse", "main", cwd=server) == git("rev-parse", "main", cwd=workspace / "alpha")
    assert git("rev-parse", "dev", cwd=servers / "beta.git") != git("rev-parse", "dev", cwd=workspace / "libs" / "beta")
    assert result_lines(run_island("deliver-push", cwd=workspace).stdout)["alpha"] == "up to date no delivery to push"


def test_deliver_and_push_in_one_command_then_a_patch(workspace: Path, servers: Path) -> None:
    alpha = workspace / "alpha"
    commit(alpha, "[FEAT] a feature")
    run_island("deliver", "--yes", "--push", cwd=workspace)
    assert git("tag", cwd=servers / "alpha.git").strip() == "v0.1.0"
    # the next patch is the version being developed: no number is skipped
    commit(alpha, "[FIX] a fix")
    result = run_island("deliver", "--yes", "--push", cwd=workspace)
    assert "    alpha  0.1.1-dev -> 0.1.1 (patch), 1 commit" in result.stdout
    assert git("tag", cwd=servers / "alpha.git").split() == ["v0.1.0", "v0.1.1"]


def test_deliver_merges_with_a_merge_commit_in_merge_mode(workspace: Path, servers: Path) -> None:
    change_the_manifest(servers, {}, "")
    work = servers / "work-manifest.git"
    manifest = work / "default.xml"
    manifest.write_text(manifest.read_text().replace("</option>", "\t<deliver-mode>merge</deliver-mode>\n\t</option>"))
    git("commit", "--quiet", "-am", "merge mode", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", cwd=work)
    run_island("sync", cwd=workspace)
    alpha = workspace / "alpha"
    commit(alpha, "[FIX] a fix")
    assert run_island("deliver", "--yes", cwd=workspace).returncode == 0
    assert git("log", "-1", "--format=%s", "main~1", cwd=alpha).strip() == "Merge branch 'dev' into 'main'"


def test_the_first_delivery_creates_the_release_branch(workspace: Path, servers: Path) -> None:
    make_server_repository(servers, "gamma.git", {"README.md": "gamma\n"}, branches=("dev",))
    change_the_manifest(servers, {}, '<project name="gamma.git" path="gamma"/>')
    run_island("sync", cwd=workspace)
    result = run_island("deliver", "--yes", "--push", cwd=workspace)
    assert "    gamma  new version.txt -> 0.0.1 (patch), 1 commit, creates main" in result.stdout
    assert git("tag", cwd=servers / "gamma.git").strip() == "v0.0.1"
    assert git("branch", "--format=%(refname:short)", cwd=servers / "gamma.git").split() == ["dev", "main"]


def test_deliver_refuses_what_it_cannot_deliver_and_changes_nothing(workspace: Path, servers: Path) -> None:
    # alpha: its main has a commit that dev has not
    work = servers / "work-alpha.git"
    commit(work, "[FIX] fixed on main")
    git("push", "--quiet", "origin", "HEAD:main", cwd=work)
    commit(workspace / "alpha", "[FIX] a fix")
    # beta: new commits and local changes
    beta = workspace / "libs" / "beta"
    commit(beta, "[FIX] a fix")
    (beta / "README.md").write_text("changed\n")
    alpha_dev = git("rev-parse", "dev", cwd=workspace / "alpha")
    result = run_island("deliver", "--yes", cwd=workspace)
    assert result.returncode != 0
    lines = result_lines(result.stdout)
    assert lines["alpha"] == "diverged   main has 1 commit that dev has not: merge it in dev first"
    assert lines["libs/beta"] == "modified   local changes: commit or stash them first"
    assert "Correct the errors above" in result.stdout
    assert git("rev-parse", "dev", cwd=workspace / "alpha") == alpha_dev
    assert "main" not in git("branch", "--format=%(refname:short)", cwd=workspace / "alpha").split()


def test_deliver_refuses_a_source_branch_behind_the_server(workspace: Path, servers: Path) -> None:
    work = servers / "work-alpha.git"
    commit(work, "[FIX] pushed by somebody else")
    git("push", "--quiet", "origin", "HEAD:dev", cwd=work)
    commit(workspace / "alpha", "[FIX] a local fix")
    result = run_island("deliver", "--yes", cwd=workspace)
    assert result_lines(result.stdout)["alpha"] == "behind     dev is 1 behind origin/dev: island sync first"


def test_deliver_refuses_a_tag_that_exists(workspace: Path) -> None:
    alpha = workspace / "alpha"
    git("tag", "v0.0.1", cwd=alpha)
    commit(alpha, "[FIX] a fix")
    result = run_island("deliver", "--yes", cwd=workspace)
    assert result_lines(result.stdout)["alpha"] == "tag exists v0.0.1 exists already: raise the version of version.txt in dev"


def test_deliver_asks_once_and_lets_change_the_versions(workspace: Path) -> None:
    commit(workspace / "alpha", "[FIX] a fix")
    commit(workspace / "libs" / "beta", "[FIX] a fix")
    # edit: alpha in major, beta left out; then yes
    result = run_island("deliver", cwd=workspace, answers="e\nmajor\nskip\ny\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "    alpha  new version.txt -> 1.0.0 (major), 1 commit" in result.stdout
    assert git("tag", cwd=workspace / "alpha").strip() == "v1.0.0"
    assert git("tag", cwd=workspace / "libs" / "beta").strip() == ""


def test_deliver_without_answer_changes_nothing(workspace: Path) -> None:
    commit(workspace / "alpha", "[FIX] a fix")
    result = run_island("deliver", cwd=workspace)
    assert "Delivery canceled" in result.stdout
    assert git("tag", cwd=workspace / "alpha").strip() == ""


def test_deliver_runs_the_release_script_of_a_project(workspace: Path) -> None:
    alpha = workspace / "alpha"
    (alpha / ".island").mkdir()
    script = alpha / ".island" / "release.bash"
    script.write_text('#!/bin/bash\necho "version $(cat version.txt)" > VERSION.md\ngit add VERSION.md\n')
    script.chmod(0o755)
    git("add", ".", cwd=alpha)
    git("commit", "--quiet", "-m", "[DEV] a release script", cwd=alpha)
    assert run_island("deliver", "--yes", cwd=workspace).returncode == 0
    assert show(alpha, "main", "VERSION.md") == "version 0.0.1\n"
    assert show(alpha, "dev", "VERSION.md") == "version 0.0.2-dev\n"
