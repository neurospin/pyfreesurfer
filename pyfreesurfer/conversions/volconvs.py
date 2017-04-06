##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Wrappers for the FreeSurfer's volume conversion utilities.
"""

# System import
import os
import glob

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


def mri_binarize(
        inputfile,
        outputfile,
        match=None,
        wm=False,
        ventricles=False,
        inv=False,
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Binarize a FreeSurfer label map.

    Binding over the FreeSurfer's 'mri_binarize' command.

    Parameters
    ----------
    inputfile: str (mandatory)
        input volume.
    outputfile: str (mandatory)
        output volume.
    match: list on int (optional)
        match labels instead of threshold.
    wm: bool (optional)
        set match vals to 2 and 41 (aseg for cerebral WM).
    inv: bool (optional)
        inverse the result.
    fsconfig: str (optional)
        The freesurfer configuration batch.
    """
    # Check input parameters
    for path in (inputfile, ):
        if not os.path.isfile(path):
            raise ValueError("'{0}' is not a valid file.".format(path))

    # Call FreeSurfer
    cmd = ["mri_binarize", "--i", inputfile, "--o", outputfile]
    if match is not None:
        cmd.append("--match")
        cmd.extend(match)
    if wm:
        cmd.append("--wm")
    if ventricles:
        cmd.append("--ventricles")
    if inv:
        cmd.append("--inv")
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()


def mri_convert(
        fsdir,
        regex,
        outdir,
        destdirname="convert",
        reslice=True,
        interpolation="interpolate",
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Export FreeSurfer '.mgz' image in Nifti format.

    Convert in native space: the destination image is resliced like the
    'rawavg.mgz' file if the reslice option is set. The converted file will
    then have a '.native' suffix.

    Binding over the FreeSurfer's 'mri_convert' command.

    Parameters
    ----------
    fsdir: str (mandatory)
        The FreeSurfer home directory with all the subjects.
    regex: str (mandatory)
        A regular expression used to locate the files to be converted from the
        'fsdir' directory.
    outdir: str (mandatory)
        The conversion destination folder.
    destdirname: str (optional, default 'convert')
        The name of the folder where each subject converted volumes will be
        saved. If None, don't create a sub folder.
    reslice: bool (optional default False)
        If True reslice the input images like the raw image.
    interpolation: str (optional default interpolate)
        The interpolation method: interpolate|weighted|nearest|cubic.
    fsconfig str (optional)
        The FreeSurfer configuration batch.

    Returns
    -------
    niftifiles: list of str
        The converted nifti files.
    """
    # Check the input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))

    # Check the interpolation method
    if interpolation not in ["interpolate", "weighted", "nearest", "cubic"]:
        raise ValueError(
            "'{0}' is not a valid interpolation method.".format(interpolation))

    # Get the images to convert from the regex
    inputs = glob.glob(os.path.join(fsdir, regex))

    # Convert each input file
    niftifiles = []
    for input_file in inputs:

        # Create the output directory
        subject = input_file.replace(fsdir, "")
        subject = subject.lstrip(os.sep).split(os.sep)[0]
        if destdirname is not None:
            subjoutdir = os.path.join(outdir, subject, destdirname)
        else:
            subjoutdir = outdir
        if not os.path.isdir(subjoutdir):
            os.makedirs(subjoutdir)

        # Create the FreeSurfer command
        basename = os.path.basename(input_file).replace(".mgz", "")
        cmd = ["mri_convert", "--resample_type", interpolation]
        # "--out_orientation", "RAS"]
        if reslice:
            reference_file = os.path.join(fsdir, subject, "mri", "rawavg.mgz")
            if not os.path.isfile(reference_file):
                raise ValueError("'{0}' does not exists, can't reslice image "
                                 "'{1}'.".format(reference_file, input_file))
            cmd += ["--reslice_like", reference_file]
            basename = basename + ".native"
        converted_file = os.path.join(subjoutdir, basename + ".nii.gz")
        niftifiles.append(converted_file)
        cmd += [input_file, converted_file]

        # Execute the FreeSurfer command
        recon = FSWrapper(cmd, shfile=fsconfig)
        recon()

    return niftifiles


def mri_vol2surf(
        hemi,
        volume_file,
        out_texture_file,
        ico_order,
        dat_file,
        fsdir,
        sid,
        surface_name="white",
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Assigns values from a volume to each surface vertices.

    Wrapper around the FreeSurfer 'mri_vol2surf' command to create the
    described texture.

    Parameters
    ----------
    hemi: str (mandatory)
        hemisphere ('lh' or 'rh').
    volume_file: str (mandatory)
        input volume path.
    out_texture_file: str (mandatory)
        output texture file.
    ico_order: int (mandatory)
        icosahedron order in [0, 7] that will be used to generate the cortical
        surface texture at a specific tessalation (the corresponding cortical
        surface can be resampled using the
        'pyfreesurfer.utils.surftools.resample_cortical_surface' function).
    dat_file: str (mandatory)
        structural to FreeSurfer space affine '.dat' transformation matrix
        file as computed by 'tkregister2'.
    fsdir: str (mandatory)
        FreeSurfer subjects directory 'SUBJECTS_DIR'.
    sid: str (mandatory)
        FreeSurfer subject identifier.
    surface_name: str (optional, default 'white')
        The surface we  want to resample ('white' or 'pial').
    fsconfig: str (optional)
        The FreeSurfer '.sh' config file.
    """
    # Check input parameters
    for path in (volume_file, dat_file):
        if not os.path.isfile(path):
            raise ValueError("'{0}' is not a valid input file.".format(path))
    for path in (fsdir, ):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))
    if hemi not in ["lh", "rh"]:
        raise ValueError("'{0}' is not a valid hemisphere value which must be "
                         "in ['lh', 'rh']".format(hemi))
    if surface_name not in ["white", "pial"]:
        raise ValueError("'{0}' is not a valid surface value which must be in "
                         "['white', 'pial']".format(surface_name))
    if ico_order < 0 or ico_order > 7:
        raise ValueError("'Ico order '{0}' is not in 0-7 "
                         "range.".format(ico_order))

    # Construct the FreeSurfer vol2surf command
    cmd = ["mri_vol2surf", "--src", volume_file, "--out", out_texture_file,
           "--srcreg", dat_file, "--hemi", hemi, "--trgsubject",
           "ico", "--icoorder", "{0}".format(ico_order), "--surf",
           surface_name, "--sd", fsdir, "--srcsubject", sid, "--noreshape",
           "--out_type", "mgz"]

    # Execute the FreeSurfer command
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()
