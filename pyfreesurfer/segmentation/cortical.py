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
import tempfile
import shutil

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.utils.filetools import get_or_check_freesurfer_subjects_dir


def recon_all(fsdir, anatfile, sid, reconstruction_stage="all", resume=False,
              t2file=None, flairfile=None, fsconfig=DEFAULT_FREESURFER_PATH):
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
    reconstruction_stage: str (optional, default 'all')
        The FreeSurfer reconstruction stage that will be launched.
    resume: bool (optional, default False)
        If true, try to resume the recon-all. This option is also usefull if
        custom segmentation is used in recon-all.
    t2file: str (optional, default None)
        Specify the path to a T2 image that will be used to improve the pial
        surfaces.
    flairfile: str (optional, default None)
        Specify the path to a FLAIR image that will be used to improve the pial
        surfaces.
    fsconfig: str (optional)
        The FreeSurfer configuration batch.
    Returns
    -------
    subjfsdir: str
        Path to the resulting FreeSurfer segmentation.
    """
    # Check input parameters
    if not os.path.isdir(fsdir):
        raise ValueError("'{0}' FreeSurfer home directory does not "
                         "exists.".format(fsdir))
    if reconstruction_stage not in ("all", "autorecon1", "autorecon2",
                                    "autorecon2-cp", "autorecon2-wm",
                                    "autorecon2-pial", "autorecon3"):
        raise ValueError("Unsupported '{0}' recon-all reconstruction "
                         "stage.".format(reconstruction_stage))

    # Call FreeSurfer segmentation
    cmd = ["recon-all", "-{0}".format(reconstruction_stage), "-subjid", sid,
           "-i", anatfile, "-sd", fsdir, "-noappend", "-no-isrunning"]
    if t2file is not None:
        cmd.extend(["-T2", t2file, "-T2pial"])
    if flairfile is not None:
        cmd.extend(["-FLAIR", t2file, "-FLAIRpial"])
    if resume:
        cmd[1] = "-make all"
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()
    subjfsdir = os.path.join(fsdir, sid)

    return subjfsdir


def recon_all_custom_wm_mask(subject_id, wm_mask, keep_orig=True,
                             subjects_dir=None, temp_dir=None,
                             fsconfig=DEFAULT_FREESURFER_PATH):
    """
    Assuming you have run recon-all (at least upto wm.mgz creation), this
    function allows to rerun recon-all using a custom white matter mask. The
    mask has to be in the subject's FreeSurfer space (1mm iso + aligned with
    brain.mgz) with values in [0; 1] (i.e. probability of being white matter).

    Parameters
    ----------
    subject_id: str
        Identifier of subject.
    wm_mask: str
        Path to the custom white matter mask. It has to be in the subject's
        FreeSurfer space (1mm iso + aligned with brain.mgz) with values in
        [0; 1] (i.e. probability of being white matter).
        For example, tt can be the 'brain_pve_2.nii.gz" white matter
        probability map created by FSL Fast.
    keep_orig: bool, default True
        Save original 'wm.seg.mgz' as 'wm.seg.orig.mgz' instead of overwriting
        it.
    subjects_dir: str, default None
        Path to the FreeSurfer subjects directory. Required if the environment
        variable $SUBJECTS_DIR is not set.
    temp_dir: str, default None
        Directory to use to store temporary files. By default OS tmp dir.
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        The FreeSurfer configuration batch.
    """
    # FreeSurfer $SUBJECTS_DIR has to be passed or set as an env variable
    subjects_dir = get_or_check_freesurfer_subjects_dir(subjects_dir)

    # Check existence of the subject's directory
    subject_dir = os.path.join(subjects_dir, subject_id)
    if not os.path.isdir(subject_dir):
        raise ValueError("Directory does not exist: %s" % subject_dir)

    # Create temporary directory to store intermediate files
    temp_dir = tempfile.mkdtemp(prefix="recon_all_custom_wm_mask_",
                                dir=temp_dir)

    # Change input mask range of values: [0-1] to [0-110]
    wm_mask_0_110 = os.path.join(temp_dir, "wm_mask_0_110.nii.gz")
    cmd_1 = ["mris_calc", "-o", wm_mask_0_110, wm_mask, "mul", "110"]
    FSWrapper(cmd_1, shfile=fsconfig)()

    # If requested save original wm.seg.mgz as wm.seg.orig.mgz
    wm_seg_mgz = os.path.join(subject_dir, "mri", "wm.seg.mgz")
    if keep_orig:
        save_as = os.path.join(subject_dir, "mri", "wm.seg.orig.mgz")
        shutil.move(wm_seg_mgz, save_as)

    # Write the new wm.seg.mgz, FreeSurfer requires MRI_UCHAR type
    cmd_2 = ["mri_convert", wm_mask_0_110, wm_seg_mgz, "-odt", "uchar"]
    FSWrapper(cmd_2, shfile=fsconfig)()

    # Clean tmp dir
    shutil.rmtree(temp_dir)

    # Rerun recon-all
    cmd_3 = ["recon-all", "-autorecon2-wm", "-autorecon3", "-s", subject_id]
    FSWrapper(cmd_3, shfile=fsconfig, subjects_dir=subjects_dir)()

    return subject_dir


def recon_all_longitudinal(outdir, subject_id, subjects_dirs, timepoints=None,
                           fsconfig=DEFAULT_FREESURFER_PATH):
    """
    Assuming you have run recon-all for all timepoints of a given subject,
    and that the results are stored in one SUBJECTS_DIR per timepoint, this
    function will:
    - create a template for the subject and process it with recon-all
    - rerun recon-all for all timepoints of the subject using the template

    Parameters
    ----------
    outdir: str
        Directory where to output. Created if not already existing.
    subject_id: str
        Identifier of subject, used for all timepoints.
    subjects_dirs: list of str
        The FreeSurfer SUBJECTS_DIRs of timepoints.
    timepoints: list of str, default None
        The timepoint names in the same order as the SUBJECTS_DIRs.
        Used to create the subject longitudinal IDs.
        By default timepoints are "1", "2"...
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        The FreeSurfer configuration batch.

    Return
    ------
    subject_template_id: str
        ID of the subject template.
    subject_long_ids: list of str
        Longitudinal IDs of the subject for all the timepoints.
    """
    # Check existence of FreeSurfer subject directories
    for subjects_dir in subjects_dirs:
        subject_dir = os.path.join(subjects_dir, subject_id)
        if not os.path.isdir(subject_dir):
            raise ValueError("Directory does not exist: %s" % subject_dir)

    # If 'timepoints' not passed, used defaults, else check validity
    if timepoints is None:
        timepoints = [str(n) for n in range(1, len(subjects_dirs)+1)]
    elif len(timepoints) != len(subjects_dirs):
        raise ValueError("There should be as many timepoints as subjects_dirs")

    # If <outdir> does not exist, create it
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # FreeSurfer requires a unique SUBJECTS_DIR will all the timepoints to
    # compute the template: create symbolic links in <outdir> to all timepoints
    subject_tp_ids = []  # To accumulate all the timepoint IDs
    for tp, subjects_dir in zip(timepoints, subjects_dirs):
        subject_tp_id = "%s_%s" % (subject_id, tp)  # subject timepoint ID
        src_path = os.path.join(subjects_dir, subject_id)
        dst_path = os.path.join(outdir, subject_tp_id)
        os.symlink(src_path, dst_path)
        subject_tp_ids.append(subject_tp_id)

    # STEP 1 - create and process template
    subject_template_id = "%s_template_%s" % (subject_id, "_".join(timepoints))
    cmd = ["recon-all", "-base", subject_template_id]
    for subj_tp_id in subject_tp_ids:
        cmd += ["-tp", subj_tp_id]
    cmd += ["-all"]
    FSWrapper(cmd, shfile=fsconfig, subjects_dir=outdir)()

    # STEP 2 - rerun recon-all for all timepoints using the template
    subject_long_ids = []
    for subj_tp_id in subject_tp_ids:
        cmd = ["recon-all", "-long", subj_tp_id, subject_template_id, "-all"]
        FSWrapper(cmd, shfile=fsconfig, subjects_dir=outdir)()
        subject_long_ids += ["%s.long.%s" % (subj_tp_id, subject_template_id)]

    return subject_template_id, subject_long_ids


def recon_all_localgi(outdir, subject_id, subjects_dir,
                      fsconfig=DEFAULT_FREESURFER_PATH):
    """
    Computes local measurements of pial-surface gyrification at thousands of
    points over the cortical surface.

    Parameters
    ----------
    outdir: str
        Directory where to output. Created if not already existing.
    subject_id: str
        Identifier of subject.
    subjects_dir: str
        The FreeSurfer SUBJECTS_DIR.
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        The FreeSurfer configuration batch.

    Return
    ------
    subject_dir: str
        the FreeSurfer results for the subject.
    """
    # Check input parameters
    subject_dir = os.path.join(subjects_dir, subject_id)
    if not os.path.isdir(subject_dir):
        raise ValueError("'{0}' FreeSurfer subject directory does not "
                         "exists.".format(subject_dir))

    # If <outdir> does not exist, create it
    # if not os.path.isdir(outdir):
    #    os.mkdir(outdir)

    # Call FreeSurfer local gyrification
    cmd = ["recon-all", "-localGI", "-subjid", subject_id, "-sd", subjects_dir,
           "-no-isrunning"]
    recon = FSWrapper(cmd, shfile=fsconfig, env=os.environ)
    recon()

    return subject_dir
