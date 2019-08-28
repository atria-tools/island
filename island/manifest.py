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
from . import repo_config
from . import link_config
from . import tools
from . import env
from . import multiprocess
from . import config

from lxml import etree

def is_lutin_init():
	if os.path.exists(env.get_island_path()) == False:
		debug.verbose("Lutin is not init: path does not exist: '" + env.get_island_path() + "'")
		return False
	if     os.path.exists(env.get_island_path_config()) == False \
	   and os.path.exists(env.get_island_path_config_old()) == False:
		debug.verbose("Lutin is not init: config does not exist: '" + env.get_island_path_config() + "' or '" + env.get_island_path_config_old() + "'")
		return False
	if os.path.exists(env.get_island_path_manifest()) == False:
		debug.verbose("Lutin is not init: Manifest does not exist: '" + env.get_island_path_manifest() + "'")
		return False
	return True

def check_lutin_is_init():
	# check if .XXX exist (create it if needed)
	if is_lutin_init() == False:
		debug.error("System not init: missing config: '" + str(env.get_island_path()) + "'. Call <island init> first")
		exit(-1)

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
		self.links = []
		self.deliver_master = "master"
		self.deliver_develop = "develop"
		self.deliver_mode = "merge"
		# load the manifest
		self._load()
		# check error in manifest (double path ...)
		self._check_double_path([])
	
	def get_links(self):
		return self.links
	
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
				tag_sha1 = None
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					elif attr == "path":
						path = child.attrib[attr]
					elif attr == "tag":
						tag_sha1 = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,tag,sync-s]")
				if name == "":
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'name' ==> specify the git to clone ...")
				self.projects.append({
				    "name":name,
				    "path":path,
				    "tag":tag_sha1,
				    })
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "' path='" + path + "' tag='" + str(tag_sha1) + "'");
				continue
			if child.tag == "option":
				# not managed ==> future use
				type_option = ""
				value_option = ""
				for attr in child.attrib:
					if attr == "type":
						type_option = child.attrib[attr]
					elif attr == "value":
						value_option = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[type,value]")
				if type_option == "deliver_master":
					self.deliver_master = value_option
				elif type_option == "deliver_develop":
					self.deliver_develop = value_option
				elif type_option == "deliver_mode":
					self.deliver_mode = value_option
					if self.deliver_mode not in ["merge","fast_forward"]:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: option 'deliver_mode' value availlable: [merge,fast_forward]")
				else:
					debug.warning("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow 'type' value availlable: [deliver_master,deliver_develop,deliver_mode]")
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
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[source,destination]")
				if source == "":
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'source' ==> specify the git to clone ...")
				if destination == "":
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'destination' ==> specify the git to clone ...")
				self.links.append({
				    "source":source,
				    "destination":destination,
				    })
				debug.debug("Add link: '" + str(destination) + "' ==> '" + str(source) + "'")
				continue
			debug.info("(l:" + str(child.sourceline) + ")     '" + str(child.tag) + "' values=" + str(child.attrib));
			debug.error("(l:" + str(child.sourceline) + ") Parsing error Unknow NODE : '" + str(child.tag) + "' availlable:[remote,include,default,project,option,link]")
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
			if env.need_process_with_filter(elem["name"]) == False:
				debug.info("Filter repository: " + str(elem["name"]))
				continue
			conf = repo_config.RepoConfig()
			conf.name = elem["name"]
			conf.tag = elem["tag"]
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
		
		## -------------------------------------------------------------
		## -- add Volatile ...
		## -------------------------------------------------------------
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
			conf.remotes = [
				{
					'name': 'origin',
					'fetch': base_volatile,
					'mirror': []
				}
				]
			conf.select_remote = {
					'name': 'origin',
					'fetch': base_volatile,
					'sync': False,
					'mirror': []
				}
			out.append(conf)
		## -------------------------------------------------------------
		if False:
			debug.info("list of all repo:")
			for elem in out:
				debug.info("    '" + elem.name + "'")
				debug.info("        path: " + elem.path)
				debug.info("        remotes: " + str(elem.remotes))
				debug.info("        select_remote: " + str(elem.select_remote))
				debug.info("        branch: " + elem.branch)
		return out


def tag_manifest(manifest_xml_filename, all_tags):
	tree = etree.parse(manifest_xml_filename)
	debug.debug("manifest : '" + manifest_xml_filename + "'")
	root = tree.getroot()
	includes = []
	if root.tag != "manifest":
		debug.error("(l:" + str(child.sourceline) + ") in '" + str(file) + "' have not main xml node='manifest'")
		return False
	for child in root:
		if type(child) == etree._Comment:
			debug.verbose("(l:" + str(child.sourceline) + ")     comment='" + str(child.text) + "'");
			continue
		if child.tag == "remote":
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
			new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename),name)
			if os.path.exists(new_name_xml) == False:
				debug.error("(l:" + str(child.sourceline) + ") The file does not exist : '" + new_name_xml + "'")
			includes.append({
			    "name":name,
			    "path":new_name_xml,
			    "manifest":None
			    })
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
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,tag,sync-s]")
			if name == "":
				debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'name' ==> specify the git to clone ...")
			for elem_tag in all_tags:
				if elem_tag["name"] == name:
					child.set("tag", elem_tag["tag"])
			continue
		if child.tag == "option":
			# not managed ==> future use
			continue
		if child.tag == "link":
			continue
		debug.info("(l:" + str(child.sourceline) + ")     '" + str(child.tag) + "' values=" + str(child.attrib));
		debug.error("(l:" + str(child.sourceline) + ") Parsing error Unknow NODE : '" + str(child.tag) + "' availlable:[remote,include,default,project,option,link]")
	tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
	# now we parse all sub repo:
	for elem in includes:
		tag_manifest(elem["path"], all_tags)



def tag_clear(manifest_xml_filename):
	tree = etree.parse(manifest_xml_filename)
	debug.debug("manifest : '" + manifest_xml_filename + "'")
	root = tree.getroot()
	includes = []
	if root.tag != "manifest":
		debug.error("(l:" + str(child.sourceline) + ") in '" + str(file) + "' have not main xml node='manifest'")
		return False
	for child in root:
		if type(child) == etree._Comment:
			debug.verbose("(l:" + str(child.sourceline) + ")     comment='" + str(child.text) + "'");
			continue
		if child.tag == "remote":
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
			new_name_xml = os.path.join(os.path.dirname(manifest_xml_filename),name)
			if os.path.exists(new_name_xml) == False:
				debug.error("(l:" + str(child.sourceline) + ") The file does not exist : '" + new_name_xml + "'")
			includes.append({
			    "name":name,
			    "path":new_name_xml,
			    "manifest":None
			    })
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
		debug.info("(l:" + str(child.sourceline) + ")     '" + str(child.tag) + "' values=" + str(child.attrib));
		debug.error("(l:" + str(child.sourceline) + ") Parsing error Unknow NODE : '" + str(child.tag) + "' availlable:[remote,include,default,project,option,link]")
	tree.write(manifest_xml_filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
	# now we parse all sub repo:
	for elem in includes:
		tag_clear(elem["path"])
	