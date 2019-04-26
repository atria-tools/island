#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

import sys
import threading
import time
import sys
import os
import subprocess
import shlex
# Local import
from realog import debug
from . import tools
from . import env


def run_command_direct_shell(cmd_line, cwd=None, shell=False):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	subprocess.check_call(args, shell=shell)
	return ""
##
## @brief Execute the command and ruturn generate data
##
def run_command_direct(cmd_line, cwd=None):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	"""
	if True:
		subprocess.check_call(args)
		return ""
	"""
	try:
		# create the subprocess
		#p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		#p = subprocess.check_call(args)
		"""
		if cwd != None:
			debug.info("path = " + cwd)
		"""
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
	except subprocess.CalledProcessError as e:
		debug.error("subprocess.CalledProcessError : " + str(args))
	except:
		debug.error("Exception on : " + str(args))
	# launch the subprocess:
	output, err = p.communicate()
	if sys.version_info >= (3, 0):
		output = output.decode("utf-8")
		err = err.decode("utf-8")
	# Check errors:
	if p.returncode == 0:
		if output == None:
			return err[:-1];
		return output[:-1];
	else:
		return False



def run_command(cmd_line, cwd=None):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	try:
		# create the subprocess
		"""
		if cwd != None:
			debug.info("path = " + cwd)
		"""
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
	except subprocess.CalledProcessError as e:
		debug.error("subprocess.CalledProcessError : " + str(args))
	except:
		debug.error("Exception on : " + str(args))
	# launch the subprocess:
	output, err = p.communicate()
	if sys.version_info >= (3, 0):
		output = output.decode("utf-8")
		err = err.decode("utf-8")
	# Check error :
	return [p.returncode, output[:-1], err[:-1]]
