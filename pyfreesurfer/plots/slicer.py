##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import glob

# Pyfreesurfer import
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


# Define the axis mapping
AXIS_MAP = {
    "C": 0,
    "A": 1,
    "S": 2
}
AXIS_NAME = {
    "C": "coronal",
    "A": "axial",
    "S": "sagittal"
}


def slice_aparc_overlay(fsdir, sid, outdir, cut_axis="C",
                        slice_interval=(0, 255, 1), erase=False,
                        fsconfig=DEFAULT_FREESURFER_PATH):
    """ Slice the anatomical volume overlayed with the pial and white surfaces.
    Wrapping around the 'tkmedit' command.

    Parameters
    ----------
    fsdir: str (mandatory)
        the FreeSurfer segmentation home directory.
    sid: str (mandatory)
        the subject identifier.
    outdir: str (mandatory)
        the valid destination folder where sliced data will be written.
    cut_axis: str (optional, default 'C')
        the cut axis, use 'C' for Coronal, 'A' for Axial and 'S' for Sagittal.
    slice_interval: 3-uplet (optional, default (0, 255, 1))
        the slice interval (start index, stop index, increment).
    erase: bool (optional, default)
        if the destination subjects already exists and if this option is True,
        delete the folder, otherwise raise a ValueError.

    Returns
    -------
    slices: list of str
        the generated PNG slices.
    """
    # Check input parameters
    if cut_axis not in AXIS_MAP:
        raise ValueError(
            "{0} axis is not recognized: use {1}.".format(cut_axis, AXIS_MAP))
    subjdir = os.path.join(fsdir, sid)
    if not os.path.isdir(subjdir):
        raise ValueError("'{0}' is not a valid FreeSurfer subject "
                         "directory.".format(subjdir))
    if not os.path.isdir(outdir):
        raise ValueError("'{0}' is not a valid destination directory.".format(
            outdir))

    # Check T1 file existence
    anat_file = os.path.join(subjdir, "mri", "nu.mgz")
    if not os.path.isfile(anat_file):
        raise Exception("'{0}' file is missing.".format(anat_file))

    # Generate/execute the tcl slicer script for each axis
    os.environ["SUBJECTS_DIR"] = fsdir
    path_template = os.path.join(os.path.dirname(__file__),
                                 "tkmedit_slicer.tcl")
    path_script = os.path.join(outdir,
                               "tkmedit_slicer_{0}.tcl".format(cut_axis))
    rgb_file = os.path.join(outdir, "slice-{0}-$slice.rgb".format(cut_axis))
    config = {
        "ORIENT": AXIS_MAP[cut_axis],
        "START": slice_interval[0],
        "END": slice_interval[1],
        "INCR": slice_interval[2],
        "RGBFILE": rgb_file
    }
    with open(path_template, "r") as open_file:
        script = open_file.read() % config
    with open(path_script, "w") as open_file:
        open_file.write(script)
    cmd = ["tkmedit", sid, "nu.mgz", "-tcl", path_script]
    process = FSWrapper(cmd, shfile=fsconfig)
    process()

    # Convert RGB files to PNG files with ImageMagik
    slices = []
    for path in glob.glob(rgb_file.replace("$slice", "*")):
        png_file = path.replace(".rgb", ".png")
        slices.append(png_file)
        cmd = ["convert", path, png_file]
        process = FSWrapper(cmd, shfile=fsconfig)
        process()
        os.remove(path)

    return slices
