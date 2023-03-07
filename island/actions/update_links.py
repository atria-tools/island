# -*- coding: utf-8 -*-
"""Update tools.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug

from island import env, tools


# Update the links:
def update(configuration, mani, type_call):
    # TODO: do not remove link when not needed
    if len(configuration.get_links()) != 0 or len(mani.get_links()) != 0:
        debug.info(type_call + ": remove old links ...")
        for elem in configuration.get_links():
            base_path = os.path.join(env.get_island_root_path(), elem["destination"])
            debug.info(type_call + ":     link: " + str(base_path))
            if os.path.islink(base_path) is True:
                os.unlink(base_path)
            else:
                debug.error(
                    type_call + ": remove link is not authorised ==> not a link",
                    crash=False,
                )
                have_error = True
        configuration.clear_links()
        debug.info(type_call + ": add new links ...")
        for elem in mani.get_links():
            base_path = os.path.join(env.get_island_root_path(), elem["destination"])
            source_path = os.path.join(env.get_island_root_path(), elem["source"])
            debug.info(type_call + ":     link: " + str(base_path))
            if os.path.exists(base_path) is True:
                debug.error(
                    type_call + ": create link is not possible ==> path already exist",
                    crash=False,
                )
                have_error = True
            else:
                tools.create_directory_of_file(base_path)
                os.symlink(source_path, base_path)
                configuration.add_link(elem["source"], elem["destination"])
    configuration.store()
