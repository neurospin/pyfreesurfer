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
from pyfreesurfer.conversions.volconvs import mri_binarize
from pyfreesurfer.conversions.volconvs import mri_convert
from pyfreesurfer.conversions.volconvs import mri_vol2surf


class FreeSurferMRIBinarize(unittest.TestCase):
    """ Test the FreeSurfer label map binarization:
    'pyfreesurfer.conversions.volconvs.mri_binarize'
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
            "inputfile": "/my/path/mock_infile",
            "outputfile": "/my/path/mock_outfile",
            "match": [2, 10],
            "wm": True,
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, mri_binarize, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_normal_execution(self, mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]

        # Test execution
        mri_binarize(**self.kwargs)
        self.assertEqual([
            mock.call(["which", "mri_binarize"], env={}, stderr=-1, stdout=-1),
            mock.call(["mri_binarize", "--i", self.kwargs["inputfile"],
                       "--o", self.kwargs["outputfile"], "--match"] +
                      self.kwargs["match"] + ["--wm"],
                      env={}, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)


class FreeSurferMRIConvert(unittest.TestCase):
    """ Test the FreeSurfer exportation:
    'pyfreesurfer.conversions.volconvs.mri_convert'
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
            "regex": "mock_regex",
            "outdir": "/my/path/mock_outdir",
            "reslice": True,
            "interpolation": "interpolate",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, mri_convert, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    def test_badinterpolationerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["interpolation"] = "WRONG"
        self.assertRaises(ValueError, mri_convert, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.makedirs")
    @mock.patch("pyfreesurfer.conversions.volconvs.glob.glob")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    def test_badreferenceerror_execution(self, mock_isdir, mock_glob,
                                         mock_mkdir, mock_isfile):
        """ Bad reference file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False]
        mock_glob.return_value = ["/my/path/mock_tobeconverted"]
        mock_isfile.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, mri_convert, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.makedirs")
    @mock.patch("pyfreesurfer.conversions.volconvs.glob.glob")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob, mock_mkdir,
                              mock_isfile):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False]
        mock_glob.return_value = [
            "/my/path/mock_fsdir/Lola/mri/mock_tobeconverted.mgz"]
        mock_isfile.side_effect = [True]

        # Test execution
        niftifiles = mri_convert(**self.kwargs)
        basename = os.path.basename(mock_glob.return_value[0]).replace(
            ".mgz", "")
        converted_file = os.path.join(self.kwargs["outdir"], "Lola", "convert",
                                      basename + ".native.nii.gz")
        reference_file = os.path.join(self.kwargs["fsdir"], "Lola", "mri",
                                      "rawavg.mgz")
        self.assertEqual([
            mock.call(["which", "mri_convert"], env={}, stderr=-1, stdout=-1),
            mock.call(["mri_convert", "--resample_type",
                       self.kwargs["interpolation"], "--reslice_like",
                       reference_file, mock_glob.return_value[0],
                       converted_file], env={}, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)


class FreeSurferMRIVol2Surf(unittest.TestCase):
    """ Test the FreeSurfer volume to surface method:
    'pyfreesurfer.conversions.volconvs.mri_vol2surf'
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
            "hemi": "lh",
            "volume_file": "/my/path/mock_volumefile",
            "out_texture_file": "/my/path/mock_outtexturefile",
            "ico_order": 7,
            "dat_file": "/my/path/mock_datfile",
            "fsdir": "/my/path/mock_fsdir",
            "sid": "Lola",
            "surface_name": "white",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, mri_vol2surf, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_baddirerror_raise(self, mock_isfile, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, mri_vol2surf, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_badhemierror_raise(self, mock_isfile, mock_isdir):
        """ Wrong hemisphere name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["hemi"] = "WRONG"
        self.assertRaises(ValueError, mri_vol2surf, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_badsurfaceerror_raise(self, mock_isfile, mock_isdir):
        """ Wrong surface name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["surface_name"] = "WRONG"
        self.assertRaises(ValueError, mri_vol2surf, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_badicoordererror_raise(self, mock_isfile, mock_isdir):
        """ Wrong ico order -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True, True, True]
        mock_isdir.side_effect = [True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["ico_order"] = -1
        self.assertRaises(ValueError, mri_vol2surf, **wrong_kwargs)
        wrong_kwargs["ico_order"] = 8
        self.assertRaises(ValueError, mri_vol2surf, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_isdir):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        mri_vol2surf(**self.kwargs)
        self.assertEqual([
            mock.call(["which", "mri_vol2surf"], env={}, stderr=-1, stdout=-1),
            mock.call(["mri_vol2surf", "--src", self.kwargs["volume_file"],
                       "--out", self.kwargs["out_texture_file"],
                       "--srcreg", self.kwargs["dat_file"], "--hemi",
                       self.kwargs["hemi"], "--trgsubject", "ico",
                       "--icoorder", "{0}".format(self.kwargs["ico_order"]),
                       "--surf", self.kwargs["surface_name"], "--sd",
                       self.kwargs["fsdir"], "--srcsubject",
                       self.kwargs["sid"], "--noreshape", "--out_type",
                       "mgz"], env={}, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)


if __name__ == "__main__":
    unittest.main()
