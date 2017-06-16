##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest
import sys
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
    from mock import patch
    mock_builtin = "__builtin__"
else:
    import unittest.mock as mock
    from unittest.mock import patch
    mock_builtin = "builtins"

# Pyfreesurfer import
from pyfreesurfer.exceptions import FreeSurferRuntimeError
from pyfreesurfer.exceptions import FreeSurferConfigurationError
from pyfreesurfer.exceptions import HCPRuntimeError
from pyfreesurfer.exceptions import HCPConfigurationError


class FreeSurferError(unittest.TestCase):
    """ Test the FreeSurfer error messages:
    'pyfreesurfer.exceptions.FreeSurferError'
    """
    def test_normal_execution(self):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        FreeSurferRuntimeError("algorithm_name", "parameters", error="error")
        FreeSurferConfigurationError("command_name")


class HCPError(unittest.TestCase):
    """ Test the HCP error messages:
    'pyfreesurfer.exceptions.HCPError'
    """
    def test_normal_execution(self):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        HCPRuntimeError("algorithm_name", "parameters", error="error")
        HCPConfigurationError("command_name")


if __name__ == "__main__":
    unittest.main()
