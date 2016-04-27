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
import textwrap
import math
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
from pyfreesurfer.utils.filetools import surf2ctm
from pyfreesurfer.utils.filetools import parse_fs_lut


class FreeSurferCTM(unittest.TestCase):
    """ Test the CTM surface conversion:
    'pyfreesurfer.utils.filetools.surf2ctm'
    """
    def setUp(self):
        """ Define function parameters.
        """
        self.kwargs = {
            "fsdir": "/my/path/mock_fsdir",
            "outdir": "/my/path/mock_outdir"
        }

        # Construct an eight-sided polyhedron.
        f = math.sqrt(2.0) / 2.0
        verts = [
            (0, -1, 0),
            (-f, 0, f),
            (f, 0, f),
            (f, 0, -f),
            (-f, 0, -f),
            (0, 1, 0)]
        faces = [
            (0, 2, 1),
            (0, 3, 2),
            (0, 4, 3),
            (0, 1, 4),
            (5, 1, 2),
            (5, 2, 3),
            (5, 3, 4),
            (5, 4, 1)]
        labels = range(6)
        meta = dict((index, {"color": (1, 1, 1, 1)}) for index in labels)
        SurfStruct = namedtuple("SurfStruct",
                                "vertices triangles labels metadata")
        self.surface = SurfStruct(verts, faces, labels, meta)

    @mock.patch("pyfreesurfer.utils.filetools.os.path")
    def test_badfileerror_raise(self, mock_path):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [False, True, True]
        mock_path.join.side_effect = lambda *x: "/".join(x)

        # Test execution
        self.assertRaises(ValueError, surf2ctm, **self.kwargs)

    @mock.patch("pyfreesurfer.utils.filetools.openctm.ctmSave")
    @mock.patch("pyfreesurfer.utils.filetools.TriSurface.load")
    @mock.patch("pyfreesurfer.utils.filetools.os.path")
    def test_normal_execution(self, mock_path, mock_surf, mock_save):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [True, True, True, True, True, True]
        mock_path.join.side_effect = lambda *x: "/".join(x)
        mock_path.basename.return_value = "basename"
        mock_surf.return_value = self.surface

        # Test execution
        paths_ctm = surf2ctm(**self.kwargs)
        self.assertEqual(len(mock_path.isfile.call_args_list), 6)
        self.assertEqual(len(mock_path.join.call_args_list), 10)
        self.assertEqual(len(mock_save.call_args_list), 4)
        self.assertEqual(len(mock_surf.call_args_list), 4)


class FreeSurferLUT(unittest.TestCase):
    """ Test the FreeSurfer lookup table parsing:
    'pyfreesurfer.utils.filetools.parse_fs_lut'
    """
    def setUp(self):
        """ Define function parameters.
        """
        self.kwargs = {
            "path_lut": "/my/path/mock_lut"
        }
        self.lut_data = """
        #$Id: FreeSurferColorLUT.txt,v 1.70.2.7 2012/08/27 17:20:08 nicks Exp $

        #No. Label Name:                            R   G   B   A

        0   Unknown                                 0   0   0   0
        1   Left-Cerebral-Exterior                  70  130 180 0
        2   Left-Cerebral-White-Matter              245 245 245 0
        3   Left-Cerebral-Cortex                    205 62  78  0
        4   Left-Lateral-Ventricle                  120 18  134 0
        5   Left-Inf-Lat-Vent                       196 58  250 0
        6   Left-Cerebellum-Exterior                0   148 0   0
        7   Left-Cerebellum-White-Matter            220 248 164 0
        8   Left-Cerebellum-Cortex                  230 148 34  0
        9   Left-Thalamus                           0   118 14  0
        10  Left-Thalamus-Proper                    0   118 14  0
        11  Left-Caudate                            122 186 220 0
        12  Left-Putamen                            236 13  176 0
        13  Left-Pallidum                           12  48  255 0
        14  3rd-Ventricle                           204 182 142 0
        15  4th-Ventricle                           42  204 164 0
        16  Brain-Stem                              119 159 176 0
        17  Left-Hippocampus                        220 216 20  0
        18  Left-Amygdala                           103 255 255 0
        """
        self.lut_data = textwrap.dedent(self.lut_data).splitlines()

    @mock.patch("os.path")
    def test_badfileerror_raise(self, mock_path):
        """ No lookup table file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [False]

        # Test execution
        self.assertRaises(ValueError, parse_fs_lut, **self.kwargs)

    @mock.patch("{0}.ValueError".format(mock_builtin))
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("os.path")
    def test_badparsingerror_raise(self, mock_path, mock_open, mock_error):
        """ Bad lookup table file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [True]
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
        parse_fs_lut(**self.kwargs)
        self.assertEqual(len(mock_error.call_args_list), 1)

    @mock.patch("{0}.ValueError".format(mock_builtin))
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("os.path")
    def test_normal_execution(self, mock_path, mock_open, mock_error):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_path.isfile.side_effect = [True]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.readlines.return_value = self.lut_data
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        fs_lut_names, fs_lut_colors = parse_fs_lut(**self.kwargs)
        self.assertEqual(len(fs_lut_names), 19)
        self.assertEqual(len(fs_lut_colors), 19)
        self.assertEqual(sorted(fs_lut_names.keys()),
                         sorted(fs_lut_colors.keys()))
        self.assertEqual(fs_lut_names[0], "Unknown")
        self.assertEqual(fs_lut_colors[0], (0, 0, 0))

if __name__ == "__main__":
    unittest.main()
