"""Action script for init.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
    tools,
)


def help():
    return "Init a island repository (need 'fetch' after)"


def add_specific_arguments(my_args, section):
    my_args.add("b", "branch", haveParam=True, desc="Branch of the manifest (default: the default branch of the server)")
    my_args.add("m", "manifest", haveParam=True, desc="Name of the manifest")
    my_args.add("k", "ssh-key", haveParam=True, desc="Ssh private key used to access on the git servers (set in all the repository)")
    my_args.add("u", "user-name", haveParam=True, desc="Git user name (set in all the repository)")
    my_args.add("e", "user-email", haveParam=True, desc="Git user email (set in all the repository)")


def execute(_arguments):
    if len(_arguments) == 0:
        debug.error("Missing argument to execute the current action ...")

    # the configuration available:
    branch = ""  # the default branch of the server
    manifest_name = "default.xml"
    address_manifest = ""
    ssh_key = ""
    user_name = ""
    user_email = ""
    for elem in _arguments:
        if elem.get_option_name() == "branch":
            debug.info("find branch name: '" + elem.get_arg() + "'")
            branch = elem.get_arg()
        elif elem.get_option_name() == "manifest":
            debug.info("find mmanifest name: '" + elem.get_arg() + "'")
            manifest_name = elem.get_arg()
        elif elem.get_option_name() == "ssh-key":
            debug.info("find ssh key: '" + elem.get_arg() + "'")
            ssh_key = commands.get_ssh_key_path(elem.get_arg())
        elif elem.get_option_name() == "user-name":
            debug.info("find user name: '" + elem.get_arg() + "'")
            user_name = elem.get_arg()
        elif elem.get_option_name() == "user-email":
            debug.info("find user email: '" + elem.get_arg() + "'")
            user_email = elem.get_arg()
        elif elem.get_option_name() == "":
            if address_manifest != "":
                debug.error("Manifest adress already set : '" + address_manifest + "' !!! '" + elem.get_arg() + "'")
            address_manifest = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    if address_manifest == "":
        debug.error("Init: Missing manifest name")

    debug.info("Init with: '" + address_manifest + "' branch='" + branch + "' name of manifest='" + manifest_name + "'")

    # check if .XXX exist (create it if needed)
    if manifest.is_island_init() is True:
        debug.error("System already init: path already exist: '" + str(env.get_island_path()) + "'")

    tools.create_directory(env.get_island_path())
    # check if the git of the manifest if available

    # create the file configuration:
    conf = config.get_unique_config()
    conf.set_manifest(address_manifest)
    conf.set_branch(branch)
    conf.set_manifest_name(manifest_name)
    conf.set_ssh_key(ssh_key)
    conf.set_user_name(user_name)
    conf.set_user_email(user_email)
    conf.store()

    debug.info("Clone the manifest")
    commands.select_ssh_key(ssh_key)
    ret_values = commands.clone(env.get_island_path_manifest(), address_manifest, branch_name=branch)
    if ret_values is not False and ret_values[0] == 0:
        commands.configure_repository(env.get_island_path_manifest(), conf)

    if ret_values is False:
        debug.info("'" + str(ret_values) + "'")
        debug.error("Init does not work")
        return False

    debug.info("Init done correctly ...")

    return None
