"""System call Interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from collections.abc import Container
import shlex
import subprocess
from typing import Literal, NamedTuple

# Local import
from realog import debug


class CommandResult(NamedTuple):
    """Result of a command: its return code, then its outputs without their last new line."""

    returncode: int
    stdout: str
    stderr: str


def generic_display_error(
    return_value: CommandResult,
    type_name: str,
    error_only: bool = False,
    available_return: Container[int] = (0,),
    display_if_nothing: bool = True,
) -> None:
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


def _start(cmd_line: str, cwd: str | None) -> subprocess.Popen[bytes]:
    """Start a command line (split as a shell does, but run without shell); stop island when it cannot start."""
    args = shlex.split(cmd_line)
    debug.verbose("cmd = " + str(args))
    try:
        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    except Exception as ex:
        debug.error(f"Exception : {args} ==> {ex}")
        raise


def run_command_direct(cmd_line: str, cwd: str | None = None) -> str | Literal[False]:
    """Execute a command.

    :return: its standard output without the last new line, or False when it failed
    """
    process = _start(cmd_line, cwd)
    output, _err = process.communicate()
    if process.returncode == 0:
        return output.decode("utf-8")[:-1]
    return False


def run_command(cmd_line: str, cwd: str | None = None) -> CommandResult:
    """Execute a command.

    :return: its return code and its outputs
    """
    process = _start(cmd_line, cwd)
    output, err = process.communicate()
    return CommandResult(process.returncode, output.decode("utf-8")[:-1], err.decode("utf-8")[:-1])
