##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Wrapper for the FreeSurfer's cortical reconstruction steps.
"""

# System import
import os

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


def recon_all(fsdir, anatfile, sid, fsconfig=DEFAULT_FREESURFER_PATH):
    """ Performs all the FreeSurfer cortical reconstruction steps.

    Binding around the FreeSurfer's 'recon-all' command.

    Processing stages:

    * Motion Correction and Conform
    * NU (Non-Uniform intensity normalization)
    * Talairach transform computation
    * Intensity Normalization 1
    * Skull Strip
    * EM Register (linear volumetric registration)
    * CA Intensity Normalization
    * CA Non-linear Volumetric Registration
    * Remove Neck
    * LTA with Skull
    * CA Label (Volumetric Labeling, ie Aseg) and Statistics
    * Intensity Normalization 2 (start here for control points)
    * White matter segmentation
    * Edit WM With ASeg
    * Fill (start here for wm edits)
    * Tessellation (begins per-hemisphere operations)
    * Smooth1
    * Inflate1
    * QSphere
    * Automatic Topology Fixer
    * Final Surfs (start here for brain edits for pial surf)
    * Smooth2
    * Inflate2
    * Spherical Mapping
    * Spherical Registration
    * Spherical Registration, Contralateral hemisphere
    * Map average curvature to subject
    * Cortical Parcellation - Desikan_Killiany and Christophe (Labeling)
    * Cortical Parcellation Statistics
    * Cortical Ribbon Mask
    * Cortical Parcellation mapping to Aseg

    Parameters
    ----------
    fsdir: str (mandatory)
        The FreeSurfer working directory with all the subjects.
    anatfile: str (mandatory)
        The input anatomical image to be segmented with FreeSurfer.
    sid: str (mandatory)
        The current subject identifier.
    fsconfig: str (optional)
        The FreeSurfer configuration batch.
    Returns
    -------
    subjfsdir: str
        Path to the resulting FreeSurfer segmentation.
    """
    # Check input parameters
    if not os.path.isdir(fsdir):
        raise ValueError("'{0}' is not a valid FreeSurfer home "
                         "directory.".format(fsdir))

    # Call FreeSurfer segmentation
    cmd = ["recon-all", "-all", "-subjid", sid, "-i", anatfile, "-sd", fsdir]
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()
    subjfsdir = os.path.join(fsdir, sid)

    return subjfsdir
