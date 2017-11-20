"""
Pyfreesurfer Textures
=====================

Example automatically generated from package script.
"""


# System import
from __future__ import print_function
import os
import shutil
import argparse
from datetime import datetime
import json
from pprint import pprint
import textwrap
from argparse import RawTextHelpFormatter

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("pyfreesurfer.utils.stattools",
                     names=["textures2table"])
    bredala.register("pyfreesurfer.conversion.surftools",
                     names=["mri_surf2surf"])
except:
    pass

# Pyfreesurfer import
from pyfreesurfer import __version__ as version
from pyfreesurfer.utils.stattools import textures2table
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


# Parameters to keep trace
__hopla__ = ["runtime", "inputs", "outputs"]


# Script documentation
DOC = """
Freesurfer textures
~~~~~~~~~~~~~~~~~~~

Generate text/ascii tables of freesurfer 'sulc' and 'curv' textures data. This
can then be easily imported into a spreadsheet and/or stats program. Note that
all the subject texture vertices need to be resampled in a common space.

The statistics are generated in a 'textures' sub folder of the FreeSurfer
processing home directory.

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

python $HOME/git/pyfreesurfer/pyfreesurfer/scripts/pyfreesurfer_textures \
    -v 2 \
    -i 7 \
    -c /i2bm/local/freesurfer-5.3.0/SetUpFreeSurfer.sh \
    -d /neurospin/senior/nsap/data/V4/freesurfer \
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


def get_cmd_line_args():
    """
    Create a command line argument parser and return a dict mapping
    <argument name> -> <argument value>.
    """
    parser = argparse.ArgumentParser(
        prog="python pyfreesurfer_textures",
        description=textwrap.dedent(DOC),
        formatter_class=RawTextHelpFormatter)

    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-d", "--fsdir", dest="fsdir", required=True, metavar="PATH",
        help="the FreeSurfer processing home directory.", type=is_directory)
    required.add_argument(
        "-o", "--outdir",
        metavar="PATH", required=True, type=is_directory,
        help="the FreeSurfer processing home directory.")

    # Optional arguments
    parser.add_argument(
        "-v", "--verbose",
        type=int, choices=[0, 1, 2], default=0,
        help="increase the verbosity level: 0 silent, [1, 2] verbose.")
    parser.add_argument(
        "-e", "--erase",
        action="store_true",
        help="if activated, clean the 'textures' folder.")
    parser.add_argument(
        "-i", "--icoorder", dest="ico_order",
        default=7, type=int, choices=range(8),
        help=("specifies the order of the icosahedral tesselation (in [0, 7]) "
              "used to define the surface resolution."))
    parser.add_argument(
        "-k", "--keep",
        action="store_true",
        help=("if activated, keep the individual FreeSurfer resampled "
              "surfaces."))
    parser.add_argument(
        "-c", "--config", dest="fsconfig",
        metavar="FILE", type=is_file,
        help="the FreeSurfer configuration file.")

    # Create a dict of arguments to pass to the 'main' function
    args = parser.parse_args()
    if args.fsconfig is None:
        args.fsconfig = DEFAULT_FREESURFER_PATH

    return args


#############################################################################
# Parse the command line.

args = get_cmd_line_args()
tool = "pyfreesurfer_textures"
timestamp = datetime.now().isoformat()
tool_version = version
freesurfer_config = args.fsconfig
freesurfer_version = FSWrapper([], freesurfer_config).version
params = locals()
runtime = dict([(name, params[name])
               for name in ("freesurfer_config", "tool", "tool_version",
                            "freesurfer_version", "timestamp")])
if args.verbose > 0:
    print("[info] Start FreeSurfer cat textures...")
    print("[info] FreeSurfer data directory: {0}.".format(args.fsdir))
    print("[info] Output directory: {0}.".format(args.outdir))
    print("[info] Resampling level: {0}.".format(args.ico_order))
fsdir = args.fsdir
outdir = args.outdir
ico_order = args.ico_order
texturesdir = os.path.join(outdir, "textures")
params = locals()
inputs = dict([(name, params[name])
               for name in ("fsdir", "outdir", "ico_order", "texturesdir")])
outputs = None
if os.path.isdir(texturesdir) and args.erase:
    shutil.rmtree(texturesdir)
if not os.path.isdir(texturesdir):
    os.makedirs(texturesdir)


#############################################################################
# Summarize all the subjects' textures

textures_files = []
textures_regex = [
    os.path.join("*", "surf", "lh.thickness"),
    os.path.join("*", "surf", "rh.thickness"),
    os.path.join("*", "surf", "lh.sulc"),
    os.path.join("*", "surf", "rh.sulc"),
    os.path.join("*", "surf", "lh.curv"),
    os.path.join("*", "surf", "rh.curv"),
    os.path.join("*", "surf", "lh.curv.pial"),
    os.path.join("*", "surf", "rh.curv.pial")
]
inputs["textures_regex"] = textures_regex
for regex in textures_regex:
    textures_files.extend(
        textures2table(regex, ico_order, fsdir, outdir,
                       keep_individual_textures=args.keep, save_mode="all",
                       fsconfig=freesurfer_config))
if args.verbose > 1:
    print("[result] Textures: {0}.".format(textures_files))


#############################################################################
# Update the outputs and save them and the inputs in a 'logs' directory.

logdir = os.path.join(texturesdir, "logs")
if not os.path.isdir(logdir):
    os.mkdir(logdir)
params = locals()
outputs = dict([(name, params[name]) for name in ("textures_files", )])
for name, final_struct in [("inputs", inputs), ("outputs", outputs),
                           ("runtime", runtime)]:
    log_file = os.path.join(logdir, "{0}.json".format(name))
    with open(log_file, "wt") as open_file:
        json.dump(final_struct, open_file, sort_keys=True, check_circular=True,
                  indent=4)
if args.verbose > 1:
    print("[final]")
    pprint(outputs)
