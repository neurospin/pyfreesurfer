##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
fMRI data processing on the cortical surface using the FreeSurfer package.
"""

# System import
from __future__ import print_function
import os
import glob
import shutil
import json
import numpy

# Package import
from .configuration import environment
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH

# Pyconnectome import
from pyconnectome import DEFAULT_FSL_PATH


def mkpreproc_sess(
        sessid,
        outdir,
        fsdir,
        fsd="bold",
        perrun=True,
        persession=False,
        fwhm=5.,
        update=True,
        force=False,
        sliceorder=None,
        surface="lhrh",
        mni3052mm=True,
        mni3051mm=False,
        nomc=False,
        nostc=False,
        nosmooth=False,
        nomask=False,
        noreg=False,
        noinorm=False,
        fsconfig=DEFAULT_FREESURFER_PATH,
        fslconfig=DEFAULT_FSL_PATH,
        verbose=0):
    """ Performs all the FreeSurfer fMRI preprocessing steps.

    Binding around the FreeSurfer's 'preproc-sess' command.

    Processing stages:

    * motion correction (MC)
    * slice-timing correction (STC)
    * smoothing
    * intensity normalization (INorm)
    * brain mask creation

    Note: MC and INorm require matlab but none of the other stages does.

    Parameters
    ----------
    sessid: str (mandatory)
        the session id file or string.
    outdir: str (mandatory)
        the folder where the organized FreeSurfer data are.
    fsdir: str (mandatory)
        the FreeSurfer working home directory.
    fsd: str (optional, default 'bold')
        the folder name that contains the 'f.nii.gz' functional volume.
    perrun: bool (optional, default True)
        motion cor and reg to middle TP of each run.
    persession: bool (optional, default False)
         motion cor and reg to 1st TP of 1st run.
    fwhm: float (optional, default 5)
        FWHM : smoothing level (mm)
    update: bool (optional, default True)
        only run a stage if input is newer than output.
    force: bool (optional, default False)
        force reprocessing of all stages (turns off -update).
    sliceorder: list of int (optional, default None)
        turn on slice timing correction with the given slice order.
    surface: str (optional, default 'lhrh')
        'self' or 'fsaverage' followed by hemi 'lh', 'rh' or 'lhrh'.
    mni3052mm: bool (optional, default True)
        sample raw data to mni305 at 2mm.
    mni3051mm: bool (optional, default False)
        sample raw data to mni305 at 1mm.
    nomc: bool (optional, default False)
        don't do motion correction.
    nostc: bool (optional, default False)
        don't do slice-timing correction.
    nosmooth: bool (optional, default False)
        don't do smoothing.
    nomask: bool (optional, default False)
        don't make brain mask.
    noreg: bool (optional, default False)
        don't do registration.
    noinorm: bool (optional, default False)
        don't do inorm.
    fsconfig: str (optional, default DEFAULT_FREESURFER_PATH)
        the FreeSurfer configuration batch.
    fslconfig: str (optional, default DEFAULT_FSL_PATH)
        the FSL configuration batch.
    verbose: int (optional, default 0)
        the verbosity level.

    Returns
    -------
    lh_fsaverage: list of str
        left hemisphere of fsaverage.
    rh_fsaverage: list of str
        right hemisphere of fsaverage.
    sub_fsaverage: list of str
        volume of fsaverage (MNI305 space) - for subcortical analyses.
    bbr_sum: str
        a file containing functional-anatomical cross-modal registration
        QC score. The QC value will be between 0 and 1, with 0 being
        perfect and 1 being terrible. Generally, anything over 0.8 indicates
        that something is probably wrong. View registrations using the
        following command tkregister-sess -s sess02 -fsd bold -per-run.
    mc_plots: list of str
        a list of motion correction plot for each session.
    """
    # Change current directory to deal with FreeeSurfer logs
    pwd = os.getcwd()
    os.chdir(outdir)

    # Check input parameters
    func_files = glob.glob(os.path.join(outdir, "*", fsd, "*", "f.nii.gz"))
    if verbose > 0:
        print("[info] Found {0} fMRI file(s) to be processed.".format(
            len(func_files)))
    if surface not in ("rh", "lh", "lhrh"):
        raise ValueError("Unknown '{0}' preproc-sess surface.".format(surface))

    # Call FreeSurfer fMRI preproc
    cmd = ["preproc-sess", "-d", outdir, "-fsd", fsd, "-fwhm",
           str(fwhm), "-surface", "fsaverage", surface]
    if os.path.isfile(sessid):
        cmd += ["-sf", sessid]
    else:
        cmd += ["-s", sessid]
    if sliceorder is not None:
        cmd.extend(sliceorder)  # -stc
    for value, name in ((perrun, "-per-run"), (persession, "-per-session"),
                        (update, "-update"), (force, "-force"),
                        (mni3052mm, "-mni305-2mm"), (mni3051mm, "-mni305-1mm"),
                        (nomc, "-nomc"), (nostc, "-nostc"),
                        (nosmooth, "-nosmooth"), (nomask, "-nomask"),
                        (noreg, "-noreg"), (noinorm, "-noinorm")):
        if value:
            cmd.append(name)
    fsl_env = environment(fslconfig)
    wrap = FSWrapper(cmd, shfile=fsconfig, env=fsl_env, subjects_dir=fsdir)
    wrap()

    # QC
    # > Motion Correction plot: gives the vector motion at each time point for
    # each run. Note that it is always positive because this is a magnitude.
    # It is also 0 at the middle time point because the middle time point is
    # used as the reference.
    cmd = ["plot-twf-sess", "-d", outdir, "-fsd", fsd, "-mc"]
    if os.path.isfile(sessid):
        cmd += ["-sf", sessid]
    else:
        cmd += ["-s", sessid]
    wrap = FSWrapper(cmd, shfile=fsconfig, subjects_dir=fsdir)
    wrap()

    # > Functional-Anatomical Cross-modal Registration: a summary of
    # registration quality. The QC value will be between 0 and 1, with 0 being
    # perfect and 1 being terrible. Generally, anything over 0.8 indicates
    # that something is probably wrong. View registrations using the following
    # command tkregister-sess -s sess02 -fsd bold -per-run.
    cmd = ["tkregister-sess", "-d", outdir, "-fsd", fsd, "-per-run",
           "-bbr-sum"]
    if os.path.isfile(sessid):
        cmd += ["-sf", sessid]
    else:
        cmd += ["-s", sessid]
    wrap = FSWrapper(cmd, shfile=fsconfig, subjects_dir=fsdir)
    wrap()
    bbr_sum = os.path.join(outdir, "bbr_sum.txt")
    with open(bbr_sum, "wt") as open_file:
        open_file.write(wrap.stdout)

    # Restore working directory
    os.chdir(pwd)

    # Move FreeSurfer logs
    fs_log_dir = os.path.join(outdir, "log")
    log_dir = os.path.join(outdir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    if os.path.isdir(fs_log_dir):
        for basename in os.listdir(fs_log_dir):
            shutil.move(os.path.join(fs_log_dir, basename),
                        os.path.join(log_dir, basename))
        shutil.rmtree(fs_log_dir)

    # Outputs
    lh_fsaverage = sorted(glob.glob(os.path.join(
        outdir, "*", fsd, "*", "f*.fsaverage.lh.nii.gz")))
    rh_fsaverage = sorted(glob.glob(os.path.join(
        outdir, "*", fsd, "*", "f*.fsaverage.rh.nii.gz")))
    sub_fsaverage = sorted(glob.glob(os.path.join(
        outdir, "*", fsd, "*", "f*.mni305.*mm.nii.gz")))
    mc_plots = glob.glob(os.path.join(
        outdir, "*", fsd, "*.mcdat.png"))

    return lh_fsaverage, rh_fsaverage, sub_fsaverage, bbr_sum, mc_plots


def mkmodel_sess(
        outdir,
        tr,
        contrasts_file,
        funcstem=None,
        fsd="bold",
        perrun=True,
        persession=False,
        fwhm=5.,
        mni3052mm=True,
        mni3051mm=False,
        blocked_design=True,
        retinototy_design=False,
        abblocked_design=False,
        spmhrf=0,
        fslhrf=None,
        gammafit=None,
        ngammaderiv=None,
        fir=None,
        nconditions=None,
        refeventdur=None,
        polyfit=2,
        mcextreg=True,
        nuisreg=None,
        nskip=4,
        fsconfig=DEFAULT_FREESURFER_PATH,
        verbose=0):
    """ Configure First Level GLM Analysis for event-related and blocked
    design.

    Not yet implemented possibilities are abblocked and retinotopy design.

    Binding around the FreeSurfer's 'mkanalysis-sess ' and 'mkcontrast-sess'
    commands.

    Requires matlab or octave

    Parameters
    ----------
    outdir: str (mandatory)
        the folder where the organized FreeSurfer data are.
    tr: float (mandatory)
        TR value in seconds.
    contrasts_file: str (mandatory)
        a JSON file that contains a list of contrasts with each contrast
        being a tuple of the form: ('name', 'stat', [condition list],
        [condition list ids], [weight list]).
    funcstem: str (optional, default None)
        override default basename, need to specify extension.
        The FWHM is no relevant when you have specified a funcstem
    fsd: str (optional, default 'bold')
        the folder name that contains the 'f.nii.gz' functional volume.
    perrun: bool (optional, default True)
        motion cor and reg to middle TP of each run.
    persession: bool (optional, default False)
         motion cor and reg to 1st TP of 1st run.
    fwhm: float (optional, default 5)
        FWHM : smoothing level (mm)
    mni3052mm: bool (optional, default True)
        sample raw data to mni305 at 2mm.
    mni3051mm: bool (optional, default False)
        sample raw data to mni305 at 1mm.
    spmhrf: int (optional, default 0)
        assume SPM HRF with nderiv derivatives.
    fslhrf: int (optional, default None)
        assume FSL HRF with nderiv derivatives
    gammafit: 2-uplet (optional, default None)
        assume IRF is a gamma function (gfDelta gfTau) -> (2.25 1.25).
    ngammaderiv: int (optional, default None)
        number of derivatives to gamma function.
    fir: 2-uplet (optional, default None)
        event prestimulus and total time window (sec) for FIR designs
    nconditions: int (optional, default None)
        number of conditions (excluding fixation).
    refeventdur: int (optional, default None)
        duration (sec) of reference event for scaling.
    polyfit: int (optional, default 2)
        fit trend with polynomial of order N: 0 mean offset, 1 temporal trend,
        2 quadratic trend.
    mcextreg: bool (optional, default True)
        use motion parameters as external nuissance regressors.
    nuisreg: 2-uplet (optional, default None)
        external nuisance regressor file and number of regressors to include
        (extreg n).
    nskip: int (optional, default 4)
        skip the first N time points in each run
    fsconfig: str (optional, default DEFAULT_FREESURFER_PATH)
        the FreeSurfer configuration batch.
    verbose: int (optional, default 0)
        the verbosity level.

    Returns
    -------
    analysis_names: list of str
        the configured model names.
    """
    # Change current directory to deal with FreeeSurfer logs
    pwd = os.getcwd()
    os.chdir(outdir)

    # Check input parameters
    for path in [contrasts_file]:
        if not os.path.isfile(path):
            raise ValueError("'{0}' is not a valid file.".format(path))
    if retinototy_design or abblocked_design:
        raise NotImplementedError("Selected design not yet supported.")

    # Load contrast description file
    with open(contrasts_file, "rt") as open_file:
        contrasts = json.load(open_file)

    # Call FreeSurfer fMRI firsl level GLM analysis: a different analysis is
    # needed for each space lh, rh, and mni305.
    analysis_names = []
    for space in ["lh", "rh", "mni305"]:

        # Analysis Name - name used to reference this collection of
        # parameters.
        analysis_name = "odd.even.sm{0}.{1}".format(fwhm, space)
        analysis_names.append(analysis_name)
        if verbose > 0:
            print("[info] Performing analysis '{0}'...".format(analysis_name))

        # Set preproc options
        cmd = ["mkanalysis-sess", "-fsd", fsd, "-paradigm", "odd.even.par",
               "-analysis", analysis_name, "-TR", str(tr), "-force"]
        if funcstem is None:
            cmd += ["-fwhm", str(fwhm)]
        else:
            cmd += ["-funcstem", funcstem]
        if space in ["lh", "rh"]:
            cmd += ["-surface", "fsaverage", space]
        else:
            cmd += ["-mni305"]
        for value, name in ((perrun, ["-per-run"]),
                            (persession, ["-per-session"]),
                            (mni3052mm, ["-mni305", "2"]),
                            (mni3051mm, ["-mni305", "1"])):
            if value:
                cmd.extend(name)

        # Set design options
        cmd += ["-event-related"]
        for value, name in ((spmhrf, "-spmhrf"),
                            (fslhrf, "-fslhrf"),
                            (ngammaderiv, "-ngammaderiv"),
                            (refeventdur, "-refeventdur"),
                            (nconditions, "-nconditions")):
            if value is not None:
                cmd.extend([name, str(value)])
        for value, name in ((gammafit, "-gammafit"),
                            (fir, "-fir")):
            if value is not None:
                cmd.extend([name] + [str(e) for e in value])

        # Set noise, drift, and temporal filtering options
        cmd += ["-polyfit", str(polyfit), "-nskip", str(nskip)]
        if mcextreg:
            cmd += ["-mcextreg"]
        if nuisreg is not None:
            cmd += ["-nuisreg", nuisreg[0], str(nuisreg[1])]

        # Create the analysis configuration file
        wrap = FSWrapper(cmd, shfile=fsconfig)
        wrap()

        # Create the contrasts
        for contrast_name, _, _, conditions, weights in contrasts:
            cmd = ["mkcontrast-sess", "-debug", "-analysis", analysis_name,
                   "-contrast", contrast_name, "-ncond", str(nconditions),
                   "-wcond"]
            wcond = numpy.zeros((nconditions,))
            wcond[conditions] = weights
            cmd += [str(e) for e in wcond]
            wrap = FSWrapper(cmd, shfile=fsconfig, env=os.environ)
            wrap()

    # Restore working directory
    os.chdir(pwd)

    # Move FreeSurfer logs
    fs_log_dir = os.path.join(outdir, "log")
    log_dir = os.path.join(outdir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    if os.path.isdir(fs_log_dir):
        for basename in os.listdir(fs_log_dir):
            shutil.move(os.path.join(fs_log_dir, basename),
                        os.path.join(log_dir, basename))
        shutil.rmtree(fs_log_dir)

    return analysis_names


def mkstat_sess(
        sessid,
        outdir,
        fsdir,
        analysis_names,
        svres=False,
        svres_unwhitened=False,
        run_wise=False,
        max_threads=False,
        overwrite=False,
        fsconfig=DEFAULT_FREESURFER_PATH,
        verbose=0):
    """ First-Level GLM Analysis

    Binding around the FreeSurfer's 'selxavg3-sess ' command.

    Requires matlab or octave.

    Parameters
    ----------
    sessid: str (mandatory)
        the session id file or string.
    outdir: str (mandatory)
        the folder where the organized FreeSurfer data are.
    fsdir: str (mandatory)
        the FreeSurfer working home directory.
    analysis_names: list of str (mandatory)
        the configured model names.
    svres: bool (optional, default False)
        save residuals (usually not needed).
    svres_unwhitened: bool (optional, default False)
        save unwhitened residuals (usually not needed).
    run_wise: bool (optional, default False)
        analyze each run separately.
    max_threads: bool (optional, default False)
        use all CPUs.
    overwrite: bool (optional, default False)
         delete analysis if session of already analyzed.
    fsconfig: str (optional, default DEFAULT_FREESURFER_PATH)
        the FreeSurfer configuration batch.
    verbose: int (optional, default 0)
        the verbosity level.
    """
    # Change directory to project directory
    pwd = os.getcwd()
    os.chdir(outdir)

    # Call FreeSurfer fMRI preproc
    cmd = ["selxavg3-sess", "-d", outdir, "-debug", "-no-preproc"]
    if os.path.isfile(sessid):
        cmd += ["-sf", sessid]
    else:
        cmd += ["-s", sessid]
    for value, name in ((svres, "-svres"),
                        (svres_unwhitened, "-svres-unwhitened"),
                        (run_wise, "-run-wise"),
                        (overwrite, "-overwrite"),
                        (max_threads, "-max-threads")):
        if value:
            cmd.append(name)
    log_dir = os.path.join(outdir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    cmd += ["-log", os.path.join(log_dir, "selxavg3-sess.log")]
    cmd += ["-analysis", ""]
    for name in analysis_names:
        if verbose > 0:
            print("[info] Performing analysis '{0}'...".format(name))
        cmd[-1] = name
        wrap = FSWrapper(cmd, shfile=fsconfig, env=os.environ,
                         subjects_dir=fsdir)
        wrap()

    # Restore working directory
    os.chdir(pwd)
