"""Manifest interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import copy
import os
from typing import NotRequired, TypedDict

from lxml import etree

# Local import
from realog import debug

# import pyyaml module
import yaml
from yaml.loader import SafeLoader

from . import (
    commands,
    config,
    env,
    multiprocess,
    repo_config,
)


def is_island_init() -> bool:
    if not os.path.exists(env.get_island_path()):
        debug.verbose(f"Island is not init: path does not exist: '{env.get_island_path()}'")
        return False
    if not os.path.exists(env.get_island_path_config()):
        debug.verbose(f"Island is not init: config does not exist: '{env.get_island_path_config()}'")
        return False
    if not os.path.exists(env.get_island_path_manifest()):
        debug.verbose(f"Island is not init: Manifest does not exist: '{env.get_island_path_manifest()}'")
        return False
    return True


def check_island_is_init() -> None:
    # check if .XXX exist (create it if needed)
    if not is_island_init():
        debug.error(f"System not init: missing config: '{env.get_island_path()}'. Call <island init> first")
        exit(-1)


def configure_all_repository(configuration: "config.Config", previous_config: dict[str, str]) -> int:
    """Apply the configuration of the workspace on all the downloaded repository (manifest included).

    :param configuration: Configuration of the workspace.
    :param previous_config: Git configuration previously set by island (removed if no more needed).
    :return: Number of repository configured.
    """
    list_path = [env.get_island_path_manifest()]
    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error(
            f"Missing manifest file : '{file_source_manifest}'",
            ret_value=env.ret_manifest_is_not_existing,
        )
    for elem in Manifest(file_source_manifest).get_all_configs():
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(os.path.join(git_repo_path, ".git")) is True:
            list_path.append(git_repo_path)
    new_config = commands.get_repository_config(configuration)
    to_remove = {key: value for key, value in previous_config.items() if key not in new_config}
    for path in list_path:
        commands.unset_local_config(path, to_remove)
        commands.set_local_config(path, new_config)
    return len(list_path)


class ProjectEntry(TypedDict):
    """A project as a manifest lists it."""

    name: str
    path: str  # "": the name of the repository
    tag: str | None
    private: NotRequired[bool]  # not published (a public repository of artifacts, Maven Central...)


class SubManifest(TypedDict):
    """A manifest that a manifest includes (xml) or imports (vcs .repos file)."""

    name: str
    path: str
    manifest: "_ManifestBase | None"


# the options of a manifest (the 'option' node)
ManifestDefault = TypedDict(
    "ManifestDefault",
    {
        "remote": str,
        "revision": str,  # todo: rename 'branch-release'
        "sync": bool,
        "branch-develop": str,
        "default-branch": str,
        "deliver-mode": NotRequired[str],
    },
)


class _ManifestBase:
    """What the manifests share: their projects and remotes, and the configurations of the projects."""

    def __init__(self, file: str) -> None:
        self.file = file
        self.projects: list[ProjectEntry] = []
        self.default: ManifestDefault | None = None
        self.default_base: ManifestDefault = {
            "remote": "origin",
            "revision": "master",
            "sync": False,
            "branch-develop": "dev",
            "default-branch": "dev",
        }
        self.remotes: list[repo_config.Remote] = []
        self.includes: list[SubManifest] = []
        self.imports: list[SubManifest] = []
        self.links: list[dict[str, str]] = []
        # the same defaults as an 'option' node that does not give them
        self.deliver_master = "master"
        self.deliver_develop = "dev"
        self.deliver_mode = "fast_forward"
        # load the manifest
        self._load()
        # check error in manifest (double path ...)
        self._check_double_path([])

    def _load(self) -> None:
        raise NotImplementedError

    def get_links(self) -> list[dict[str, str]]:
        return self.links

    def _create_path_with_elem(self, element: ProjectEntry) -> str:
        path = element["path"]
        if path == "":
            path = element["name"]
            if len(path) >= 4 and path[-4:] == ".git":
                path = path[:-4]
        return path

    def _check_double_path(self, list_path: list[str] | None = None, space: str = "") -> None:
        if list_path is None:
            list_path = []
        debug.debug(f"{space}check path : '{self.file}'")
        for elem in self.projects:
            path = self._create_path_with_elem(elem)
            debug.debug(f"{space}    check path:'{path}'")
            if path in list_path:
                debug.error(f"Check Manifest error : double use of the path '{path}'")
            list_path.append(path)
        for elem_include in self.includes:
            if elem_include["manifest"] is not None:
                elem_include["manifest"]._check_double_path(list_path, space + "    ")

    def get_all_configs(
        self, default: ManifestDefault | None = None, upper_remotes: list[repo_config.Remote] | None = None, use_filter: bool = True
    ) -> list[repo_config.RepoConfig]:
        """Get the configuration of every project: those of this manifest, of the manifests it includes or imports, and the volatile ones.

        :param default: Options of the parent manifest (None: this manifest is the top one)
        :param upper_remotes: Remotes of the parent manifests
        :param use_filter: Keep only the projects of the option --filter (False: all of them)
        :return: the configuration of each project
        """
        if upper_remotes is None:
            upper_remotes = []
        out: list[repo_config.RepoConfig] = []
        # the top manifest is called without default; the included ones get it from their parent
        is_top_manifest = default is None
        if default is None:
            default = copy.deepcopy(self.default) if self.default is not None else copy.deepcopy(self.default_base)
        # add all local project
        for elem in self.projects:
            debug.verbose(f"parse element {elem}")
            if use_filter and env.need_process_with_filter(elem["name"]) is False:
                debug.info(f"Filter repository: {elem['name']}")
                continue
            conf = repo_config.RepoConfig()
            conf.name = elem["name"]
            conf.tag = elem["tag"]
            conf.private = elem.get("private", False)
            conf.path = self._create_path_with_elem(elem)

            # add default remote for the project (search in inherited element)
            conf.remotes = [remote for remote in self.remotes if remote["name"] == default["remote"]]
            if len(conf.remotes) == 0:
                conf.remotes = [remote for remote in upper_remotes if remote["name"] == default["remote"]]
            if len(conf.remotes) == 0:
                debug.error(
                    f"    No remote detected: {len(conf.remotes)} for {conf.name} with default remote name : {default['remote']} self remote: {self.remotes}"
                )
                continue
            # select default remote, with the submodule synchronization of the manifest
            conf.select_remote = copy.deepcopy(conf.remotes[0])
            conf.select_remote["sync"] = default["sync"]
            debug.debug(f"    copy select={conf.select_remote}")
            conf.branch = default["default-branch"]
            out.append(conf)
        # create a temporary variable to transmit the remote to includes
        upper_remotes_forward = copy.deepcopy(upper_remotes) + self.remotes
        # add all include and import project
        for elem_sub in self.includes + self.imports:
            if elem_sub["manifest"] is not None:
                out.extend(elem_sub["manifest"].get_all_configs(default, upper_remotes_forward, use_filter))
        if is_top_manifest:
            out.extend(self._get_volatile_configs())
        return out

    def _get_volatile_configs(self) -> list[repo_config.RepoConfig]:
        """Get the configuration of the volatile projects: those the workspace adds to its manifest."""
        out = []
        for elem in config.get_unique_config().get_volatile():
            conf = repo_config.RepoConfig()
            base_volatile, repo_volatile = repo_config.split_repo(elem["git_address"])
            conf.name = repo_volatile
            conf.path = elem["path"]
            conf.branch = "master"
            conf.volatile = True
            conf.remotes = [{"name": "origin", "fetch": base_volatile, "mirror": []}]
            conf.select_remote = {"name": "origin", "fetch": base_volatile, "sync": False, "mirror": []}
            out.append(conf)
        return out


class ManifestVSC(_ManifestBase):
    """A vcs .repos file that a manifest imports: a list of repositories, fetched from the remotes of the manifest."""

    def _load(self) -> None:
        debug.debug(f"manifest VSC: '{self.file}'")
        with open(self.file) as f:
            data = yaml.load(f, Loader=SafeLoader)
        if "repositories" not in data:
            debug.error(f"in '{self.file}' VSC manifest: missing root key: repositories ")
        for name, value in data["repositories"].items():
            if "type" in value and value["type"] != "git":
                debug.error(f"in '{self.file}' VSC manifest: unsupported type: '{value['type']}' for {name}")
            if "url" not in value:
                debug.error(f"in '{self.file}' VSC manifest: missing 'url' for {name}")
            url = value["url"]
            # TODO: Manage URL remote element ==> dynamic add !!! and manage http(s)://xxx.yyy/*
            url_split = url.split(":")
            if len(url_split) > 1:
                url = url_split[-1]
            version = None
            if "version" in value:
                version = str(value["version"])
            self.projects.append(ProjectEntry(name=url, path=name, tag=version))


class Manifest(_ManifestBase):
    """A manifest in xml: remotes, options, projects, links, and other manifests included or imported."""

    def _load(self) -> None:
        debug.debug(f"manifest : '{self.file}'")
        tree = etree.parse(self.file)
        root = tree.getroot()
        if root.tag != "manifest":
            debug.error(f"(l:{root.sourceline}) in '{self.file}' have not main xml node='manifest'")
        for child in root:
            if isinstance(child, etree._Comment):
                debug.verbose(f"(l:{child.sourceline})     comment='{child.text}'")
                continue
            if child.tag == "remote":
                name = "origin"
                fetch = ""
                for attr in child.attrib:
                    if attr == "name":
                        name = str(child.attrib[attr])
                    elif attr == "fetch":
                        fetch = str(child.attrib[attr])
                        if len(fetch) >= 2 and fetch[:2] == "..":
                            # we have a relative island manifest ==> use local manifest origin to get the full origin
                            cmd = "git remote get-url origin"
                            debug.verbose(f"execute : {cmd}")
                            base_origin = multiprocess.run_command(cmd, cwd=env.get_island_path_manifest()).stdout
                            debug.verbose(f"base_origin={base_origin}")
                            while len(fetch) >= 2 and fetch[:2] == "..":
                                fetch = fetch[2:]
                                while len(fetch) >= 1 and (fetch[0] == "/" or fetch[0] == "\\"):
                                    fetch = fetch[1:]
                                offset_1 = base_origin.rfind("/")
                                offset_2 = base_origin.rfind(":")
                                base_origin = base_origin[:offset_1] if offset_1 > offset_2 else base_origin[:offset_2]
                            debug.verbose(f"new base_origin={base_origin}")
                            debug.verbose(f"tmp fetch={fetch}")
                            fetch = f"{base_origin}/{fetch}" if fetch != "" else base_origin
                            debug.verbose(f"new fetch={fetch}")
                        while len(fetch) > 1 and (fetch[-1] == "\\" or fetch[-1] == "/"):
                            fetch = fetch[:-1]
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr!s}', available:[name,fetch]"
                        )
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}' fetch='{fetch}'")
                # parse the sub global mirror list
                mirror_list: list[repo_config.Mirror] = []
                for child_2 in child:
                    if child_2.tag == "mirror":
                        # find a new mirror
                        mirror_name = ""
                        mirror_fetch = ""
                        for attr_2 in child_2.attrib:
                            if attr_2 == "name":
                                mirror_name = str(child_2.attrib[attr_2])
                            elif attr_2 == "fetch":
                                mirror_fetch = str(child_2.attrib[attr_2])
                                while len(mirror_fetch) > 1 and (mirror_fetch[-1] == "\\" or mirror_fetch[-1] == "/"):
                                    mirror_fetch = mirror_fetch[:-1]
                            else:
                                debug.error(
                                    f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child_2.tag}'  attribute : '{attr_2!s}', available:[name,fetch]"
                                )
                        debug.debug(f"mirror: '{mirror_name}' '{mirror_fetch}'")
                        if mirror_name == "":
                            debug.error(f"(l:{child_2.sourceline}) Missing mirror 'name'")
                        if mirror_fetch == "":
                            debug.error(f"(l:{child_2.sourceline}) Missing mirror 'fetch'")
                        mirror_list.append(repo_config.Mirror(name=mirror_name, fetch=mirror_fetch))
                    else:
                        debug.error(f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child_2.tag}', available:[mirror]")
                self.remotes.append(repo_config.Remote(name=name, fetch=fetch, mirror=mirror_list))
                continue

            if child.tag == "import":
                type_manifest = "vcs"
                name = ""
                for attr in child.attrib:
                    if attr == "type":
                        type_manifest = str(child.attrib[attr])
                        if type_manifest not in ["vcs"]:
                            debug.error(
                                f"(l:{child.sourceline}) Parsing the manifest: {child.tag} attribute '{attr}={type_manifest}' value available: [vcs]"
                            )
                    elif attr == "name":
                        name = str(child.attrib[attr])
                    else:
                        debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr!s}', available:[name]")
                new_name_yaml = os.path.join(os.path.dirname(self.file), name)
                if os.path.exists(new_name_yaml) is False:
                    debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_yaml}'")
                self.imports.append(SubManifest(name=name, path=new_name_yaml, manifest=None))
                continue
            if child.tag == "include":
                name = ""
                for attr in child.attrib:
                    if attr == "name":
                        name = str(child.attrib[attr])
                    else:
                        debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr!s}', available:[name]")
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
                # check if the file exist ...
                new_name_xml = os.path.join(os.path.dirname(self.file), name)
                if os.path.exists(new_name_xml) is False:
                    debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
                self.includes.append(SubManifest(name=name, path=new_name_xml, manifest=None))
                continue
            if child.tag == "option":
                remote = "origin"
                deliver_master = "master"
                sync = False
                deliver_source = "dev"
                default_branch = "dev"
                deliver_mode = "fast_forward"

                for child_2 in child:
                    if child_2.tag == "branch-release":
                        deliver_master = child_2.text or ""
                    elif child_2.tag == "branch-develop":
                        deliver_source = child_2.text or ""
                    elif child_2.tag == "default-branch":
                        default_branch = child_2.text or ""
                    elif child_2.tag == "default-remote":
                        remote = child_2.text or ""
                    elif child_2.tag == "deliver-mode":
                        deliver_mode = child_2.text or ""
                        if deliver_mode not in ["merge", "fast_forward"]:
                            debug.error(f"(l:{child.sourceline}) Parsing the manifest: option 'deliver-mode' value available: [merge,fast_forward]")
                    elif child_2.tag == "synchronize-submodule":
                        sync_tmp = child_2.text or ""
                        if sync_tmp.lower() == "true" or sync_tmp == "1" or sync_tmp.lower() == "yes":
                            sync = True
                        elif sync_tmp.lower() == "false" or sync_tmp == "0" or sync_tmp.lower() == "no":
                            sync = False
                        else:
                            debug.error(
                                f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child.tag}/{child_2.tag}', value:'{sync_tmp}' available:[true,1,yes,false,0,no]"
                            )
                    else:
                        debug.error(
                            f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child.tag}/{child_2.tag}', available:[branch-release,branch-develop,default-branch,default-remote,synchronize-submodule]"
                        )
                self.default = {
                    "remote": remote,
                    "revision": deliver_master,
                    "sync": sync,
                    "branch-develop": deliver_source,
                    "default-branch": default_branch,
                    "deliver-mode": deliver_mode,
                }
                self.deliver_master = deliver_master
                self.deliver_develop = deliver_source
                self.deliver_mode = deliver_mode
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}':")
                debug.debug(f"    - default-branch:'{default_branch}':")
                debug.debug(f"    - default-remote:'{remote}':")
                debug.debug(f"    - synchronize-submodule:'{sync}':")
                debug.debug(f"    - branch-release:'{deliver_master}':")
                debug.debug(f"    - branch-develop:'{deliver_source}':")
                debug.debug(f"    - deliver-mode:'{deliver_mode}':")
                continue
            if child.tag == "project":
                name = ""
                path = ""
                tag_sha1: str | None = None
                private = False
                for attr in child.attrib:
                    if attr == "name":
                        name = str(child.attrib[attr])
                    elif attr == "path":
                        path = str(child.attrib[attr])
                    elif attr == "tag":
                        tag_sha1 = str(child.attrib[attr])
                    elif attr == "private":
                        private = str(child.attrib[attr]).lower() in ("true", "1", "yes")
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr!s}', available:[name,path,tag,private]"
                        )
                if name == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'name' ==> specify the git to clone ..."
                    )
                self.projects.append(ProjectEntry(name=name, path=path, tag=tag_sha1, private=private))
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}' path='{path}' tag='{tag_sha1!s}'")
                continue
            if child.tag == "link":
                # not managed ==> future use
                source = ""
                destination = ""
                for attr in child.attrib:
                    if attr == "source":
                        source = str(child.attrib[attr])
                    elif attr == "destination":
                        destination = str(child.attrib[attr])
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr!s}', available:[source,destination]"
                        )
                if source == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'source' ==> specify the git to clone."
                    )
                if destination == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'destination' ==> specify the git to clone."
                    )
                self.links.append({"source": source, "destination": destination})
                debug.debug(f"Add link: '{destination}' ==> '{source}'")
                continue
            debug.info(f"(l:{child.sourceline})     '{child.tag}' values={child.attrib}")
            debug.error(f"(l:{child.sourceline}) Parsing error unknown NODE : '{child.tag}' available:[remote,include,default,project,option,link]")
        # now we parse all sub repo:
        for elem in self.includes:
            elem["manifest"] = Manifest(elem["path"])
        for elem in self.imports:
            elem["manifest"] = ManifestVSC(elem["path"])

        # inside data    child.text


def tag_manifest(manifest_xml_filename: str, all_tags: list[dict[str, str]]) -> bool | None:
    tree = etree.parse(manifest_xml_filename)
    debug.debug(f"manifest : '{manifest_xml_filename}'")
    root = tree.getroot()
    includes: list[SubManifest] = []
    if root.tag != "manifest":
        debug.error(f"(l:{root.sourceline}) in '{manifest_xml_filename}' have not main xml node='manifest'")
        return False
    for child in root:
        if isinstance(child, etree._Comment):
            debug.verbose(f"(l:{child.sourceline})     comment='{child.text}'")
            continue
        if child.tag == "remote":
            continue
        if child.tag == "include":
            name = ""
            for attr in child.attrib:
                if attr == "name":
                    name = str(child.attrib[attr])
                else:
                    debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr!s}', available:[name]")
            debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
            # check if the file exist ...
            new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename), name)
            if os.path.exists(new_name_xml) is False:
                debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
            includes.append(SubManifest(name=name, path=new_name_xml, manifest=None))
            continue
        if child.tag == "default":
            continue
        if child.tag == "project":
            name = ""
            for attr in child.attrib:
                if attr == "name":
                    name = str(child.attrib[attr])
                elif attr in ("path", "tag", "private"):
                    continue
                else:
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr!s}', available:[name,path,tag,private]"
                    )
            if name == "":
                debug.error(f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'name' ==> specify the git to clone.")
            for elem_tag in all_tags:
                if elem_tag["name"] == name:
                    child.set("tag", elem_tag["tag"])
            continue
        if child.tag in ("option", "link", "import"):
            # the imported .repos files have no tag
            continue
        debug.info(f"(l:{child.sourceline})     '{child.tag}' values={child.attrib}")
        debug.error(
            f"(l:{child.sourceline}) Parsing error unknown NODE : '{child.tag}' available:[remote,include,import,default,project,option,link]"
        )
    tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
    # now we parse all sub repo:
    for elem in includes:
        tag_manifest(elem["path"], all_tags)
    return None


def tag_clear(manifest_xml_filename: str) -> bool | None:
    tree = etree.parse(manifest_xml_filename)
    debug.debug(f"manifest : '{manifest_xml_filename}'")
    root = tree.getroot()
    includes: list[SubManifest] = []
    if root.tag != "manifest":
        debug.error(f"(l:{root.sourceline}) in '{manifest_xml_filename}' have not main xml node='manifest'")
        return False
    for child in root:
        if isinstance(child, etree._Comment):
            debug.verbose(f"(l:{child.sourceline})     comment='{child.text}'")
            continue
        if child.tag == "remote":
            continue
        if child.tag == "include":
            name = ""
            for attr in child.attrib:
                if attr == "name":
                    name = str(child.attrib[attr])
                else:
                    debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr!s}', available:[name]")
            debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
            # check if the file exist ...
            new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename), name)
            if os.path.exists(new_name_xml) is False:
                debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
            includes.append(SubManifest(name=name, path=new_name_xml, manifest=None))
            continue
        if child.tag == "default":
            continue
        if child.tag == "project":
            child.attrib.pop("tag", "")
            continue
        if child.tag in ("option", "link", "import"):
            continue
        debug.info(f"(l:{child.sourceline})     '{child.tag}' values={child.attrib}")
        debug.error(
            f"(l:{child.sourceline}) Parsing error unknown NODE : '{child.tag}' available:[remote,include,import,default,project,option,link]"
        )
    tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
    # now we parse all sub repo:
    for elem in includes:
        tag_clear(elem["path"])
    return None
