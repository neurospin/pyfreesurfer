##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Wrapper for the FreeSurfer Tracula tool.
"""

# Standard
import os

# Package
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.utils.filetools import get_or_check_freesurfer_subjects_dir
from pyfreesurfer.wrapper import FSWrapper

# Third-party
import numpy
from pyconnectomist.utils.dwitools import read_bvals_bvecs


# Templates to generate Tracula configuration file
CONFIG_TEMPLATE = """
setenv SUBJECTS_DIR {subjects_dir}
set subjlist = ({subjlist})
set dtroot = {dtroot}
set dcmlist = ({dcmlist})
set bvecfile = {bvecfile}
set bvalfile = {bvalfile}
set nb0 = {nb0}
set dob0 = 0
set doeddy = {doeddy:d}
set dorotbvecs = {dorotbvecs:d}
set doregflt = 0
set doregbbr = {doregbbr:d}
set doregmni = {doregmni:d}
set doregcvs = 0

# Unused trac-all options

# set runlist = ()
# set dcmroot = /
# set b0mlist = ()
# set b0plist = ()
# set echospacing = None
# set thrbet = 0.3
# set mnitemp = $FSLDIR/data/standard/MNI152_T1_1mm_brain.nii.gz
# set cvstemp = cvs_avg35
# set cvstempdir = $FREESURFER_HOME/subjects
# set usemaskanat = 1
# set pathlist = ( lh.cst_AS rh.cst_AS \
#                  lh.unc_AS rh.unc_AS \
#                  lh.ilf_AS rh.ilf_AS \
#                  fmajor_PP fminor_PP \
#                  lh.atr_PP rh.atr_PP \
#                  lh.ccg_PP rh.ccg_PP \
#                  lh.cab_PP rh.cab_PP \
#                  lh.slfp_PP rh.slfp_PP \
#                  lh.slft_PP rh.slft_PP )
# set ncpts = (6 6 5 5 5 5 7 5 5 5 5 5 4 4 5 5 5 5)
# set trainfile = $FREESURFER_HOME/trctrain/trainlist.txt
# set nstick = 2
# set nburnin = 200
# set nsample = 7500
# set nkeep = 5
# set reinit = 0
"""

LONG_CONFIG_TEMPLATE = "set baselist = ({baselist})\n" + CONFIG_TEMPLATE


def trac_all(outdir, subject_id, dwi, bvals, bvecs, bedpostx_dir,
             subjects_dir=None, do_eddy=False, do_rotate_bvecs=True,
             do_bbregister=True, do_register_mni=True,
             fsconfig=DEFAULT_FREESURFER_PATH):
    """

    Parameters
    ----------
    outdir: str
        Root directory where to create the subject's output directory.
        Created if not existing.
    subject_id: str
        Identifier of subject.
    dwi: str
        Path to input Nifti diffusion-weighted volumes.
    bvals: str
        Path to b-values of diffusion-weighted volumes.
    bvecs: str
        Path to diffusion-sensitized directions.
    subjects_dir: str, default None
        Path to the FreeSurfer subjects directory. Required if the
        environment variable $SUBJECTS_DIR is not set.
    do_eddy: bool, default False
        Apply FSL eddy-current correction.
    do_rotate_bvecs: bool, default True
        Rotate bvecs to match eddy-current correction.
    do_bbregister: bool, default True
        Register diffusion to T1 using bbregister.
    do_register_mni:
        Register T1 to MNI.
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        Path to the FreeSurfer configuration file.

    Returns
    -------
    subject_outdir: str
        Path to subject's output directory.
    """
    # FreeSurfer $SUBJECTS_DIR has to be passed or set as an env variable
    subjects_dir = get_or_check_freesurfer_subjects_dir(subjects_dir)

    # Check existence of input files/directories
    for path in [dwi, bvals, bvecs, bedpostx_dir, fsconfig]:
        if not os.path.exists(path):
            raise ValueError("File or directory does not exist: %s" % path)

    # Create directory <outdir>/<subject_id>/dmri if not existing
    subject_outdir = os.path.join(outdir, subject_id)
    subject_dmri_dir = os.path.join(subject_outdir, "dmri")
    if not os.path.isdir(subject_dmri_dir):
        os.makedirs(subject_dmri_dir)

    # Number of b0 volumes
    _, bvecs_array, _, nb_b0s = read_bvals_bvecs(bvals_path=bvals,
                                                 bvecs_path=bvecs,
                                                 min_bval=200.)

    # The bvecs can be stored as a 3 x N or N x 3 matrix (N directions).
    # FreeSurfer requires the 2nd convention (one row per direction).
    # read_bvals_bvecs() always loads the bvecs file as a N x 3 numpy array,
    # save this numpy array in <outdir>/<subject_id>/mri and use it as the
    # bvecs file to be sure to be in the right convention.
    bvecs_Nx3 = os.path.join(subject_dmri_dir, "bvecs_Nx3")
    numpy.savetxt(bvecs_Nx3, bvecs_array)

    # Create configuration file
    config_str = CONFIG_TEMPLATE.format(subjects_dir=subjects_dir,
                                        subjlist=subject_id,
                                        dtroot=outdir,
                                        dcmlist=dwi,
                                        bvecfile=bvecs_Nx3,
                                        bvalfile=bvals,
                                        nb0=nb_b0s,
                                        doeddy=do_eddy,
                                        dorotbvecs=do_rotate_bvecs,
                                        doregbbr=do_bbregister,
                                        doregmni=do_register_mni)
    path_config = os.path.join(subject_outdir, "trac-all.dmrirc")
    with open(path_config, "w") as f:
        f.write(config_str)

    # Run Tracula preparation
    cmd_prep = ["trac-all", "-prep", "-c", path_config]
    FSWrapper(cmd_prep, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    # FreeSurfer requires the bedpostX files to be in
    # <outdir>/<subject_id>/dmri.bedpostX

    # Create the directory if not existing
    dmri_bedpostx_dir = os.path.join(subject_outdir, "dmri.bedpostX")
    if not os.path.isdir(dmri_bedpostx_dir):
        os.mkdir(dmri_bedpostx_dir)

    # Create symbolic links to all bedpostX files
    for fn in os.listdir(bedpostx_dir):
        source = os.path.join(bedpostx_dir, fn)
        target = os.path.join(dmri_bedpostx_dir, fn)
        os.symlink(source, target)

    # Tracula pathways tractography
    cmd_path = ["trac-all", "-path", "-c", path_config]
    FSWrapper(cmd_path, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    return subject_outdir


# TODO: longitudinal
# def trac_all_longitudinal(subject_timepoint_ids, subject_template_id):
