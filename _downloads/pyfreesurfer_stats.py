"""
Pyfreesurfer Stats
==================

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
                     names=["aparcstats2table", "asegstats2table"])
except:
    pass

# Pyfreesurfer import
from pyfreesurfer import __version__ as version
from pyfreesurfer.utils.stattools import aparcstats2table
from pyfreesurfer.utils.stattools import asegstats2table
from pyfreesurfer.wrapper import FSWrapper
from pyfreesurfer import DEFAULT_FREESURFER_PATH


# Parameters to keep trace
__hopla__ = ["runtime", "inputs", "outputs"]


# Script documentation
DOC = """
Freesurfer statistics
~~~~~~~~~~~~~~~~~~~~~

Generate text/ascii tables of FreeSurfer parcellation stats data
'aseg.stats' and '?h.aparc.stats'. This can then be easily imported into a
spreadsheet and/or stats program.

The statistics are generated in a 'stats' sub folder of the FreeSurfer
processing home directory.

Command:

python $HOME/git/pyfreesurfer/pyfreesurfer/scripts/pyfreesurfer_stats \
    -v 2 \
    -c /i2bm/local/freesurfer/SetUpFreeSurfer.sh \
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
        prog="python pyfreesurfer_stats",
        description=textwrap.dedent(DOC),
        formatter_class=RawTextHelpFormatter)

    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-d", "--fsdir",
        required=True, metavar="PATH", type=is_directory,
        help="the FreeSurfer processing home directory.")
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
        help="if activated, clean the 'stats' folder.")
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
tool = "pyfreesurfer_stats"
timestamp = datetime.now().isoformat()
tool_version = version
freesurfer_config = args.fsconfig
freesurfer_version = FSWrapper([], freesurfer_config).version
params = locals()
runtime = dict([(name, params[name])
               for name in ("freesurfer_config", "tool", "tool_version",
                            "freesurfer_version", "timestamp")])
if args.verbose > 0:
    print("[info] Start FreeSurfer cat stats...")
    print("[info] Directory: {0}.".format(args.fsdir))
fsdir = args.fsdir
outdir = args.outdir
statsdir = os.path.join(outdir, "stats")
params = locals()
inputs = dict([(name, params[name])
              for name in ("fsdir", "outdir", "statsdir")])
outputs = None
if os.path.isdir(statsdir) and args.erase:
    shutil.rmtree(statsdir)
if not os.path.isdir(statsdir):
    os.makedirs(statsdir)


#############################################################################
# Summarize all the subjects' statistics

statfiles = aparcstats2table(fsdir, outdir, fsconfig=freesurfer_config)
statfiles.extend(asegstats2table(fsdir, outdir, fsconfig=freesurfer_config))
if args.verbose > 1:
    print("[result] Stats: {0}.".format(statfiles))


#############################################################################
# Update the outputs and save them and the inputs in a 'logs' directory.

logdir = os.path.join(statsdir, "logs")
if not os.path.isdir(logdir):
    os.mkdir(logdir)
params = locals()
outputs = dict([(name, params[name]) for name in ("statfiles", )])
for name, final_struct in [("inputs", inputs), ("outputs", outputs),
                           ("runtime", runtime)]:
    log_file = os.path.join(logdir, "{0}.json".format(name))
    with open(log_file, "wt") as open_file:
        json.dump(final_struct, open_file, sort_keys=True, check_circular=True,
                  indent=4)
if args.verbose > 1:
    print("[final]")
    pprint(outputs)
