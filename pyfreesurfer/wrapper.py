##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import subprocess
import json
import re
import warnings

# Pyfreesurfer import
from .configuration import environment
from .exceptions import FreeSurferConfigurationError
from .exceptions import FreeSurferRuntimeError
from .info import DEFAULT_FREESURFER_PATH
from .info import FREESURFER_RELEASE


class FSWrapper(object):
    """ Parent class for the wrapping of FreeSurfer functions.
    """
    def __init__(self, cmd, shfile=DEFAULT_FREESURFER_PATH):
        """ Initialize the FSWrapper class by setting properly the
        environment.

        Parameters
        ----------
        cmd: list of str (mandatory)
            the FreeSurfer command to execute.
        shfile: str (optional, default NeuroSpin path)
            the path to the FreeSurfer 'SetUpFreeSurfer.sh' configuration file.
        """
        self.cmd = cmd
        self.shfile = shfile
        self.version = None
        self.environment = self._freesurfer_version_check()

        # Update the environment variables
        if "SUBJECTS_DIR" in os.environ:
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

        # Raise exception of exitcode is not zero
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
                    if self.version != FREESURFER_RELEASE:
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
