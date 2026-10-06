"""Actions of island: one islandAction_NAME.py file per action, and the helpers they share.

The action loader finds the files named islandAction_NAME.py here and in the workspace (two levels down
at most), and runs the action NAME through these functions of its file:

- help() -> str: the description of the action; its first line is the one of the action list.
- help_example() -> str (optional): the examples shown after the arguments.
- add_specific_arguments(my_args, section) -> None (optional): declare the arguments of the action in
  the death.Arguments of the command line.
- have_unknow_argument() -> bool (optional): True to accept the arguments it does not declare.
- execute(arguments) -> int | None: run the action with its parsed arguments; None is a success, any
  other value is the exit code of island (a negative one, as the ret_action_* of island.env, is an error).
"""
