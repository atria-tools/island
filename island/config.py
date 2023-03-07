#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Config main interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""
import copy
import json
import os
from typing import Optional

# Local import
from realog import debug

from . import (
    env,
    repo_config,
    tools,
)


env.get_island_path_config()


class Config:
    def __init__(self) -> None:
        self._repo = ""
        self._branch = "master"
        self._manifest_name = "default.xml"
        self._volatiles = []
        self._current_link = []
        self.load()

    def load(self) -> bool:
        if os.path.exists(env.get_island_path_config()) is False:
            return True
        self._volatiles = []
        self._current_link = []
        with open(env.get_island_path_config()) as json_file:
            data = json.load(json_file)
            if "repo" in data.keys():
                self._repo = data["repo"]
            if "branch" in data.keys():
                self._branch = data["branch"]
            if "manifest_name" in data.keys():
                self._manifest_name = data["manifest_name"]
            if "volatiles" in data.keys():
                for elem in data["volatiles"]:
                    if "git_address" in elem.keys() and "path" in elem.keys():
                        self.add_volatile(elem["git_address"], elem["path"])
            if "link" in data.keys():
                for elem in data["link"]:
                    if "source" in elem.keys() and "destination" in elem.keys():
                        self.add_link(elem["source"], elem["destination"])
            return True
        return False

    def store(self) -> bool:
        data = {}
        data["repo"] = self._repo
        data["branch"] = self._branch
        data["manifest_name"] = self._manifest_name
        data["volatiles"] = self._volatiles
        data["link"] = self._current_link
        with open(env.get_island_path_config(), "w") as outfile:
            json.dump(data, outfile, indent=4)
            return True
        return False

    def set_manifest(self, value):
        self._repo = value

    def get_manifest(self):
        return self._repo

    def set_branch(self, value):
        self._branch = value

    def get_branch(self):
        return self._branch

    def set_manifest_name(self, value):
        self._manifest_name = value

    def get_manifest_name(self):
        return self._manifest_name

    def add_volatile(self, git_adress, local_path):
        for elem in self._volatiles:
            if elem["path"] == local_path:
                debug.error(
                    "can not have multiple local repositoty on the same PATH",
                    crash=False,
                )
                return False
        self._volatiles.append({"git_address": git_adress, "path": local_path})
        return True

    def get_volatile(self):
        return copy.deepcopy(self._volatiles)

    def get_links(self):
        return self._current_link

    def add_link(self, source, destination) -> bool:
        for elem in self._current_link:
            if elem["destination"] == destination:
                debug.error(
                    "can not have multiple destination folder in link " + destination,
                    crash=False,
                )
                return False
        self._current_link.append({"source": source, "destination": destination})
        return True

    def remove_link(self, destination) -> None:
        for elem in self._current_link:
            if elem["destination"] == destination:
                del self._current_link[elem]
                return
        debug.warning("Request remove link that does not exist")

    def clear_links(self):
        self._current_link = []

    def get_manifest_config(self):
        conf = repo_config.RepoConfig()
        base_volatile, repo_volatile = repo_config.split_repo(self.get_manifest())
        conf.name = repo_volatile
        conf.path = os.path.join("." + env.get_system_base_name(), "manifest")  # env.get_island_path_manifest()
        conf.branch = "master"
        conf.volatile = False
        conf.remotes = [{"name": "origin", "fetch": base_volatile, "mirror": []}]
        conf.select_remote = {
            "name": "origin",
            "fetch": base_volatile,
            "sync": False,
            "mirror": [],
        }
        return conf


_unique_config: Optional[Config] = None


def get_unique_config() -> Config:
    global _unique_config
    if _unique_config is None:
        _unique_config = Config()
    return _unique_config
