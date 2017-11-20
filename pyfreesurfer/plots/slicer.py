##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides image manipulation tools.
"""

# System import
import os
import glob

# Pyfreesurfer import
import pyfreesurfer
from pyfreesurfer.utils.filetools import parse_fs_lut
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


def tkmedit_slice(fsdir, sid, outdir, stype="edges", cut_axis="C",
                  slice_interval=(0, 255, 1), path_lut=None,
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
    stype: str (optional, default 'edges')
        the slicer type: 'edges' stands for pial/white edges overlay, 'aseg'
        stands for subcortical regions overlay and 'aparc' stands for cortical
        labels overlay.
    cut_axis: str (optional, default 'C')
        the cut axis, use 'C' for Coronal, 'A' for Axial and 'S' for Sagittal.
    slice_interval: 3-uplet (optional, default (0, 255, 1))
        the slice interval (start index, stop index, increment).
    path_lut: str (optional, default None)
        the lookup table to use for label coloration: mandatory option
        for the 'aparc' and 'aseg' slicer.

    Returns
    -------
    slices: list of str
        the generated PNG slices.
    """
    # Check input parameters
    if stype not in ["edges", "aparc", "aseg"]:
        raise ValueError("Unrecognize slicing type '{0}'. Implemented options "
                         "are ['edges', 'aparc', 'aseg'].".format(stype))
    if stype in ["aparc", "aseg"] and path_lut is None:
        raise ValueError("Need to specify the 'path_lut' parameter when the "
                         "slicing is set to '{0}'.".format(stype))
    if stype in ["aparc", "aseg"] and not os.path.isfile(path_lut):
        raise ValueError("'{0}' lookup table path does not "
                         "exists.".format(path_lut))
    if cut_axis not in AXIS_MAP:
        raise ValueError(
            "'{0}' axis is not recognized: use {1}.".format(cut_axis,
                                                            AXIS_MAP))
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
        raise ValueError("'{0}' FreeSurfer anatomical file is "
                         "missing.".format(anat_file))

    # Generate/execute the tcl slicer script for each axis
    fsvar = os.environ.get("SUBJECTS_DIR")
    os.environ["SUBJECTS_DIR"] = fsdir
    if stype == "edges":
        path_template = os.path.join(
            os.path.dirname(pyfreesurfer.__file__), "plots",
            "tkmedit_slicer_edges.tcl")
    else:
        path_template = os.path.join(
            os.path.dirname(pyfreesurfer.__file__), "plots",
            "tkmedit_slicer_labels.tcl")
    if stype == "aparc":
        fs_lut_names, fs_lut_colors = parse_fs_lut(path_lut)
        path_lut = os.path.join(outdir, "CustomFreeSurferColorLUT.txt")
        with open(path_lut, "wt") as open_file:
            for label in sorted(fs_lut_names.keys()):
                name = fs_lut_names[label]
                r, g, b = fs_lut_colors[label]
                a = 255
                if label >= 1000:
                    a = 0
                open_file.write("{0}{1}{2}{3}{4}{5}\n".format(
                    str(label).ljust(10, " "), name.ljust(50, " "),
                    str(r).ljust(4, " "), str(g).ljust(4, " "),
                    str(b).ljust(4, " "), str(a).ljust(4, " ")))
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
    if stype != "edges":
        config["LOOKUPTABLE"] = path_lut
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

    # Restore environ
    if fsvar is not None:
        os.environ["SUBJECTS_DIR"] = fsvar
    else:
        del os.environ["SUBJECTS_DIR"]

    return slices
