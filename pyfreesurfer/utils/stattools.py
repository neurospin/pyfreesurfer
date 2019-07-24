##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides stat file manipulation tools.
"""

# Sytem import
import re
import os
import csv
import json
import glob
import numpy
import shutil
import nibabel
import tempfile

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FSL_PATH
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.conversions.surfconvs import mri_surf2surf
from pyfreesurfer.utils.filetools import get_or_check_freesurfer_subjects_dir


CONFIG_TEMPLATE = """
setenv SUBJECTS_DIR {subjects_dir}
set subjlist = ({subjlist})
set dtroot = {dtroot}
"""


def trac_all(outdir, subjects_dir=None, temp_dir=None,
             fsconfig=DEFAULT_FREESURFER_PATH, fslconfig=DEFAULT_FSL_PATH):
    """ Anisotropy and diffusivity along the trajectory of a pathway.

    Parameters
    ----------
    outdir: str
        Root directory where to create the subject's output directory.
        Created if not existing.
    subjects_dir: str, default None
        Path to the FreeSurfer subjects directory. Required if the
        environment variable $SUBJECTS_DIR is not set.
    temp_dir: str, default None
        Directory to use to store temporary files. By default OS tmp dir.
    fsconfig: str, default <pyfreesurfer.DEFAULT_FREESURFER_PATH>
        Path to the FreeSurfer configuration file.

    Returns
    -------
    statdir: str
        The directory containing the FreeSurfer summary files.
    outlierfile: str
        A file that contains the subjects flagged as outliers.
    """
    # FreeSurfer $SUBJECTS_DIR has to be passed or set as an env variable
    subjects_dir = get_or_check_freesurfer_subjects_dir(subjects_dir)

    # Find all the subjects with a pathway stat file
    statdirs = glob.glob(os.path.join(subjects_dir, "*", "dpath"))
    subjects = set([path.split(os.sep)[-2] for path in statdirs])
    subjects = " ".join(subjects)

    # Create directory for temporary files
    temp_dir = tempfile.mkdtemp(prefix="trac-all_", dir=temp_dir)

    # Create configuration file
    config_str = CONFIG_TEMPLATE.format(subjects_dir=subjects_dir,
                                        subjlist=subjects,
                                        dtroot=subjects_dir)
    path_config = os.path.join(temp_dir, "trac-all.dmrirc")
    with open(path_config, "w") as f:
        f.write(config_str)

    # Run Tracula preparation
    cmd_prep = ["trac-all", "-stat", "-c", path_config]
    FSWrapper(cmd_prep, shfile=fsconfig, subjects_dir=subjects_dir,
              add_fsl_env=True, fsl_sh=fslconfig)()

    # Move results to destination folder
    statdir = os.path.join(subjects_dir, "stats")
    shutil.move(statdir, outdir)

    # Clean tmp dir
    shutil.rmtree(temp_dir)

    # Detect outliers
    statdir = os.path.join(outdir, "stats")
    outlierfile = os.path.join(outdir, "outliers.json")
    logfiles = glob.glob(os.path.join(statdir, "*.log"))
    outliers = set()
    regex = r"^Found outlier path: .*"
    for path in logfiles:
        with open(path, "rt") as open_file:
            for match in re.findall(regex, open_file.read(),
                                    flags=re.MULTILINE):
                outliers.add(match.replace("Found outlier path: ", ""))
    with open(outlierfile, "wt") as open_file:
        json.dump(list(outliers), open_file, indent=4)

    return statdir, outlierfile


def tractstats2table(fsdir, outdir, fsconfig=DEFAULT_FREESURFER_PATH):
    """ Generate text/ascii tables of FreeSurfer tracula pathways anisotropy
    and diffusivity summary from 'dpath/<hemi>.<path>/pathstats.overall.txt'
    and 'dpath/<hemi>.<path>/pathstats.byvoxel.txt'.

    This can then be easily imported into a spreadsheet and/or stats program.

    Binding over the FreeSurfer's 'tractstats2table' command.

    Parameters
    ----------
    fsdir: (mandatory)
        The freesurfer working directory with all the subjects.
    outdir: str (mandatory)
        The destination folder.
    fsconfig: str (optional)
        The FreeSurfer configuration batch.

    Return
    ------
    statfiles: list of str
        The FreeSurfer summary files.
    """
    # Check input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))

    # Parameter that will contain the output group statistics
    statfiles = []

    # Fist find all the subjects with a pathway stat file
    pathstatfiles = glob.glob(
        os.path.join(fsdir, "*", "dpath", "*", "pathstats.overall.txt"))

    # Split these files by pathway names
    pathwayfiles = {}
    for path in pathstatfiles:
        pathwayname = path.split(os.sep)[-2]
        if pathwayname not in pathwayfiles:
            pathwayfiles[pathwayname] = []
        pathwayfiles[pathwayname].append(path)

    # Save the FreeSurfer current working directory and set the new one
    fscwd = None
    if "SUBJECTS_DIR" in os.environ:
        fscwd = os.environ["SUBJECTS_DIR"]
    os.environ["SUBJECTS_DIR"] = fsdir

    # Create the output stat directory
    fsoutdir = os.path.join(outdir, "overall_stats")
    if not os.path.isdir(fsoutdir):
        os.mkdir(fsoutdir)

    # Call freesurfer
    for name, files in pathwayfiles.items():

        statfile = os.path.join(fsoutdir, "{0}.csv".format(name))
        statfiles.append(statfile)
        cmd = [
            "tractstats2table", "--inputs"] + files + [
            "--overall", "--tablefile", statfile]

        recon = FSWrapper(cmd, shfile=fsconfig)
        recon()

    # Restore the FreeSurfer working directory
    if fscwd is not None:
        os.environ["SUBJECTS_DIR"] = fscwd

    return statfiles


def population_summary(statsdir, sid=None):
    """ Compute the mean, std from the FreeSurfer individual scores.
    If a subject identifier is given, return the FreeSurfer subject scores.

    Parameters
    ----------
    statsdir: str (mandatory)
        the path to the summary FreeSurfer 'stats' as generated by
        'pyfreesurfer.utils.stattools.aparcstats2table' and
        'pyfreesurfer.utils.stattools.asegstats2table'.
    sid: str (optional, default None)
        if None, compute the statistic from all the subjects,
        otherwise return only the specified subject scores.

    Returns
    -------
    popstats: dict
        the population statistic or the individual scores.
    """
    # Test input parameter
    if not os.path.isdir(statsdir):
        raise ValueError("'{0}' FreeSurfer home directory does not "
                         "exists.".format(statsdir))

    # Go through all statistics
    popstats = {
        "lh": {},
        "rh": {},
        "aseg": {}
    }

    # Detect all the files to be processed
    stats = glob.glob(os.path.join(statsdir, "*.csv"))
    for fpath in stats:

        # Detect file type
        basename = os.path.basename(fpath)
        if basename.startswith("aparc.2009s"):
            continue
        basename = basename.split(".")[0]
        if basename.startswith("aseg"):
            stype, _, sname = basename.split("_")
            hemi = "aseg"
            subject_header = "Measure:volume"
        elif basename.startswith("aparc"):
            stype, _, hemi, sname = basename.split("_")
            subject_header = "{0}.{1}.{2}".format(hemi, stype, sname)
        else:
            continue

        # Parse file
        if sname not in popstats[hemi]:
            popstats[hemi][sname] = {}
        with open(fpath, "rt") as openfile:
            reader = csv.DictReader(openfile)
            for line in reader:
                subject = line.pop(subject_header)
                if sid is not None:
                    if subject != sid:
                        continue
                for key, value in line.items():
                    popstats[hemi][sname].setdefault(key, []).append(
                        float(value))
        for region_name, values in popstats[hemi][sname].items():
            mean = numpy.mean(values)
            std = numpy.std(values)
            popstats[hemi][sname][region_name] = {
                "values": values,
                "m": mean,
                "s": std
            }

    return popstats


def aparcstats2table(fsdir, outdir, fsconfig=DEFAULT_FREESURFER_PATH):
    """ Generate text/ascii tables of freesurfer parcellation stats data
    '?h.aparc.stats' for both templates (Desikan & Destrieux).

    This can then be easily imported into a spreadsheet and/or stats program.

    Binding over the FreeSurfer's 'aparcstats2table' command.

    Parameters
    ----------
    fsdir: (mandatory)
        The freesurfer working directory with all the subjects.
    outdir: str (mandatory)
        The statistical destination folder.
    fsconfig: str (optional)
        The freesurfer configuration batch.

    Return
    ------
    statfiles: list of str
        The freesurfer summary stats.
    """
    # Check input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))

    # Parameter that will contain the output stats
    statfiles = []

    # Fist find all the subjects with a stat dir
    statdirs = glob.glob(os.path.join(fsdir, "*", "stats"))
    subjects = [item.lstrip(os.sep).split("/")[-2] for item in statdirs]

    # Save the FreeSurfer current working directory and set the new one
    fscwd = None
    if "SUBJECTS_DIR" in os.environ:
        fscwd = os.environ["SUBJECTS_DIR"]
    os.environ["SUBJECTS_DIR"] = fsdir

    # Create the output stat directory
    fsoutdir = os.path.join(outdir, "stats")
    if not os.path.isdir(fsoutdir):
        os.mkdir(fsoutdir)

    # Call freesurfer: Desikan template
    for hemi in ["lh", "rh"]:
        for meas in ["area", "volume", "thickness", "thicknessstd",
                     "meancurv", "gauscurv", "foldind", "curvind"]:

            statfile = os.path.join(
                fsoutdir, "aparc_stats_{0}_{1}.csv".format(hemi, meas))
            statfiles.append(statfile)
            cmd = ["aparcstats2table", "--subjects"] + subjects + [
                "--hemi", hemi, "--meas", meas, "--tablefile", statfile,
                "--delimiter", "comma", "--parcid-only"]

            recon = FSWrapper(cmd, shfile=fsconfig)
            recon()

    # Call freesurfer: Destrieux template
    for hemi in ["lh", "rh"]:
        for meas in ["area", "volume", "thickness", "thicknessstd",
                     "meancurv", "gauscurv", "foldind", "curvind"]:

            statfile = os.path.join(
                fsoutdir, "aparc.2009s_stats_{0}_{1}.csv".format(hemi, meas))
            statfiles.append(statfile)
            cmd = ["aparcstats2table", "--subjects"] + subjects + [
                "--parc", "aparc.a2009s", "--hemi", hemi, "--meas", meas,
                "--tablefile", statfile, "--delimiter", "comma",
                "--parcid-only"]

            recon = FSWrapper(cmd, shfile=fsconfig)
            recon()

    # Restore the FreeSurfer working directory
    if fscwd is not None:
        os.environ["SUBJECTS_DIR"] = fscwd

    return statfiles


def asegstats2table(fsdir, outdir, fsconfig=DEFAULT_FREESURFER_PATH):
    """ Generate text/ascii tables of freesurfer parcellation stats data
    'aseg.stats'.

    This can then be easily imported into a spreadsheet and/or stats program.

    Binding over the FreeSurfer's 'asegstats2table' command.

    Parameters
    ----------
    fsdir: str (mandatory)
        The freesurfer working directory with all the subjects.
    outdir: str (mandatory)
        The statistical destination folder.
    fsconfig: str (optional)
        The freesurfer configuration batch.

    Return
    ------
    statfiles: list of str
        The freesurfer summary stats.
    """
    # Check input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))

    # Parameter that will contain the output stats
    statfiles = []

    # Fist find all the subjects with a stat dir
    statdirs = glob.glob(os.path.join(fsdir, "*", "stats"))
    subjects = [item.lstrip(os.sep).split("/")[-2] for item in statdirs]

    # Save the FreeSurfer current working directory and set the new one
    fscwd = None
    if "SUBJECTS_DIR" in os.environ:
        fscwd = os.environ["SUBJECTS_DIR"]
    os.environ["SUBJECTS_DIR"] = fsdir

    # Create the output stat directory
    fsoutdir = os.path.join(outdir, "stats")
    if not os.path.isdir(fsoutdir):
        os.mkdir(fsoutdir)

    # Call freesurfer
    statfile = os.path.join(fsoutdir, "aseg_stats_volume.csv")
    statfiles.append(statfile)
    cmd = ["asegstats2table", "--subjects"] + subjects + [
        "--meas", "volume", "--tablefile", statfile, "--delimiter", "comma"]
    recon = FSWrapper(cmd, shfile=fsconfig)
    recon()

    # Restore the FreeSurfer working directory
    if fscwd is not None:
        os.environ["SUBJECTS_DIR"] = fscwd

    return statfiles


def textures2table(
        regex,
        ico_order,
        fsdir,
        outdir,
        keep_individual_textures=False,
        save_mode="numpy",
        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Generate text/ascii tables of freesurfer textures data.

    This can then be easily imported into a spreadsheet and/or stats program.
    Note that all the subject texture vertices need to be resampled in a common
    space.

    Parameters
    ----------
    regex: str (mandatory)
        a regular expression used to locate the files to be converted from
        the 'fsdir' directory.
    ico_order: int (mandatory)
        icosahedron order in [0, 7] that will be used to generate the cortical
        surface texture at a specific tessalation (the corresponding cortical
        surface can be resampled using the
        'clindmri.segmentation.freesurfer.resample_cortical_surface' function).
    fsdir: str (mandatory)
        FreeSurfer subjects directory 'SUBJECTS_DIR'.
    outdir: str (mandatory)
        The textures destination folder.
    keep_individual_textures: bool (optional, default False)
        if True, keep the individual resampled subject textures on disk.
    save_mode: str (optional, default 'numpy')
        save result in 'csv' or in 'numpy' or 'all'. In CSV format we keep
        only 4 digits and in Numpy format we save several single arrays into
        a single file.
    fsconfig: str (optional)
        the FreeSurfer '.sh' config file.

    Returns
    -------
    textures_files: list of str
        a list of file containing the selected subjects summary texture values.
    """
    # Check input parameters
    for path in (fsdir, outdir):
        if not os.path.isdir(path):
            raise ValueError("'{0}' is not a valid directory.".format(path))
    if save_mode not in ["numpy", "csv", "all"]:
        raise ValueError("'{0}' is not a valid save option must be "
                         "in ['numpy', 'csv', 'all']".format(save_mode))

    # Get the requested subject textures from the regex
    textures = glob.glob(os.path.join(fsdir, regex))

    # Resample each texture file
    basename = os.path.basename(regex)
    fsoutdir = os.path.join(outdir, "textures")
    surfacesdir = os.path.join(fsoutdir, basename)
    if not os.path.isdir(surfacesdir):
        os.makedirs(surfacesdir)
    textures_map = {}
    for texturefile in textures:

        # Get the subject id
        sid = texturefile.replace(fsdir, "")
        sid = sid.lstrip(os.sep).split(os.sep)[0]

        # Get the hemisphere
        hemi = basename.split(".")[0]

        # Create the destination resamples texture file
        resampled_texturefile = os.path.join(surfacesdir, "{0}_{1}.mgz".format(
            sid, basename))

        # Reasmple the surface
        mri_surf2surf(hemi, texturefile, resampled_texturefile,
                      ico_order=ico_order, fsdir=fsdir, sid=sid,
                      fsconfig=fsconfig)

        # Check that the resampled texture has the expected size
        profile_array = nibabel.load(resampled_texturefile).get_data()
        profile_dim = profile_array.ndim
        profile_shape = profile_array.shape
        if profile_dim != 3:
            raise ValueError(
                "Expected profile texture array of dimension 3 not "
                "'{0}'".format(profile_dim))
        if (profile_shape[1] != 1) or (profile_shape[2] != 1):
            raise ValueError(
                "Expected profile texture array of shape (*, 1, 1) not "
                "'{0}'.".format(profile_shape))

        # Organize the resampled textures in a single file
        if sid in textures_map:
            raise ValueError("Subject '{0}' already treated. Check the intput "
                             "'regex'.".format(sid))
        textures_map[sid] = profile_array.ravel().astype(numpy.single)

    # Remove surfaces folder
    if not keep_individual_textures:
        shutil.rmtree(surfacesdir)

    # Save textures in CSV or in Numpy
    textures_files = []
    if save_mode in ["csv", "all"]:
        textures_file = os.path.join(fsoutdir, basename + "." +
                                     str(ico_order) + ".csv")
        with open(textures_file, "wb") as open_file:
            csv_writer = csv.writer(open_file, delimiter=",")
            for sid in sorted(textures_map.keys()):
                row = [sid]
                row.extend(
                    ["{0:.4f}".format(elem) for elem in textures_map[sid]])
                csv_writer.writerow(row)
        textures_files.append(textures_file)
    if save_mode in ["numpy", "all"]:
        textures_file = os.path.join(fsoutdir, basename + "." +
                                     str(ico_order) + ".npz")
        numpy.savez(textures_file, **textures_map)
        textures_files.append(textures_file)

    return textures_files
