#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

import os
import threading
import re

debug_level=3
debug_color=False

color_default= ""
color_red    = ""
color_green  = ""
color_yellow = ""
color_blue   = ""
color_purple = ""
color_cyan   = ""


debug_lock = threading.Lock()

##
## @brief Set log level of the console log system
## @param[in] id (int) Value of the log level:
##              0: None
##              1: error
##              2: warning
##              3: info
##              4: debug
##              5: verbose
##              6: extreme_verbose
##
def set_level(id):
	global debug_level
	debug_level = id
	#print "SetDebug level at " + str(debug_level)

##
## @brief Get the current debug leval
## @return The value of the log level. Show: @ref set_level
##
def get_level():
	global debug_level
	return debug_level

##
## @brief Enable color of the console Log system
##
def enable_color():
	global debug_color
	debug_color = True
	global color_default
	color_default= "\033[00m"
	global color_red
	color_red    = "\033[31m"
	global color_green
	color_green  = "\033[32m"
	global color_yellow
	color_yellow = "\033[33m"
	global color_blue
	color_blue   = "\033[01;34m"
	global color_purple
	color_purple = "\033[35m"
	global color_cyan
	color_cyan   = "\033[36m"

##
## @brief Disable color of the console Log system
##
def disable_color():
	global debug_color
	debug_color = True
	global color_default
	color_default= ""
	global color_red
	color_red    = ""
	global color_green
	color_green  = ""
	global color_yellow
	color_yellow = ""
	global color_blue
	color_blue   = ""
	global color_purple
	color_purple = ""
	global color_cyan
	color_cyan   = ""

##
## @brief Print a extreme verbose log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def extreme_verbose(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 6 \
	   or force == True:
		debug_lock.acquire()
		print(color_blue + input + color_default)
		debug_lock.release()

##
## @brief Print a verbose log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def verbose(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 5 \
	   or force == True:
		debug_lock.acquire()
		print(color_blue + input + color_default)
		debug_lock.release()

##
## @brief Print a debug log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def debug(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 4 \
	   or force == True:
		debug_lock.acquire()
		print(color_green + input + color_default)
		debug_lock.release()

##
## @brief Print an info log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def info(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 3 \
	   or force == True:
		debug_lock.acquire()
		print(input + color_default)
		debug_lock.release()

##
## @brief Print a warning log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def warning(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 2 \
	   or force == True:
		debug_lock.acquire()
		print(color_purple + "[WARNING] " + input + color_default)
		debug_lock.release()

##
## @brief Print a todo log
## @param[in] input (string) Value to print if level is enough
## @param[in] force (bool) force display (no check of log level)
##
def todo(input, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 3 \
	   or force == True:
		debug_lock.acquire()
		print(color_purple + "[TODO] " + input + color_default)
		debug_lock.release()

##
## @brief Print an error log
## @param[in] input (string) Value to print if level is enough
## @param[in] thread_id (int) Current thead ID of the builder thread
## @param[in] force (bool) force display (no check of log level)
## @param[in] crash (bool) build error has appear ==> request stop of all builds
##
def error(input, thread_id=-1, force=False, crash=True):
	global debug_lock
	global debug_level
	if    debug_level >= 1 \
	   or force == True:
		debug_lock.acquire()
		print(color_red + "[ERROR] " + input + color_default)
		debug_lock.release()
	if crash == True:
		exit(-1)
		#os_exit(-1)
		#raise "error happend"


##
## @brief Print a log for a specific element action like generateing .so or binary ...
## @param[in] type (string) type of action. Like: "copy file", "StaticLib", "Prebuild", "Library" ...
## @param[in] lib (string) Name of the library/binary/package that action is done
## @param[in] dir (string) build direction. ex: "<==", "==>" ...
## @param[in] name (string) Destination of the data
## @param[in] force (bool) force display (no check of log level)
##
def print_element(type, lib, dir, name, force=False):
	global debug_lock
	global debug_level
	if    debug_level >= 3 \
	   or force == True:
		debug_lock.acquire()
		print(color_cyan + type + color_default + " : " + color_yellow + lib + color_default + " " + dir + " " + color_blue + name + color_default)
		debug_lock.release()

##
## @brief Print a compilation return (output)
## @param[in] my_string (string) Std-error/std-info that is generate by the build system
##
def print_compilator(my_string):
	global debug_color
	global debug_lock
	if debug_color == True:
		my_string = my_string.replace('\\n', '\n')
		my_string = my_string.replace('\\t', '\t')
		my_string = my_string.replace('error:', color_red+'error:'+color_default)
		my_string = my_string.replace('warning:', color_purple+'warning:'+color_default)
		my_string = my_string.replace('note:', color_green+'note:'+color_default)
		my_string = re.sub(r'([/\w_-]+\.\w+):', r'-COLORIN-\1-COLOROUT-:', my_string)
		my_string = my_string.replace('-COLORIN-', color_yellow)
		my_string = my_string.replace('-COLOROUT-', color_default)
	
	debug_lock.acquire()
	print(my_string)
	debug_lock.release()

##
## @brief Get the list of default color
## @return A map with keys: "default","red","green","yellow","blue","purple","cyan"
##
def get_color_set() :
	global color_default
	global color_red
	global color_green
	global color_yellow
	global color_blue
	global color_purple
	global color_cyan
	return {
	    "default": color_default,
	    "red": color_red,
	    "green": color_green,
	    "yellow": color_yellow,
	    "blue": color_blue,
	    "purple": color_purple,
	    "cyan": color_cyan,
	    }
