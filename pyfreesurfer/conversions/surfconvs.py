##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Wrappers for the FreeSurfer's surface conversion utilities.
"""

# System import
import os
import glob
import numpy
import nibabel
from nibabel import freesurfer

# Pyfreesurfer import
from pyfreesurfer.utils.regtools import tkregister_translation
from pyfreesurfer.utils.surftools import apply_affine_on_mesh
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer.utils.surftools import TriSurface


def mri_surf2surf(
        hemi,
        input_surface_file,
        output_surface_file,
        ico_order,
        fsdir,
        sid,
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Resample surface vertices.

    Binding over the FreeSurfer's 'mri_surf2surf' command.

    Parameters
    ----------
    hemi: str (mandatory)
        hemisphere ('lh' or 'rh').
    input_surface_file: str (mandatory)
        input surface path.
    output_surface_file: str (mandatory)
        output '.mgz' surface path.
    ico_order: int (mandatory)
        icosahedron order in [0, 7] that will be used to generate the cortical
        surface texture at a specific tessalation (the corresponding cortical
        surface can be resampled using the
        'clindmri.segmentation.freesurfer.resample_cortical_surface' function).
    fsdir: str (mandatory)
        FreeSurfer subjects directory 'SUBJECTS_DIR'.
    sid: str (mandatory)
        FreeSurfer subject identifier.
    fsconfig: str (optional)
        The FreeSurfer '.sh' config file.
    """
    # Check input parameters
    for path in (input_surface_file, output_surface_file):
        if not os.path.isfile(path):
            raise ValueError("'{0}' is not a valid input file.".format(path))
    for path in (fsdir, ):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))
    if hemi not in ["lh", "rh"]:
        raise ValueError("'{0}' is not a valid hemisphere value which must be "
                         "in ['lh', 'rh']".format(hemi))
    if ico_order < 0 or ico_order > 7:
        raise ValueError("'Ico order '{0}' is not in 0-7 "
                         "range.".format(ico_order))

    # Set the output surface extension if necessary
    if not output_surface_file.endswith(".mgz"):
        output_surface_file += ".mgz"

    # Define FreeSurfer command
    cmd = ["mri_surf2surf", "--hemi", hemi, "--srcsurfval", input_surface_file,
           "--srcsubject", sid, "--trgsubject", "ico", "--trgicoorder",
           str(ico_order), "--trgsurfval", output_surface_file, "--sd", fsdir,
           "--trg_type", "mgz"]

    # Execute the FreeSurfer command
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()


def resample_cortical_surface(
        fsdir,
        regex,
        outdir,
        orders=[4, 5, 6, 7],
        surface_name="white",
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Resamples one cortical surface onto an icosahedron.

    Resample the white or pial FreeSurfer cotical surface using the
    'mri_surf2surf' command. Map also the associated annotation file.

    Can resample at different icosahedron order which specifies the size of the
    icosahedron according to the following table:
    Order  Number of Vertices
    0              12
    1              42
    2             162
    3             642
    4            2562
    5           10242
    6           40962
    7          163842

    Binding over the FreeSurfer's 'mri_surf2surf' command.

    Parameters
    ----------
    fsdir: str (mandatory)
        The freesurfer home directory with all the subjects.
    regex: str (mandatory)
        A regular expression used to locate the surface files to be converted
        from the 'fsdir' directory.
    outdir: str (optional, default None)
        The destination folder.
    orders: list of int
        The icosahedron orders.
    surface_name: str (optional, default 'white')
        The surface we want to resample ('white' or 'pial').
    fsconfig: str (optional)
        The freesurfer configuration batch.

    Returns
    -------
    resamplefiles: list of str
        The resample surfaces.
    annotfiles: list of str
        The resample annotations.
    """
    # Check input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))
    if surface_name not in ["white", "pial"]:
        raise ValueError("'{0}' is not a valid surface value which must be in "
                         "['white', 'pial']".format(surface_name))
    norders = numpy.asarray(orders)
    if norders.min() < 0 or norders.max() > 7:
        raise ValueError("'At least one value in {0} is not in 0-7 "
                         "range.".format(orders))

    # Get all the subjects with the specified surface
    surfaces = glob.glob(os.path.join(fsdir, regex))

    # Go through all the subjects with the desired surface
    resamplefiles = []
    annotfiles = []
    for surf in surfaces:

        # Get some information based on the surface path
        subject_id = surf.split("/")[-3]
        hemi = os.path.basename(surf).split(".")[0]
        convertdir = os.path.join(outdir, subject_id, "convert")
        if not os.path.isdir(convertdir):
            os.makedirs(convertdir)

        # Go through all specified orders
        for level in orders:

            # Construct the FS surface map command
            convertfile = os.path.join(convertdir, "{0}.{1}.{2}".format(
                hemi, surface_name, level))
            resamplefiles.append(convertfile)
            cmd = ["mri_surf2surf", "--sval-xyz", surface_name,
                   "--srcsubject", subject_id, "--trgsubject", "ico",
                   "--trgicoorder", str(level), "--tval", convertfile,
                   "--tval-xyz", "--hemi", hemi, "--sd", fsdir]

            # Execute the FS command
            recon = FSWrapper(cmd, shfile=fsconfig)
            recon()

            # Construct the FS label map command
            annotfile = os.path.join(convertdir, "{0}.aparc.annot.{1}".format(
                hemi, level))
            annotfiles.append(annotfile)
            if not os.path.isfile(annotfile):
                svalannot = os.path.join(fsdir, subject_id, "label",
                                         "{0}.aparc.annot".format(hemi))
                cmd = ["mri_surf2surf", "--srcsubject", subject_id,
                       "--trgsubject", "ico", "--trgicoorder", str(level),
                       "--hemi", hemi, "--sval-annot", svalannot,
                       "--tval", annotfile, "--sd", fsdir]

                # Execute the FS command
                recon = FSWrapper(cmd, shfile=fsconfig)
                recon()

    # Remove duplicate annotation files
    annotfiles = list(set(annotfiles))

    return sorted(resamplefiles), sorted(annotfiles)


def surf_convert(
        fsdir,
        t1files,
        surffiles,
        rm_orig=False,
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Export FreeSurfer surfaces to the native space.

    Note that all the returned vetices are given in the index coordinate
    system.
    The subject id in the t1 and surf files must appear in the '-3' position:
        xxx/subject_id/convert/t1.nii.gz

    Parameters
    ----------
    fsdir: str (mandatory)
        The FreeSurfer working directory with all the subjects.
    t1files: str (mandatory)
        The t1 nifti files.
    surffiles:
        The surfaces to be converted.
    rm_orig: bool (optional)
        If True remove the input surfaces.
    fsconfig: str (optional)
        The FreeSurfer configuration batch.

    Returns
    -------
    csurffiles:
        The converted surfaces in the native space indexed coordinates.
    """
    # Check input parameters
    for path in t1files + surffiles:
        if not os.path.isfile(path):
            raise ValueError("'{0}' is not a valid file.".format(path))
    if not os.path.isdir(fsdir):
        raise ValueError("'{0}' is not a valid directory.".format(fsdir))

    # Create a t1 subject map
    t1map = {}
    for fname in t1files:
        subject_id = fname.split(os.path.sep)[-3]
        if subject_id in t1map:
            raise ValueError("Can't map two t1 for subject "
                             "'{0}'.".format(subject_id))
        t1map[subject_id] = fname

    # Convert all the surfaces
    csurffiles = []
    for fname in surffiles:

        # Get the t1 reference image
        subject_id = fname.split(os.path.sep)[-3]
        t1file = t1map[subject_id]
        t1_image = nibabel.load(t1file)

        # Compute the conformed space to the native anatomical deformation
        asegfile = os.path.join(fsdir, subject_id, "mri", "aseg.mgz")
        physical_to_index = numpy.linalg.inv(t1_image.get_affine())
        translation = tkregister_translation(asegfile, fsconfig)
        deformation = numpy.dot(physical_to_index, translation)

        # Load and warp the mesh
        # The mesh: a 2-uplet with vertex (x, y, z) coordinates and
        # mesh triangles
        mesh = freesurfer.read_geometry(fname)
        surf = TriSurface(vertices=apply_affine_on_mesh(mesh[0], deformation),
                          triangles=mesh[1])

        # Save the mesh in the native space
        outputfile = fname + ".native"
        surf.save(outputfile)
        csurffiles.append(outputfile)

        # Construct the surfaces binarized volume
        binarizedfile = os.path.join(outputfile + ".nii.gz")
        overlay = numpy.zeros(t1_image.shape, dtype=numpy.uint)
        indices = numpy.round(surf.vertices).astype(int).T
        indices[0, numpy.where(indices[0] >= t1_image.shape[0])] = 0
        indices[1, numpy.where(indices[1] >= t1_image.shape[1])] = 0
        indices[2, numpy.where(indices[2] >= t1_image.shape[2])] = 0
        overlay[indices.tolist()] = 1
        overlay_image = nibabel.Nifti1Image(overlay, t1_image.get_affine())
        nibabel.save(overlay_image, binarizedfile)

        # Clean input surface if specified
        if rm_orig:
            os.remove(fname)

    return csurffiles
