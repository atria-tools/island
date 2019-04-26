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
# Local import
from realog import debug

# print os.name # ==> 'posix'
if platform.system() == "Linux":
	OS = "Linux"
elif platform.system() == "Windows":
	OS = "Windows"
elif platform.system() == "Darwin":
	OS = "MacOs"
else:
	debug.error("Unknow the Host OS ... '" + platform.system() + "'")

debug.debug("host.OS = " + OS)

