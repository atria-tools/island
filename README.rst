Lutin
=====

`island` is a generic source downloader and syncronizer is a FREE software tool.

It is compatible with basic format of repo-git manifest. This project is created to be easyest to read with simple interface
(no internal git usage, but user level git usage) The main point to create the "fork" is the non-support of repo of relativity
in submodule of git (submodule reference with ../xxx.git) This point is really important when you want to have a rellocable
manifest and project with submodule. The simpl eexample is the atria-soft / generic-library / musicdsp that are availlable on
github, gitlab, bitbucket and personal server.


.. image:: https://badge.fury.io/py/island.png
    :target: https://pypi.python.org/pypi/island

Release (master)
----------------

.. image:: https://travis-ci.org/HeeroYui/island.svg?branch=master
    :target: https://travis-ci.org/HeeroYui/island



Developement (dev)
------------------

.. image:: https://travis-ci.org/HeeroYui/island.svg?branch=dev
    :target: https://travis-ci.org/HeeroYui/island


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

Select all branch availlable in the worktree: (checkout origin/dev in dev branch and track it, do nothing if the branch does not exist)

  island checkout dev

Show the status of the workspace

  island status

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
  - parallele download / sync / push ...

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

