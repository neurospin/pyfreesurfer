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
import math
import nibabel
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
from pyfreesurfer.conversions.surfconvs import interhemi_surfreg
from pyfreesurfer.conversions.surfconvs import midgray_surface
from pyfreesurfer.conversions.surfconvs import mri_surf2surf
from pyfreesurfer.conversions.surfconvs import resample_cortical_surface
from pyfreesurfer.conversions.surfconvs import surf_convert


class FreeInterhemiSurfreg(unittest.TestCase):
    """ Test the FreeSurfer inter hemispheric surface regularization:
    'pyfreesurfer.conversions.surfconvs.interhemi_surfreg'
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
            "outdir": "/my/path/mock_outdir",
            "fsdir": "/my/path/mock_fsdir",
            "sid": "Lola",
            "template_file": "/my/path/mock_template",
            "destname": "surfreg",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    def test_badhemierror_raise(self):
        """ Wrong hemisphere name -> raise ValueError.
        """
        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["hemi"] = "WRONG"
        self.assertRaises(ValueError, interhemi_surfreg, **wrong_kwargs)

    def test_baddirerror_raise(self):
        """ Bad input directory -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, interhemi_surfreg, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.unlink")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.symlink")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.listdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.mkdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.islink")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    def test_badhemierror_raise(self, mock_isdir, mock_islink, mock_mkdir,
                                mock_listdir, mock_link, mock_unlink):
        """ Wrong hemisphere name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False, False]
        mock_islink.side_effect = [True, False]
        mock_listdir.return_value = ["scripts", "mri"]
        mock_link.return_value = True
        mock_unlink.return_value = True
        mock_mkdir.return_value = True

        # Test execution
        xhemidir, spherefile = interhemi_surfreg(**self.kwargs)
        cenv = {}
        if "SUBJECTS_DIR" in os.environ:
            cenv = {"SUBJECTS_DIR": os.environ["SUBJECTS_DIR"]}
        self.assertEqual([
            mock.call(["which", "surfreg"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["surfreg", "--s", self.kwargs["destname"], "--t",
                       "fsaverage_sym", "--{0}".format(self.kwargs["hemi"])],
                      env=cenv, stderr=-1, stdout=-1),
            mock.call(["which", "xhemireg"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["xhemireg", "--s", self.kwargs["destname"]], env=cenv,
                      stderr=-1, stdout=-1),
            mock.call(["which", "surfreg"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["surfreg", "--s", self.kwargs["destname"], "--t",
                       "fsaverage_sym", "--{0}".format(self.kwargs["hemi"]),
                       "--xhemi"],
                      env=cenv, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(
            os.path.join(self.kwargs["outdir"], self.kwargs["destname"],
                         "xhemi"),
            xhemidir)
        self.assertEqual(
            os.path.join(self.kwargs["fsdir"], self.kwargs["sid"], "surf",
                         "{0}.fsaverage_sym.sphere.reg".format(
                                self.kwargs["hemi"])),
            spherefile)


class FreeSurferMidgraySurface(unittest.TestCase):
    """ Test the FreeSurfer mid-thickness gray surface extraction:
    'pyfreesurfer.conversions.surfconvs.midgray_surface'
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
            "outdir": "/my/path/mock_outdir",
            "fsdir": "/my/path/mock_fsdir",
            "sid": "Lola",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    def test_badfileerror_raise(self):
        """ Bad input file -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, midgray_surface, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_baddirerror_raise(self, mock_isfile):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, False]

        # Test execution
        self.assertRaises(ValueError, midgray_surface, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badhemierror_raise(self, mock_isfile, mock_isdir):
        """ Wrong hemisphere name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, False]
        mock_isdir.side_effect = [True, False]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["hemi"] = "WRONG"
        self.assertRaises(ValueError, midgray_surface, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.islink")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_isdir, mock_islink):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_islink.return_value = True
        mock_isfile.side_effect = [True, False]
        mock_isdir.side_effect = [True, False]

        # Test execution
        midgray_file, mirror_midgray_file = midgray_surface(**self.kwargs)
        white_file = os.path.join(
            self.kwargs["fsdir"], self.kwargs["sid"], "surf",
            "{0}.white".format(self.kwargs["hemi"]))
        cenv = {}
        if "SUBJECTS_DIR" in os.environ:
            cenv = {"SUBJECTS_DIR": os.environ["SUBJECTS_DIR"]}
        self.assertEqual([
            mock.call(["which", "mris_expand"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["mris_expand", "-thickness", white_file, "0.5",
                      midgray_file],
                      env=cenv, stderr=-1, stdout=-1),
            mock.call(["which", "mris_expand"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["mris_expand", "-thickness", white_file, "-0.5",
                      mirror_midgray_file],
                      env=cenv, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 2)


class FreeSurferMRISurf2Surf(unittest.TestCase):
    """ Test the FreeSurfer vertices resampling:
    'pyfreesurfer.conversions.surfconvs.mri_surf2surf'
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
            "input_surface_file": "/my/path/mock_inputfile",
            "output_surface_file": "/my/path/mock_outputfile",
            "ico_order": 7,
            "fsdir": "/my/path/mock_fsdir",
            "sid": "Lola",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, mri_surf2surf, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_baddirerror_raise(self, mock_isfile, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True]
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, mri_surf2surf, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badhemierror_raise(self, mock_isfile, mock_isdir):
        """ Wrong hemisphere name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["hemi"] = "WRONG"
        self.assertRaises(ValueError, mri_surf2surf, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badicoordererror_raise(self, mock_isfile, mock_isdir):
        """ Wrong ico order -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True, True, True]
        mock_isdir.side_effect = [True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["ico_order"] = -1
        self.assertRaises(ValueError, mri_surf2surf, **wrong_kwargs)
        wrong_kwargs["ico_order"] = 8
        self.assertRaises(ValueError, mri_surf2surf, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_isdir):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        cenv = {}
        if "SUBJECTS_DIR" in os.environ:
            cenv = {"SUBJECTS_DIR": os.environ["SUBJECTS_DIR"]}
        mri_surf2surf(**self.kwargs)
        self.assertEqual([
            mock.call(["which", "mri_surf2surf"], env=cenv, stderr=-1,
                      stdout=-1),
            mock.call(["mri_surf2surf", "--hemi", self.kwargs["hemi"],
                       "--srcsurfval", self.kwargs["input_surface_file"],
                       "--srcsubject", self.kwargs["sid"], "--trgsubject",
                       "ico", "--trgicoorder", str(self.kwargs["ico_order"]),
                       "--trgsurfval", self.kwargs["output_surface_file"],
                       "--sd", self.kwargs["fsdir"], "--trg_type", "mgz"],
                      env=cenv, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)


class FreeSurferResampleCorticalSurface(unittest.TestCase):
    """ Test the FreeSurfer cortical surface resampling:
    'pyfreesurfer.conversions.surfconvs.resample_cortical_surface'
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
            "regex": "Lola/surf/lh.white",
            "outdir": "/my/path/mock_outdir",
            "destdirname": "convert",
            "orders": [4, 5, 6, 7],
            "surface_name": "white",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, resample_cortical_surface, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.volconvs.os.path.isdir")
    def test_badsurfaceerror_raise(self, mock_isdir):
        """ Wrong surface name -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["surface_name"] = "WRONG"
        self.assertRaises(ValueError, resample_cortical_surface,
                          **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    def test_badicoordererror_raise(self, mock_isdir):
        """ Wrong ico order -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["orders"] = [-1, 2]
        self.assertRaises(ValueError, resample_cortical_surface,
                          **wrong_kwargs)
        wrong_kwargs["orders"] = [2, 8]
        self.assertRaises(ValueError, resample_cortical_surface,
                          **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.makedirs")
    @mock.patch("pyfreesurfer.conversions.surfconvs.glob.glob")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob, mock_makedirs):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, False]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"],
                                               self.kwargs["regex"])]

        # Test execution
        resamplefiles, annotfiles = resample_cortical_surface(**self.kwargs)
        self.assertEqual(len(self.mock_popen.call_args_list), 16)
        self.assertEqual(len(self.mock_env.call_args_list), 8)
        expected_resamplefiles = [
            os.path.join(self.kwargs["outdir"], "Lola", "convert",
                         "lh.white.{0}".format(i))
            for i in self.kwargs["orders"]]
        expected_annotfiles = [
            os.path.join(self.kwargs["outdir"], "Lola", "convert",
                         "lh.aparc.annot.{0}".format(i))
            for i in self.kwargs["orders"]]
        self.assertEqual(expected_resamplefiles, resamplefiles)
        self.assertEqual(expected_annotfiles, annotfiles)


class FreeSurferSurfConvert(unittest.TestCase):
    """ Test the FreeSurfer surface to native space exportation:
    'pyfreesurfer.conversions.surfconvs.surf_conver'
    """
    def setUp(self):
        """ Define function parameters.
        """
        self.kwargs = {
            "fsdir": "/my/path/mock_fsdir",
            "t1files": ["/my/path/Lola/mri/mock_t1"],
            "surffiles": ["/my/path/out/Lola/surf/mock_surf"],
            "sidpos": -3,
            "rm_orig": True,
            "fsconfig": "/my/path/mock_fsconfig"
        }
        f = math.sqrt(2.0) / 2.0
        self.verts = [
            (0, -1, 0),
            (-f, 0, f),
            (f, 0, f),
            (f, 0, -f),
            (-f, 0, -f),
            (0, 1, 0)]
        self.faces = [
            (0, 2, 1),
            (0, 3, 2),
            (0, 4, 3),
            (0, 1, 4),
            (5, 1, 2),
            (5, 2, 3),
            (5, 3, 4),
            (5, 4, 1)]

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, surf_convert, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_baddirerror_raise(self, mock_isfile, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, surf_convert, **self.kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_badsubjecterror_raise(self, mock_isfile, mock_isdir):
        """ Bad subject in t1 files -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True, True]
        mock_isdir.side_effect = [True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["t1files"] += wrong_kwargs["t1files"]
        self.assertRaises(ValueError, surf_convert, **wrong_kwargs)

    @mock.patch("pyfreesurfer.conversions.surfconvs.os.remove")
    @mock.patch("pyfreesurfer.conversions.surfconvs.nibabel.save")
    @mock.patch("pyfreesurfer.conversions.surfconvs.TriSurface.save")
    @mock.patch("pyfreesurfer.conversions.surfconvs.freesurfer.read_geometry")
    @mock.patch("pyfreesurfer.conversions.surfconvs.tkregister_translation")
    @mock.patch("pyfreesurfer.conversions.surfconvs.nibabel.load")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isdir")
    @mock.patch("pyfreesurfer.conversions.surfconvs.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_isdir, mock_load,
                              mock_trans, mock_read, mock_trisave,
                              mock_nisave, mock_rm):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, True, True]
        mock_isdir.side_effect = [True]
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((2, 2, 2)),
                                                     numpy.eye(4))
        mock_trans.return_value = numpy.eye(4)
        mock_read.return_value = (numpy.asarray(self.verts),
                                  numpy.asarray(self.faces))

        # Test execution
        csurffiles = surf_convert(**self.kwargs)
        self.assertEqual(csurffiles, [item + ".native"
                                      for item in self.kwargs["surffiles"]])


if __name__ == "__main__":
    unittest.main()
