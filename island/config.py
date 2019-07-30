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
		
	
	# set it deprecated at 2020/07
	def load_old(self):
		config_property = tools.file_read_data(env.get_island_path_config_old())
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
	
	def convert_config_file(self):
		debug.warning("INTERNAL: Convert your configuration file: " + str(env.get_island_path_config_old()) + " -> " + str(env.get_island_path_config()))
		self.load_old()
		self.store()
		tools.remove_file(env.get_island_path_config_old())
	
	def load(self):
		# transform the old format of configuration (use json now ==> simple
		if os.path.exists(env.get_island_path_config_old()) == True:
			self.convert_config_file()
		if os.path.exists(env.get_island_path_config()) == False:
			return True
		self._volatiles = []
		with open(env.get_island_path_config()) as json_file:
			data = json.load(json_file)
			if "repo" in data.keys():
				self._repo = data["repo"]
			if "branch" in data.keys():
				self._branch = data["branch"]
			if "manifest_name" in data.keys():
				self._manifest_name = data["manifest_name"]
			return True
		return False
	
	def store(self):
		data = {}
		data["repo"] = self._repo
		data["branch"] = self._branch
		data["manifest_name"] = self._manifest_name
		with open(env.get_island_path_config(), 'w') as outfile:
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

