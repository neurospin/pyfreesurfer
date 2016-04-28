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
    def test_normal_execution(self, mock_isdir):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True]

        # Test execution
        subjfsdir = recon_all(**self.kwargs)

        self.assertEqual([
            mock.call(["which", "recon-all"], env={}, stderr=-1, stdout=-1),
            mock.call(["recon-all", "-all", "-subjid", self.kwargs["sid"],
                       "-i", self.kwargs["anatfile"], "-sd",
                       self.kwargs["fsdir"]], env={}, stderr=-1, stdout=-1)],
            self.mock_popen.call_args_list)
        self.assertEqual(len(self.mock_env.call_args_list), 1)
        self.assertEqual(subjfsdir, os.path.join(self.kwargs["fsdir"],
                                                 self.kwargs["sid"]))


if __name__ == "__main__":
    unittest.main()
