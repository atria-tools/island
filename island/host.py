#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Type of host detection.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""
import platform

from realog import debug


if platform.system() == "Linux":
    OS = "Linux"
elif platform.system() == "Windows":
    OS = "Windows"
elif platform.system() == "Darwin":
    OS = "MacOs"
else:
    debug.error(f"Unknown the Host OS ... '{platform.system()}'")

debug.debug("host.OS = {OS}")
