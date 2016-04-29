##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from collections import namedtuple
import unittest
import sys
import copy
import os
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
from pyfreesurfer.plots.slicer import tkmedit_slice


class FreeSurferSlicer(unittest.TestCase):
    """ Test the FreeSurfer slicer:
    'pyfreesurfer.plots.slicer.tkmedit_slice'
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
            "sid": "Lola",
            "outdir": "/my/path/mock_outdir",
            "stype": "edges",
            "cut_axis": "C",
            "slice_interval": (0, 255, 1),
            "path_lut": "/my/path/mock_lut",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    def test_badstypeerror_raise(self):
        """ Bad slice type -> raise ValueError.
        """
        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["stype"] = "WRONG"
        self.assertRaises(ValueError, tkmedit_slice, **wrong_kwargs)

    def test_noluterror_raise(self):
        """ No lookup table -> raise ValueError.
        """
        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["stype"] = "aseg"
        wrong_kwargs["path_lut"] = None
        self.assertRaises(ValueError, tkmedit_slice, **wrong_kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_badluteerror_raise(self, mock_isfile):
        """ Bad lookup table -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["stype"] = "aseg"
        self.assertRaises(ValueError, tkmedit_slice, **wrong_kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_badaxiseerror_raise(self, mock_isfile):
        """ Bad cut axis -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["stype"] = "aseg"
        wrong_kwargs["cut_axis"] = "WRONG"
        self.assertRaises(ValueError, tkmedit_slice, **wrong_kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.path.isdir")
    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_badsubjdireerror_raise(self, mock_isfile, mock_isdir):
        """ Bad subject directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, tkmedit_slice, **self.kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.path.isdir")
    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_badoutdireerror_raise(self, mock_isfile, mock_isdir):
        """ Bad output directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]
        mock_isdir.side_effect = [True, False]

        # Test execution
        self.assertRaises(ValueError, tkmedit_slice, **self.kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.path.isdir")
    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_badanateerror_raise(self, mock_isfile, mock_isdir):
        """ Bad anatomical file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False]
        mock_isdir.side_effect = [True, True]

        # Test execution
        self.assertRaises(ValueError, tkmedit_slice, **self.kwargs)

    @mock.patch("pyfreesurfer.plots.slicer.os.remove")
    @mock.patch("pyfreesurfer.plots.slicer.glob.glob")
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.plots.slicer.os.path.isdir")
    @mock.patch("pyfreesurfer.plots.slicer.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_isdir, mock_open,
                              mock_glob, mock_remove):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]
        mock_isdir.side_effect = [True, True]
        mock_glob.return_value = ["/my/path/mock_snap.rgb"]

        # Test execution
        slices = tkmedit_slice(**self.kwargs)
        path_script = os.path.join(
            self.kwargs["outdir"],
            "tkmedit_slicer_{0}.tcl".format(self.kwargs["cut_axis"]))
        self.assertEqual(
            slices,
            [item.replace(".rgb", ".png") for item in mock_glob.return_value])
        self.assertEqual([
            mock.call(mock_glob.return_value[0])],
            mock_remove.call_args_list)
        self.assertEqual(len(self.mock_popen.call_args_list), 4)
        self.assertEqual(len(self.mock_env.call_args_list), 2)


if __name__ == "__main__":
    unittest.main()
