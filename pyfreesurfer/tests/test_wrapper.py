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
    mock_builtin = "__builtin__"
else:
    import unittest.mock as mock
    from unittest.mock import patch
    mock_builtin = "builtins"

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer.wrapper import HCPWrapper


class FreeSurferWrapper(unittest.TestCase):
    """ Test the FreeSurfer wrapper:
    'pyfreesurfer.wrapper.FSWrapper'
    """
    def setUp(self):
        """ Define function parameters.
        """
        # Mocking popen
        self.popen_patcher = patch("pyfreesurfer.wrapper.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": (
                "export FREESURFER_HOME=/home\nmock_OK", "mock_NONE"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        self.mock_popen.return_value = mock_process

        # Define function parameters
        self.kwargs = {
            "cmd": ["freesurfer", "mock"],
            "shfile": "/my/path/mock_shfile"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()

    @mock.patch("pyfreesurfer.wrapper.os.path")
    def test_badfileerror_raise(self, mock_path):
        """ Bad configuration file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, FSWrapper, **self.kwargs)

    @mock.patch("pyfreesurfer.wrapper.FSWrapper._environment")
    @mock.patch("{0}.ValueError".format(mock_builtin))
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("os.path")
    def test_noreleaseerror_raise(self, mock_path, mock_open, mock_error,
                                  mock_env):
        """ No FreeSurfer release found -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [True]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.read.return_value = "WRONG"
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)
        mock_env.return_value = {"FREESURFER_HOME": "/my/path/mock_fshome"}

        # Test execution
        process = FSWrapper(**self.kwargs)
        self.assertEqual(process.environment, mock_env.return_value)
        self.assertEqual(len(mock_error.call_args_list), 1)

    @mock.patch("warnings.warn")
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("os.path")
    def test_normal_execution(self, mock_path, mock_open, mock_warn):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [True]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.read.return_value = (
            "freesurfer-Linux-centos4_x86_64-stable-pub-v5.2.0")
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        os.environ["FREESURFER_HOME"] = "/my/path/mock_fshome"
        process = FSWrapper(**self.kwargs)
        self.assertEqual(len(mock_warn.call_args_list), 1)


class THCPWrapper(unittest.TestCase):
    """ Test the HCP wrapper:
    'pyfreesurfer.wrapper.HCPWrapper'
    """
    def setUp(self):
        """ Define function parameters.
        """
        # Define function parameters
        self.kwargs = {
            "env": {"FSLDIR": "/my/path/mock_fslhome",
                    "FREESURFER_HOME": "/my/path/mock_fshome",
                    "HCPPIPEDIR": "/my/path/mock_hcphome"},
            "fslconfig": "/my/path/mock_fsl",
            "fsconfig": "/my/path/mock_fs"
        }

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_normal_execution(self, mock_env):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fsversion_noenv(self, mock_env):
        """ Test the fsversion version method: no env.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)
        del process.environment["FREESURFER_HOME"]
        self.assertEqual(process.freesurfer_version(), None)

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fsversion_nofile(self, mock_env):
        """ Test the freesurfer version method: no file.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.freesurfer_version(), None)

    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.wrapper.os.path.exists")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fsversion(self, mock_env, mock_exists, mock_open):
        """ Test the freesurfer version method.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_exists.side_effects = [True, False]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.readline.return_value = "5.3.0"
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.freesurfer_version(),
                         mock_file.readline.return_value)

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fslversion_noenv(self, mock_env):
        """ Test the fsl version method: no env.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)
        del process.environment["FSLDIR"]
        self.assertEqual(process.fsl_version(), None)

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fslversion_nofile(self, mock_env):
        """ Test the fsl version method: no file.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.fsl_version(), None)

    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.wrapper.os.path.exists")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_fslversion(self, mock_env, mock_exists, mock_open):
        """ Test the fsl version method.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_exists.side_effects = [True, False]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.read.return_value = "5.0.9"
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.fsl_version(),
                         mock_file.read.return_value)

    @mock.patch("pyfreesurfer.wrapper.subprocess.Popen")
    @mock.patch("pyfreesurfer.wrapper.environment")
    def test_test_gradunwarpversion_error(self, mock_env, mock_popen):
        """ Test the test_gradunwarp version method: error.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": ("", "mock_NONE"),
            "returncode": 1
        }
        mock_process.configure_mock(**attrs)
        mock_popen.return_value = mock_process

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.gradunwarp_version(), None)

    @mock.patch("pyfreesurfer.wrapper.subprocess.Popen")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_gradunwarpversion(self, mock_env, mock_popen):
        """ Test the gradunwarp version method.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": ("mock_OK", "5.2.1"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        mock_popen.return_value = mock_process

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.gradunwarp_version(),
                         attrs["communicate.return_value"][1])

    @mock.patch("pyfreesurfer.wrapper.subprocess.Popen")
    @mock.patch("pyfreesurfer.wrapper.environment")
    def test_wbcommandversion_error(self, mock_env, mock_popen):
        """ Test the wbcommand version method: error.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": ("", "mock_NONE"),
            "returncode": 1
        }
        mock_process.configure_mock(**attrs)
        mock_popen.return_value = mock_process

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.wbcommand_version(), None)

    @mock.patch("pyfreesurfer.wrapper.subprocess.Popen")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_wbcommandversion(self, mock_env, mock_popen):
        """ Test the wbcommand version method.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_process = mock.Mock()
        attrs = {
            "communicate.return_value": ("Version: 5.0.0", "mock_NONE"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        mock_popen.return_value = mock_process

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.wbcommand_version(),
                         attrs["communicate.return_value"][0][9:])

    @mock.patch("pyfreesurfer.configuration.environment")
    def test_hcpversion_noenv(self, mock_env):
        """ Test the hcp version method: no env.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]

        # Test execution
        process = HCPWrapper(**self.kwargs)
        del process.environment["HCPPIPEDIR"]
        self.assertEqual(process.hcp_version(), None)

    @mock.patch("pyfreesurfer.wrapper.os.path.exists")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_hcpversion_nofile(self, mock_env, mock_exists):
        """ Test the hcp version method: no file.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_exists.return_value = False

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.hcp_version(), None)

    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pyfreesurfer.wrapper.os.path.exists")
    @mock.patch("pyfreesurfer.configuration.environment")
    def test_hcpversion(self, mock_env, mock_exists, mock_open):
        """ Test the hcp version method.
        """
        # Set the mocked functions returned values
        mock_env.side_effects = [{"FS": "FS"}, {"FSL": "FSL"}]
        mock_exists.side_effects = [True, False]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.read.return_value = "5.0.9"
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        process = HCPWrapper(**self.kwargs)
        self.assertEqual(process.hcp_version(),
                         mock_file.read.return_value)


if __name__ == "__main__":
    unittest.main()
