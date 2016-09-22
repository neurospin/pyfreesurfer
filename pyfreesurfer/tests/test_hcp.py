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
import copy
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
    from mock import patch
else:
    import unittest.mock as mock
    from unittest.mock import patch

# Pyfreesurfer import
from pyfreesurfer.hcp import prefreesurfer_hcp
from pyfreesurfer.hcp import freesurfer_hcp
from pyfreesurfer.hcp import postfreesurfer_hcp


class PreFreeSurferHCP(unittest.TestCase):
    """ Test the prefreesurfer HCP script wrapping:
    'pyfreesurfer.hcp.prefreesurfer_hcp'
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

        # Define function parameters
        self.kwargs = {
            "path": "/my/path/mock_workdir",
            "subject": "Lola",
            "t1": ["/my/path/mock_t1"],
            "t2": ["/my/path/mock_t2"],
            "fmapmag": "/my/path/mock_mag",
            "fmapphase": "/my/path/mock_phase",
            "hcpdir": "/my/path/mock_hcp",
            "brainsize": 150,
            "fmapgeneralelectric": "NONE",
            "echodiff": 2.46,
            "SEPhaseNeg": "NONE",
            "SEPhasePos": "NONE",
            "echospacing": "NONE",
            "seunwarpdir": "NONE",
            "t1samplespacing": 0.0000074,
            "t2samplespacing": 0.0000021,
            "unwarpdir": "z",
            "gdcoeffs": "NONE",
            "avgrdcmethod": "SiemensFieldMap",
            "topupconfig": "NONE",
            "wbcommand": "/my/path/mock_wb",
            "fslconfig": "/my/path/mock_fsl",
            "fsconfig": "/my/path/mock_fs"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()

    def test_baddirerror_raise(self):
        """ Bad input directory -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, prefreesurfer_hcp, **self.kwargs)

    @mock.patch("pyfreesurfer.hcp.os.path.isdir")
    def test_badfileerror_raise(self, mock_isdir):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, False]

        # Test execution
        self.assertRaises(ValueError, prefreesurfer_hcp, **self.kwargs)

    @mock.patch("pyfreesurfer.hcp.os.path.isfile")
    @mock.patch("pyfreesurfer.hcp.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, False]
        mock_isfile.side_effect = [True, True, True, True, False]

        # Test execution
        t1w_folder, t1_img, t1_img_brain, t2_img = prefreesurfer_hcp(
            **self.kwargs)

        workdir = os.path.join(self.kwargs["path"], self.kwargs["subject"],
                               "T1w")
        self.assertEqual(
            t1_img,
            os.path.join(workdir, "T1w_acpc_dc_restore.nii.gz"))
        self.assertEqual(
            t1_img_brain,
            os.path.join(workdir, "T1w_acpc_dc_restore_brain.nii.gz"))
        self.assertEqual(
            t2_img,
            os.path.join(workdir, "T2w_acpc_dc_restore.nii.gz"))
        self.assertEqual(len(mock_isdir.call_args_list), 3)
        self.assertEqual(len(mock_isfile.call_args_list), 4)


class FreeSurferHCP(unittest.TestCase):
    """ Test the freesurfer HCP script wrapping:
    'pyfreesurfer.hcp.freesurfer_hcp'
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

        # Define function parameters
        self.kwargs = {
            "subject": "Lola",
            "t1w_folder": "/my/path/mock_t1_folder",
            "t1_img": "/my/path/mock_t1",
            "t1_img_brain": "/my/path/mock_t1_brain",
            "t2_img": "/my/path/mock_t2",
            "hcpdir": "/my/path/mock_hcp",
            "wbcommand": "/my/path/mock_wb",
            "fslconfig": "/my/path/mock_fsl",
            "fsconfig": "/my/path/mock_fs"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()

    def test_baddirerror_raise(self):
        """ Bad input directory -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, freesurfer_hcp, **self.kwargs)

    @mock.patch("pyfreesurfer.hcp.os.path.isdir")
    def test_badfileerror_raise(self, mock_isdir):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, False]

        # Test execution
        self.assertRaises(ValueError, freesurfer_hcp, **self.kwargs)

    @mock.patch("pyfreesurfer.hcp.os.path.isfile")
    @mock.patch("pyfreesurfer.hcp.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, False]
        mock_isfile.side_effect = [True, True, True, False]

        # Test execution
        freesurfer_hcp(**self.kwargs)
        self.assertEqual(len(mock_isdir.call_args_list), 3)
        self.assertEqual(len(mock_isfile.call_args_list), 3)


class PostFreeSurferHCP(unittest.TestCase):
    """ Test the postfreesurfer HCP script wrapping:
    'pyfreesurfer.hcp.postfreesurfer_hcp'
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

        # Define function parameters
        self.kwargs = {
            "path": "/my/path/mock_path",
            "subject": "Lola",
            "hcpdir": "/my/path/mock_hcp",
            "wbcommand": "/my/path/mock_wb",
            "fslconfig": "/my/path/mock_fsl",
            "fsconfig": "/my/path/mock_fs"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()

    def test_baddirerror_raise(self):
        """ Bad input directory -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, postfreesurfer_hcp, **self.kwargs)

    @mock.patch("pyfreesurfer.hcp.os.path.isdir")
    def test_normal_execution(self, mock_isdir):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, False]

        # Test execution
        postfreesurfer_hcp(**self.kwargs)
        self.assertEqual(len(mock_isdir.call_args_list), 3)


if __name__ == "__main__":
    unittest.main()
