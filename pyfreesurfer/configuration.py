##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides tools to configure FreeSurfer.
"""

# System import
import os
import re
import subprocess


def environment(sh_file=None, env={}):
    """ Function that return a dictionary containing the environment
    needed by a program (for instance FSL or FreeSurfer).

    In the configuration file, the variable are expected to be defined
    as 'VARIABLE_NAME=value'.

    Parameters
    ----------
    sh_file: str (mandatory)
        the path to the sh script used to set up the environment.
    env: dict (optional, default empty)
        the default environment used to parse the configuration sh file.

    Returns
    -------
    environment: dict
        a dict containing the program configuration.
    """
    # Use sh commands and a string instead of a list since
    # we're using shell=True
    # Pass empty environment to get only the program variables
    command = ["bash", "-c", ". '{0}' ; /usr/bin/printenv".format(sh_file)]
    process = subprocess.Popen(command, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if not isinstance(stdout, str):
        stdout = stdout.decode("utf8")
    if process.returncode != 0:
        raise Exception(
            "Could not parse 'sh_file' {0}. Maybe you should check if all "
            "the dependencies are installed".format(stderr))

    # Parse the output : each line should be of the form
    # 'VARIABLE_NAME=value'
    environment = {}
    for line in stdout.split(os.linesep):
        if line.startswith("export"):
            line = line.replace("export ", "")
            line = line.replace("'", "")
        match = re.match(r"^(\w+)=(\S*)$", line)
        if match:
            name, value = match.groups()
            if name != "PWD":
                environment[name] = value

    return environment


def concat_environment(env1, env2):
    """ Concatenate two environments.

    1 - Check duplicated keys and concatenate their values.
    2 - Update the concatenated environment.

    Parameters
    ----------
    env1: dict (mandatory)
        First environment.
    env2: dict (mandatory)
        Second environment.

    Returns
    -------
    concat_env: dict
        Updated environment where the duplicated keys values are concatenated
        with ':'.
    """
    concat_env = env1
    for key, value in env2.items():
        if key in concat_env.keys():
            if value != concat_env[key]:
                concat_env[key] += ":" + env2[key]
        else:
            concat_env[key] = env2[key]
    return concat_env
