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
import textwrap
import numpy
import nibabel
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
from pyfreesurfer.utils.stattools import aparcstats2table
from pyfreesurfer.utils.stattools import asegstats2table
from pyfreesurfer.utils.stattools import population_summary
from pyfreesurfer.utils.stattools import textures2table


class FreeSurferAparc2Table(unittest.TestCase):
    """ Test the aparc text/ascii tables generation:
    'pyfreesurfer.utils.stattools.aparcstats2table'
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
            "outdir": "/my/path/mock_outdir",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, aparcstats2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "stats")]
        os.environ["SUBJECTS_DIR"] = "/my/path/default_subjdir"

        # Test execution
        statfiles = aparcstats2table(**self.kwargs)
        fsoutdir = os.path.join(self.kwargs["outdir"], "stats")
        expected_statfiles = []
        for hemi in ["lh", "rh"]:
            for meas in ["area", "volume", "thickness", "thicknessstd",
                         "meancurv", "gauscurv", "foldind", "curvind"]:
                expected_statfiles.append(os.path.join(
                    fsoutdir, "aparc_stats_{0}_{1}.csv".format(hemi, meas)))
        self.assertEqual([
            mock.call(self.kwargs["fsdir"]),
            mock.call(self.kwargs["outdir"]),
            mock.call(fsoutdir)],
            mock_isdir.call_args_list)
        self.assertEqual(len(self.mock_popen.call_args_list), 32)
        self.assertEqual(len(self.mock_env.call_args_list), 16)
        self.assertEqual(statfiles, expected_statfiles)


class FreeSurferAseg2Table(unittest.TestCase):
    """ Test the aseg text/ascii tables generation:
    'pyfreesurfer.utils.stattools.asegstats2table'
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
            "outdir": "/my/path/mock_outdir",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()
        self.env_patcher.stop()

    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_badfileerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, asegstats2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "stats")]
        os.environ["SUBJECTS_DIR"] = "/my/path/default_subjdir"

        # Test execution
        statfiles = asegstats2table(**self.kwargs)
        fsoutdir = os.path.join(self.kwargs["outdir"], "stats")
        expected_statfiles = [os.path.join(fsoutdir, "aseg_stats_volume.csv")]
        self.assertEqual([
            mock.call(self.kwargs["fsdir"]),
            mock.call(self.kwargs["outdir"]),
            mock.call(fsoutdir)],
            mock_isdir.call_args_list)
        self.assertEqual(len(self.mock_popen.call_args_list), 2)
        self.assertEqual(len(self.mock_env.call_args_list), 1)
        self.assertEqual(statfiles, expected_statfiles)


class FreeSurferTextures2Table(unittest.TestCase):
    """ Test the textures text/ascii tables generation:
    'pyfreesurfer.utils.stattools.textures2table'
    """
    def setUp(self):
        """ Define function parameters
        """
        self.kwargs = {
            "regex": os.path.join("*", "surf", "lh.sulc"),
            "ico_order": 7,
            "fsdir": "/my/path/mock_fsdir",
            "outdir": "/my/path/mock_outdir",
            "keep_individual_textures": False,
            "save_mode": "all",
            "fsconfig": "/my/path/mock_fsconfig"
        }

    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False, True]

        # Test execution
        self.assertRaises(ValueError, textures2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_badsavemodeerror_raise(self, mock_isdir):
        """ Bad save mode -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True]

        # Test execution
        wrong_kwargs = copy.copy(self.kwargs)
        wrong_kwargs["save_mode"] = "WRONG"
        self.assertRaises(ValueError, textures2table, **wrong_kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.nibabel.load")
    @mock.patch("pyfreesurfer.utils.stattools.mri_surf2surf")
    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_wrongdimension_raise(self, mock_isdir, mock_glob, mock_surf,
                                  mock_load):
        """ Wrong dimension -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "surf", "lh.sulc")]
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((10, 1)),
                                                     numpy.eye(4))

        # Test execution
        self.assertRaises(ValueError, textures2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.nibabel.load")
    @mock.patch("pyfreesurfer.utils.stattools.mri_surf2surf")
    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_wrongshape_raise(self, mock_isdir, mock_glob, mock_surf,
                              mock_load):
        """ Wrong shape -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "surf", "lh.sulc")]
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((10, 1, 2)),
                                                     numpy.eye(4))

        # Test execution
        self.assertRaises(ValueError, textures2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.nibabel.load")
    @mock.patch("pyfreesurfer.utils.stattools.mri_surf2surf")
    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_Wrongregex_raise(self, mock_isdir, mock_glob, mock_surf,
                              mock_load):
        """ Wrong regex -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "surf", "lh.sulc")] * 2
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((10, 1, 1)),
                                                     numpy.eye(4))

        # Test execution
        self.assertRaises(ValueError, textures2table, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.numpy.savez")
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.utils.stattools.shutil.rmtree")
    @mock.patch("pyfreesurfer.utils.stattools.nibabel.load")
    @mock.patch("pyfreesurfer.utils.stattools.mri_surf2surf")
    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob, mock_surf,
                              mock_load, mock_rmtree, mock_open, mock_savez):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True, True]
        mock_glob.return_value = [os.path.join(self.kwargs["fsdir"], "Lola",
                                               "surf", "lh.sulc")]
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((10, 1, 1)),
                                                     numpy.eye(4))
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.readlines.return_value = ["WRONG Unknown 0 0 0 0"]
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        textures_files = textures2table(**self.kwargs)
        basename = os.path.basename(self.kwargs["regex"])
        fsoutdir = os.path.join(self.kwargs["outdir"], "textures")
        expected_textures_files = [
            os.path.join(fsoutdir, basename + "." +
                         str(self.kwargs["ico_order"]) + ".csv"),
            os.path.join(fsoutdir, basename + "." +
                         str(self.kwargs["ico_order"]) + ".npz")]
        self.assertEqual([
            mock.call(self.kwargs["fsdir"]),
            mock.call(self.kwargs["outdir"]),
            mock.call(os.path.join(fsoutdir, basename))],
            mock_isdir.call_args_list)
        self.assertEqual(len(mock_surf.call_args_list), 1)
        self.assertEqual(len(mock_load.call_args_list), 1)
        self.assertEqual([
            mock.call(os.path.join(fsoutdir, basename,
                                   "Lola_{0}.mgz".format(basename)))],
            mock_load.call_args_list)
        self.assertEqual([
            mock.call(os.path.join(fsoutdir, basename))],
            mock_rmtree.call_args_list)
        self.assertEqual([
            mock.call(os.path.join(fsoutdir, basename))],
            mock_rmtree.call_args_list)
        self.assertEqual(len(mock_savez.call_args_list), 1)
        self.assertEqual([
            mock.call(os.path.join(
                fsoutdir, basename + "." + str(self.kwargs["ico_order"]) +
                ".csv"), "wb")],
            mock_open.call_args_list)
        self.assertEqual(textures_files, expected_textures_files)


class FreeSurferPopulationSummary(unittest.TestCase):
    """ Test the population summay generation:
    'pyfreesurfer.utils.stattools.population_summary'
    """
    def setUp(self):
        """ Define function parameters
        """
        self.kwargs = {
            "statsdir": "/my/path/mock_statsdir",
            "sid": None,
        }

    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_baddirerror_raise(self, mock_isdir):
        """ Bad input directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, population_summary, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.stattools.csv.DictReader")
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.utils.stattools.glob.glob")
    @mock.patch("pyfreesurfer.utils.stattools.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_glob, mock_open,
                              mock_reader):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, True]
        mock_glob.return_value = [
            os.path.join(self.kwargs["statsdir"], "aparc_stats_lh_area.csv"),
            os.path.join(self.kwargs["statsdir"], "aseg_stats_volume.csv"),
            os.path.join(self.kwargs["statsdir"], "other.csv")]
        mock_reader.side_effect = [
            [{"inferiortemporal": "3019.0", "lateralorbitofrontal": "2307.0",
             "lh.aparc.area": "Lola"}],
            [{"CC_Central": "490.3", "Right-choroid-plexus": "2200.7",
             "Measure:volume": "Lola"}],
            [{"inferiortemporal": "3019.0", "lateralorbitofrontal": "2307.0",
             "lh.aparc.area": "Lola"}],
            [{"CC_Central": "490.3", "Right-choroid-plexus": "2200.7",
             "Measure:volume": "Lola"}]
        ]

        # Test execution
        popstats = population_summary(**self.kwargs)
        self.assertEqual([
            mock.call(self.kwargs["statsdir"])],
            mock_isdir.call_args_list)
        self.assertEqual([
            mock.call(mock_glob.return_value[0], "rt"),
            mock.call(mock_glob.return_value[1], "rt")],
            mock_open.call_args_list)
        self.assertEqual(sorted(popstats.keys()), sorted(["aseg", "lh", "rh"]))
        self.assertEqual(popstats["lh"]["area"]["lateralorbitofrontal"],
                         {"m": 2307.0, "s": 0.0, "values": [2307.0]})
        self.kwargs["sid"] = "Toto"
        popstats = population_summary(**self.kwargs)
        self.assertEqual(popstats["lh"]["area"], {})


if __name__ == "__main__":
    unittest.main()
