##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides registration tools.
"""

# System import
import os
import glob
import re
import numpy

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


def conformed_to_native_space(
        fsdir,
        regex,
        outdir,
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Return the conformed to native transformation files.

    Create a registration matrix between the conformed space (orig.mgz) and
    the native anatomical (rawavg.mgz).

    Binding over the FreeSurfer's 'tkregister2' command.

    Parameters
    ----------
    fsdir: str (mandatory)
        The FreeSurfer working directory with all the subjects.
    regex: str
        A regular expression used to locate the mri files to be converted
        from the 'fsdir' directory.
    outdir: str
        The destination folder.
    fsconfig: str (optional)
        The FreeSurfer configuration batch.

    Returns
    -------
    trffiles: list of str
        The conformed to native transformation files.
    """
    # Check the input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))

    # Get all the subjects with a 'mri' directory
    mridirs = glob.glob(os.path.join(fsdir, regex))

    # Go through all the subjects with the desired folder
    trffiles = []
    for path_mri in mridirs:

        # Get some information based on the folder path
        subject_id = path_mri.rstrip(os.path.sep).split(os.path.sep)[-2]
        convertdir = os.path.join(outdir, subject_id, "convert")
        if not os.path.isdir(convertdir):
            os.makedirs(convertdir)

        # Check that the two images of interest are present
        rawfile = os.path.join(path_mri, "rawavg.mgz")
        origfile = os.path.join(path_mri, "orig.mgz")
        for path in (rawfile, origfile):
            if not os.path.isfile(path):
                raise ValueError("In folder '{0}' can't find file "
                                 "'{1}'.".format(path_mri, path))

        # Construct the FreeSurfer command
        trffile = os.path.join(convertdir, "register.native.dat")
        trffiles.append(trffile)
        cmd = ["tkregister2", "--mov", rawfile, "--targ", origfile,
               "--reg", trffile, "--noedit", "--regheader"]

        # Execute the FreeSurfer command
        recon = FSWrapper(cmd, shfile=fsconfig)
        recon()

    return trffiles


def tkregister_translation(mgzfile, fsconfig=DEFAULT_FREESURFER_PATH):
    """ Get the tkregister translation.

    FreeSurfer use a special origin for the Right-Anterior-Superior
    (anatomical coordinates) space. To get the standard, freesurfer scanner
    space in RAS coordinates we can use the 'mri_info --vox2ras aseg.mgz' or
    'mri_info --vox2ras-trk aseg.mgz' commands respectively.

    Binding over the FreeSurfer's 'mri_info' command.

    Parameters
    ----------
    mgzfile: str (mandatory)
        a FreeSurfer '.mgz' file.
    fsconfig: str (mandatory)
        the freesurfer configuration file.

    Returns
    -------
    translation: array
        the translation matrix between the ras and ras-tkregister spaces.
    """
    # Check the input parameter
    if not os.path.isfile(mgzfile):
        raise ValueError("'{0}' is not a valid '.mgz' file.".format(mgzfile))

    # Get the affine matrices corresponding to the the ras or ras-tkregister
    # spaces
    affines = {}
    for tkregister in [True, False]:

        # Execute the FreeSurfer command
        command = ["mri_info", "--vox2ras", mgzfile]
        if tkregister:
            command[1] = "--vox2ras-tkr"
        process = FSWrapper(command, shfile=fsconfig)
        process()

        # Get the affine matrix displayed in the stdout
        affine = process.stdout.splitlines()
        affine = ",".join([line.strip() for line in affine])
        affine = re.sub(r"  *", ",", affine)
        affine = numpy.fromstring(affine, dtype=float, sep=",").reshape(4, 4)
        affines[tkregister] = affine

    # Compute the translation
    translation = numpy.eye(4)
    translation += (affines[False] - affines[True])

    return translation
