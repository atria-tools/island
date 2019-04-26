#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##
import platform
import sys
import os
import copy
# Local import
from realog import debug
from . import tools
from . import env
from . import multiprocess


env.get_island_path_config()


class Config():
	def __init__(self):
		self._repo = ""
		self._branch = "master"
		self._manifest_name = "default.xml"
		
		self.load()
		
	
	def load(self):
		config_property = tools.file_read_data(env.get_island_path_config())
		element_config = config_property.split("\n")
		for line in element_config:
			if    len(line) == 0 \
			   or line[0] == "#":
				# simple comment line ==> pass
				pass
			elif line[:5] == "repo=":
				self._repo = line[5:]
			elif line[:7] == "branch=":
				self._branch = line[7:]
			elif line[:5] == "file=":
				self._manifest_name = line[5:]
			else:
				debug.warning("island config error: can not parse: '" + str(line) + "'")
		return True
	
	def store(self):
		data = "repo=" + self._repo + "\nbranch=" + self._branch + "\nfile=" + self._manifest_name
		tools.file_write_data(env.get_island_path_config(), data)
	
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

