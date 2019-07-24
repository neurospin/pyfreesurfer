##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides tools to wrap FreeSurfer commands.
"""

# System import
import os
import subprocess
import json
import re
import warnings

# Pyfreesurfer import
from .configuration import environment
from .configuration import concat_environment
from .exceptions import FreeSurferConfigurationError
from .exceptions import FreeSurferRuntimeError
from .exceptions import HCPConfigurationError
from .exceptions import HCPRuntimeError
from .info import DEFAULT_FREESURFER_PATH
from .info import DEFAULT_FSL_PATH
from .info import FREESURFER_RELEASE


class FSWrapper(object):
    """ Parent class for the wrapping of FreeSurfer functions.
    """
    def __init__(self, cmd, shfile=DEFAULT_FREESURFER_PATH, env=None,
                 subjects_dir=None, add_fsl_env=False, fsl_sh=None):
        """ Initialize the FSWrapper class by setting properly the
        environment.

        Parameters
        ----------
        cmd: list of str (mandatory)
            the FreeSurfer command to execute.
        shfile: str (optional, default NeuroSpin path)
            the path to the FreeSurfer 'SetUpFreeSurfer.sh' configuration file.
        env: dict (optional, default None)
            An environment to add to the FreeSurfer environment,
            e.g. os.environ to maintain current env in the FreeSurfer env.
        subjects_dir: str, default None.
            To set the $SUBJECTS_DIR environment variable.
        add_fsl_env:  bool, default False
            To activate the FSL environment, required for commands like
            bbregister.
        fsl_sh: str, default NeuroSpin path
            Path to the Bash script setting the FSL environment, if needed.
        """
        self.cmd = cmd
        self.shfile = shfile
        self.version = None
        self.environment = self._freesurfer_version_check()

        if env is not None:
            self.environment = concat_environment(self.environment, env)

        # If requested add FSL environment
        if add_fsl_env:
            # Import here so that the dependency is not mandatory for
            # the rest of the package
            from pyconnectome.wrapper import FSLWrapper
            if fsl_sh is None:
                fsl_sh = DEFAULT_FSL_PATH
            fsl_env = FSLWrapper([], shfile=fsl_sh).environment
            self.environment = concat_environment(self.environment, fsl_env)

        # Update the environment variables
        if subjects_dir is not None:
            self.environment["SUBJECTS_DIR"] = subjects_dir
        elif "SUBJECTS_DIR" in os.environ:
            self.environment["SUBJECTS_DIR"] = os.environ["SUBJECTS_DIR"]

        if (len(self.cmd) > 0 and self.cmd[0] == "tkmedit" and
                "DISPLAY" in os.environ):
            self.environment["DISPLAY"] = os.environ["DISPLAY"]

    def __call__(self):
        """ Run the FreeSurfer command.
        """
        # Check Freesurfer has been configured so the command can be found
        process = subprocess.Popen(["which", self.cmd[0]],
                                   env=self.environment,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode
        if self.exitcode != 0:
            raise FreeSurferConfigurationError(self.cmd[0])

        # Execute the command
        process = subprocess.Popen(
            self.cmd,
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode

        # Raise exception if exitcode is not zero
        if self.exitcode != 0:
            raise FreeSurferRuntimeError(
                self.cmd[0], " ".join(self.cmd[1:]), self.stderr + self.stdout)

    def _environment(self):
        """ Return a dictionary of the environment needed by FreeSurfer
        binaries.

        In order not to parse the configuration ntimes, it is stored in the
        'FREESURFER_CONFIGURED' environment variable.
        """
        # Check if FreeSurfer has already been configures
        env = os.environ.get("FREESURFER_CONFIGURED", None)

        # Configure FreeSurfer
        if env is None:

            # FreeSurfer home directory
            fs_home = os.environ.get("FREESURFER_HOME", None)
            env = {}
            if fs_home is not None:
                env["FREESURFER_HOME"] = fs_home

            # Parse configuration file
            env = environment(self.shfile, env)

            # Save the result
            os.environ["FREESURFER_CONFIGURED"] = json.dumps(env)

        # Load configuration
        else:
            env = json.loads(env)

        return env

    def _freesurfer_version_check(self):
        """ Check that a tested FreeSurfer version is installed. This method
        also returns the FreeSurfer environment.

        Returns
        -------
        environment: dict
            the configured FreeSurfer environment.
        """
        # If a configuration file is passed
        if os.path.isfile(self.shfile):

            # Parse FreeSurfer environment
            environment = self._environment()

            # Check FreeSurfer version
            version_file = os.path.join(environment["FREESURFER_HOME"],
                                        "build-stamp.txt")
            version_regex = "\d.\d.\d"
            with open(version_file, "r") as open_file:
                match_object = re.findall(version_regex, open_file.read())
                if len(match_object) != 1:
                    message = ("Can't detect 'FREESURFER' version from "
                               "version file '{0}'. You have not "
                               "provided a valid configuration file.".format(
                                   version_file))
                    raise ValueError(message)
                else:
                    self.version = match_object[0]
                    if self.version not in FREESURFER_RELEASE:
                        message = ("Installed '{0}' version of FreeSurfer "
                                   "not tested. Currently supported version "
                                   "is '{1}'.".format(self.version,
                                                      FREESURFER_RELEASE))
                        warnings.warn(message)

        # Configuration file is not a file
        else:
            message = ("'{0}' is not a valid file, can't configure "
                       "FreeSurfer.".format(self.shfile))
            raise ValueError(message)

        return environment


class HCPWrapper(object):
    """ Parent class for the wrapping of HCP functions.
    """
    def __init__(self, env, fslconfig=DEFAULT_FSL_PATH,
                 fsconfig=DEFAULT_FREESURFER_PATH):
        """ Initialize the HCPWrapper class.

        Parameters
        ----------
        env: dict (mandatory)
            the HCP environment.
        fslconfig: str (optional, default NeuroSpin path)
            the path to the FSL 'fsl.sh' configuration file.
        fsconfig: str (optional, default NeuroSpin path)
            the path to the FreeSurfer configuration file.
        """
        # Class parameter
        self.fslconfig = fslconfig
        self.fsconfig = fsconfig

        # Load FreeSurfer configuration
        fs_home = os.environ.get("FREESURFER_HOME", None)
        fs_env = {}
        if fs_home is not None:
            fs_env["FREESURFER_HOME"] = fs_home
        fs_env = environment(self.fsconfig, fs_env)

        # Load FSL configuration
        fsl_env = environment(self.fslconfig)

        # Concatenate FSL, FreeSurfer and current environment variables
        concat_env = concat_environment(fs_env, fsl_env)
        self.environment = concat_environment(concat_env, env)

    def __call__(self, cmd):
        """ Run the HCP command.

        Parameters
        ----------
        cmd: list of str (mandatory)
            the HCP command to execute.
        """
        # Check HCP pipelines has been configured so the command can be
        # found
        process = subprocess.Popen(
            ["which", cmd[0]],
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode
        if self.exitcode != 0:
            raise HCPConfigurationError(cmd[0])

        # Format the command
        fcmd = [cmd[0]]
        for indx, key in enumerate(cmd[1::2]):
            value = cmd[2 * indx + 2]
            fcmd.append("{0}={1}".format(key, value))

        # Execute the command
        process = subprocess.Popen(
            fcmd,
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode
        if self.exitcode != 0:
            error_message = ["STDOUT", "----", self.stdout, "STDERR", "----",
                             self.stderr]
            error_message = "\n".join(error_message)
            raise HCPRuntimeError(cmd[0], cmd, error_message)

    def freesurfer_version(self):
        """ Check for FreeSurfer version on system.

        Returns
        -------
        version : str
           version number as string or None if FreeSurfer not found.
        """
        try:
            fs_home = self.environment["FREESURFER_HOME"]
        except KeyError:
            return None
        version_file = os.path.join(fs_home, "build-stamp.txt")
        if not os.path.exists(version_file):
            return None
        with open(version_file, "rt") as fopen:
            version = fopen.readline()
        version_regex = "\d.\d.\d"
        version = re.findall(version_regex, version)[0]
        return version

    def fsl_version(self):
        """ Check for FSL version on system.

        Returns
        -------
        version : str
           version number as string or None if FSL not found.
        """
        try:
            basedir = self.environment["FSLDIR"]
        except KeyError:
            return None
        version_file = os.path.join(basedir, "etc", "fslversion")
        if not os.path.exists(version_file):
            return None
        with open(version_file, "rt") as fopen:
            out = fopen.read()
        return out.strip("\n")

    def gradunwarp_version(self):
        """ Check for gradunwarp version on system.

        Returns
        -------
        version : str
           version number as string or None if gradunwarp not found.
        """
        cmd = ["gradient_unwarp.py", "-v"]
        process = subprocess.Popen(
            cmd,
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exitcode = process.returncode
        if exitcode != 0:
            return None
        return stderr.strip("\n")

    def wbcommand_version(self):
        """ Check for wbcommand version on system.

        Returns
        -------
        version : str
           version number as string or None if wbcommand not found.
        """
        cmd = ["wb_command", "-version"]
        process = subprocess.Popen(
            cmd,
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exitcode = process.returncode
        if exitcode != 0:
            return None
        version_regex = "Version: \d.\d.\d"
        version = re.findall(version_regex, stdout)[0].replace("Version: ", "")
        return version

    def hcp_version(self):
        """ Check for HCP version on system.

        Returns
        -------
        version : str
           version number as string or None if HCP not found.
        """
        try:
            basedir = self.environment["HCPPIPEDIR"]
        except KeyError:
            return None
        version_file = os.path.join(basedir, "version.txt")
        if not os.path.exists(version_file):
            return None
        with open(version_file, "rt") as open_file:
            version = open_file.read()
        return version.strip("\n")
