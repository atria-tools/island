Island
======

`island` is a generic source downloader and synchronizer is a FREE software tool.

It is compatible with basic format of repo-git manifest. This project is created to be easiest to read with simple interface
(no internal git usage, but user level git usage) The main point to create the "fork" is the non-support of repo of relativity
in submodule of git (submodule reference with ../xxx.git) This point is really important when you want to have a relocate
manifest and project with submodule. The simpl example is the atria-soft / generic-library / musicdsp that are available on
github, gitlab, bitbucket and personal server.


![https://badge.fury.io/py/island.png](https://badge.fury.io/py/island.png))

Instructions
------------

This is a tool to download ```git``` source repositiry in a versatile worktree

island is under a FREE license that can be found in the LICENSE file.
Any contribution is more than welcome ;)

git repository
--------------

http://github.com/HeeroYui/island/

Documentation
-------------

http://HeeroYui.github.io/island/

Installation
------------

Requirements: ``Python >= 2.7`` and ``pip``

Just run:

  pip install island

or with pipx run:

  pipx install island

Install pip on debian/ubuntu:

  sudo apt-get install pip

Install pip on ARCH-linux:

  sudo pacman -S pip

Install pip on MacOs:

  sudo easy_install pip

Usage
-----

Select a manifest:

  island init http://github.com/atria-soft/manifest.git

Download and synchronize the sources:

  island sync

Get what changed on the servers, without touching the working trees (it tells what each project has to pull):

  island fetch

sync and fetch work on 5 projects at a time and show one line per project as it ends (cloned, updated
with the number of new commits, up to date, modified...), its warnings and errors under it, then a
summary. Choose how many projects run at a time with ```-j``` (```-j 1``` one after the other;
```--wait``` also runs one at a time), or with ```get_default_jobs()``` in the islandConfig.py of the
workspace:

  island -j 10 sync

Deliver the projects: release their develop branch (dev) on their release branch (main, created at the
first delivery) with a new version, then push the deliveries. Every project is checked first, one line
each (what it delivers, from which version to which one, or why it is skipped), then one plan is shown
and accepted once, or edited project by project:

  island deliver
  island deliver-push

The version comes from the version.txt of the project (created at 0.0.0 when missing; a release script
.island/release.bash of the project may copy it elsewhere, in a pom.xml for instance). Its step is
proposed from the commits: an [API] or BREAKING one gives major, a [FEAT] one minor, any other patch.
After the release X.Y.Z, version.txt is X.Y.(Z+1)-dev on the develop branch. Nothing changes while a
project has local changes, a branch behind the server, a release branch with commits the develop one
has not, or a tag that exists. Without questions, in a given step, and pushed at once:

  island deliver --yes --bump=minor --push
  island --filter=etk deliver

A Maven project keeps its version in its pom.xml: X.Y.Z on the release branch, X.Y.(Z+1)-SNAPSHOT on the
develop one. Between the projects of the workspace, a release depends on releases only (those delivered
with it, else the last ones), and a develop branch on the -SNAPSHOT of its dependencies: the projects not
delivered follow them with a commit of their own. A dependency with commits to deliver, or never
released, joins the delivery of the project that needs it, so this delivers etk too when it changed:

  island --filter=gale deliver

A project never released is delivered in the version of its pom, when it is needed or asked for:

  island deliver --unreleased

A project marked private in the manifest (```<project ... private="true"/>```) is not published, and
no public project may depend on it.

Then deliver the manifest, each project pinned on its last release:

  island manifest-deliver --push

Select all branch available in the work-tree: (checkout origin/dev in dev branch and track it, do nothing if the branch does not exist)

  island checkout dev

Show the status of the workspace

  island status

Use a specific ssh key (stored in the workspace and set in all the repository, a direct ```git``` command use it too):

  island init --ssh-key ~/.ssh/id_ed25519_other git@github.com:atria-soft/manifest.git

Select, display or remove the ssh key of an existing workspace:

  island ssh-key ~/.ssh/id_ed25519_other
  island ssh-key
  island ssh-key --remove

Use a specific git user name and email (stored in the workspace and set in all the repository):

  island init --user-name "My Name" --user-email my.name@example.com git@github.com:atria-soft/manifest.git

Select, display or remove the git user of an existing workspace:

  island user --name "My Name" --email my.name@example.com
  island user
  island user --remove

Develop in local (with virtual env):
====================================

see: https://setuptools.pypa.io/en/latest/userguide/development_mode.html

Create your development environment:
```bash
# Create a virtual environment
python -m venv .venv
# Activate the python virtual environment
source .venv/bin/activate
# Install the package in editable mode (dynamic use of files), with the development tools
pip install --editable '.[dev]'
```

Check the code before a commit (the CI runs the same on Python 3.11 to 3.14):
```bash
ruff check .            # lint (add --fix to correct what can be)
ruff format .           # format
mypy                    # types, in strict mode
pytest                  # tests, island run on local git repositories
```

or with pipx:
```bash
pipx install --editable .
```

Run the application . ```island --help```

Manual set in production:
=========================

install generic tools for deployment
```bash
pip3 install twine
```

Create the new version:

```bash
# Clean previous packages
 \rm -rf dist/
# Compile the package
python3 -m build
# Upload the package
python3 -m twine upload dist/*
```


TODO list
---------

  - When sync checkout the new manifest
  - status: show how many time late we are on the branch
  - sync: filter the apply of this cmd
  - create snapshot
  - use a snapshot
  - commit all change in a single commit name and date
  - push all change in the origin branch
  - stash/unstash all change
  - permit to set the pasword when requested by git
  - sync: show download progress
  - support single project mirror
  - support submodule mirror
  - support project upstream
  - support submodule add upstream
  - push modilfication in all late mirorr (force mode optionnal) ==> for automatic server synchronisation in 4 lines
  - a good documation of the format and the usage
  - parallele push, status ...

License (MPL v2.0)
---------------------

Copyright island Edouard DUPIN

Licensed under the Mozilla Public License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.mozilla.org/MPL/2.0/

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
