##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
This module can be used to render the produced FreeSurfer data.
"""

# System import
import matplotlib


# Make sure that we don't get DISPLAY problems when running without X
matplotlib.use("Agg")
