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
import math
import numpy
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
from pyfreesurfer.utils.surftools import apply_affine_on_mesh
from pyfreesurfer.utils.filetools import TriSurface


class FreeSurferTriSurface(unittest.TestCase):
    """ Test the triangular surface structure:
    'pyfreesurfer.utils.surftools.TriSurface'
    """
    def setUp(self):
        """ Define function parameters.
        """
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

        self.kwargs = {
            "vertices": numpy.asarray(verts),
            "triangles": numpy.asarray(faces),
            "inflated_vertices": numpy.asarray(verts)
        }

    def test_normal_execution(self):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        surf = TriSurface(**self.kwargs)
        self.assertTrue(numpy.allclose(self.kwargs["vertices"],
                                       surf.vertices))
        self.assertTrue(numpy.allclose(self.kwargs["triangles"],
                                       surf.triangles))
        self.assertTrue(numpy.allclose(self.kwargs["inflated_vertices"],
                                       surf.inflated_vertices))
        self.assertEqual(surf.shape(), (6, 18, 8))


class FreeSurferApplyAffine(unittest.TestCase):
    """ Test the apply affine transformation to vertices function:
    'pyfreesurfer.utils.surftools.apply_affine_on_mesh'
    """
    def setUp(self):
        """ Define function parameters.
        """
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

        self.kwargs = {
            "vertices": numpy.asarray(verts),
            "affine": numpy.eye(4)
        }

    def test_normal_execution(self):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        warp_vertex = apply_affine_on_mesh(**self.kwargs)
        self.assertTrue(numpy.allclose(self.kwargs["vertices"], warp_vertex))


if __name__ == "__main__":
    unittest.main()
