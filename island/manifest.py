#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Manifest interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""
import json
import copy
import os
from typing import List, Dict, Any

# import pyyaml module
import yaml
from yaml.loader import SafeLoader


from lxml import etree

# Local import
from realog import debug

from . import (
    config,
    env,
    multiprocess,
    repo_config,
)


def is_lutin_init():
    if os.path.exists(env.get_island_path()) is False:
        debug.verbose(f"Island is not init: path does not exist: '{env.get_island_path()}'")
        return False
    if os.path.exists(env.get_island_path_config()) is False and os.path.exists(env.get_island_path_config_old()) is False:
        debug.verbose(f"Island is not init: config does not exist: '{env.get_island_path_config()}' or '{env.get_island_path_config_old()}'")
        return False
    if os.path.exists(env.get_island_path_manifest()) is False:
        debug.verbose(f"Island is not init: Manifest does not exist: '{env.get_island_path_manifest()}'")
        return False
    return True


def check_lutin_is_init():
    # check if .XXX exist (create it if needed)
    if not is_lutin_init():
        debug.error(f"System not init: missing config: '{env.get_island_path()}'. Call <island init> first")
        exit(-1)


class ManifestVSC:
    def __init__(self, manifest_yaml: str) -> None:
        self.manifest_yaml = manifest_yaml
        self.projects: List[Dict] = []
        self.default = None
        self.default_base = {
            "remote": "origin",
            "revision": "master",  # todo: rename 'branch-release'
            "sync": False,
            "branch-develop": "dev",
            "default-branch": "dev",
        }
        self.remotes: List[Dict] = []
        self.deliver_master = "master"
        self.deliver_develop = "develop"
        self.deliver_mode = "merge"
        # load the manifest
        self._load()
        # check error in manifest (double path ...)
        self._check_double_path([])

    def get_links(self):
        return []

    def _load(self):
        debug.debug(f"manifest VSC: '{self.manifest_yaml}'")
        data = {}
        with open(self.manifest_yaml) as f:
            data = yaml.load(f, Loader=SafeLoader)
        if "repositories" not in data:
            debug.error(f"in '{self.manifest_yaml}' VSC manifest: missing root key: repositories ")
        for name, value in data["repositories"].items():
            if "type" in value and value["type"] != "git":
                debug.error(f"in '{self.manifest_yaml}' VSC manifest: unsupported type: '{value['type']}' for {name}")
            if "url" not in value:
                debug.error(f"in '{self.manifest_yaml}' VSC manifest: missing 'url' for {name}")
            url = value["url"]
            # TODO: Manage URL remote element ==> dynamic add !!! and manage http(s)://xxx.yyy/*
            url_split = url.split(":")
            if len(url_split) > 1:
                url = url_split[-1]
            version = None
            if "version" not in value:
                version = value["version"]
            self.projects.append(
                {
                    "name": url,
                    "path": name,
                    "tag": version,
                }
            )

    def _create_path_with_elem(self, element):
        # debug.info(f"create path : {json.dumps(element)}")
        path = element["path"]
        if path == "":
            path = element["name"]
            if len(path) >= 4 and path[-4:] == ".git":
                path = path[:-4]
        # debug.info(f"    generate path {path}")
        return path

    def _check_double_path(self, list_path=[], space=""):
        # debug.debug(f"{space}check path : '{self.manifest_yaml}'")
        for elem in self.projects:
            path = self._create_path_with_elem(elem)
            debug.debug(f"{space}    check path:'{path}'")
            if path in list_path:
                debug.error(f"Check Manifest error : double use of the path '{path}'")
            list_path.append(path)

    def get_all_configs(self, default=None, upper_remotes=[]):
        out = []
        if default is None:
            if self.default is not None:
                default = copy.deepcopy(self.default)
            else:
                default = copy.deepcopy(self.default_base)
        # debug.error(f" self.default={self.default}")
        # add all local project
        for elem in self.projects:
            debug.verbose(f"parse element {elem}")
            if env.need_process_with_filter(elem["name"]) is False:
                debug.info(f"Filter repository: {elem['name']}")
                continue
            conf = repo_config.RepoConfig()
            conf.name = elem["name"]
            conf.tag = elem["tag"]
            conf.path = self._create_path_with_elem(elem)

            # add default remote for the project (search in inherited element)
            for remote in self.remotes:
                debug.verbose(f"    Local Remote: {remote}")
                if remote["name"] == default["remote"]:
                    conf.remotes.append(remote)
            if len(conf.remotes) == 0:
                for remote in upper_remotes:
                    debug.verbose(f"    upper Remote: {remote}")
                    if remote["name"] == default["remote"]:
                        conf.remotes.append(remote)
            if len(conf.remotes) == 0:
                debug.error(
                    f"    No remote detected: {len(conf.remotes)} for {conf.name} with default remote name : {default['remote']} self remote: {self.remotes}"
                )

            # select default remote:
            conf.select_remote = None
            debug.debug(f"    remotes count: {len(conf.remotes)}")
            for remote in conf.remotes:
                debug.debug(f"    remote={remote}")
                debug.debug(f"    Check remote : {remote['name']} == {default['remote']}")
                debug.verbose(f"          remote={remote}")
                debug.verbose(f"          default={default}")
                if remote["name"] == default["remote"]:
                    conf.select_remote = copy.deepcopy(remote)
                    debug.debug(f"    copy select={conf.select_remote}")

                    # copy the submodule synchronization
                    conf.select_remote["sync"] = default["sync"]
                    break
            if conf.select_remote == None:
                debug.error(f"missing remote for project: {conf.name}")

            conf.branch = default["revision"]
            out.append(conf)
        # create a temporary variable to transmit the remote to includes
        upper_remotes_forward = copy.deepcopy(upper_remotes)
        for remote in self.remotes:
            upper_remotes_forward.append(remote)

        if False:
            debug.info("list of all repo:")
            for elem in out:
                debug.info(f"    '{elem.name}'")
                debug.info(f"        path: {elem.path}")
                debug.info(f"        remotes: {elem.remotes}")
                debug.info(f"        select_remote: {elem.select_remote}")
                debug.info(f"        branch: {elem.branch}")
        return out


class Manifest:
    def __init__(self, manifest_xml: str) -> None:
        self.manifest_xml = manifest_xml
        self.projects: List[Dict] = []
        self.default = None
        self.default_base = {
            "remote": "origin",
            "revision": "master",  # todo: rename 'branch-release'
            "sync": False,
            "branch-develop": "dev",
            "default-branch": "dev",
        }
        self.remotes: List[Dict] = []
        self.includes: List[Dict] = []
        self.imports: List[Dict] = []
        self.links: List[Dict] = []
        self.deliver_master = "master"
        self.deliver_develop = "develop"
        self.deliver_mode = "merge"
        # load the manifest
        self._load()
        # check error in manifest (double path ...)
        self._check_double_path([])

    def get_links(self) -> Dict[str, Any]:
        return self.links

    def _load(self) -> None:
        debug.debug(f"manifest : '{self.manifest_xml}'")
        tree = etree.parse(self.manifest_xml)
        root = tree.getroot()
        if root.tag != "manifest":
            debug.error(f"(l:{child.sourceline}) in '{file}' have not main xml node='manifest'")
        for child in root:
            if type(child) == etree._Comment:
                debug.verbose(f"(l:{child.sourceline})     comment='{child.text}'")
                continue
            if child.tag == "remote":
                name = "origin"
                fetch = ""
                for attr in child.attrib:
                    if attr == "name":
                        name = child.attrib[attr]
                    elif attr == "fetch":
                        fetch = child.attrib[attr]
                        if len(fetch) >= 2 and fetch[:2] == "..":
                            # we have a relative island manifest ==> use local manifest origin to get the full origin
                            cmd = "git remote get-url origin"
                            debug.verbose(f"execute : {cmd}")
                            base_origin = multiprocess.run_command(cmd, cwd=env.get_island_path_manifest())
                            debug.verbose(f"base_origin={base_origin[1]}")
                            base_origin = base_origin[1]
                            while len(fetch) >= 2 and fetch[:2] == "..":
                                fetch = fetch[2:]
                                while len(fetch) >= 1 and (fetch[0] == "/" or fetch[0] == "\\"):
                                    fetch = fetch[1:]
                                offset_1 = base_origin.rfind("/")
                                offset_2 = base_origin.rfind(":")
                                if offset_1 > offset_2:
                                    base_origin = base_origin[:offset_1]
                                else:
                                    base_origin = base_origin[:offset_2]
                            debug.verbose(f"new base_origin={base_origin}")
                            debug.verbose(f"tmp fetch={fetch}")
                            if fetch != "":
                                fetch = f"{base_origin}/{fetch}"
                            else:
                                fetch = base_origin
                            debug.verbose(f"new fetch={fetch}")
                        while len(fetch) > 1 and (fetch[-1] == "\\" or fetch[-1] == "/"):
                            fetch = fetch[:-1]
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr}', available:[name,fetch]"
                        )
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}' fetch='{fetch}'")
                # parse the sub global mirror list
                mirror_list = []
                for child_2 in child:
                    if child_2.tag == "mirror":
                        # find a new mirror
                        mirror_name = ""
                        mirror_fetch = ""
                        for attr_2 in child_2.attrib:
                            if attr_2 == "name":
                                mirror_name = child_2.attrib[attr_2]
                            elif attr_2 == "fetch":
                                mirror_fetch = child_2.attrib[attr_2]
                                while len(mirror_fetch) > 1 and (mirror_fetch[-1] == "\\" or mirror_fetch[-1] == "/"):
                                    mirror_fetch = mirror_fetch[:-1]
                            else:
                                debug.error(
                                    f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child_2.tag}'  attribute : '{attr_2}', available:[name,fetch]"
                                )
                        debug.debug(f"mirror: '{mirror_name}' '{mirror_fetch}'")
                        if mirror_name == "":
                            debug.error(f"(l:{child_2.sourceline}) Missing mirror 'name'")
                        if mirror_fetch == "":
                            debug.error(f"(l:{child_2.sourceline}) Missing mirror 'fetch'")
                        mirror_list.append(
                            {
                                "name": mirror_name,
                                "fetch": mirror_fetch,
                            }
                        )
                    else:
                        debug.error(f"(l:{child_2.sourceline}) Parsing the manifest : unknown '{child_2.tag}', available:[mirror]")
                self.remotes.append({"name": name, "fetch": fetch, "mirror": mirror_list})
                continue

            if child.tag == "import":
                type_manifest = "vcs"
                name = ""
                for attr in child.attrib:
                    if attr == "type":
                        type_manifest = child.attrib[attr]
                        if type_manifest not in ["vcs"]:
                            debug.error(
                                f"(l:{child.sourceline}) Parsing the manifest: {child.tag} attribute '{attr}={type_manifest}' value available: [vcs]"
                            )
                    elif attr == "name":
                        name = child.attrib[attr]
                    else:
                        debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr}', available:[name]")
                new_name_yaml = os.path.join(os.path.dirname(self.manifest_xml), name)
                if os.path.exists(new_name_yaml) is False:
                    debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_yaml}'")
                self.imports.append({"name": name, "path": new_name_yaml, "type": type_manifest})
                continue
            if child.tag == "include":
                name = ""
                for attr in child.attrib:
                    if attr == "name":
                        name = child.attrib[attr]
                    else:
                        debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr}', available:[name]")
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
                # check if the file exist ...
                new_name_xml = os.path.join(os.path.dirname(self.manifest_xml), name)
                if os.path.exists(new_name_xml) is False:
                    debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
                self.includes.append({"name": name, "path": new_name_xml, "manifest": None})
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
                        deliver_master = child_2.text
                    elif child_2.tag == "branch-develop":
                        deliver_source = child_2.text
                    elif child_2.tag == "default-branch":
                        default_branch = child_2.text
                    elif child_2.tag == "default-remote":
                        remote = child_2.text
                    elif child_2.tag == "deliver-mode":
                        deliver_mode = child_2.text
                        if deliver_mode not in ["merge", "fast_forward"]:
                            debug.error(f"(l:{child.sourceline}) Parsing the manifest: option 'deliver-mode' value available: [merge,fast_forward]")
                    elif child_2.tag == "synchronize-submodule":
                        sync_tmp = child_2.text
                        if sync_tmp.lower() == "true" or sync_tmp == "1" or sync_tmp.lower() == "yes":
                            sync = True
                        elif sync_tmp.lower() == "false" or sync_tmp == "0" or sync_tmp.lower() == "no":
                            sync = False
                        else:
                            debug.error(
                                f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}/{child2.tag}', value:'{sync}' available:[true,1,yes,false,0,no]"
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
                tag_sha1 = None
                for attr in child.attrib:
                    if attr == "name":
                        name = child.attrib[attr]
                    elif attr == "path":
                        path = child.attrib[attr]
                    elif attr == "tag":
                        tag_sha1 = child.attrib[attr]
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr}', available:[name,tag,sync-s]"
                        )
                if name == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'name' ==> specify the git to clone ..."
                    )
                self.projects.append(
                    {
                        "name": name,
                        "path": path,
                        "tag": tag_sha1,
                    }
                )
                debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}' path='{path}' tag='{str(tag_sha1)}'")
                continue
            if child.tag == "link":
                # not managed ==> future use
                source = ""
                destination = ""
                for attr in child.attrib:
                    if attr == "source":
                        source = child.attrib[attr]
                    elif attr == "destination":
                        destination = child.attrib[attr]
                    else:
                        debug.error(
                            f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr}', available:[source,destination]"
                        )
                if source == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'source' ==> specify the git to clone."
                    )
                if destination == "":
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'destination' ==> specify the git to clone."
                    )
                self.links.append(
                    {
                        "source": source,
                        "destination": destination,
                    }
                )
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

    def _create_path_with_elem(self, element):
        path = element["path"]
        if path == "":
            path = element["name"]
            if len(path) >= 4 and path[-4:] == ".git":
                path = path[:-4]
        return path

    def _check_double_path(self, list_path=[], space=""):
        debug.debug(f"{space}check path : '{self.manifest_xml}'")
        for elem in self.projects:
            path = self._create_path_with_elem(elem)
            debug.debug(f"{space}    check path:'{path}'")
            if path in list_path:
                debug.error(f"Check Manifest error : double use of the path '{path}'")
            list_path.append(path)
        for elem in self.includes:
            elem["manifest"]._check_double_path(list_path, space + "    ")

    def get_all_configs(self, default=None, upper_remotes=[]):
        out = []
        if default == None:
            if self.default != None:
                default = copy.deepcopy(self.default)
            else:
                default = copy.deepcopy(self.default_base)
        # debug.error(f" self.default={self.default}")
        # add all local project
        for elem in self.projects:
            debug.verbose(f"parse element {elem}")
            if env.need_process_with_filter(elem["name"]) is False:
                debug.info(f"Filter repository: {elem['name']}")
                continue
            conf = repo_config.RepoConfig()
            conf.name = elem["name"]
            conf.tag = elem["tag"]
            conf.path = self._create_path_with_elem(elem)

            # add default remote for the project (search in inherited element)
            for remote in self.remotes:
                debug.verbose(f"    Local Remote: {remote}")
                if remote["name"] == default["remote"]:
                    conf.remotes.append(remote)
            if len(conf.remotes) == 0:
                for remote in upper_remotes:
                    debug.verbose(f"    upper Remote: {remote}")
                    if remote["name"] == default["remote"]:
                        conf.remotes.append(remote)
            if len(conf.remotes) == 0:
                debug.error(
                    f"    No remote detected: {len(conf.remotes)} for {conf.name} with default remote name : {default['remote']} self remote: {self.remotes}"
                )

            # select default remote:
            conf.select_remote = None
            debug.debug(f"    remotes count: {len(conf.remotes)}")
            for remote in conf.remotes:
                debug.debug(f"    remote={remote}")
                debug.debug(f"    Check remote : {remote['name']} == {default['remote']}")
                debug.verbose(f"          remote={remote}")
                debug.verbose(f"          default={default}")
                if remote["name"] == default["remote"]:
                    conf.select_remote = copy.deepcopy(remote)
                    debug.debug(f"    copy select={conf.select_remote}")

                    # copy the submodule synchronization
                    conf.select_remote["sync"] = default["sync"]
                    break
            if conf.select_remote == None:
                debug.error(f"missing remote for project: {conf.name}")

            conf.branch = default["revision"]
            out.append(conf)
        # create a temporary variable to transmit the remote to includes
        upper_remotes_forward = copy.deepcopy(upper_remotes)
        for remote in self.remotes:
            upper_remotes_forward.append(remote)
        # add all include project
        for elem in self.includes:
            list_project = elem["manifest"].get_all_configs(default, upper_remotes_forward)
            for elem_proj in list_project:
                out.append(elem_proj)
        # add all import project
        for elem in self.imports:
            list_project = elem["manifest"].get_all_configs(default, upper_remotes_forward)
            for elem_proj in list_project:
                out.append(elem_proj)

        # -------------------------------------------------------------
        # -- add Volatile ...
        # -------------------------------------------------------------
        debug.verbose("include volatile config")
        # TODO: maybe find a better way to do this...
        conf_global = config.get_unique_config()
        for elem in conf_global.get_volatile():
            conf = repo_config.RepoConfig()
            base_volatile, repo_volatile = repo_config.split_repo(elem["git_address"])
            conf.name = repo_volatile
            conf.path = elem["path"]
            conf.branch = "master"
            conf.volatile = True
            conf.remotes = [{"name": "origin", "fetch": base_volatile, "mirror": []}]
            conf.select_remote = {
                "name": "origin",
                "fetch": base_volatile,
                "sync": False,
                "mirror": [],
            }
            out.append(conf)
        # -------------------------------------------------------------
        if False:
            debug.info("list of all repo:")
            for elem in out:
                debug.info(f"    '{elem.name}'")
                debug.info(f"        path: {elem.path}")
                debug.info(f"        remotes: {elem.remotes}")
                debug.info(f"        select_remote: {elem.select_remote}")
                debug.info(f"        branch: {elem.branch}")
        return out


def tag_manifest(manifest_xml_filename, all_tags):
    tree = etree.parse(manifest_xml_filename)
    debug.debug(f"manifest : '{manifest_xml_filename}'")
    root = tree.getroot()
    includes = []
    if root.tag != "manifest":
        debug.error("(l:{child.sourceline}) in '{file}' have not main xml node='manifest'")
        return False
    for child in root:
        if type(child) == etree._Comment:
            debug.verbose(f"(l:{child.sourceline})     comment='{child.text}'")
            continue
        if child.tag == "remote":
            continue
        if child.tag == "include":
            name = ""
            for attr in child.attrib:
                if attr == "name":
                    name = child.attrib[attr]
                else:
                    debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr}', available:[name]")
            debug.debug(f"(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
            # check if the file exist ...
            new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename), name)
            if os.path.exists(new_name_xml) is False:
                debug.error(f"(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
            includes.append({"name": name, "path": new_name_xml, "manifest": None})
            continue
        if child.tag == "default":
            continue
        if child.tag == "project":
            name = ""
            path = ""
            tag_sha1 = None
            for attr in child.attrib:
                if attr == "name":
                    name = child.attrib[attr]
                elif attr == "path":
                    path = child.attrib[attr]
                elif attr == "tag":
                    tag_sha1 = child.attrib[attr]
                else:
                    debug.error(
                        f"(l:{child.sourceline}) Parsing the manifest: unknown '{child.tag}'  attribute : '{attr}', available:[name,tag,sync-s]"
                    )
            if name == "":
                debug.error(f"(l:{child.sourceline}) Parsing the manifest: '{child.tag}'  missing attribute: 'name' ==> specify the git to clone.")
            for elem_tag in all_tags:
                if elem_tag["name"] == name:
                    child.set("tag", elem_tag["tag"])
            continue
        if child.tag == "option":
            # not managed ==> future use
            continue
        if child.tag == "link":
            continue
        debug.info(f"(l:{child.sourceline})     '{child.tag}' values={child.attrib}")
        debug.error(f"(l:{child.sourceline}) Parsing error unknown NODE : '{child.tag}' available:[remote,include,default,project,option,link]")
    tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
    # now we parse all sub repo:
    for elem in includes:
        tag_manifest(elem["path"], all_tags)


def tag_clear(manifest_xml_filename):
    tree = etree.parse(manifest_xml_filename)
    debug.debug(f"manifest : '{manifest_xml_filename}'")
    root = tree.getroot()
    includes = []
    if root.tag != "manifest":
        debug.error("(l:{child.sourceline}) in '{file}' have not main xml node='manifest'")
        return False
    for child in root:
        if type(child) == etree._Comment:
            debug.verbose("(l:{child.sourceline})     comment='{child.text}'")
            continue
        if child.tag == "remote":
            continue
        if child.tag == "include":
            name = ""
            for attr in child.attrib:
                if attr == "name":
                    name = child.attrib[attr]
                else:
                    debug.error(f"(l:{child.sourceline}) Parsing the manifest : unknown '{child.tag}'  attribute : '{attr}', available:[name]")
            debug.debug("(l:{child.sourceline})     find '{child.tag}' : name='{name}'")
            # check if the file exist ...
            new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename), name)
            if os.path.exists(new_name_xml) is False:
                debug.error("(l:{child.sourceline}) The file does not exist : '{new_name_xml}'")
            includes.append({"name": name, "path": new_name_xml, "manifest": None})
            continue
        if child.tag == "default":
            continue
        if child.tag == "project":
            child.attrib.pop("tag", None)
            continue
        if child.tag == "option":
            continue
        if child.tag == "link":
            continue
        debug.info(f"(l:{child.sourceline})     '{child.tag}' values={child.attrib}")
        debug.error(f"(l:{child.sourceline}) Parsing error unknown NODE : '{child.tag}' available:[remote,include,default,project,option,link]")
    tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
    # now we parse all sub repo:
    for elem in includes:
        tag_clear(elem["path"])
