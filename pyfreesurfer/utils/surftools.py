##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


"""
Modules that provides surface manipulation tools.
"""


# System import
import copy
import numpy
from nibabel import freesurfer
from nibabel.gifti import giftiio


class TriSurface(object):
    """ A class representing a triangulated 3D surface.

    The surface contains 'ntrian' triangles, each having 3 vertices with
    3 coordinates.
    """

    def __init__(self, vertices, triangles, labels=None, metadata=None,
                 inflated_vertices=None):
        """ Create a new surface.

        Parameters
        ----------
        vertices: array (nvert, 3)
            the mesh vertices.
        triangles: array (ntrian, 3)
            the indices of the vertices of each triangle.
        labels: array (nvert)
            a label associated to each vertex.
        metadata: dict
            a mapping between each label and associated 'color' and 'region'
            name.
        inflated_vertices: array (nvert, 3)
            the mesh inflated vertices.
        """
        self.vertices = vertices
        self.triangles = triangles
        if labels is None:
            self.labels = numpy.asarray([0, ] * vertices.shape[0])
        else:
            self.labels = labels
        self.metadata = metadata
        self.inflated_vertices = inflated_vertices

    def save(self, out_file, gifti=False):
        """ Export a mesh in the FreeSurfer format.

        Parameters
        ----------
        out_file: str (mandatory)
            the location where the mesh will be written.
        gifti: bool, default False
            if set save the result in Gifti format.
        """
        freesurfer.write_geometry(out_file, self.vertices, self.triangles)
        if self.inflated_vertices is not None:
            out_file += ".inflated"
            freesurfer.write_geometry(out_file, self.inflated_vertices,
                                      self.triangles)

    @classmethod
    def load(self, meshfile, inflatedmeshpath=None, annotfile=None):
        """ Load a FreeSurfer surface.

        Parameters
        ----------
        meshfile: str (mandatory)
            the location of the file containing the FreeSurfer mesh to be
            loaded.
        inflatedmeshpath: str (optional, default None)
            the location of the file containing the FreeSurfer inflated mesh
            to be loaded.
        annotfile: str (optional, default None)
            the location of the file containing the FreeSurfer annotations to
            be loaded.

        Returns
        -------
        surf: TriSurface
            a triangular surface representation.
        """
        vertices, triangles = freesurfer.read_geometry(meshfile)
        if inflatedmeshpath is not None:
            inflated_vertices, _triangles = freesurfer.read_geometry(
                inflatedmeshpath)
            if not numpy.allclose(triangles, _triangles):
                raise ValueError("'{0}' and '{1}' do not represent the same "
                                 "surface.".format(meshfile, inflatedmeshpath))
        else:
            inflated_vertices = None
        if annotfile is not None:
            labels, ctab, regions = freesurfer.read_annot(
                annotfile, orig_ids=False)
            meta = dict(
                (index, {"region": item[0], "color": item[1][:4].tolist()})
                for index, item in enumerate(zip(regions, ctab)))
        else:
            labels = None
            meta = None

        return TriSurface(vertices=vertices, triangles=triangles,
                          labels=labels, metadata=meta,
                          inflated_vertices=inflated_vertices)

    def save_vtk(self, outfile, inflated=False):
        """ Export a mesh in '.vtk' format.

        This code uses vtk.

        Parameters
        ----------
        outfile: str (mandatory)
            the location where the mesh will be written.
        inflated: bool (optional, default False)
            if True write the inflated volume.
        """
        # Import here since vtk is not required by the package
        import vtk

        # Check that the inflated vertices are specified if requested
        if inflated and self.inflated_vertices is None:
            raise ValueError("Can't save inflated volume '{0}' since it has "
                             "not been specified.".format(outfile))

        # Create the desired polydata
        polydata = self._polydata(inflated=inflated)

        # Write the polydata
        writer = vtk.vtkPolyDataWriter()
        # writer.SetDataModeToAscii()
        writer.SetFileTypeToASCII()
        writer.SetFileName(outfile)
        if vtk.VTK_MAJOR_VERSION <= 5:
            writer.SetInput(polydata)
        else:
            writer.SetInputData(polydata)
        writer.Write()

    def nedges(self):
        """ TriSurface number of edges.

        Returns
        -------
        nb_edges: int
            using Euler's formula for triangle mesh return an approximation of
            the number of edges of the TriSurface.
        """
        return 3 * self.vertices.shape[0]

    def shape(self):
        """ TriSurface shape.

        Returns
        -------
        out: 3-uplet
            the number of points, edges, faces of the TriSurface.
        """
        return self.vertices.shape[0], self.nedges(), self.triangles.shape[0]

    def geodesic_distance(self, point1, point2):
        """ Compute the geodesic path between two points of a mesh.

        Parameters
        ----------
        point1: array (3, )
            a point of the mesh.
        point2: array (3, )
            a point of the mesh.

        Returns
        -------
        path: array (M, 3)
            the geodesic path between two points.
        """
        # Import here since vtk is not required by the package
        import vtk

        # Create polydata
        surf_polydata = self._polydata()

        # Get point indices
        ind1 = numpy.argwhere(
            numpy.all(self.vertices == point1, axis=1)).squeeze().tolist()
        ind2 = numpy.argwhere(
            numpy.all(self.vertices == point2, axis=1)).squeeze().tolist()
        if not isinstance(ind1, int) or not isinstance(ind2, int):
            raise ValueError("Input points are not in mesh.")

        # Create distance
        dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
        dijkstra.SetInput(surf_polydata)
        dijkstra.SetStartVertex(ind1)
        dijkstra.SetEndVertex(ind2)
        dijkstra.Update()

        # Get the path
        path = []
        output = dijkstra.GetOutput()
        for ind in range(output.GetNumberOfPoints()):
            path.append(output.GetPoint(ind))
        path = numpy.asarray(path)

        return path

    def labelize(self, shape, shift=0):
        """ Compute a label image of the TriSurface.

        Parameters
        ----------
        shape: 3-uplet (mandatory)
            the image shape.
        shift: int (optional, default 0)
            shift the labels of this number.

        Returns
        -------
        label_array: array
            an array with the surface labels.
        nb_of_labels: int
            the number of valid labels.
        """
        label_array = numpy.zeros(shape, dtype=numpy.int16)
        indices = numpy.round(self.vertices).astype(int)
        nb_of_labels = 0
        for label in set(self.labels):
            if label != -1:
                nb_of_labels += 1
                label_indices = indices[numpy.where(self.labels == label)]
                label_array[label_indices.T.tolist()] = label + shift
        return label_array, nb_of_labels

    def voxelize(self, shape, tol=0):
        """ Compute the enclosed points of the TriSurface.

        This code uses vtk.

        Parameters
        ----------
        shape: 3-uplet
            the image shape.

        Returns
        -------
        inside_array: array
            a mask array with the enclosed voxels.
        """
        # Import here since vtk is not required by the package
        import vtk
        try:
            import vtk.util.numpy_support
        except:
            pass

        # Construct the mesh grid from shape
        nx, ny, nz = shape
        gridx, gridy, gridz = numpy.meshgrid(numpy.linspace(0, nx - 1, nx),
                                             numpy.linspace(0, ny - 1, ny),
                                             numpy.linspace(0, nz - 1, nz))

        # Create polydata
        vtk_points = vtk.vtkPoints()
        for point in zip(gridx.flatten(), gridy.flatten(), gridz.flatten()):
            vtk_points.InsertNextPoint(point)
        points_polydata = vtk.vtkPolyData()
        points_polydata.SetPoints(vtk_points)
        surf_polydata = self._polydata()

        # Compute enclosed points
        enclosed_pts = vtk.vtkSelectEnclosedPoints()
        enclosed_pts.SetInput(points_polydata)
        enclosed_pts.SetTolerance(tol)
        enclosed_pts.SetSurface(surf_polydata)
        enclosed_pts.SetCheckSurface(1)
        enclosed_pts.Update()
        inside_points = enclosed_pts.GetOutput().GetPointData().GetArray(
            "SelectedPoints")
        enclosed_pts.ReleaseDataFlagOn()
        enclosed_pts.Complete()

        # Convert result as a numpy array
        inside_array = vtk.util.numpy_support.vtk_to_numpy(
            inside_points).reshape(ny, nx, nz)
        inside_array = numpy.swapaxes(inside_array, 1, 0)

        return inside_array

    def _polydata(self, inflated=False):
        """ Compute a vtk polydata of the TriSurface.

        This code uses vtk.

        Parameters
        ----------
        inflated: bool (optional, default False)
            If True use the inflated vertices.

        Returns
        -------
        polydata: vtkPolyData
            the TriSurface vtk polydata.
        """
        # Import here since vtk is not required by the package
        import vtk

        # Select the vertices to use
        labels = copy.deepcopy(self.labels)
        if inflated:
            vertices = self.inflated_vertices
        else:
            vertices = self.vertices

        # First setup points, triangles and colors.
        vtk_points = vtk.vtkPoints()
        vtk_triangles = vtk.vtkCellArray()
        vtk_colors = vtk.vtkUnsignedCharArray()
        vtk_colors.SetNumberOfComponents(1)
        labels[numpy.where(labels < 0)] = 0
        for index in range(len(vertices)):
            vtk_points.InsertNextPoint(vertices[index])
            vtk_colors.InsertNextTuple1(labels[index])
        for triangle in self.triangles:
            vtk_triangle = vtk.vtkTriangle()
            vtk_triangle.GetPointIds().SetId(0, triangle[0])
            vtk_triangle.GetPointIds().SetId(1, triangle[1])
            vtk_triangle.GetPointIds().SetId(2, triangle[2])
            vtk_triangles.InsertNextCell(vtk_triangle)

        # Create (geometry and topology) the associated polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        polydata.GetPointData().SetScalars(vtk_colors)
        polydata.SetPolys(vtk_triangles)

        return polydata


def apply_affine_on_mesh(vertices, affine):
    """ Apply an affine transformation on each vetex of the mesh.

    Parameters
    ----------
    vertices: array (N, 3)
        N vertices.
    affine: array (4, 4)
        an affine transformation to applied.

    Returns
    -------
    warp_vertices: array (N, 3)
        N interpolated vertices.
    """
    N, _ = vertices.shape
    ones = numpy.ones((N, 1), dtype=vertices.dtype)
    homogenous_vertices = numpy.concatenate((vertices, ones), axis=1)
    warp_vertices = numpy.dot(affine, homogenous_vertices.T).T[..., :3]
    return warp_vertices
