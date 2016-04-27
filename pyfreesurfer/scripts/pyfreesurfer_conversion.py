#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import os
import shutil
import argparse

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("pyfreesurfer.conversions.voltools",
        names=["mri_convert"])
    bredala.register("pyfreesurfer.conversions.surftools",
        names=["resample_cortical_surface", "surf_convert"])
    bredala.register("pyfreesurfer.utils.regtools",
        names=["conformed_to_native_space"])
except:
    pass

# Pyfreesurfer import
from pyfreesurfer import __version__ as version
from pyfreesurfer import DEFAULT_FREESURFER_PATH
from pyfreesurfer.conversions.voltools import mri_convert
from pyfreesurfer.conversions.surftools import resample_cortical_surface
from pyfreesurfer.utils.regtools import conformed_to_native_space
from pyfreesurfer.conversions.surftools import surf_convert


# Parameters to keep trace
__hopla__ = ["tool", "version", "config", "inputs", "outputs",
             "subjdir", "convertdir", "niftifiles", "trffile",
             "surfaces", "annotations"]


# Script documentation
doc = """
Freesurfer conversion
~~~~~~~~~~~~~~~~~~~~~

Convert the results returned by the FreeSurfer cortical reconstruction
pipeline.

Steps:

1- Nifti conversions: aseg - aparc+aseg - aparc.a2009s+aseg - wm - t1.
   Export FreeSurfer '.mgz' images of interest in Nifti format. These
   images are resliced like the 'rawavg.mgz' file, have a '.native'
   suffix and are stored in a 'convert' folder.

2- Registration matrix: between the conformed space (orig.mgz)
   and the native anatomical (rawavg.mgz).

3- Surface conversions: resample the white or pial FreeSurfer
   surfaces at different resolutions (impacts the number of vertex)
   with common mesh that can be directly used in a longitudinal
   setting. The results are also stored in a 'convert' folder with
   a '.native' suffix and the considered level in the file name. Vetex
   are expressed in the index coordinate system.

Command:

python $HOME/git/pyfreesurfer/pyfreesurfer/scripts/pyfreesurfer_conversion \
    -v 2 \
    -c /i2bm/local/freesurfer/SetUpFreeSurfer.sh \
    -d /neurospin/senior/nsap/data/V4/freesurfer \
    -s ag110371 \
    -o /neurospin/senior/nsap/data/V4/qc/freesurfer \
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
    help="if activated, clean the result folder.")
parser.add_argument(
    "-c", "--config", dest="fsconfig", metavar="FILE", required=True,
    help="the FreeSurfer configuration file.", type=is_file)
parser.add_argument(
    "-d", "--fsdir", dest="fsdir", required=True, metavar="PATH",
    help="the FreeSurfer processing home directory.", type=is_directory)
parser.add_argument(
    "-o", "--outdir", dest="outdir", required=True, metavar="PATH",
    help="the FreeSurfer conversion home directory.", type=is_directory)
parser.add_argument(
    "-s", "--subjectid", dest="subjectid", required=True,
    help="the subject identifier.")
args = parser.parse_args()


"""
First construct the subject FreeSurfer directory and check its existance on
the file system.
"""
tool = "FreeSurfer conversions"
config = args.fsconfig or DEFAULT_FREESURFER_PATH 
if args.verbose > 0:
    print("[info] Start FreeSurfer conversions...")
    print("[info] Directory: {0}.".format(args.fsdir))
    print("[info] Subject: {0}.".format(args.subjectid))
subjdir = os.path.join(args.fsdir, args.subjectid)
inputs = [subjdir]
outputs = []
convertdir = os.path.join(args.outdir, args.subjectid, "convert")
if not os.path.isdir(subjdir):
    raise ValueError(
        "'{0}' is not a FreeSurfer subject folder.".format(subjdir))
if not os.path.isdir(convertdir):
    os.mkdir(convertdir)
elif args.erase:
    shutil.rmtree(convertdir)
    os.mkdir(convertdir)


"""
Step 1: Nifti conversions.
"""
if args.verbose > 0:
    print("[info] Start Nifti conversions...")
niftifiles = {}
for modality in ["aparc+aseg", "aparc.a2009s+aseg", "aseg", "wm", "rawavg"]:
    regex = os.path.join(args.subjectid, "mri", "{0}.mgz".format(modality))
    niftifiles[modality] = mri_convert(
        args.fsdir, regex, args.outdir, reslice=True,
        interpolation="nearest", fsconfig=config)
    outputs += niftifiles[modality]
    if args.verbose > 1:
        print("[result] {0}: {1}.".format(modality, niftifiles[modality]))


"""
Step 2: Registration matrix.
"""
if args.verbose > 0:
    print("[info] Start Registration matrix...")
regex = os.path.join(args.subjectid, "mri")
trffile = conformed_to_native_space(
    args.fsdir, regex, args.outdir, fsconfig=config)
outputs.append(trffile)
if args.verbose > 1:
    print("[result] trffile: {0}.".format(trffile))


"""
Step 3: Surface conversions.
"""
if args.verbose > 0:
    print("[info] Start surface conversions...")
surfaces = {}
annotations = []
for modality in ["pial", "white"]:
    for hemi in ["lh", "rh"]:
        name = "{0}.{1}".format(hemi, modality)
        regex = os.path.join(args.subjectid, "surf", name)
        resamplefiles, annotfiles = resample_cortical_surface(
            args.fsdir, regex, args.outdir, orders=[4, 5, 6, 7],
            surface_name=modality, fsconfig=config)
        annotations.extend(annotfiles)
        surfaces[name] = surf_convert(
            args.fsdir, niftifiles["rawavg"], resamplefiles,
            rm_orig=True, fsconfig=config)
        outputs += surfaces[name]
        if args.verbose > 1:
            print("[result] {0}: {1}.".format(name, surfaces[name]))
annotations = list(set(annotations))
outputs += annotations
if args.verbose > 1:
    print("[result] Annotations: {0}.".format(annotations))

