##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest
import sys
import os
import textwrap
import numpy
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
    from mock import patch
else:
    import unittest.mock as mock
    from unittest.mock import patch

# Pyfreesurfer import
from pyfreesurfer.utils.regtools import conformed_to_native_space
from pyfreesurfer.utils.regtools import tkregister_translation


class FreeSurferTranslation(unittest.TestCase):
    """ Test the translation extraction:
    'pyfreesurfer.utils.regtools.tkregister_translation'
    """
    def setUp(self):
        """ Run before each test - the mock_popen will be available and in the
        right state in every test<something> function.
        """
        # Define affine representation
        affine = """ -1.00000    0.00000    0.00000  126.09036
        0.00000    0.00000    1.00000  -97.27711
        0.00000   -1.00000    0.00000   98.27710
        0.00000    0.00000    0.00000    1.00000
        """
        # Mocking popen
        self.popen_patcher = patch("pyfreesurfer.wrapper.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": (textwrap.dedent(affine),
                                         "mock_NONE"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        self.mock_popen.return_value = mock_process

        # Mocking set environ
        self.env_patcher = patch(
            "pyfreesurfer.wrapper.FSWrapper._freesurfer_version_check")
        self.mock_env = self.env_patcher.start()
        self.mock_env.return_value = {}

        # Define function parameters
        self.kwargs = {
            "mgzfile": "/my/path/mock_mgz",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.utils.regtools.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, tkregister_translation, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.regtools.os.path.isfile")
    def test_normal_execution(self, mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]

        # Test execution
        translation = tkregister_translation(**self.kwargs)
        self.assertEqual([mock.call(self.kwargs["mgzfile"])],
                         mock_isfile.call_args_list)
        self.assertEqual(len(self.mock_popen.call_args_list), 4)
        self.assertEqual(len(self.mock_env.call_args_list), 2)
        self.assertTrue(numpy.allclose(translation, numpy.eye(4)))


class FreeSurferConformedToNative(unittest.TestCase):
    """ Test the conformed to native transformation extraction:
    'pyfreesurfer.utils.regtools.conformed_to_native_space'
    """
    def setUp(self):
        """ Run before each test - the mock_popen will be available and in the
        right state in every test<something> function.
        """
        # Mocking popen
        self.popen_patcher = patch("pyfreesurfer.wrapper.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": ("mock_OK", "mock_NONE"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        self.mock_popen.return_value = mock_process

        # Mocking set environ
        self.env_patcher = patch(
            "pyfreesurfer.wrapper.FSWrapper._freesurfer_version_check")
        self.mock_env = self.env_patcher.start()
        self.mock_env.return_value = {}

        # Define function parameters
        self.kwargs = {
            "fsdir": "/my/path/mock_fsdir",
            "regex": "/my/path/mock_regex",
            "outdir": "/my/path/mock_outdir",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.utils.regtools.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, conformed_to_native_space, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.regtools.os.path.isfile")
    @mock.patch("pyfreesurfer.utils.regtools.glob.glob")
    @mock.patch("pyfreesurfer.utils.regtools.os.path.isdir")
    def test_badfileerror_raise(self, mock_isdir, mock_glob, mock_isfile):
        """ Bad mri file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_isfile.side_effect = [False, True]
        mock_glob.return_value = ["my/path/mock_mri"]

        # Test execution
        self.assertRaises(ValueError, conformed_to_native_space, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.regtools.os.path.isfile")
    @mock.patch("pyfreesurfer.utils.regtools.glob.glob")
    @mock.patch("pyfreesurfer.utils.regtools.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob, mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_isfile.side_effect = [True, True]
        mock_glob.return_value = ["my/path/mock_mri"]

        # Test execution
        trffile = os.path.join(self.kwargs["outdir"], "path", "convert",
                               "register.native.dat")
        trffiles = conformed_to_native_space(**self.kwargs)
        self.assertEqual(len(mock_isdir.call_args_list), 3)
        self.assertEqual(len(mock_isfile.call_args_list), 2)
        self.assertEqual(len(self.mock_popen.call_args_list), 2)
        self.assertEqual(len(self.mock_env.call_args_list), 1)
        self.assertEqual(trffiles, [trffile])


if __name__ == "__main__":
    unittest.main()
