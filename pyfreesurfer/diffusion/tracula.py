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
import tempfile
import shutil

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
set bveclist = ({bveclist})
set bvallist = ({bvallist})
set dob0 = 0
set doeddy = {doeddy:d}
set dorotbvecs = {dorotbvecs:d}
set doregflt = 0
set doregbbr = {doregbbr:d}
set doregmni = {doregmni:d}
set doregcvs = 0

# Unused trac-all options

# set runlist = ()
# set dcmroot = ()
# set nb0 = ()  # automatically detected by FreeSurfer since 5.2
# from b-value table, even if low b-values are not exactly 0
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


def create_bedpostx_organization(subject_id, bedpostx_dir, subjects_dir=None):
    """
    Tracula requires the BedpostX output files to be stored in the FreeSurfer
    folder of the subject: <subjects_dir>/<subject_id>/dmri.bedpostX
    Since we run Bedpostx outside of FreeSurfer/Tracula, this function creates
    the needed file organization using symbolic links.

    Parameters
    ----------
    subject_id: str
        Identifier of subject.
    bedpostx_dir: str
        BedpostX output directory.
    subjects_dir: str, default None
        Path to the FreeSurfer subjects directory. Required if the
        environment variable $SUBJECTS_DIR is not set.

    Returns
    -------
    fs_bedpostx_dir: str
        Path to the FreeSurfer BedpostX directory.
    """
    # FreeSurfer $SUBJECTS_DIR has to be passed or set as an env variable
    subjects_dir = get_or_check_freesurfer_subjects_dir(subjects_dir)

    # Check that subject's dir exists
    subject_dir = os.path.join(subjects_dir, subject_id)
    if not os.path.isdir(subject_dir):
        raise ValueError("Directory does not exist: %s" % subject_dir)

    # Create the FreeSurfer BedpostX directory if not existing
    fs_bedpostx_dir = os.path.join(subject_dir, "dmri.bedpostX")
    if not os.path.isdir(fs_bedpostx_dir):
        os.mkdir(fs_bedpostx_dir)

    # Create symbolic links to all BedpostX files
    for fn in os.listdir(bedpostx_dir):
        source = os.path.join(bedpostx_dir, fn)
        target = os.path.join(fs_bedpostx_dir, fn)
        os.symlink(source, target)

    return fs_bedpostx_dir


def trac_all(outdir, subject_id, dwi, bvals, bvecs, bedpostx_dir,
             subjects_dir=None, do_eddy=False, do_rotate_bvecs=True,
             do_bbregister=True, do_register_mni=True, temp_dir=None,
             fsconfig=DEFAULT_FREESURFER_PATH):
    """ Pathway reconstruction.

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
    bedpostx_dir: str
        BedpostX output directory.
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
    temp_dir: str, default None
        Directory to use to store temporary files. By default OS tmp dir.
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

    # Load bvecs and number of b0 volumes
    _, bvecs_array, _, nb_b0s = read_bvals_bvecs(bvals_path=bvals,
                                                 bvecs_path=bvecs,
                                                 min_bval=200.)

    # Create directory <outdir>/<subject_id>
    subject_outdir = os.path.join(outdir, subject_id)
    if not os.path.isdir(subject_outdir):
        os.makedirs(subject_outdir)

    # Create directory for temporary files
    temp_dir = tempfile.mkdtemp(prefix="trac-all_", dir=temp_dir)

    # The bvecs can be stored as a 3 x N or N x 3 matrix (N directions).
    # FreeSurfer requires the 2nd convention (one row per direction).
    # read_bvals_bvecs() always loads the bvecs file as a N x 3 numpy array,
    # save this numpy array in a temporary directory and use it as the
    # bvecs file to be sure to be in the right convention.
    bvecs_Nx3 = os.path.join(temp_dir, "bvecs_Nx3")
    numpy.savetxt(bvecs_Nx3, bvecs_array)

    # Create configuration file
    config_str = CONFIG_TEMPLATE.format(subjects_dir=subjects_dir,
                                        subjlist=subject_id,
                                        dtroot=outdir,
                                        dcmlist=dwi,
                                        bveclist=bvecs_Nx3,
                                        bvallist=bvals,
                                        doeddy=do_eddy,
                                        dorotbvecs=do_rotate_bvecs,
                                        doregbbr=do_bbregister,
                                        doregmni=do_register_mni)
    path_config = os.path.join(temp_dir, "trac-all.dmrirc")
    with open(path_config, "w") as f:
        f.write(config_str)

    # Run Tracula preparation
    cmd_prep = ["trac-all", "-prep", "-c", path_config]
    FSWrapper(cmd_prep, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    # Tracula requires the BedpostX files to be stored in
    # <outdir>/<subject_id>/dmri.bedpostX
    create_bedpostx_organization(subject_id=subject_id, subjects_dir=outdir,
                                 bedpostx_dir=bedpostx_dir)

    # Tracula pathways tractography
    cmd_path = ["trac-all", "-path", "-c", path_config]
    FSWrapper(cmd_path, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    # Clean tmp dir
    shutil.rmtree(temp_dir)

    return subject_outdir


def trac_all_longitudinal(outdir, subject_template_id, subject_timepoint_ids,
                          dwis, bvalss, bvecss, bedpostx_dirs,
                          subjects_dir=None, do_eddy=False,
                          do_rotate_bvecs=True, do_bbregister=True,
                          do_register_mni=True, temp_dir=None,
                          fsconfig=DEFAULT_FREESURFER_PATH):
    """

    Parameters
    ----------
    outdir: str
        Root directory where to create the subject's output directories.
        Created if not existing.
    subject_template_id: str
        Identifier of the subject template.
    subject_timepoint_ids: str
        Identifiers of the subject for all the timepoints.
    dwis: list of str
        Paths to Nifti diffusion series. In the order corresponding to
        <subject_timepoint_ids>.
    bvalss: list of str
        Paths to b-values of diffusion series. In the order corresponding to
        <dwis>.
    bvecss: list of str
        Paths to diffusion-sensitized directions of diffusion series. In the
        order corresponding to <dwis>.
    bedpostx_dirs: list of str
        BedpostX output directories. In the order corresponding to <dwis>.
    subjects_dir: str, default None
        Path to the FreeSurfer longitudinal subjects directory. Required if
        the environment variable $SUBJECTS_DIR is not set.
    do_eddy: bool, default False
        Apply FSL eddy-current correction.
    do_rotate_bvecs: bool, default True
        Rotate bvecs to match eddy-current correction.
    do_bbregister: bool, default True
        Register diffusion to T1 using bbregister.
    do_register_mni:
        Register T1 to MNI.
    temp_dir: str, default None
        Set the root temporary directory.
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        Path to the FreeSurfer configuration file.

    Returns
    -------
    subject_long_outdirs: list of str
        Path to longitudinal subject's output directories.
    """
    # Check input arguments

    # Check that the user has passed non-empty lists of the same length
    list_args = [subject_timepoint_ids, dwis, bvalss, bvecss, bedpostx_dirs]
    are_all_lists = all(map(lambda x: isinstance(x, list), list_args))
    all_same_size = len(set(map(len, list_args))) == 1
    non_empty = len(subject_timepoint_ids) > 1
    if not (are_all_lists & all_same_size & non_empty):
        raise ValueError("'subject_timepoint_ids', 'dwis', 'bvals', 'bvecs' "
                         "and 'bedpostx_dirs' must be lists of IDs/paths.")

    # FreeSurfer $SUBJECTS_DIR has to be passed or set as an env variable
    subjects_dir = get_or_check_freesurfer_subjects_dir(subjects_dir)

    # Check existence of input files/directories
    input_paths = dwis + bvalss + bvecss + bedpostx_dirs + [fsconfig]
    for path in input_paths:
        if not os.path.exists(path):
            raise ValueError("File or directory does not exist: %s" % path)

    # Create directory for temporary files
    temp_dir = tempfile.mkdtemp(prefix="trac-all_longitudinal_", dir=temp_dir)

    # The bvecs can be stored as a 3 x N or N x 3 matrix (N directions).
    # FreeSurfer requires the 2nd convention (one row per direction).
    # read_bvals_bvecs() always loads the bvecs file as a N x 3 numpy array,
    # save this numpy array in a temporary directory and use it as the
    # bvecs file to be sure to be in the right convention.
    bvecss_Nx3 = []
    for tp_sid, bvals, bvecs in zip(subject_timepoint_ids, bvalss, bvecss):
        _, bvecs_array, _, _ = read_bvals_bvecs(bvals_path=bvals,
                                                bvecs_path=bvecs,
                                                min_bval=200.)
        bvecs_Nx3 = os.path.join(temp_dir, "bvecs_Nx3_%s" % tp_sid)
        numpy.savetxt(bvecs_Nx3, bvecs_array)
        bvecss_Nx3.append(bvecs_Nx3)

    # Create configuration file
    str_subjlist = " ".join(subject_timepoint_ids)
    str_baselist = " ".join([subject_template_id] * len(subject_timepoint_ids))
    str_dwis = " ".join(dwis)
    str_bveclist = " ".join(bvecss_Nx3)
    str_bvallist = " ".join(bvalss)
    config_str = LONG_CONFIG_TEMPLATE.format(subjects_dir=subjects_dir,
                                             subjlist=str_subjlist,
                                             baselist=str_baselist,
                                             dtroot=outdir,
                                             dcmlist=str_dwis,
                                             bveclist=str_bveclist,
                                             bvallist=str_bvallist,
                                             doeddy=do_eddy,
                                             dorotbvecs=do_rotate_bvecs,
                                             doregbbr=do_bbregister,
                                             doregmni=do_register_mni)
    path_config = os.path.join(temp_dir, "trac-all.long.dmrirc")
    with open(path_config, "w") as f:
        f.write(config_str)

    # For each timepoint of subject:
    subject_long_outdirs = []
    for tp_sid, bedpostx_dir in zip(subject_timepoint_ids, bedpostx_dirs):

        # Create <outdir>/<tp sid>.long.<template id> if not existing
        long_sid = "%s.long.%s" % (tp_sid, subject_template_id)
        long_outdir = os.path.join(outdir, long_sid)
        if not os.path.isdir(long_outdir):
            os.makedirs(long_outdir)
        subject_long_outdirs.append(long_outdir)

        # Tracula requires the bedpostX files to be stored in
        # <outdir>/<tp sid>.long.<template id>/dmri.bedpostX
        create_bedpostx_organization(subject_id=long_sid, subjects_dir=outdir,
                                     bedpostx_dir=bedpostx_dir)

    # Run Tracula preparation
    cmd_prep = ["trac-all", "-prep", "-c", path_config]
    FSWrapper(cmd_prep, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    # Tracula pathways tractography
    cmd_path = ["trac-all", "-path", "-c", path_config]
    FSWrapper(cmd_path, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True)()

    # Clean tmp dir
    shutil.rmtree(temp_dir)

    return subject_long_outdirs
