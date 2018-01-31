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
        self.ctab = [
            numpy.array([255, 0, 0, 1])] * 6
        self.labels = numpy.asarray(range(6))
        meta = dict((index, {"color": (1, 1, 1, 1)}) for index in self.labels)

        # Deal with vtk
        self.is_vtk_installed = True
        try:
            import vtk
        except:
            self.is_vtk_installed = False

            class dummy_vtk(object):
                VTK_MAJOR_VERSION = 6

                def nop(*args, **kwargs): pass

                def __getattr__(self, _): return self.nop
            sys.modules["vtk"] = dummy_vtk()
            sys.modules["vtk.util.numpy_support"] = dummy_vtk()

        # Define default arguments
        self.kwargs = {
            "vertices": numpy.asarray(verts),
            "triangles": numpy.asarray(faces),
            "inflated_vertices": numpy.asarray(verts),
            "labels": self.labels
        }

    def tearDown(self):
        """ Run after each test.
        """
        if not self.is_vtk_installed:
            del sys.modules["vtk"]

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

    @mock.patch("nibabel.freesurfer.write_geometry")
    def test_save(self, mock_writegeo):
        """ Test the save method.
        """
        # Test execution
        surf = TriSurface(**self.kwargs)
        out_file = "/my/path/mock_destination"
        surf.save(out_file)

    @mock.patch("nibabel.freesurfer.read_annot")
    @mock.patch("nibabel.freesurfer.read_geometry")
    def test_load(self, mock_readgeo, mock_readannot):
        """ Test the load method.
        """
        # Set the mocked functions returned values
        mock_readgeo.side_effect = [
            (self.kwargs["vertices"], self.kwargs["triangles"]),
            (self.kwargs["inflated_vertices"], self.kwargs["triangles"])]
        mock_readannot.return_value = [
            self.labels, self.ctab, self.labels]

        # Test execution
        meshfile = "/my/path/mock_mesh"
        inflatedmeshpath = "/my/path/mock_infmesh"
        annotfile = "/my/path/mock_annot"
        surf = TriSurface.load(meshfile, inflatedmeshpath=inflatedmeshpath,
                               annotfile=annotfile)
        self.assertTrue(numpy.allclose(self.kwargs["vertices"],
                                       surf.vertices))
        self.assertTrue(numpy.allclose(self.kwargs["triangles"],
                                       surf.triangles))
        self.assertTrue(numpy.allclose(self.kwargs["inflated_vertices"],
                                       surf.inflated_vertices))
        self.assertEqual(surf.shape(), (6, 18, 8))

    @mock.patch("vtk.vtkPolyDataWriter")
    @mock.patch("vtk.vtkPolyData")
    @mock.patch("vtk.vtkTriangle")
    @mock.patch("vtk.vtkUnsignedCharArray")
    @mock.patch("vtk.vtkCellArray")
    @mock.patch("vtk.vtkPoints")
    def test_savevtk(self, mock_vtkpoint, mock_vtkcell, mock_vtkuarray,
                     mock_vtktriangle, mock_vtkpoly, mock_vtkwrite):
        """ Test the save vtk method.
        """
        # Test execution
        surf = TriSurface(**self.kwargs)
        out_file = "/my/path/mock_destination"
        surf.save_vtk(out_file, inflated=True)

    def test_labelize(self):
        """ Test the labelize method.
        """
        # Test execution
        surf = TriSurface(**self.kwargs)
        surf.vertices += 1
        label_array, nb_of_labels = surf.labelize(shape=(3, 3, 3))
        self.assertEqual(6, nb_of_labels)

    @mock.patch("vtk.vtkPolyDataWriter")
    @mock.patch("vtk.util")
    @mock.patch("vtk.vtkSelectEnclosedPoints")
    @mock.patch("pyfreesurfer.utils.surftools.TriSurface._polydata")
    @mock.patch("vtk.vtkPolyData")
    @mock.patch("vtk.vtkPoints")
    def test_voxelize(self, mock_vtkpoint, mock_vtkpoly, mock_poly,
                      mock_vtkslect, mock_vtkutil, mock_vtkwrite):
        """ Test the voxelize vtk method.
        """
        # Set the mocked functions returned values
        mock_poly.return_value = object()
        mock_vtkutil.numpy_support.vtk_to_numpy.return_value = numpy.ones(
            (3, 3, 3), dtype=int)

        # Test execution
        surf = TriSurface(**self.kwargs)
        out_file = "/my/path/mock_destination"
        inside_array = surf.voxelize(shape=(3, 3, 3), tol=0)
        self.assertTrue(numpy.allclose(
            inside_array,
            mock_vtkutil.numpy_support.vtk_to_numpy.return_value))


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
