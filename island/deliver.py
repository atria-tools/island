"""Delivery of the projects: release the source branch (dev) on the destination branch (main), then push.

A delivery runs in three steps:

1. check every project, several at a time (one line each): what it has to deliver, from which version
   to which one, or why it is skipped; nothing is changed but a fetch;
2. show the plan and ask once to go on (or to change the version of a project);
3. deliver each project of the plan: merge the source branch in the destination one (created at the
   first delivery), write version.txt, run .island/release.bash when the project has one, commit and
   tag the release, bring the source branch to the release (fast-forward) and start its next version
   ("-dev"). The repository ends on the branch it was on.

The version comes from version.txt (0.0.0 without it); the step (patch, minor, major) is proposed from
the subjects of the commits delivered: an [API] or BREAKING one gives major, a [FEAT] one minor, any
other patch.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import os
import re
import shlex
from typing import Literal

from lxml import etree
from realog import debug

from . import commands, env, maven, multiprocess, parallel, tools
from .parallel import ProjectResult, Status
from .repo_config import RepoConfig


Bump = Literal["patch", "minor", "major"]
BUMPS: tuple[Bump, ...] = ("patch", "minor", "major")

# the subject of the commit that starts the next version on the source branch (the second one was used before)
DEV_VERSION_MESSAGES = ("[VERSION] update dev tag version", "[DEV] update dev tag version")
# the subject of the commit of a project that follows the new versions of its dependencies
FOLLOW_PREFIX = "[DEV] Follow "
VERSION_FILE = "version.txt"


def is_island_commit(subject: str) -> bool:
    """Tell a commit island made itself (a version, a dependency followed): it is nothing to deliver."""
    return subject in DEV_VERSION_MESSAGES or subject.startswith(FOLLOW_PREFIX)


class DeliverError(Exception):
    """A git command of a delivery failed."""


def _git(path: str, *args: str) -> multiprocess.CommandResult:
    cmd = shlex.join(["git", *args])
    debug.verbose("execute : " + cmd)
    return multiprocess.run_command(cmd, cwd=path)


def _last_line(ret: multiprocess.CommandResult) -> str:
    """The last line git told: on its error output, else on its standard output."""
    return (ret.stderr or ret.stdout).split("\n")[-1]


def _git_or_fail(path: str, step: str, *args: str) -> str:
    ret = _git(path, *args)
    if ret.returncode != 0:
        raise DeliverError(f"{step}: {_last_line(ret)}")
    return ret.stdout


def _ref_exists(path: str, ref: str) -> bool:
    return _git(path, "rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode == 0


def _subjects(path: str, from_ref: str | None, to_ref: str) -> list[str]:
    """Subjects of the commits of to_ref that from_ref has not (all of them without from_ref), oldest first."""
    ret = _git(path, "log", "--reverse", "--format=%s", to_ref if from_ref is None else from_ref + ".." + to_ref)
    return [line for line in ret.stdout.split("\n") if line != ""]


# ----------------------------------------------------------------------------------------------------
# versions
# ----------------------------------------------------------------------------------------------------


@dataclass
class Version:
    """A version of version.txt: three numbers, maybe a suffix (1.3.1-dev: the version being developed)."""

    numbers: list[int]
    suffix: str = ""

    @staticmethod
    def parse(text: str) -> "Version":
        text = text.strip()
        if text == "":
            return Version([0, 0, 0])
        base, _, suffix = text.partition("-")
        numbers = [int(elem) for elem in base.split(".") if elem.strip().isdigit()][:3]
        return Version(numbers + [0] * (3 - len(numbers)), suffix.strip())

    def __str__(self) -> str:
        text = ".".join(str(elem) for elem in self.numbers)
        return text + "-" + self.suffix if self.suffix != "" else text

    def release(self, bump: Bump) -> "Version":
        """The version released from this one: a version being developed (X.Y.Z-dev) is released as X.Y.Z at least."""
        major, minor, patch = self.numbers
        being_developed = self.suffix != ""
        if being_developed and (bump == "patch" or (bump == "minor" and patch == 0) or (bump == "major" and minor == 0 and patch == 0)):
            return Version([major, minor, patch])
        if bump == "major":
            return Version([major + 1, 0, 0])
        if bump == "minor":
            return Version([major, minor + 1, 0])
        return Version([major, minor, patch + 1])

    def next_dev(self, suffix: str = "dev") -> "Version":
        """The version developed after this release: the next patch, being developed (-dev, -SNAPSHOT for Maven)."""
        return Version([self.numbers[0], self.numbers[1], self.numbers[2] + 1], suffix)


def parse_bump(text: str | None) -> Bump | None:
    """Read a step of version given on the command line (None: none given or a wrong one)."""
    for bump in BUMPS:
        if text == bump:
            return bump
    return None


def suggest_bump(subjects: Sequence[str]) -> Bump:
    """Propose the step of a version from the subjects of the commits it delivers."""
    if any(re.match(r"\s*\[(API|BREAK)", subject) or "BREAKING" in subject for subject in subjects):
        return "major"
    if any(re.match(r"\s*\[FEAT", subject) for subject in subjects):
        return "minor"
    return "patch"


# ----------------------------------------------------------------------------------------------------
# check: what each project has to deliver
# ----------------------------------------------------------------------------------------------------


@dataclass
class DeliverPlan:
    """What a project delivers."""

    project: RepoConfig
    path: str
    remote: str
    source: str
    destination: str
    version: Version
    has_version_file: bool
    destination_exists: bool  # False: the first delivery creates it
    subjects: list[str] = field(default_factory=list)
    bump: Bump = "patch"
    pom: maven.Pom | None = None  # the pom of the source branch, for a Maven project
    # the version of each dependency of the workspace in the release (released versions only), then on the source branch
    dependency_pins: dict[str, str] = field(default_factory=dict)
    dev_dependencies: dict[str, str] = field(default_factory=dict)
    # a project never released with nothing new: delivered only when asked, or when a delivered project needs it
    unreleased: bool = False
    # never released: its version is the one it develops (a pom in 0.1.0 is released in 0.1.0 at first)
    first_release: bool = False

    @property
    def new_version(self) -> Version:
        if self.first_release and self.version.suffix == "" and self.version.numbers != [0, 0, 0]:
            return Version(self.version.numbers, "first").release(self.bump)
        return self.version.release(self.bump)

    @property
    def version_file(self) -> str:
        """Where the version is: version.txt, else the pom of a Maven project."""
        return VERSION_FILE if self.has_version_file or self.pom is None else maven.POM_FILE

    @property
    def dev_version(self) -> Version:
        """The version the source branch develops after the delivery."""
        return self.new_version.next_dev("dev" if self.version_file == VERSION_FILE else "SNAPSHOT")

    @property
    def pom_dev_version(self) -> str:
        return str(self.new_version.next_dev("SNAPSHOT"))

    @property
    def tag(self) -> str:
        return "v" + str(self.new_version)

    @property
    def current(self) -> str:
        """The version before the delivery, as the plan shows it."""
        if self.has_version_file is False and self.pom is None:
            return "new " + VERSION_FILE
        return str(self.version) + (" never released" if self.first_release else "")

    def describe(self) -> str:
        text = f"{self.current} -> {self.new_version} ({self.bump}), {len(self.subjects)} commit{'s' if len(self.subjects) > 1 else ''}"
        if self.destination_exists is False:
            text += ", creates " + self.destination
        if len(self.dependency_pins) != 0:
            text += ", with " + ", ".join(f"{key.split(':')[-1]} {version}" for key, version in self.dependency_pins.items())
        return text


def check_project(elem: RepoConfig, source: str, destination: str, extra_subjects: Sequence[str] = ()) -> tuple[ProjectResult, DeliverPlan | None]:
    """Tell what a project has to deliver from its source branch to its destination one (after a fetch).

    :param extra_subjects: What the project delivers besides its commits (the manifest: the projects it pins anew)
    """
    path = os.path.join(env.get_island_root_path(), elem.path)
    if elem.volatile is True:
        return ProjectResult(Status.SKIPPED, "volatile", "not managed by the manifest"), None
    if os.path.exists(path) is False:
        return ProjectResult(Status.WARNING, "missing", "not downloaded (island sync)"), None
    if os.path.exists(os.path.join(path, ".git")) is False:
        return ProjectResult(Status.ERROR, "error", "the folder is not a git repository"), None
    remote = elem.select_remote["name"]
    ret = _git(path, "fetch", "--tags", remote)
    if ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", "fetch: " + _last_line(ret)), None
    if commands.get_current_branch(path) is None:
        return ProjectResult(Status.SKIPPED, "empty", "no commit"), None

    remote_source = f"{remote}/{source}"
    remote_destination = f"{remote}/{destination}"
    local_source = _ref_exists(path, source)
    if local_source is False and _ref_exists(path, remote_source) is False:
        return ProjectResult(Status.SKIPPED, "no " + source, f"no branch {source}: nothing is developed apart"), None
    source_ref = source if local_source else remote_source
    if local_source and _ref_exists(path, remote_source):
        behind = commands.count_commits(path, source, remote_source)
        if behind != 0:
            return ProjectResult(Status.ERROR, "behind", f"{source} is {behind} behind {remote_source}: island sync first"), None
    local_destination = _ref_exists(path, destination)
    destination_ref: str | None = None
    if _ref_exists(path, remote_destination):
        destination_ref = remote_destination
        if local_destination:
            behind = commands.count_commits(path, destination, remote_destination)
            if behind != 0:
                return ProjectResult(Status.ERROR, "behind", f"{destination} is {behind} behind {remote_destination}: update it first"), None
            destination_ref = destination
    elif local_destination:
        destination_ref = destination
    if destination_ref is not None:
        apart = commands.count_commits(path, source_ref, destination_ref)
        if apart != 0:
            return ProjectResult(
                Status.ERROR,
                "diverged",
                f"{destination} has {apart} commit{'s' if apart > 1 else ''} that {source} has not: merge it in {source} first",
            ), None

    subjects = [subject for subject in _subjects(path, destination_ref, source_ref) if is_island_commit(subject) is False] + list(extra_subjects)
    pom = None
    pom_text = _git(path, "show", f"{source_ref}:{maven.POM_FILE}")
    if pom_text.returncode == 0:
        try:
            pom = maven.parse_pom(pom_text.stdout)
        except ValueError as ex:
            return ProjectResult(Status.ERROR, "error", f"{maven.POM_FILE}: {ex}"), None
    version_text = _git(path, "show", f"{source_ref}:{VERSION_FILE}")
    # version.txt first, else the pom of a Maven project
    version_source = version_text.stdout if version_text.returncode == 0 else (pom.version if pom is not None else "")
    version = Version.parse(version_source)
    known = version_text.returncode == 0 or pom is not None
    first_release = release_tag(path, remote, destination) is None
    unreleased = len(subjects) == 0 and first_release
    if len(subjects) == 0 and unreleased is False:
        return ProjectResult(Status.OK, "up to date", f"{version if known else 'no ' + VERSION_FILE}, nothing to deliver"), None
    if commands.check_repository_is_modify(path) is True:
        if unreleased:
            return ProjectResult(Status.WARNING, "unreleased", "never released, local changes: it can not be delivered now"), None
        return ProjectResult(Status.ERROR, "modified", "local changes: commit or stash them first"), None
    if unreleased:
        subjects = ["first release"]
    plan = DeliverPlan(
        project=elem,
        path=path,
        remote=remote,
        source=source,
        destination=destination,
        version=version,
        has_version_file=version_text.returncode == 0,
        destination_exists=destination_ref is not None,
        subjects=subjects,
        bump=suggest_bump(subjects),
        pom=pom,
        unreleased=unreleased,
        first_release=first_release,
    )
    error = check_tag(plan)
    if error is not None:
        return error, None
    if unreleased:
        return ProjectResult(Status.OK, "unreleased", f"{version if known else 'no ' + VERSION_FILE}, never released"), plan
    return ProjectResult(Status.CHANGED, "to deliver", plan.describe()), plan


def check_tag(plan: DeliverPlan) -> ProjectResult | None:
    """Refuse a version whose tag exists already, here or on the server (the fetch took the tags)."""
    if _ref_exists(plan.path, "refs/tags/" + plan.tag):
        return ProjectResult(Status.ERROR, "tag exists", f"{plan.tag} exists already: raise the version of {plan.version_file} in {plan.source}")
    return None


def check_all(
    projects: Sequence[RepoConfig], source: str, destination: str, action: str = "deliver-check", extra_subjects: Sequence[str] = ()
) -> list[tuple[RepoConfig, ProjectResult, DeliverPlan | None]]:
    """Check the projects several at a time.

    :return: for each project, its result and its plan (None: nothing it can deliver)
    """
    plans: dict[int, DeliverPlan] = {}

    def job(elem: RepoConfig) -> ProjectResult:
        result, plan = check_project(elem, source, destination, extra_subjects)
        if plan is not None:
            plans[id(elem)] = plan
        return result

    results = parallel.run_on_projects(action, projects, job)
    return [(elem, result, plans.get(id(elem))) for elem, result in zip(projects, results, strict=True)]


def check_projects(
    projects: Sequence[RepoConfig], source: str, destination: str, action: str = "deliver-check", extra_subjects: Sequence[str] = ()
) -> tuple[list[DeliverPlan], bool]:
    """Check the projects several at a time.

    :return: the plans of the projects to deliver (the never released ones too), and True when a project is in error
    """
    checked = check_all(projects, source, destination, action, extra_subjects)
    return [plan for _, _, plan in checked if plan is not None], any(result.status is Status.ERROR for _, result, _ in checked)


# ----------------------------------------------------------------------------------------------------
# manifest: the release of each project it pins
# ----------------------------------------------------------------------------------------------------


def release_tag(path: str, remote: str, destination: str) -> str | None:
    """The last release (tag v*) of the destination branch, local first, else on the server."""
    for ref in (destination, f"{remote}/{destination}"):
        if _ref_exists(path, ref):
            ret = _git(path, "describe", "--tags", "--abbrev=0", "--match", "v*", ref)
            return ret.stdout if ret.returncode == 0 else None
    return None


def pin_projects(projects: Sequence[RepoConfig], destination: str) -> tuple[list[dict[str, str]], bool]:
    """Find the release each project is pinned on, several at a time.

    :return: the pins ({"name", "tag"}), and True when a project is in error
    """
    pins: dict[int, dict[str, str]] = {}

    def job(elem: RepoConfig) -> ProjectResult:
        path = os.path.join(env.get_island_root_path(), elem.path)
        if elem.volatile is True:
            return ProjectResult(Status.SKIPPED, "volatile", "not managed by the manifest")
        if os.path.exists(os.path.join(path, ".git")) is False:
            return ProjectResult(Status.WARNING, "not pinned", "not downloaded (island sync)")
        tag = release_tag(path, elem.select_remote["name"], destination)
        if tag is None:
            return ProjectResult(Status.WARNING, "not pinned", f"no release on {destination}: follows its branch")
        pins[id(elem)] = {"name": elem.name, "tag": tag}
        if tag not in commands.get_tags_remote(path, elem.select_remote["name"]):
            return ProjectResult(Status.WARNING, "pinned", f"{tag}, not on the server yet: island deliver-push")
        return ProjectResult(Status.OK, "pinned", tag)

    results = parallel.run_on_projects("manifest-pins", projects, job)
    return [pins[id(elem)] for elem in projects if id(elem) in pins], parallel.has_error(results)


def pin_changes(manifest_elem: RepoConfig, destination: str, manifest_name: str, pins: Sequence[dict[str, str]]) -> list[str]:
    """What the pins change against the last release of the manifest, one line per project."""
    path = os.path.join(env.get_island_root_path(), manifest_elem.path)
    previous: dict[str, str] = {}
    for ref in (destination, f"{manifest_elem.select_remote['name']}/{destination}"):
        ret = _git(path, "show", f"{ref}:{manifest_name}")
        if ret.returncode == 0:
            root = etree.fromstring(ret.stdout.encode())
            previous = {str(node.get("name")): str(node.get("tag")) for node in root.iter("project") if node.get("tag") is not None}
            break
    return [f"pin {pin['name']} {previous.get(pin['name'], 'unpinned')} -> {pin['tag']}" for pin in pins if previous.get(pin["name"]) != pin["tag"]]


# ----------------------------------------------------------------------------------------------------
# Maven: the dependencies between the projects of the workspace
# ----------------------------------------------------------------------------------------------------


@dataclass
class MavenProject:
    """A project of the workspace that has a pom, as it is developed."""

    project: RepoConfig
    path: str
    pom: maven.Pom
    branch: str  # the branch it is developed on: the source branch, else its current branch
    ref: str  # where its pom is read: that branch, local or on the server
    release: str | None  # its last release on the destination branch (without the v)
    destination_ref: str | None


def read_workspace(projects: Sequence[RepoConfig], source: str, destination: str) -> tuple[dict[str, MavenProject], list[str]]:
    """Read the pom of each project of the workspace on the branch it is developed on.

    :return: the Maven projects by key (groupId:artifactId), and the errors (a pom island can not read, a cycle)
    """
    workspace: dict[str, MavenProject] = {}
    errors: list[str] = []
    for elem in projects:
        path = os.path.join(env.get_island_root_path(), elem.path)
        if elem.volatile is True or os.path.exists(os.path.join(path, ".git")) is False:
            continue
        current = commands.get_current_branch(path)
        if current is None:
            continue
        remote = elem.select_remote["name"]
        if _ref_exists(path, source):
            branch, ref = source, source
        elif _ref_exists(path, f"{remote}/{source}"):
            branch, ref = source, f"{remote}/{source}"
        else:
            branch, ref = current, current
        ret = _git(path, "show", f"{ref}:{maven.POM_FILE}")
        if ret.returncode != 0:
            continue
        try:
            pom = maven.parse_pom(ret.stdout)
        except ValueError as ex:
            errors.append(f"{parallel.project_name(elem)}: {maven.POM_FILE}: {ex}")
            continue
        destination_ref = next((name for name in (destination, f"{remote}/{destination}") if _ref_exists(path, name)), None)
        tag = release_tag(path, remote, destination)
        workspace[pom.key] = MavenProject(elem, path, pom, branch, ref, None if tag is None else tag.removeprefix("v"), destination_ref)
    try:
        maven.dependency_order({key: [dependency.key for dependency in info.pom.dependencies] for key, info in workspace.items()})
    except ValueError as ex:
        errors.append(str(ex))
    return workspace, errors


@dataclass
class Chain:
    """What the dependencies between the projects ask of a delivery."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # the projects not delivered that follow the new versions of their dependencies: key -> {dependency key: version}
    follows: dict[str, dict[str, str]] = field(default_factory=dict)
    # the projects a delivered project needs (never released, or with commits to deliver), and which projects need them
    added: list[DeliverPlan] = field(default_factory=list)
    needed_by: dict[str, list[str]] = field(default_factory=dict)


def _artifact(key: str) -> str:
    return key.split(":")[-1]


def _pending_commits(info: MavenProject) -> int:
    """The commits of a project not delivered yet (island's own ones apart)."""
    return len([subject for subject in _subjects(info.path, info.destination_ref, info.ref) if is_island_commit(subject) is False])


def _released_dependencies(info: MavenProject, version: str, cache: dict[tuple[str, str], dict[str, str]]) -> dict[str, str]:
    """The dependencies of the workspace of a release of a project, as its pom gives them."""
    if (info.pom.key, version) not in cache:
        ret = _git(info.path, "show", f"v{version}:{maven.POM_FILE}")
        dependencies: dict[str, str] = {}
        if ret.returncode == 0:
            try:
                dependencies = {dependency.key: dependency.version for dependency in maven.parse_pom(ret.stdout).dependencies}
            except ValueError:
                dependencies = {}
        cache[(info.pom.key, version)] = dependencies
    return cache[(info.pom.key, version)]


def chain_plans(plans: Sequence[DeliverPlan], workspace: Mapping[str, MavenProject], optional: Mapping[str, DeliverPlan] | None = None) -> Chain:
    """Set the versions of the dependencies of each delivered project, and check the delivery holds together.

    A release depends on releases only: the one delivered with it, else the last one of the dependency, which
    must have nothing left to deliver. On the source branch a project depends on the version its dependencies
    develop (-SNAPSHOT): the projects not delivered follow the new ones.

    :param optional: The plans of the projects not asked for, by key: one a delivered project needs joins Chain.added
    """
    optional = optional or {}
    chain = Chain()
    planned = {plan.pom.key: plan for plan in plans if plan.pom is not None}

    def dev_version(key: str) -> str:
        return planned[key].pom_dev_version if key in planned else workspace[key].pom.version

    for key, plan in planned.items():
        assert plan.pom is not None
        plan.dependency_pins.clear()
        plan.dev_dependencies.clear()
        name = parallel.project_name(plan.project)
        for dependency in plan.pom.dependencies:
            if dependency.key not in workspace or dependency.key == key:
                continue
            info = workspace[dependency.key]
            dependency_name = parallel.project_name(info.project)
            if info.project.private and plan.project.private is False:
                chain.errors.append(f"{name} is public and depends on {dependency_name}, which is private")
            if dependency.key in planned:
                pin = str(planned[dependency.key].new_version)
            elif dependency.key in optional:
                if optional[dependency.key] not in chain.added:
                    chain.added.append(optional[dependency.key])
                chain.needed_by.setdefault(dependency_name, []).append(name)
                continue
            elif info.release is None:
                chain.errors.append(f"{name} depends on {dependency_name}, which has no release: deliver it too")
                continue
            else:
                pending = _pending_commits(info)
                if pending != 0:
                    chain.errors.append(
                        f"{name} depends on {dependency_name}, which has {pending} commit{'s' if pending > 1 else ''} to deliver: deliver it too"
                    )
                pin = info.release
            plan.dependency_pins[dependency.key] = pin
            plan.dev_dependencies[dependency.key] = dev_version(dependency.key)
    for key, info in workspace.items():
        if key in planned:
            continue
        changes = {
            dependency.key: dev_version(dependency.key)
            for dependency in info.pom.dependencies
            if dependency.key in planned and dependency.version != dev_version(dependency.key)
        }
        if len(changes) == 0:
            continue
        if commands.check_repository_is_modify(info.path):
            chain.errors.append(
                f"{parallel.project_name(info.project)} has local changes: it can not follow {', '.join(_artifact(name) for name in changes)}"
            )
        chain.follows[key] = changes
    chain.warnings.extend(_divergences(planned, workspace))
    return chain


def _divergences(planned: Mapping[str, DeliverPlan], workspace: Mapping[str, MavenProject]) -> list[str]:
    """Tell a release that would pull two versions of the same project of the workspace."""
    warnings = []
    cache: dict[tuple[str, str], dict[str, str]] = {}
    for key, plan in planned.items():
        if plan.project.private:
            continue
        versions: dict[str, dict[str, str]] = {}  # dependency key -> version -> through which project
        todo = [(dependency, version, _artifact(key)) for dependency, version in plan.dependency_pins.items()]
        seen = set()
        while todo:
            dependency, version, through = todo.pop()
            versions.setdefault(dependency, {}).setdefault(version, through)
            if (dependency, version) in seen or dependency not in workspace:
                continue
            seen.add((dependency, version))
            if dependency in planned and str(planned[dependency].new_version) == version:
                below = planned[dependency].dependency_pins
            else:
                below = _released_dependencies(workspace[dependency], version, cache)
            todo.extend((name, below_version, _artifact(dependency)) for name, below_version in below.items() if name in workspace)
        for dependency, found in sorted(versions.items()):
            if len(found) > 1:
                detail = ", ".join(f"{version} through {through}" for version, through in sorted(found.items()))
                warnings.append(
                    f"{parallel.project_name(plan.project)} {plan.new_version} pulls {_artifact(dependency)} in several versions: {detail}"
                )
    return warnings


def chain_and_complete(plans: list[DeliverPlan], workspace: Mapping[str, MavenProject], optional: Mapping[str, DeliverPlan]) -> Chain:
    """Chain the plans, adding to them the projects they need (never released, or with commits to deliver), until none is missing."""
    needed_by: dict[str, list[str]] = {}
    while True:
        chain = chain_plans(plans, workspace, optional)
        for name, needers in chain.needed_by.items():
            needed_by.setdefault(name, []).extend(needer for needer in needers if needer not in needed_by.get(name, []))
        if len(chain.added) == 0:
            chain.needed_by = needed_by
            return chain
        plans.extend(plan for plan in chain.added if plan not in plans)


def follow_projects(workspace: Mapping[str, MavenProject], chain: Chain) -> bool:
    """Commit, on the branch each project is developed on, the new versions of its dependencies.

    :return: True when a project failed
    """
    followers = {id(workspace[key].project): (workspace[key], changes) for key, changes in chain.follows.items()}
    if len(followers) == 0:
        return False

    def job(elem: RepoConfig) -> ProjectResult:
        info, changes = followers[id(elem)]
        original_branch = commands.get_current_branch(info.path) or info.branch
        text = ", ".join(f"{_artifact(name)} {version}" for name, version in changes.items())
        try:
            if _ref_exists(info.path, info.branch) is False:
                _git_or_fail(info.path, "follow", "branch", "--track", info.branch, info.ref)
            _git_or_fail(info.path, "follow", "checkout", "--quiet", info.branch)
            maven.write_versions(info.path, None, changes)
            _git_or_fail(info.path, "follow", "add", maven.POM_FILE)
            _git_or_fail(info.path, "follow", "commit", "--quiet", "--message", FOLLOW_PREFIX + text)
        except (DeliverError, ValueError) as ex:
            _git(info.path, "checkout", "--quiet", original_branch)
            return ProjectResult(Status.ERROR, "error", str(ex))
        _git(info.path, "checkout", "--quiet", original_branch)
        return ProjectResult(Status.CHANGED, "follows", f"{text} on {info.branch}")

    return parallel.has_error(parallel.run_on_projects("follow", [info.project for info, _ in followers.values()], job))


# ----------------------------------------------------------------------------------------------------
# plan: shown, then accepted (or changed) once
# ----------------------------------------------------------------------------------------------------


def _ask(question: str) -> str:
    try:
        return input(question).strip().lower()
    except EOFError:
        return ""


def confirm_plans(
    plans: list[DeliverPlan], forced_bump: Bump | None, assume_yes: bool, validate: Callable[[list[DeliverPlan]], Chain] | None = None
) -> tuple[list[DeliverPlan], Chain]:
    """Show the plan and ask to go on; [e]dit asks the step of each project.

    :param validate: Checks the plan (the dependencies between the projects) each time it is shown
    :return: the plans to deliver (none when the user stops or the plan is wrong), and what the check found
    """
    if forced_bump is not None:
        for plan in plans:
            plan.bump = forced_bump
    while True:
        chain = validate(plans) if validate is not None else Chain()
        width = max(len(parallel.project_name(plan.project)) for plan in plans)
        print(f"Deliver {len(plans)} project{'s' if len(plans) > 1 else ''}:")
        for plan in plans:
            print(f"    {parallel.project_name(plan.project):<{width}}  {plan.describe()}")
        for name, needers in sorted(chain.needed_by.items()):
            print(f"Added, needed by {', '.join(needers)}: {name}")
        if len(chain.follows) != 0:
            print("Then follow the new versions on the branch they are developed on:")
            print("    " + ", ".join(sorted(_artifact(key) for key in chain.follows)))
        for warning in chain.warnings:
            print("Warning: " + warning)
        for error in chain.errors:
            print("Error: " + error)
        if len(chain.errors) != 0 and assume_yes is True:
            print("Delivery stopped: nothing changed.")
            return [], chain
        if assume_yes is True:
            return plans, chain
        if len(chain.errors) != 0:
            answer = _ask("The plan can not be delivered: [e]dit the versions, [n]o: ")
        else:
            answer = _ask("Deliver them? [y]es, [n]o, [e]dit the versions: ")
        if answer in ("y", "yes", "o", "oui") and len(chain.errors) == 0:
            return plans, chain
        if answer in ("e", "edit"):
            plans = edit_plans(plans)
            if len(plans) == 0:
                print("Nothing to deliver.")
                return [], Chain()
            continue
        print("Delivery canceled (nothing changed; --yes delivers without asking).")
        return [], Chain()


def edit_plans(plans: list[DeliverPlan]) -> list[DeliverPlan]:
    """Ask the step of each project: Enter keeps the proposal, s(kip) leaves the project out."""
    kept = []
    for plan in plans:
        print(f"{parallel.project_name(plan.project)} {plan.current}:")
        for subject in plan.subjects[-15:]:
            print("    " + subject)
        if len(plan.subjects) > 15:
            print(f"    ... and {len(plan.subjects) - 15} older")
        skip = False
        while True:
            choices = "/".join(bump.upper() if bump == plan.bump else bump for bump in BUMPS)
            answer = _ask(f"    version {choices}/skip (Enter: {plan.bump} -> {plan.new_version}): ")
            if answer == "":
                break
            match = [bump for bump in BUMPS if bump.startswith(answer)]
            if len(match) == 1:
                plan.bump = match[0]
                break
            if "skip".startswith(answer):
                skip = True
                break
        if skip:
            continue
        error = check_tag(plan)
        if error is not None:
            print("    " + error.message + ": left out")
            continue
        kept.append(plan)
    return kept


# ----------------------------------------------------------------------------------------------------
# delivery of a project
# ----------------------------------------------------------------------------------------------------


def _write_version(plan: DeliverPlan, dev: bool, step: str, hook: Callable[[str], None] | None) -> None:
    """Write the version of the release (or of the source branch after it) in version.txt and in the pom."""
    if plan.has_version_file or plan.pom is None:
        version = plan.new_version.next_dev() if dev else plan.new_version
        tools.file_write_data(os.path.join(plan.path, VERSION_FILE), str(version) + "\n")
        _git_or_fail(plan.path, step, "add", VERSION_FILE)
    if plan.pom is not None:
        try:
            if dev:
                maven.write_versions(plan.path, plan.pom_dev_version, plan.dev_dependencies)
            else:
                maven.write_versions(plan.path, str(plan.new_version), plan.dependency_pins)
        except ValueError as ex:
            raise DeliverError(f"{step}: {maven.POM_FILE}: {ex}") from ex
    if hook is not None:
        hook(plan.path)
    if commands.call_island_release_script(plan.path):
        debug.info("release script of " + plan.path + " done")
    _git_or_fail(plan.path, step, "add", "--update")


def deliver_project(
    plan: DeliverPlan,
    merge_mode: str,
    on_release: Callable[[str], None] | None = None,
    on_dev: Callable[[str], None] | None = None,
) -> ProjectResult:
    """Deliver a project as its plan says; on a failure, put the repository back on its branch and tell where it stopped.

    :param merge_mode: "merge" (a merge commit) or "fast_forward"
    :param on_release: Called in the folder of the project before the release commit (the manifest pins its projects)
    :param on_dev: Called before the commit of the next version on the source branch
    """
    path = plan.path
    original_branch = commands.get_current_branch(path) or plan.source
    release = plan.new_version
    step = "start"
    try:
        step = "prepare the branches"
        if _ref_exists(path, plan.source) is False:
            _git_or_fail(path, step, "branch", "--track", plan.source, f"{plan.remote}/{plan.source}")
        if plan.destination_exists and _ref_exists(path, plan.destination) is False:
            _git_or_fail(path, step, "branch", "--track", plan.destination, f"{plan.remote}/{plan.destination}")
        step = "merge " + plan.source + " in " + plan.destination
        if plan.destination_exists:
            _git_or_fail(path, step, "checkout", "--quiet", plan.destination)
            if merge_mode == "merge":
                ret = _git(path, "merge", "--no-ff", plan.source, "--message", f"Merge branch '{plan.source}' into '{plan.destination}'")
            else:
                ret = _git(path, "merge", "--ff-only", plan.source)
            if ret.returncode != 0:
                _git(path, "merge", "--abort")
                raise DeliverError(f"{step}: {_last_line(ret)}")
        else:
            _git_or_fail(path, step, "checkout", "--quiet", "-b", plan.destination, plan.source)
        step = "release " + str(release)
        _write_version(plan, False, step, on_release)
        # the release commit may change nothing (a first release in the version of the pom): it carries the tag all the same
        _git_or_fail(path, step, "commit", "--quiet", "--allow-empty", "--message", f"[RELEASE] Release v{release}")
        _git_or_fail(path, step, "tag", "--annotate", plan.tag, "--message", f"[TAG] create tag {plan.tag}")
        step = "bring " + plan.source + " to the release"
        _git_or_fail(path, step, "checkout", "--quiet", plan.source)
        _git_or_fail(path, step, "merge", "--ff-only", plan.destination)
        step = "start " + str(plan.dev_version)
        _write_version(plan, True, step, on_dev)
        _git_or_fail(path, step, "commit", "--quiet", "--message", DEV_VERSION_MESSAGES[0])
    except DeliverError as ex:
        _git(path, "checkout", "--quiet", original_branch)
        return ProjectResult(Status.ERROR, "error", f"{ex} (stopped there, nothing pushed)")
    _git(path, "checkout", "--quiet", original_branch)
    return ProjectResult(Status.CHANGED, "delivered", f"{plan.tag} on {plan.destination}, {plan.source} at {plan.dev_version}")


def deliver_plans(
    plans: Sequence[DeliverPlan],
    merge_mode: str,
    action: str = "deliver",
    hooks: dict[int, tuple[Callable[[str], None], Callable[[str], None]]] | None = None,
) -> bool:
    """Deliver the plans several at a time.

    :return: True when a project failed
    """
    by_project = {id(plan.project): plan for plan in plans}
    hooks = hooks or {}

    def job(elem: RepoConfig) -> ProjectResult:
        plan = by_project[id(elem)]
        on_release, on_dev = hooks.get(id(elem), (None, None))
        return deliver_project(plan, merge_mode, on_release, on_dev)

    return parallel.has_error(parallel.run_on_projects(action, [plan.project for plan in plans], job))


# ----------------------------------------------------------------------------------------------------
# push of the deliveries
# ----------------------------------------------------------------------------------------------------


def push_project(elem: RepoConfig, branches: Sequence[str], remote: str | None = None) -> ProjectResult:
    """Push a delivery: the branches ahead of the server, and the tags of the destination branch the server has not.

    :param branches: The destination branch first, then the source one
    """
    path = os.path.join(env.get_island_root_path(), elem.path)
    if elem.volatile is True:
        return ProjectResult(Status.SKIPPED, "volatile", "not managed by the manifest")
    if os.path.exists(os.path.join(path, ".git")) is False:
        return ProjectResult(Status.WARNING, "missing", "not downloaded (island sync)")
    if commands.get_current_branch(path) is None:
        return ProjectResult(Status.SKIPPED, "empty", "no commit")
    remote = remote or elem.select_remote["name"]
    ret = _git(path, "fetch", remote)
    if ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", "fetch: " + _last_line(ret))
    to_push: list[str] = []
    for branch in branches:
        if _ref_exists(path, branch) is False:
            continue
        remote_branch = f"{remote}/{branch}"
        if _ref_exists(path, remote_branch) is False:
            to_push.append(branch)
            continue
        behind = commands.count_commits(path, branch, remote_branch)
        if behind != 0:
            return ProjectResult(Status.ERROR, "behind", f"{branch} is {behind} behind {remote_branch}: nothing pushed")
        if commands.count_commits(path, remote_branch, branch) != 0:
            to_push.append(branch)
    remote_tags = set(commands.get_tags_remote(path, remote))
    tags: list[str] = []
    if _ref_exists(path, branches[0]):
        merged = _git(path, "tag", "--merged", branches[0]).stdout.split("\n")
        tags = [tag for tag in merged if tag != "" and tag not in remote_tags]
    # a delivery is a release branch or a tag the server has not, or the commits island made (versions followed):
    # the work in progress of the source branch alone is not pushed
    if len(tags) == 0 and branches[0] not in to_push:
        island_only = [
            branch
            for branch in to_push
            if _ref_exists(path, f"{remote}/{branch}") and all(is_island_commit(subject) for subject in _subjects(path, f"{remote}/{branch}", branch))
        ]
        if len(island_only) == 0:
            return ProjectResult(Status.OK, "up to date", "no delivery to push")
        to_push = island_only
    to_push.extend(tags)
    ret = _git(path, "push", "--set-upstream", remote, *to_push)
    if ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", "push: " + _last_line(ret))
    return ProjectResult(Status.CHANGED, "pushed", ", ".join(to_push))


def push_projects(projects: Sequence[RepoConfig], branches: Sequence[str], remote: str | None = None, action: str = "deliver-push") -> bool:
    """Push the deliveries of the projects several at a time.

    :param branches: The destination branch first (its tags are pushed), then the source one
    :return: True when a project failed
    """
    return parallel.has_error(parallel.run_on_projects(action, projects, lambda elem: push_project(elem, branches, remote)))
