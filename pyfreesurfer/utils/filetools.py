##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides file manipulation tools.
"""

# System import
import os
import ctypes
import numpy
import sys
import warnings

# Package import
from .surftools import TriSurface
try:
    from pyfreesurfer.utils import openctm
    openctm_imported = True
except:
    openctm_imported = False


def make_blob(verts, ctype):
    """ Convert a list of tuples of numbers into a ctypes pointer-to-array.

    Parameters
    ----------
    verts: list (N, 3)
        the position of each vetex in 3d.
    ctype: ctype
        type for conversion.
    """
    size = len(verts) * len(verts[0])
    Blob = ctype * size
    floats = [c for v in verts for c in v]
    blob = Blob(*floats)
    return ctypes.cast(blob, ctypes.POINTER(ctype))


def surf2ctm(fsdir, outdir):
    """ Convert a FreeSurfer surface to a compressed CTM surface.

    Treat both hemishperes: 'lh' and 'rh'.

    Parameters
    ----------
    fsdir: str (mandatory)
        the subject FreeSurfer home directory where the '.white', '.pial'
        sufraces and the '.aparc.annot' files can be found.
    outdir: str
        directory where a '.ctm' file will be saved. The output file base
        name will be the same as the input 'path_mesh' file.

    Returns
    -------
    paths_ctm: dict of list of str
        the converted surfaces for each hemisphere.
    """
    # Test if openctm has been properly imported
    if not openctm_imported:
        raise ImportError("OpenCtm not installed.")

    # COMPATIBILITIES: Python 3 string encoding compatibilities.
    python_version = sys.version_info
    if python_version[:1] < (3, ):
        openctm_c_char_p = "Color"
    else:
        openctm_c_char_p = bytes(str("Color"), 'ascii')

    # Treat both hemishperes
    paths_ctm = {}
    for hemi in ["lh", "rh"]:

        # Guess file locations fom the FreeSurfer standard organization
        path_white = os.path.join(fsdir, "surf", "{0}.white".format(hemi))
        path_pial = os.path.join(fsdir, "surf", "{0}.pial".format(hemi))
        path_annot = os.path.join(fsdir, "label",
                                  "{0}.aparc.annot".format(hemi))
        for path in (path_white, path_pial, path_annot):
            if not os.path.isfile(path):
                raise ValueError("'{0}' FreeSurfer standard file cannot be "
                                 "found.".format(path))

        # Load the surfaces
        paths_ctm[hemi] = []
        for path_surf in (path_white, path_pial):
            surface = TriSurface.load(path_surf, annotfile=path_annot)

            # Convert the loaded surface in compressed CTM format
            path_ctm = os.path.join(outdir,
                                    os.path.basename(path_surf) + ".ctm")
            paths_ctm[hemi].append(path_ctm)
            colors = []
            for label in surface.labels:
                if label < 0:
                    label = 0
                color = numpy.asarray(surface.metadata[label]["color"],
                                      dtype=float)
                color /= 255.
                colors.append(tuple(color))
            pVerts = make_blob(surface.vertices, ctypes.c_float)
            pFaces = make_blob(surface.triangles, ctypes.c_uint)
            pNormals = ctypes.POINTER(ctypes.c_float)()
            pColors = make_blob(colors, ctypes.c_float)
            ctm = openctm.ctmNewContext(openctm.CTM_EXPORT)
            openctm.ctmDefineMesh(ctm, pVerts, len(surface.vertices), pFaces,
                                  len(surface.triangles), pNormals)
            openctm.ctmAddAttribMap(ctm, pColors, openctm_c_char_p)
            openctm.ctmSave(ctm, path_ctm)
            openctm.ctmFreeContext(ctm)

    return paths_ctm


def parse_fs_lut(path_lut):
    """ Parse the FreeSurfer general lookup table.

    The FreeSurfer lookup table is located in the same folder as configuration
    file, ie. '/i2bm/local/freesurfer/FreeSurferColorLUT.txt'.

    Parameters
    ----------
    path_lut: str (mandatory)
        The FreeSurfer lookup table.

    Returns
    -------
    fs_lut_names: dict
        Map with the FreeSurfer labels and the assocaited region names.
    fs_lut_colors: dict
        Map with the FreeSurfer labels and associated RGB colors.
    """
    # Check input parameter
    if not os.path.isfile(path_lut):
        raise ValueError("'{0}' FreeSurfer lookup table does not "
                         "exists.".format(path_lut))

    # Parse the FreeSurfer lookup table
    fs_lut_names = {}
    fs_lut_colors = {}
    with open(path_lut) as open_file:
        for line in open_file.readlines():
            token = line.split()
            if len(token) == 6 and token[0].isdigit():
                try:
                    fs_lut_names[int(token[0])] = token[1]
                    fs_lut_colors[int(token[0])] = (
                        int(token[2]), int(token[3]), int(token[4]))
                except:
                    raise ValueError("Can't parse '{0}' FreeSurfer lookup "
                                     "table file.".format(path_lut))

    return fs_lut_names, fs_lut_colors


def load_look_up_table(path_lut):
    """ Load a Look Up Table, provided in the FreeSurfer LUT format,
    as 3 ordered lists: labels (ints), names, colors (RGBA tuples)

    Structure:
    [.., 55, ..], [.., 'Right-Insula', .. ], [.., (80, 196, 98, 0), ..]

    Use dict(zip(<list1>, <list2>)) to get a map from one list to the other.

    Parameters
    ----------
    path_lut: str (mandatory)
        the path to the lookup table in FreeSurfer format.

    Returns
    -------
    labels: list of int
        the integer labels.
    names: list of str
        the region names.
    colors: list of 4-uplet
        the region colors.
    """
    # Load the Look Up Table and create 3 ordered lists
    try:
        table = numpy.loadtxt(path_lut, dtype=str)
        labels = table[:, 0].astype(dtype=int).tolist()
        names = table[:, 1].tolist()
        colors = [tuple(x) for x in table[:, 2:].astype(dtype=int)]
    except:
        raise Exception("Failed to load the Look Up Table: %s" % path_lut)

    return labels, names, colors


def get_or_check_freesurfer_subjects_dir(subjects_dir=None):
    """ If 'subjects_dir' is passed, check whether the directory exists,
    otherwise look for the $SUBJECTS_DIR environment variable. If
    'subjects_dir' is not passed and $SUBJECTS_DIR not in the environment,
    raise an Exception.

    Parameters
    ----------
    subjects_dir: str (optional, default None)
        the FreeSurfer subjects' directory.

    Returns
    -------
    subjects_dir: str
        the validated FreeSurfer subjects' directory.
    """
    if subjects_dir is not None:
        if not os.path.isdir(subjects_dir):
            raise ValueError("Argument 'subjects_dir' refers to non existing "
                             "directory: {}.".format(subjects_dir))
    elif "SUBJECTS_DIR" in os.environ:
        subjects_dir = os.environ["SUBJECTS_DIR"]
        if not os.path.isdir(subjects_dir):
            raise ValueError("Environment variable 'SUBJECTS_DIR' refers to "
                             "non existing directory: {}".format(subjects_dir))
    else:
        raise ValueError("Either set the FreeSurfer SUBJECTS_DIR environment "
                         "variable or set the 'subjects_dir' argument.")
    return subjects_dir


def get_or_check_path_of_freesurfer_lut(freesurfer_lut=None):
    """ Return the path to an existing FreeSurfer Look Up Table.

    If freesurfer_lut is given, check that the file exists, otherwise
    look for the FREESURFER_HOME environment variable.
    If the FreeSurfer LUT could not be found raise an Exception.

    Parameters
    ----------
    freesurfer_lut: str (optional, default None)
        path to the FreeSurfer lookup table.

    Returns
    -------
    freesurfer_lut: str
        path to the validated FreeSurfer lookup table.
    """
    if freesurfer_lut is None:
        # If path not given look for the FreeSurfer environment variable
        if "FREESURFER_HOME" in os.environ:
            FS_home = os.environ["FREESURFER_HOME"]
            freesurfer_lut = os.path.join(FS_home, "FreeSurferColorLUT.txt")
        else:
            raise Exception("Could not find FreeSurfer Look Up Table, either "
                            "set the 'freesurfer_lut' argument or the "
                            "'FREESURFER_HOME' environment variable.")

    if not os.path.isfile(freesurfer_lut):
        raise ValueError("File does not exist: %s" % freesurfer_lut)

    return freesurfer_lut
