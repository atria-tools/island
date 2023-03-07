#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Repository management.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from realog import debug

from . import env, tools


class RepoConfig:
    def __init__(self):
        self.name = ""
        self.path = ""
        self.remotes = []  # list of all remotes, with the upstream elements (needed for third party integrations)
        self.select_remote = ""
        self.branch = ""
        self.tag = None
        self.volatile = False


def split_repo(git_repo):
    debug.verbose("parse git repo in RAW: " + str(git_repo))
    if len(git_repo) > 4 and git_repo[:4] == "http":
        # http://wdfqsdfqs@qsdfqsdf/qsdfqsdf/qsdfqsdf/qsdfqs.git find the 3rd '/' and cut at this point
        elements = git_repo.split("/")
        if len(elements) < 4:
            debug.error("Can not parse the git repository : '" + str(git_repo) + "' wrong format http?://xxx@xxx.xxx/****")
        base = elements[0] + "/" + elements[1] + "/" + elements[2]
        repo = git_repo[len(base) + 1 :]
    elif len(git_repo) > 3 and git_repo[:3] == "git":
        # git@qsdfqsdf:qsdfqsdf/qsdfqsdf/qsdfqs.git find the 1st ':' and cut at this point
        elements = git_repo.split(":")
        if len(elements) < 2:
            debug.error("Can not parse the git repository : '" + str(git_repo) + "' wrong format git@xxx.xxx:****")
        base = elements[0]
        repo = git_repo[len(base) + 1 :]
    else:
        debug.error("Can not parse the git repository : '" + str(git_repo) + "' does not start with ['http', 'git']")
    debug.verbose("    base: " + str(base))
    debug.verbose("    repo: " + str(repo))
    return (base, repo)
