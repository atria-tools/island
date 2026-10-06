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

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import os
import re
import shlex
from typing import Literal

from lxml import etree
from realog import debug

from . import commands, env, multiprocess, parallel, tools
from .parallel import ProjectResult, Status
from .repo_config import RepoConfig


Bump = Literal["patch", "minor", "major"]
BUMPS: tuple[Bump, ...] = ("patch", "minor", "major")

# the subject of the commit that starts the next version on the source branch (the second one was used before)
DEV_VERSION_MESSAGES = ("[VERSION] update dev tag version", "[DEV] update dev tag version")
VERSION_FILE = "version.txt"


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

    def next_dev(self) -> "Version":
        """The version developed after this release: the next patch, being developed."""
        return Version([self.numbers[0], self.numbers[1], self.numbers[2] + 1], "dev")


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

    @property
    def new_version(self) -> Version:
        return self.version.release(self.bump)

    @property
    def tag(self) -> str:
        return "v" + str(self.new_version)

    def describe(self) -> str:
        current = str(self.version) if self.has_version_file else "new " + VERSION_FILE
        text = f"{current} -> {self.new_version} ({self.bump}), {len(self.subjects)} commit{'s' if len(self.subjects) > 1 else ''}"
        if self.destination_exists is False:
            text += ", creates " + self.destination
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

    subjects = [subject for subject in _subjects(path, destination_ref, source_ref) if subject not in DEV_VERSION_MESSAGES] + list(extra_subjects)
    version_text = _git(path, "show", f"{source_ref}:{VERSION_FILE}")
    version = Version.parse(version_text.stdout if version_text.returncode == 0 else "")
    if len(subjects) == 0:
        return ProjectResult(
            Status.OK, "up to date", f"{version if version_text.returncode == 0 else 'no ' + VERSION_FILE}, nothing to deliver"
        ), None
    if commands.check_repository_is_modify(path) is True:
        return ProjectResult(Status.ERROR, "modified", "local changes: commit or stash them first"), None
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
    )
    error = check_tag(plan)
    if error is not None:
        return error, None
    return ProjectResult(Status.CHANGED, "to deliver", plan.describe()), plan


def check_tag(plan: DeliverPlan) -> ProjectResult | None:
    """Refuse a version whose tag exists already, here or on the server (the fetch took the tags)."""
    if _ref_exists(plan.path, "refs/tags/" + plan.tag):
        return ProjectResult(Status.ERROR, "tag exists", f"{plan.tag} exists already: raise the version of {VERSION_FILE} in {plan.source}")
    return None


def check_projects(
    projects: Sequence[RepoConfig], source: str, destination: str, action: str = "deliver-check", extra_subjects: Sequence[str] = ()
) -> tuple[list[DeliverPlan], bool]:
    """Check the projects several at a time.

    :return: the plans of the projects to deliver, and True when a project is in error
    """
    plans: dict[int, DeliverPlan] = {}

    def job(elem: RepoConfig) -> ProjectResult:
        result, plan = check_project(elem, source, destination, extra_subjects)
        if plan is not None:
            plans[id(elem)] = plan
        return result

    results = parallel.run_on_projects(action, projects, job)
    return [plans[id(elem)] for elem in projects if id(elem) in plans], parallel.has_error(results)


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
# plan: shown, then accepted (or changed) once
# ----------------------------------------------------------------------------------------------------


def _ask(question: str) -> str:
    try:
        return input(question).strip().lower()
    except EOFError:
        return ""


def confirm_plans(plans: list[DeliverPlan], forced_bump: Bump | None, assume_yes: bool) -> list[DeliverPlan]:
    """Show the plan and ask to go on; [e]dit asks the step of each project.

    :return: the plans to deliver (none when the user stops)
    """
    if forced_bump is not None:
        for plan in plans:
            plan.bump = forced_bump
    while True:
        width = max(len(parallel.project_name(plan.project)) for plan in plans)
        print(f"Deliver {len(plans)} project{'s' if len(plans) > 1 else ''}:")
        for plan in plans:
            print(f"    {parallel.project_name(plan.project):<{width}}  {plan.describe()}")
        if assume_yes is True:
            return plans
        answer = _ask("Deliver them? [y]es, [n]o, [e]dit the versions: ")
        if answer in ("y", "yes", "o", "oui"):
            return plans
        if answer in ("e", "edit"):
            plans = edit_plans(plans)
            if len(plans) == 0:
                print("Nothing to deliver.")
                return []
            continue
        print("Delivery canceled (nothing changed; --yes delivers without asking).")
        return []


def edit_plans(plans: list[DeliverPlan]) -> list[DeliverPlan]:
    """Ask the step of each project: Enter keeps the proposal, s(kip) leaves the project out."""
    kept = []
    for plan in plans:
        print(f"{parallel.project_name(plan.project)} {plan.version if plan.has_version_file else '(new ' + VERSION_FILE + ')'}:")
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


def _write_version(plan: DeliverPlan, version: Version, step: str, hook: Callable[[str], None] | None) -> None:
    tools.file_write_data(os.path.join(plan.path, VERSION_FILE), str(version) + "\n")
    if hook is not None:
        hook(plan.path)
    if commands.call_island_release_script(plan.path):
        debug.info("release script of " + plan.path + " done")
    _git_or_fail(plan.path, step, "add", "--update")
    _git_or_fail(plan.path, step, "add", VERSION_FILE)


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
        _write_version(plan, release, step, on_release)
        _git_or_fail(path, step, "commit", "--quiet", "--message", f"[RELEASE] Release v{release}")
        _git_or_fail(path, step, "tag", "--annotate", plan.tag, "--message", f"[TAG] create tag {plan.tag}")
        step = "bring " + plan.source + " to the release"
        _git_or_fail(path, step, "checkout", "--quiet", plan.source)
        _git_or_fail(path, step, "merge", "--ff-only", plan.destination)
        step = "start " + str(release.next_dev())
        _write_version(plan, release.next_dev(), step, on_dev)
        _git_or_fail(path, step, "commit", "--quiet", "--message", DEV_VERSION_MESSAGES[0])
    except DeliverError as ex:
        _git(path, "checkout", "--quiet", original_branch)
        return ProjectResult(Status.ERROR, "error", f"{ex} (stopped there, nothing pushed)")
    _git(path, "checkout", "--quiet", original_branch)
    return ProjectResult(Status.CHANGED, "delivered", f"{plan.tag} on {plan.destination}, {plan.source} at {release.next_dev()}")


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
    # a delivery is a release branch or a tag the server has not: the work in progress of the source branch alone is not pushed
    if len(tags) == 0 and branches[0] not in to_push:
        return ProjectResult(Status.OK, "up to date", "no delivery to push")
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
