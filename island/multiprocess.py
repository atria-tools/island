#!/usr/bin/python
# -*- coding: utf-8 -*-
"""System call Interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import shlex
import subprocess
import sys

# Local import
from realog import debug


def generic_display_error(
    return_value,
    type_name,
    error_only=False,
    available_return=[0],
    display_if_nothing=True,
):
    debug.verbose(str(return_value))
    if return_value[0] in available_return:
        if error_only is True:
            return
        display = False
        if return_value[1] != "":
            debug.info(return_value[1])
            display = True
        if return_value[2] != "":
            debug.warning(return_value[2])
            display = True
        if display_if_nothing is False:
            return
        if display is False:
            debug.verbose("GIT(" + type_name + "): All done OK")
    else:
        display = False
        if return_value[1] != "":
            debug.warning("ERROR GIT(" + type_name + ") 1:" + return_value[1])
            display = True
        if return_value[2] != "":
            debug.warning("ERROR GIT(" + type_name + ") 2:" + return_value[2])
            display = True
        if display is False:
            debug.warning("ERROR GIT(" + type_name + "): Unknow error return_value=" + str(return_value[0]))


def run_command_direct_shell(cmd_line, cwd=None, shell=False):
    # prepare command line:
    args = shlex.split(cmd_line)
    debug.verbose("cmd = " + str(args))
    subprocess.check_call(args, shell=shell)
    return ""


#
# @brief Execute the command and ruturn generate data
#
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
        # p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p = subprocess.check_call(args)
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
            return err[:-1]
        return output[:-1]
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
    except subprocess.CalledProcessError as ex:
        debug.error(f"subprocess.CalledProcessError : {args} ==> {ex}")
    except Exception as ex:
        debug.error(f"Exception : {args} ==> {ex}")
    # launch the subprocess:
    output, err = p.communicate()
    if sys.version_info >= (3, 0):
        output = output.decode("utf-8")
        err = err.decode("utf-8")
    # Check error :
    return [p.returncode, output[:-1], err[:-1]]
