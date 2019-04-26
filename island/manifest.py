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

from lxml import etree

class RepoConfig():
	def __init__(self):
		self.name = ""
		self.path = ""
		self.remotes = [] # list of all remotes, with the upstream elements (needed for third party integrations)
		self.select_remote = ""
		self.branch = ""
		

class Manifest():
	def __init__(self, manifest_xml):
		self.manifest_xml = manifest_xml
		self.projects = []
		self.default = None
		self.default_base = {
		    "remote":"origin",
		    "revision":"master",
		    "sync":False,
		    }
		self.remotes = []
		self.includes = []
		# load the manifest
		self._load()
		# check error in manifest (double path ...)
		self._check_double_path([])
	
	def _load(self):
		tree = etree.parse(self.manifest_xml)
		debug.debug("manifest : '" + self.manifest_xml + "'")
		root = tree.getroot()
		if root.tag != "manifest":
			debug.error("(l:" + str(child.sourceline) + ") in '" + str(file) + "' have not main xml node='manifest'")
		for child in root:
			if type(child) == etree._Comment:
				debug.verbose("(l:" + str(child.sourceline) + ")     comment='" + str(child.text) + "'");
				continue
			if child.tag == "remote":
				name = "origin"
				fetch = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					elif attr == "fetch":
						fetch = child.attrib[attr]
						if     len(fetch) >= 2 \
						   and fetch[:2] == "..":
							# we have a relative island manifest ==> use local manifest origin to get the full origin
							cmd = "git remote get-url origin"
							debug.verbose("execute : " + cmd)
							base_origin = multiprocess.run_command(cmd, cwd=env.get_island_path_manifest())
							debug.verbose("base_origin=" + base_origin[1])
							base_origin = base_origin[1]
							while     len(fetch) >= 2 \
							      and fetch[:2] == "..":
								fetch = fetch[2:]
								while      len(fetch) >= 1 \
								       and (    fetch[0] == "/" \
								             or fetch[0] == "\\"):
									fetch = fetch[1:]
								offset_1 = base_origin.rfind('/')
								offset_2 = base_origin.rfind(':')
								if offset_1 > offset_2:
									base_origin = base_origin[:offset_1]
								else:
									base_origin = base_origin[:offset_2]
							debug.verbose("new base_origin=" + base_origin)
							debug.verbose("tmp fetch=" + fetch)
							if fetch != "":
								fetch = base_origin + "/" + fetch
							else:
								fetch = base_origin
							debug.verbose("new fetch=" + fetch)
						while     len(fetch) > 1 \
						      and (    fetch[-1] == "\\" \
						            or fetch[-1] == "/") :
							fetch = fetch[:-1]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,fetch]")
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "' fetch='" + fetch + "'");
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
								while     len(mirror_fetch) > 1 \
								      and (    mirror_fetch[-1] == "\\" \
								            or mirror_fetch[-1] == "/") :
									mirror_fetch = mirror_fetch[:-1]
							else:
								debug.error("(l:" + str(child_2.sourceline) + ") Parsing the manifest : Unknow '" + child_2.tag + "'  attibute : '" + attr_2 + "', availlable:[name,fetch]")
						debug.debug("mirror: '" + mirror_name + "' '" + mirror_fetch + "'")
						if mirror_name == "":
							debug.error("(l:" + str(child_2.sourceline) + ") Missing mirrot 'name'")
						if mirror_fetch == "":
							debug.error("(l:" + str(child_2.sourceline) + ") Missing mirror 'fetch'")
						mirror_list.append({
						    "name":mirror_name,
						    "fetch":mirror_fetch,
						    })
					else:
						debug.error("(l:" + str(child_2.sourceline) + ") Parsing the manifest : Unknow '" + child_2.tag + "', availlable:[mirror]")
				self.remotes.append({
				    "name":name,
				    "fetch":fetch,
				    "mirror":mirror_list
				    })
				continue
				
			if child.tag == "include":
				name = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name]")
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "'");
				# check if the file exist ...
				new_name_xml = os.path.join(os.path.dirname(self.manifest_xml),name)
				if os.path.exists(new_name_xml) == False:
					debug.error("(l:" + str(child.sourceline) + ") The file does not exist : '" + new_name_xml + "'")
				self.includes.append({
				    "name":name,
				    "path":new_name_xml,
				    "manifest":None
				    })
				continue
			if child.tag == "default":
				remote = "origin"
				revision = "master"
				sync = False
				for attr in child.attrib:
					if attr == "remote":
						remote = child.attrib[attr]
					elif attr == "revision":
						revision = child.attrib[attr]
					elif attr == "sync-s": # synchronize submodule ... automaticaly
						sync = child.attrib[attr]
						if    sync.lower() == "true" \
						   or sync == "1" \
						   or sync.lower() == "yes":
							sync = True
						elif    sync.lower() == "false" \
						     or sync == "0" \
						     or sync.lower() == "no":
							sync = False
						else:
							debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "' attbute : '" + attr + "', value:'" + sync + "' availlable:[true,1,yes,false,0,no]")
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[remote,revision,sync-s]")
				if self.default != None:
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Node '" + child.tag + "'  already set")
				self.default = {
				    "remote":remote,
				    "revision":revision,
				    "sync":sync,
				    }
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : remote='" + remote + "' revision='" + revision + "' sync=" + str(sync));
				continue
			if child.tag == "project":
				name = ""
				path = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					elif attr == "path":
						path = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,revision,sync-s]")
				if name == "":
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'name' ==> specify the git to clone ...")
				self.projects.append({
				    "name":name,
				    "path":path,
				    })
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "' path='" + path + "'");
				continue
			debug.info("(l:" + str(child.sourceline) + ")     '" + str(child.tag) + "' values=" + str(child.attrib));
			debug.error("(l:" + str(child.sourceline) + ") Parsing error Unknow NODE : '" + str(child.tag) + "' availlable:[remote,include,default,project]")
		# now we parse all sub repo:
		for elem in self.includes:
			elem["manifest"] = Manifest(elem["path"])
		
		
		# inside data    child.text
		
	
	def _create_path_with_elem(self, element):
		path = element["path"]
		if path == "":
			path = element["name"]
			if     len(path) >= 4 \
			   and path[-4:] == ".git":
				path = path[:-4]
		return path
	
	def _check_double_path(self, list_path = [], space=""):
		debug.debug(space + "check path : '" + self.manifest_xml + "'")
		for elem in self.projects:
			path = self._create_path_with_elem(elem)
			debug.debug(space + "    check path:'" + str(path) + "'")
			if path in list_path:
				debug.error("Check Manifest error : double use of the path '" + str(path) + "'")
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
		# debug.error(" self.default=" + str(self.default))
		# add all local project
		for elem in self.projects:
			debug.verbose("parse element " + str(elem))
			conf = RepoConfig()
			conf.name = elem["name"]
			conf.path = self._create_path_with_elem(elem)
			
			# add default remote for the project (search in herited element)
			for remote in self.remotes:
				debug.verbose("    Local Remote: " + str(remote))
				if remote["name"] == default["remote"]:
					conf.remotes.append(remote)
			if len(conf.remotes) == 0:
				for remote in upper_remotes:
					debug.verbose("    upper Remote: " + str(remote))
					if remote["name"] == default["remote"]:
						conf.remotes.append(remote)
			if len(conf.remotes) == 0:
				debug.error("    No remote detected: " + str(len(conf.remotes)) + " for " + conf.name + " with default remote name : " + default["remote"] + " self remote: " + str(self.remotes))
			
			# select default remote:
			conf.select_remote = None
			debug.debug("    remotes count: " + str(len(conf.remotes)))
			for remote in conf.remotes:
				debug.debug("    remote=" + str(remote))
				debug.debug("    Ckeck remote : " + remote["name"] + " == " + default["remote"])
				debug.verbose("          remote=" + str(remote))
				debug.verbose("          default=" + str(default))
				if remote["name"] == default["remote"]:
					conf.select_remote = copy.deepcopy(remote)
					debug.debug("    copy select=" + str(conf.select_remote))
					
					# copy the submodule synchronisation
					conf.select_remote["sync"] = default["sync"]
					break
			if conf.select_remote == None:
				debug.error("missing remote for project: " + str(conf.name))
			
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
		return out


