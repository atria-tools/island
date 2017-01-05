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
from . import debug
from . import tools
from . import env


##
## @brief Execute the command and ruturn generate data
##
def run_command_direct(cmd_line):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	try:
		# create the subprocess
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
	if p.returncode == 0:
		if output == None:
			return err[:-1];
		return output[:-1];
	else:
		return False


