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
from pyfreesurfer.segmentation.cortical import recon_all
from pyfreesurfer.segmentation.cortical import recon_all_custom_wm_mask
from pyfreesurfer.segmentation.cortical import recon_all_longitudinal


class FreeSurferReconAll(unittest.TestCase):
    """ Test the FreeSurfer cortical reconstruction steps:
    'pyfreesurfer.segmentation.cortical.recon_all'
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
            "anatfile": "/my/path/mock_anat",
            "sid": "Lola",
            "reconstruction_stage": "all",
            "resume": False,
            "t2file": "/my/path/mock_t2",
            "flairfile": None,
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, recon_all, **self.kwargs)

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_badstageerror_raise(self, mock_isdir):
        """ Bad input stage -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["reconstruction_stage"] = "WRONG"
        self.assertRaises(ValueError, recon_all, **wrong_kwargs)

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_normal_execution(self, mock_isdir):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True]

        # Test execution
        subjfsdir = recon_all(**self.kwargs)
        cenv = {}
        if "SUBJECTS_DIR" in os.environ:
            cenv = {"SUBJECTS_DIR": os.environ["SUBJECTS_DIR"]}
        self.assertEqual([
            mock.call(["which", "recon-all"], env=cenv, stderr=-1, stdout=-1),
            mock.call([
                "recon-all", "-all", "-subjid", self.kwargs["sid"],
                "-i", self.kwargs["anatfile"], "-sd",
                self.kwargs["fsdir"], "-noappend", "-no-isrunning",
                "-T2", self.kwargs["t2file"], "-T2pial"],
                env=cenv, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)
        self.assertEqual(subjfsdir, os.path.join(self.kwargs["fsdir"],
                                                 self.kwargs["sid"]))


class FreeSurferReconAllCustomMask(unittest.TestCase):
    """ Test the FreeSurfer cortical reconstruction steps with custom mask:
    'pyfreesurfer.segmentation.cortical.recon_all_custom_wm_mask'
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
            "subjects_dir": "/my/path/mock_fsdir",
            "wm_mask": "/my/path/mock_wmmask",
            "subject_id": "Lola",
            "keep_orig": True,
            "temp_dir": False,
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    @mock.patch("pyfreesurfer.segmentation.cortical."
                "get_or_check_freesurfer_subjects_dir")
    def test_baddirerror_raise(self, mock_fsdir, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_fsdir.return_value = self.kwargs["subjects_dir"]
        mock_isdir.return_value = False

        # Test execution
        self.assertRaises(ValueError, recon_all_custom_wm_mask, **self.kwargs)

    @mock.patch("pyfreesurfer.segmentation.cortical.shutil.rmtree")
    @mock.patch("pyfreesurfer.segmentation.cortical.shutil.move")
    @mock.patch("pyfreesurfer.segmentation.cortical.tempfile.mkdtemp")
    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    @mock.patch("pyfreesurfer.segmentation.cortical."
                "get_or_check_freesurfer_subjects_dir")
    def test_normal_execution(self, mock_fsdir, mock_isdir, mock_tmpfile,
                              mock_move, mock_rmtree):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_fsdir.return_value = self.kwargs["subjects_dir"]
        mock_isdir.side_effect = [True, False]
        mock_tmpfile.return_value = "/my/path/mock_recon_all_custom_wm_mask"

        # Test execution
        subject_dir = recon_all_custom_wm_mask(**self.kwargs)
        self.assertEqual(len(self.mock_popen.call_args_list), 6)


class FreeSurferReconAllLongitudinal(unittest.TestCase):
    """ Test the FreeSurfer longitudinal cortical reconstruction steps:
    'pyfreesurfer.segmentation.cortical.recon_all_longitudinal'
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
            "outdir": "/my/path/mock_outdir",
            "subjects_dirs": ["/my/path/mock_fsdir1", "/my/path/mock_fsdir2"],
            "subject_id": "Lola",
            "timepoints": None,
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.return_value = False

        # Test execution
        self.assertRaises(ValueError, recon_all_longitudinal, **self.kwargs)

    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_bad_timepoint(self, mock_isdir):
        """ Bad timepoint -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["timepoints"] = ["T1"]
        self.assertRaises(ValueError, recon_all_longitudinal, **wrong_kwargs)

    @mock.patch("pyfreesurfer.segmentation.cortical.os.symlink")
    @mock.patch("pyfreesurfer.segmentation.cortical.os.mkdir")
    @mock.patch("pyfreesurfer.segmentation.cortical.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_mkdir, mock_symlink):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False, False]

        # Test execution
        subject_template_id, subject_long_ids = recon_all_longitudinal(
            **self.kwargs)
        self.assertEqual(len(self.mock_popen.call_args_list), 6)


if __name__ == "__main__":
    unittest.main()
