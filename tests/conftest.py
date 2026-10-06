"""Fixtures of the end-to-end tests: a workspace synchronized from local git servers."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


# The address of the servers in the manifest, as on a real host; git reads them in the local folder (url.insteadOf).
SERVER = "git@island.test"

MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
	<remote name="origin" fetch="{fetch}"/>
	<option>
		<branch-release>main</branch-release>
		<branch-develop>dev</branch-develop>
		<default-branch>dev</default-branch>
		<default-remote>origin</default-remote>
		<synchronize-submodule>true</synchronize-submodule>
	</option>
	<project name="alpha.git" path="alpha"/>
	<project name="beta.git" path="libs/beta"/>
	<project name="empty.git" path="empty"/>
	<link source=".island/manifest/default.xml" destination="manifest.xml"/>
</manifest>
"""


def git(*args: str, cwd: Path) -> str:
    """Run git in a folder and return its standard output."""
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def make_server_repository(servers: Path, name: str, files: dict[str, str] | None) -> None:
    """Create a bare repository on the local server, with 'main' and 'dev' when files are given (none: an empty one)."""
    bare = servers / name
    git("init", "--quiet", "--bare", "--initial-branch=main", str(bare), cwd=servers)
    if files is None:
        return
    work = servers / ("work-" + name)
    git("clone", "--quiet", str(bare), str(work), cwd=servers)
    for file_name, content in files.items():
        (work / file_name).write_text(content)
    git("add", ".", cwd=work)
    git("commit", "--quiet", "-m", "first", cwd=work)
    git("push", "--quiet", "origin", "HEAD:main", "HEAD:dev", cwd=work)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home without the user's git configuration, and a fixed identity."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{key}_NAME", "Island Test")
        monkeypatch.setenv(f"GIT_{key}_EMAIL", "test@island.invalid")
    return home


@pytest.fixture
def servers(tmp_path: Path, isolated_git: Path) -> Path:
    """The local git servers: a manifest and the repositories it lists."""
    servers = tmp_path / "servers"
    servers.mkdir()
    git("config", "--global", f"url.{servers}/.insteadOf", SERVER + ":", cwd=servers)
    make_server_repository(servers, "manifest.git", {"default.xml": MANIFEST.format(fetch=SERVER)})
    make_server_repository(servers, "alpha.git", {"README.md": "alpha\n"})
    make_server_repository(servers, "beta.git", {"README.md": "beta\n"})
    make_server_repository(servers, "empty.git", None)
    return servers


def run_island(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run island as a user does, from a folder of the workspace.

    The output is decoded by hand: the text mode would turn the carriage returns of the display into new lines.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import sys; from island.bin_island import main; sys.exit(main())", *args],
        cwd=cwd,
        capture_output=True,
        env=os.environ.copy(),
        check=False,
    )
    return subprocess.CompletedProcess(result.args, result.returncode, result.stdout.decode(), result.stderr.decode())


@pytest.fixture
def workspace(tmp_path: Path, servers: Path) -> Path:
    """A workspace initialized on the local manifest and synchronized."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result = run_island("init", SERVER + ":manifest.git", "--branch=main", cwd=workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    result = run_island("sync", cwd=workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    return workspace
