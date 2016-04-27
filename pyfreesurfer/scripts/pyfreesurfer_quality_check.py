#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import argparse
import os
import shutil
import numpy
import nibabel
import copy

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("pyfreesurfer.utils.stattools",
                     names=["population_summary"])
    bredala.register("pyfreesurfer.plots.slicer",
                     names=["slice_aparc_overlay"])
    bredala.register("pyfreesurfer.plots.polar",
                     names=["polar_plot"])
    bredala.register("pyfreesurfer.utils.filetools",
                     names=["surf2ctm"])
except:
    pass

# Clindmri import
from pyfreesurfer import __version__ as version
from pyfreesurfer.utils.stattools import population_summary
from pyfreesurfer.plots.slicer import slice_aparc_overlay
from pyfreesurfer.plots.slicer import AXIS_NAME
from pyfreesurfer.plots.polar import polar_plot
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.utils.filetools import surf2ctm


# Parameters to keep trace
__hopla__ = ["tool", "version", "config", "inputs", "outputs",
             "subjdir", "fsconfig", "slices", "polars", "qcoutdir",
             "increment", "surfaces"]


# Script documentation
doc = """
FreeSurfer Quality Check
~~~~~~~~~~~~~~~~~~~~~~~~

Inspect the results returned by the FreeSurfer segmentation.

Steps:

1- Create the population statistic.

2- Create polar plots.

3- Create white/pial mesh overlays.

4- Compress the FreeSurfer surfaces

Command:

python $HOME/git/pyfreesurfer/pyfreesurfer/scripts/pyfreesurfer_quality_check \
    -v 2 \
    -c /i2bm/local/freesurfer/SetUpFreeSurfer.sh \
    -d /neurospin/senior/nsap/data/V4/freesurfer \
    -s ag110371 \
    -o /neurospin/senior/nsap/data/V4/qc/freesurfer \
    -i 20 \
    -e
"""


def is_file(filearg):
    """ Type for argparse - checks that file exists but does not open.
    """
    if not os.path.isfile(filearg):
        raise argparse.ArgumentError(
            "The file '{0}' does not exist!".format(filearg))
    return filearg


def is_directory(dirarg):
    """ Type for argparse - checks that directory exists.
    """
    if not os.path.isdir(dirarg):
        raise argparse.ArgumentError(
            "The directory '{0}' does not exist!".format(dirarg))
    return dirarg


parser = argparse.ArgumentParser(description=doc)
parser.add_argument(
    "-v", "--verbose", dest="verbose", type=int, choices=[0, 1, 2], default=0,
    help="increase the verbosity level: 0 silent, [1, 2] verbose.")
parser.add_argument(
    "-e", "--erase", dest="erase", action="store_true",
    help="if activated, clean the result folder if already created.")
parser.add_argument(
    "-c", "--fsconfig", dest="fsconfig", metavar="FILE", required=True,
    help="the FreeSurfer configuration file.", type=is_file)
parser.add_argument(
    "-d", "--fsdir", dest="fsdir", required=True, metavar="PATH",
    help="the FreeSurfer processing home directory.", type=is_directory)
parser.add_argument(
    "-o", "--outdir", dest="outdir", metavar="PATH", type=is_directory,
    help="the FreeSurfer QC home directory, default is 'fsdir'.")
parser.add_argument(
    "-s", "--subjectid", dest="subjectid", required=True,
    help="the subject identifier.")
parser.add_argument(
    "-i", "--incr", dest="incr", default=1, type=int,
    help="the increment between to slices.")
args = parser.parse_args()


"""
First construct the subject FreeSurfer directory and check its existance on
the file system.
"""
tool = "FreeSurfer QC"
config = args.fsconfig or DEFAULT_FREESURFER_PATH
if args.verbose > 0:
    print("[info] Start FreeSurfer QC...")
    print("[info] Directory: {0}.".format(args.fsdir))
    print("[info] Subject: {0}.".format(args.subjectid))
subjdir = os.path.join(args.fsdir, args.subjectid)
outdir = args.outdir
increment = args.incr
inputs = [subjdir]
outputs = []
if outdir is None:
    outdir = args.fsdir
    qcdir = os.path.join(subjdir, "qc")
else:
    qcdir = os.path.join(outdir, args.subjectid)
if not os.path.isdir(subjdir):
    raise ValueError(
        "'{0}' is not a FreeSurfer subject folder.".format(subjdir))
if not os.path.isdir(qcdir):
    os.mkdir(qcdir)
elif args.erase:
    shutil.rmtree(qcdir)
    os.mkdir(qcdir)

"""
Create the population statistic and get the subjects measures
"""
popstats = population_summary(args.fsdir)
indstats = population_summary(args.fsdir, args.subjectid)


"""
Create polar plots
"""
polars = []
for name, cohort_stats in popstats.items():
    individual_stats = indstats[name]
    snapfile = os.path.join(qcdir, "polarplot-{0}.png".format(name))
    polars.append(snapfile)
    polar_plot(individual_stats, cohort_stats, snapfile,
               name="polarplot-{0}".format(name))



"""
Create white/pial mesh overlays
"""
slices_mesh = []
for cut_axis in ["C", "A", "S"]:
    axisdir = os.path.join(qcdir, AXIS_NAME[cut_axis], "aparc_mesh")
    if not os.path.isdir(axisdir):
        os.makedirs(axisdir)
    slices_mesh.append(
        slice_aparc_overlay(args.fsdir, args.subjectid, axisdir,
                            cut_axis=cut_axis, erase=False,
                            slice_interval=(0, 255, increment),
                            fsconfig=config))
"""
Create aparc segmentation overlays
"""
slices_segmentation = []
for cut_axis in ["C", "A", "S"]:
    axisdir = os.path.join(qcdir, AXIS_NAME[cut_axis], "aparc_segmentation")
    if not os.path.isdir(axisdir):
        os.makedirs(axisdir)
    slices_segmentation.append(
        slice_aparc_segmentation(args.fsdir, args.subjectid, axisdir,
                                 cut_axis=cut_axis, erase=False,
                                 slice_interval=(0, 255, increment),
                                 fsconfig=config,
                                 fslookup=None))


"""
Compress the FreeSurfer surfaces
"""
surfaces = surf2ctm(subjdir, qcdir)

"""
Update the script outputs
"""
outputs = polars + slices_mesh + slices_segmentation + surfaces
