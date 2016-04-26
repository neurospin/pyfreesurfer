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
    bredala.register("clindmri.segmentation.freesurfer",
                     names=["textures2table", "mri_surf2surf"])
except:
    pass

# Wrappers of FreeSurfer's tabs
from pyfreesurfer.utils.datatools import textures2table


# Parameters to keep trace
__hopla__ = ["fsdir", "ico_order", "fsconfig", "textures_regex",
             "textures_files"]


# Script documentation
doc = """
Freesurfer textures
~~~~~~~~~~~~~~~~~~~

Generate text/ascii tables of freesurfer 'sulc' and 'curv' textures data. This
can then be easily imported into a spreadsheet and/or stats program. Note that
all the subject texture vertices need to be resampled in a common space.

The statistics are generated in a 'textures' sub folder of the FreeSurfer
'SUBJECTS_DIR' directory.

The 'sulc' surface
------------------

The 'sulc' conveys information on how far removed a particular vertex point
on a surface is from a hypothetical 'mid-surface' that exists between the gyri
and sulci. This surface is chosen so that the 'mean' of all these
displacements is zero. The 'sulc' gives a indication then of linear distance
and displacements: how 'deep' and how 'high' are brain folds.

In FreeSurfer, gyri have negative 'sulc' values, and indicate how far 'down'
a point has to travel to reach this 'mid-surface'. Sulci have positive 'sulc'
values, and indicate how far 'up' a point needs to travel to reach the
mid-surface.

The 'curv' surface
------------------

The 'curv' conveys information on the curvature (not distance) at a specific
vertex point. The sharper the curve, the higher the value
(positive or negative). Areas with positive curvature correspond to
curvatures in sulci, i.e. curving 'up'. Areas with negative curvature
correspond to curves pointing 'down', i.e. gyri.

Note that the 'curv.pial' is the smoothed mean curvature of the pial surface,
whereas the 'curv' is that of the white surface.

Command
-------

python $HOME/git/caps-clindmri/clindmri/scripts/freesurfer_textures.py \
    -v 2 \
    -i 7 \
    -c /i2bm/local/freesurfer-5.3.0/SetUpFreeSurfer.sh \
    -d /neurospin/imagen/BL/processed/freesurfer \
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
    "-e", "--erase", dest="erase", action="store_true",
    help="if activated, clean the subject folder.")
parser.add_argument(
    "-c", "--config", dest="fsconfig", metavar="FILE", required=True,
    help="the FreeSurfer configuration file.", type=is_file)
parser.add_argument(
    "-d", "--fsdir", dest="fsdir", required=True, metavar="PATH",
    help="the FreeSurfer processing home directory.", type=is_directory)
parser.add_argument(
    "-i", "--icoorder", dest="ico_order", default=7, type=int,
    choices=range(8),
    help=("specifies the order of the icosahedral tesselation (in [0, 7]) "
          "used to define the surface resolution."))
parser.add_argument(
    "-k", "--keep", dest="keep",  action="store_true",
    help=("if activated, keep the individual FreeSurfer resampled surfaces."))

# Parsing a Command Line
args = parser.parse_args()


"""
First check if the texture output directory exists on the file system, and
clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start FreeSurfer cat textures...")
    print("[info] Directory: {0}.".format(args.fsdir))
fsdir = args.fsdir
texturesdir = os.path.join(fsdir, "textures")
if os.path.isdir(texturesdir) and args.erase:
    shutil.rmtree(texturesdir)
if not os.path.isdir(texturesdir):
    os.makedirs(texturesdir)

"""
Summarize all the subjects' textures
"""
textures_files = []
ico_order = args.ico_order
fsconfig = args.fsconfig
textures_regex = [
    os.path.join("*", "surf", "lh.sulc"),
    os.path.join("*", "surf", "rh.sulc"),
    os.path.join("*", "surf", "lh.curv"),
    os.path.join("*", "surf", "rh.curv"),
    os.path.join("*", "surf", "lh.curv.pial"),
    os.path.join("*", "surf", "rh.curv.pial")
]
for regex in textures_regex:
    textures_files.extend(
        textures2table(regex, ico_order, fsdir,
                       keep_individual_textures=args.keep, save_mode="all",
                       fsconfig=fsconfig))
if args.verbose > 1:
    print("[result] Textures: {0}.".format(textures_files))
