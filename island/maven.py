"""Maven projects of the workspace: their pom.xml, and the dependencies between them.

The pom is read with lxml, and changed line by line where lxml found the element: the layout, the
comments and the indentation of the file stay as they are.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import os

from lxml import etree


POM_FILE = "pom.xml"
_NAMESPACE = "{http://maven.apache.org/POM/4.0.0}"


@dataclass
class Dependency:
    """A dependency of a pom: its key (groupId:artifactId), its version, and the line of the version."""

    key: str
    version: str
    line: int


@dataclass
class Pom:
    """What island reads of a pom: its key, its version and its dependencies (in dependencies, not in dependencyManagement)."""

    key: str
    version: str
    version_line: int
    dependencies: list[Dependency] = field(default_factory=list)


def _child(node: etree._Element, name: str) -> etree._Element | None:
    found = node.find(_NAMESPACE + name)
    return found if found is not None else node.find(name)


def _text(node: etree._Element, name: str) -> tuple[str, int]:
    child = _child(node, name)
    if child is None or child.text is None:
        return "", 0
    line = child.sourceline
    return child.text.strip(), line if isinstance(line, int) else 0


def parse_pom(content: str) -> Pom:
    """Read a pom from its content.

    :raise ValueError: on a pom island cannot read
    """
    try:
        root = etree.fromstring(content.encode())
    except etree.XMLSyntaxError as ex:
        raise ValueError(f"wrong pom: {ex}") from ex
    group, _ = _text(root, "groupId")
    parent = _child(root, "parent")
    if group == "" and parent is not None:
        group, _ = _text(parent, "groupId")
    artifact, _ = _text(root, "artifactId")
    version, version_line = _text(root, "version")
    if group == "" or artifact == "" or version == "":
        raise ValueError("the pom has no groupId, artifactId or version of its own")
    pom = Pom(f"{group}:{artifact}", version, version_line)
    dependencies = _child(root, "dependencies")
    for node in [] if dependencies is None else dependencies:
        if not isinstance(node.tag, str) or node.tag.removeprefix(_NAMESPACE) != "dependency":
            continue
        dep_group, _ = _text(node, "groupId")
        dep_artifact, _ = _text(node, "artifactId")
        dep_version, line = _text(node, "version")
        if dep_version != "":
            pom.dependencies.append(Dependency(f"{dep_group}:{dep_artifact}", dep_version, line))
    return pom


def read_pom(path: str) -> Pom | None:
    """Read the pom of a project folder (None: it has none)."""
    file = os.path.join(path, POM_FILE)
    if os.path.isfile(file) is False:
        return None
    with open(file) as handle:
        return parse_pom(handle.read())


def set_versions(content: str, version: str | None, dependencies: Mapping[str, str]) -> str:
    """Change the version of a pom and of some of its dependencies, nothing else of the file.

    :param version: The new version of the project (None: unchanged)
    :param dependencies: The new version of each dependency, by key (the others are unchanged)
    :return: the new content
    """
    pom = parse_pom(content)
    lines = content.split("\n")
    changes = []
    if version is not None and version != pom.version:
        changes.append((pom.version_line, pom.version, version))
    for dependency in pom.dependencies:
        new = dependencies.get(dependency.key)
        if new is not None and new != dependency.version:
            changes.append((dependency.line, dependency.version, new))
    for line, old, new in changes:
        text = lines[line - 1]
        if f">{old}<" not in text:
            raise ValueError(f"the version '{old}' is not alone on the line {line} of the pom: change it by hand")
        lines[line - 1] = text.replace(f">{old}<", f">{new}<", 1)
    return "\n".join(lines)


def write_versions(path: str, version: str | None, dependencies: Mapping[str, str]) -> None:
    """Change the version of the pom of a project folder and of some of its dependencies."""
    file = os.path.join(path, POM_FILE)
    with open(file) as handle:
        content = handle.read()
    new = set_versions(content, version, dependencies)
    if new != content:
        with open(file, "w") as handle:
            handle.write(new)


def dependency_order(dependencies: Mapping[str, Sequence[str]]) -> list[str]:
    """Order the projects so that each one comes after those it depends on.

    :param dependencies: The projects each project depends on, by project (the projects outside are ignored)
    :raise ValueError: on a cycle of dependencies
    """
    order: list[str] = []
    state: dict[str, str] = {}

    def visit(name: str, path: list[str]) -> None:
        if state.get(name) == "done":
            return
        if state.get(name) == "visiting":
            raise ValueError("cycle of dependencies: " + " -> ".join([*path, name]))
        state[name] = "visiting"
        for dependency in dependencies[name]:
            if dependency in dependencies:
                visit(dependency, [*path, name])
        state[name] = "done"
        order.append(name)

    for name in dependencies:
        visit(name, [])
    return order
