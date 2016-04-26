#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
"""

# System import
from __future__ import print_function
import os
import shutil
import argparse

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("clindmri.segmentation.freesurfer", names=["recon_all"])
except:
    pass

# Wrappers of FreeSurfer's tabs
from pyfreesurfer.segmentation import recon_all


# Parameters to keep trace
__hopla__ = ["fsdir", "subjectid", "anatfile"]


# Script documentation
doc = """
Freesurfer segmentation
~~~~~~~~~~~~~~~~~~~~~~~

Performs all the FreeSurfer cortical reconstruction process.

Steps:

1- Motion Correction and Conform
2- NU (Non-Uniform intensity normalization)
3- Talairach transform computation
4- Intensity Normalization 1
5- Skull Strip
6- EM Register (linear volumetric registration)
7- CA Intensity Normalization
8- CA Non-linear Volumetric Registration
9- Remove Neck
10- LTA with Skull
11- CA Label (Volumetric Labeling, ie Aseg) and Statistics
12- Intensity Normalization 2 (start here for control points)
13- White matter segmentation
14- Edit WM With ASeg
15- Fill (start here for wm edits)
16- Tessellation (begins per-hemisphere operations)
17- Smooth1
18- Inflate1
19- QSphere
20- Automatic Topology Fixer
21- Final Surfs (start here for brain edits for pial surf)
22- Smooth2
23- Inflate2
24- Spherical Mapping
25- Spherical Registration
26- Spherical Registration, Contralateral hemisphere
27- Map average curvature to subject
28- Cortical Parcellation - Desikan_Killiany and Christophe (Labeling)
29- Cortical Parcellation Statistics
30- Cortical Ribbon Mask
31- Cortical Parcellation mapping to Aseg

Command:

python $HOME/git/clindmri/scripts/freesurfer_reconall.py
    -v 2
    -c /i2bm/local/freesurfer/SetUpFreeSurfer.sh
    -d /volatile/imagen/dmritest/freesurfer
    -s 000043561374
    -a /volatile/imagen/dmritest/t1.nii.gz
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

# Setting up a Parser
parser = argparse.ArgumentParser(description=doc)

# Defining Arguments
parser.add_argument(
    "-v", "--verbose", dest="verbose", type=int, choices=[0, 1, 2], default=0,
    help="increase the verbosity level: 0 silent, [1, 2] verbose.")
parser.add_argument(
    "-e", "--errase", dest="errase", action="store_true",
    help="if activated, clean the subject folder.")
parser.add_argument(
    "-c", "--config", dest="fsconfig", metavar="FILE", required=True,
    help="the FreeSurfer configuration file.", type=is_file)
parser.add_argument(
    "-d", "--fsdir", dest="fsdir", required=True, metavar="PATH",
    help="the FreeSurfer processing home directory.", type=is_directory)
parser.add_argument(
    "-s", "--subjectid", dest="subjectid", required=True,
    help="the subject identifier.")
parser.add_argument(
    "-a", "--anatfile", dest="anatfile", metavar="FILE", required=True,
    help="the subject anatomical image to be processed.", type=is_file)

# Parsing a Command Line
args = parser.parse_args()


"""
First check if the subject FreeSurfer directory exists on the file system, and
clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start FreeSurfer recon_all...")
    print("[info] Directory: {0}.".format(args.fsdir))
    print("[info] Subject: {0}.".format(args.subjectid))
    print("[info] Anatomy: {0}.".format(args.anatfile))
fsdir = args.fsdir
subjectid = args.subjectid
anatfile = args.anatfile
subjdir = os.path.join(fsdir, subjectid)
if os.path.isdir(subjdir) and args.errase:
    shutil.rmtree(subjdir)


"""
Segmentation: all steps
"""
subjdir = recon_all(fsdir, anatfile, subjectid, fsconfig=args.fsconfig)
if args.verbose > 1:
    print("[result] In folder: {0}.".format(subjdir))
