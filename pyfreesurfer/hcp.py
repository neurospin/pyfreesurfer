#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Wrapper around the HCP prefreesurfer, freesurfer and postfreesurfer
scripts.

**Requirements for this module**

Installed versions of:

- FSL (version 5.0.6),
- FreeSurfer (version 5.3.0-HCP),
- gradunwarp (HCP version 1.0.2) if doing gradient distortion correction

Environment:

- FSLDIR
- FREESURFER_HOME
- HCPPIPEDIR
- CARET7DIR
- PATH (to be able to find gradient_unwarp.py)
"""

# System import
from __future__ import print_function
import os

# Pyfreesurfer import
from pyfreesurfer.wrapper import HCPWrapper
from .info import DEFAULT_WORKBENCH_PATH
from .info import DEFAULT_FREESURFER_PATH
from .info import DEFAULT_FSL_PATH


def prefreesurfer_hcp(path, subject, t1, t2, fmapmag, fmapphase, hcpdir,
                      brainsize=150, fmapgeneralelectric="NONE", echodiff=2.46,
                      SEPhaseNeg="NONE", SEPhasePos="NONE", echospacing="NONE",
                      seunwarpdir="NONE", t1samplespacing=0.0000074,
                      t2samplespacing=0.0000021, unwarpdir="z",
                      gdcoeffs="NONE", avgrdcmethod="SiemensFieldMap",
                      topupconfig="NONE", wbcommand=DEFAULT_WORKBENCH_PATH,
                      fslconfig=DEFAULT_FSL_PATH,
                      fsconfig=DEFAULT_FREESURFER_PATH):
    """ Performs all the HCP PreFreeSurfer steps.

    1. To average any image repeats (i.e. multiple T1w or T2w images
       available).
    2. To create a native, undistorted structural volume space for the subject
       Subject images in this native space will be distortion corrected
       for gradient and b0 distortions and rigidly aligned to the axes
       of the MNI space. 'Native, undistorted structural volume space'
       is sometimes shortened to the 'subject's native space' or simply
       'native space'.
    3. To provide an initial robust brain extraction.
    4. To align the T1w and T2w structural images (register them to the native
       space).
    5. To perform bias field correction.
    6. To register the subject's native space to the MNI space.

    At least one T1 weighted image and one T2 weighted image are required for
    this script to work.

    The main output directories are:

    * The t1w_folder: which is created by concatenating the following three
      option values: --path/--subject/--t1
    * The t2w_folder: which is created by concatenating the following three
      option values: --path/--subject/--t2
    * The atlas_space_folder: /path/subject/MNINonLinear

    The full list of output directories is:

    * /t1w_folder/T1w?_GradientDistortionUnwarp
    * /t1w_folder/AverageT1wImages
    * /t1w_folder/ACPCAlignment
    * /t1w_folder/BrainExtraction_FNIRTbased
    * /t1w_folder/xfms - transformation matrices and warp fields
    * /t2w_folder/T2w?_GradientDistortionUnwarp
    * /t2w_folder/AverageT1wImages
    * /t2w_folder/ACPCAlignment
    * /t2w_folder/BrainExtraction_FNIRTbased
    * /t2w_folder/xfms - transformation matrices and warp fields
    * /t2w_folder/T2wToT1wDistortionCorrectAndReg
    * /t1w_folder/BiasFieldCorrection_sqrtT1wXT1w
    * /atlas_space_folder
    * /atlas_space_folder/xfms

    The following settings for AvgrdcSTRING, MagnitudeInputName,
    PhaseInputName, and TE are for using the Siemens specific Gradient Echo
    Field Maps that are collected and used in the standard HCP protocol.

    The values set below are for the HCP Protocol using the Siemens Connectom
    Scanner: t1samplespacing=0.0000074, t2samplespacing=0.0000021,
    unwarpdir='z'.

    **References**

    [HCP]: http://www.humanconnectome.org
    [GlasserEtAl]: http://www.ncbi.nlm.nih.gov/pubmed/23668970
    [FSL]: http://fsl.fmrib.ox.ac.uk

    Parameters
    ----------
    path: str (mandatory)
        path to study data folder (~ to FreeSurfer home directory). Used with
        --subject input to create full path to root directory for all outputs
        generated as path/subject.
    subject: str (mandatory)
        subject ID. Used with --path input to create full path to root
        directory for all outputs generated as path/subject.
    t1: list of str (mandatory)
        list of full paths to T1-weighted structural images for the subject.
    t2: list of str (mandatory)
        list of full paths to T2-weighted structural images for the subject.
    brainsize: int (optional, default 150)
        brain size estimate in mm, 150 for humans.
    fmapmag: str (mandatory)
        Siemens Gradient Echo Fieldmap magnitude file.
    fmapphase: str (mandatory)
        Siemens Gradient Echo Fieldmap phase file.
    hcpdir: str (mandatory)
        the path to the HCP project containing the script of interest.
    fmapgeneralelectric: str (optional, default 'NONE')
        general Electric Gradient Echo Field Map file.
        Two volumes in one file: 1. field map in deg, 2. magnitude.
    echodiff: float (optional, default 2.46)
        delta TE in ms for field map or 'NONE' if not used.
        2.46 for 3T scanner or 1.02ms for 7T.
    SEPhaseNeg: str (optional, default 'NONE')
        for spin echo field map, path to volume with a negative phase encoding
        direction (LR in HCP data), set to 'NONE' if not using Spin Echo Field
        Maps.
    SEPhasePos: str (optional, default 'NONE')
        for spin echo field map, path to volume with a positive phase encoding
        direction (RL in HCP data), set to 'NONE' if not using Spin Echo Field
        Maps.
    echospacing: str (optional, default 'NONE')
        echo Spacing or Dwelltime of Spin Echo Field Map or 'NONE' if not used.
    seunwarpdir: str (optional, default 'NONE')
        phase encoding direction of the spin echo field map.
        (Only applies when using a spin echo field map.)
    t1samplespacing: float (optional, default 0.0000074)
        T1 image sample spacing.
        Set to NONE if not doing readout distortion correction.
    t2samplespacing: float (optional, default 0.0000021)
        T2 image sample spacing, 'NONE' if not used.
        Set to NONE if not doing readout distortion correction.
    unwarpdir: str (optional, default 'z')
        readout direction of the T1w and T2w images (Used with either a
        gradient echo field map or a spin echo field map).
        Set NONE if not doing readout distortion correction.
    gdcoeffs: str (optional, default 'NONE')
        file containing gradient distortion coefficients.
        Set to NONE to skip gradient distortion correction.
    avgrdcmethod: str (optional, default 'SiemensFieldMap')
        averaging and readout distortion correction method.
    topupconfig: str (optional, default 'NONE')
        configuration file for topup or 'NONE' if not used.
    wbcommand: str (optional, default DEFAULT_WORKBENCH_PATH)
        the path containing the wbcommand.
    fslconfig: str (optional, default NeuroSpin path)
        the path to the FSL 'fsl.sh' configuration file.
    fsconfig: str (optional, default NeuroSpin path)
        the path to the FreeSurfer configuration file.

    Returns
    -------
    t1w_folder: str
        the destination folder.
    t1_img: str
        the preprocessed T1w image.
    t1_img_brain: str
        the preprocessed T1w image brain.
    t2_img: str
        the preprocessed T2w image.
    """
    # Check input parameters: directories
    for directory in (path, hcpdir, wbcommand):
        if not os.path.isdir(directory):
            raise ValueError(
                "'{0}' is not a valid directory.".format(directory))

    # Check input parameters: filenames
    filenames = t1 + t2
    if fmapmag != "NONE":
        filenames.append(fmapmag)
    if fmapphase != "NONE":
        filenames.append(fmapphase)
    for filename in filenames:
        if not os.path.isfile(filename):
            raise ValueError("'{0}' is not a valid file.".format(filename))

    # High resolution T1w MNI template
    t1w_template = os.path.join(
        hcpdir, "global", "templates", "MNI152_T1_0.7mm.nii.gz")
    # High resolution brain extracted MNI template
    t1w_template_brain = os.path.join(
        hcpdir, "global", "templates", "MNI152_T1_0.7mm_brain.nii.gz")
    # High resolution MNI brain mask template
    template_mask = os.path.join(
        hcpdir, "global", "templates", "MNI152_T1_0.7mm_brain_mask.nii.gz")
    # Low resolution T1w MNI template
    t1w_template_2mm = os.path.join(
        hcpdir, "global", "templates", "MNI152_T1_2mm.nii.gz")
    # Low resolution MNI brain mask template
    template_2mm_mask = os.path.join(
        hcpdir, "global", "templates", "MNI152_T1_2mm_brain_mask_dil.nii.gz")
    # High resolution T2w MNI Template
    t2w_template = os.path.join(
        hcpdir, "global", "templates", "MNI152_T2_0.7mm.nii.gz")
    # High resolution T2w brain extracted MNI Template
    t2w_template_brain = os.path.join(
        hcpdir, "global", "templates", "MNI152_T2_0.7mm_brain.nii.gz")
    # Low resolution T2w MNI Template
    t2w_template_2mm = os.path.join(
        hcpdir, "global", "templates", "MNI152_T2_2mm.nii.gz")
    # FNIRT 2mm T1w configuration
    fnirtconfig = os.path.join(
        hcpdir,
        "global", "config", "T1_2_MNI152_2mm.cnf")

    # Command path
    prefs_pipeline = os.path.join(
        hcpdir, "PreFreeSurfer", "PreFreeSurferPipeline.sh")

    # Define HCP command
    prefs_cmd = [prefs_pipeline,
                 "--path", path,
                 "--subject", subject,
                 "--t1", ", ".join(t1),
                 "--t2", ", ".join(t2),
                 "--t1template", t1w_template,
                 "--t1templatebrain", t1w_template_brain,
                 "--t1template2mm", t1w_template_2mm,
                 "--t2template", t2w_template,
                 "--t2templatebrain", t2w_template_brain,
                 "--t2template2mm", t2w_template_2mm,
                 "--templatemask", template_mask,
                 "--template2mmmask", template_2mm_mask,
                 "--brainsize", str(brainsize),
                 "--fnirtconfig", fnirtconfig,
                 "--fmapmag", fmapmag,
                 "--fmapphase", fmapphase,
                 "--fmapgeneralelectric", fmapgeneralelectric,
                 "--echodiff", str(echodiff),
                 "--SEPhaseNeg", SEPhaseNeg,
                 "--SEPhasePos", SEPhasePos,
                 "--echospacing", echospacing,
                 "--seunwarpdir", seunwarpdir,
                 "--t1samplespacing", str(t1samplespacing),
                 "--t2samplespacing", str(t2samplespacing),
                 "--unwarpdir", unwarpdir,
                 "--gdcoeffs", gdcoeffs,
                 "--avgrdcmethod", avgrdcmethod,
                 "--topupconfig", topupconfig]

    # Define the HCP environment variable
    process = HCPWrapper(
        env={
            "HCPPIPEDIR": hcpdir,
            "HCPPIPEDIR_PreFS": os.path.join(hcpdir, "PreFreeSurfer",
                                             "scripts"),
            "HCPPIPEDIR_Global": os.path.join(hcpdir, "global", "scripts"),
            "HCPPIPEDIR_Templates": os.path.join(hcpdir, "global" "templates"),
            "HCPPIPEDIR_Config": os.path.join(hcpdir, "global", "config"),
            "CARET7DIR": wbcommand,
            "PATH": os.environ["PATH"]},
        fslconfig=fslconfig,
        fsconfig=fsconfig)

    # Execute the HCP command
    process(prefs_cmd)

    # T1w folder
    t1w_folder = os.path.join(path, subject, "T1w")
    # T1w FreeSurfer Input (Full Resolution)
    t1_img = os.path.join(t1w_folder, "T1w_acpc_dc_restore.nii.gz")
    # T1w FreeSurfer Input (Full Resolution)
    t1_img_brain = os.path.join(t1w_folder, "T1w_acpc_dc_restore_brain.nii.gz")
    # T2w FreeSurfer Input (Full Resolution)
    t2_img = os.path.join(t1w_folder, "T2w_acpc_dc_restore.nii.gz")

    return t1w_folder, t1_img, t1_img_brain, t2_img


def freesurfer_hcp(subject, t1w_folder, t1_img, t1_img_brain, t2_img, hcpdir,
                   wbcommand=DEFAULT_WORKBENCH_PATH,
                   fslconfig=DEFAULT_FSL_PATH,
                   fsconfig=DEFAULT_FREESURFER_PATH):
    """ Performs all the HCP FreeSurfer steps.

    1. Make Spline Interpolated Downsample to 1mm.
    2. Initial recon-all steps (with flags that are part of "-autorecon1", with
       the exception of -skullstrip).
    3. Generate brain mask.
    4. Call recon-all to run most of the "-autorecon2" stages, but turning off
       smooth2, inflate2, curvstats, and segstats stages.
    5. High resolution white matter and fine tune T2w to T1w registration.
    6. Intermediate Recon-all Steps.
    7. High resolution pial matter (adjusts the pial surface based on the the
       T2w image).
    8. Final recon-all steps.

    Parameters
    ----------
    subject: str (mandatory)
        the current subject identifier.
    t1w_folder: str (mandatory)
        the FreeSurfer working directory with all the subjects.
    t1_img: str (mandatory)
        the input anatomical image to be segmented with FreeSurfer
        (Full Resolution).
    t1_img_brain: str (mandatory)
        the input anatomical brain image to be segmented with FreeSurfer
        (Full Resolution).
    t2_img: str (mandatory)
        the input T2 image (Full Resolution).
    hcpdir: str (mandatory)
        the path to the HCP project containing the script of interest.
    wbcommand: str (optional, default DEFAULT_WORKBENCH_PATH)
        the path containing the wbcommand.
    fslconfig: str (optional, default NeuroSpin path)
        the path to the FSL 'fsl.sh' configuration file.
    fsconfig: str (optional, default NeuroSpin path)
        the path to the FreeSurfer configuration file.
    """
    # Check input parameters: directories
    for directory in (t1w_folder, hcpdir, wbcommand):
        if not os.path.isdir(directory):
            raise ValueError("'{0}' is not a valid directory.".format(
                             directory))

    # Check input parameters: filenames
    for filename in (t1_img, t1_img_brain, t2_img):
        if not os.path.isfile(filename):
            raise ValueError("'{0}' is not a valid filename.".format(
                             filename))

    # Command path
    fs_pipeline = os.path.join(
        hcpdir, "FreeSurfer", "FreeSurferPipeline.sh")

    # Define HCP command
    fs_cmd = [fs_pipeline,
              "--subject", subject,
              "--subjectDIR", t1w_folder,
              "--t1", t1_img,
              "--t1brain", t1_img_brain,
              "--t2", t2_img]

    # Define the HCP environment variables
    process = HCPWrapper(
        env={
            "HCPPIPEDIR": hcpdir,
            "HCPPIPEDIR_FS": os.path.join(hcpdir, "FreeSurfer", "scripts"),
            "CARET7DIR": wbcommand},
        fslconfig=fslconfig,
        fsconfig=fsconfig)

    # Execute the HCP command
    process(fs_cmd)


def postfreesurfer_hcp(path, subject, hcpdir,
                       wbcommand=DEFAULT_WORKBENCH_PATH,
                       fslconfig=DEFAULT_FSL_PATH,
                       fsconfig=DEFAULT_FREESURFER_PATH):
    """ Performs all the HCP PostFreeSurfer steps.

    1. Conversion of FreeSurfer Volumes and Surfaces to NIFTI and GIFTI and
       Create Caret Files and Registration.
    2. Create FreeSurfer ribbon file at full resolution.
    3. Myelin Mapping.

    Parameters
    ----------
    path: str (mandatory)
        the FreeSurfer working directory with all the subjects.
    subject: str (mandatory)
        the current subject identifier.
    hcpdir: str (mandatory)
        the path to the HCP project containing the script of interest.
    wbcommand: str (optional, default DEFAULT_WORKBENCH_PATH)
        the path containing the wbcommand.
    fslconfig: str (optional, default NeuroSpin path)
        the path to the FSL 'fsl.sh' configuration file.
    fsconfig: str (optional, default NeuroSpin path)
        the path to the FreeSurfer configuration file.
    """
    for directory in (path, hcpdir, wbcommand):
        if not os.path.isdir(directory):
            raise ValueError("'{0}' is not a valid directory.".format(
                             directory))

    surf_atlas_dir = os.path.join(
        hcpdir, "global", "templates", "standard_mesh_atlases")
    grayordinates_space_dir = os.path.join(
        hcpdir, "global", "templates", "91282_Greyordinates")
    subcortical_gray_labels = os.path.join(
        hcpdir, "global", "config", "FreeSurferSubcorticalLabelTableLut.txt")
    freeSurfer_labels = os.path.join(
        hcpdir, "global", "config", "FreeSurferAllLut.txt")
    reference_myelin_maps = os.path.join(
        hcpdir, "global", "templates", "standard_mesh_atlases",
        "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii")

    # Command path
    postfs_pipeline = os.path.join(
        hcpdir, "PostFreeSurfer", "PostFreeSurferPipeline.sh")

    # Define HCP command
    postfs_cmd = [postfs_pipeline,
                  "--path", path,
                  "--subject", subject,
                  "--surfatlasdir", surf_atlas_dir,
                  "--grayordinatesdir", grayordinates_space_dir,
                  "--grayordinatesres", 2,
                  "--hiresmesh", 164,
                  "--lowresmesh", 32,
                  "--subcortgraylabels", subcortical_gray_labels,
                  "--freesurferlabels", freeSurfer_labels,
                  "--refmyelinmaps", reference_myelin_maps,
                  "--regname", "FS"]

    # Define the HCP environment variables
    process = HCPWrapper(
        env={
            "HCPPIPEDIR": hcpdir,
            "HCPPIPEDIR_PostFS": os.path.join(hcpdir, "PostFreeSurfer",
                                              "scripts"),
            "CARET7DIR": wbcommand},
        fslconfig=fslconfig,
        fsconfig=fsconfig)

    # Execute the HCP command
    process(postfs_cmd)
