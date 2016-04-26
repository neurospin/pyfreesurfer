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
                     names=["aparcstats2table", "asegstats2table"])
except:
    pass

# Wrappers of FreeSurfer's tabs
from pyfreesurfer.utils.datatools import aparcstats2table
from pyfreesurfer.utils.datatools import asegstats2table


# Parameters to keep trace
__hopla__ = ["fsdir", "statfiles"]


# Script documentation
doc = """
Freesurfer statistics
~~~~~~~~~~~~~~~~~~~~~

Generate text/ascii tables of FreeSurfer parcellation stats data
'aseg.stats' and '?h.aparc.stats'. This can then be easily imported into a
spreadsheet and/or stats program.

The statistics are generated in a 'stats' sub folder of the FreeSurfer
'SUBJECTS_DIR' directory.

Command:

python $HOME/git/caps-clindmri/clindmri/scripts/freesurfer_stats.py \
    -v 2 \
    -c /i2bm/local/freesurfer/SetUpFreeSurfer.sh \
    -d /neurospin/imagen/FU2/processed/freesurfer \
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

# Parsing a Command Line
args = parser.parse_args()


"""
First check if the statistic directory exists on the file system, and
clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start FreeSurfer cat stats...")
    print("[info] Directory: {0}.".format(args.fsdir))
fsdir = args.fsdir
statsdir = os.path.join(fsdir, "stats")
if os.path.isdir(statsdir) and args.erase:
    shutil.rmtree(statsdir)
if not os.path.isdir(statsdir):
    os.makedirs(statsdir)


"""
Summarize all the subjects' statistics
"""
statfiles = aparcstats2table(fsdir, fsconfig=args.fsconfig)
statfiles.extend(asegstats2table(fsdir, fsconfig=args.fsconfig))
if args.verbose > 1:
    print("[result] Stats: {0}.".format(statfiles))
