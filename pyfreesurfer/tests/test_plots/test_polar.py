##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from collections import namedtuple
import unittest
import sys
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
    from mock import patch
else:
    import unittest.mock as mock
    from unittest.mock import patch

# Pyfreesurfer import
from pyfreesurfer.plots.polar import polar_plot


class FreeSurferPolarPlot(unittest.TestCase):
    """ Test the polar plot:
    'pyfreesurfer.plots.polar.polar_plot'
    """
    def setUp(self):
        """ Define function parameters.
        """
        individual_stats = {
            "volume": {
                "3rd-Ventricle": {
                    "m": 1337.5999999999999,
                    "s": 0.0,
                    "values": [1337.6]},
                "4th-Ventricle": {
                    "m": 1742.0999999999999,
                    "s": 0.0,
                    "values": [1742.1]},
            }
        }
        cohort_stats = {
            "volume": {
                "3rd-Ventricle": {
                    "m": 1645.2444444444445,
                    "s": 574.40348403290159,
                    "values": [1416.4, 692.0, 1982.3, 1835.0, 1701.5,
                               977.4, 2238.3, 2626.7, 1337.6]},
                "4th-Ventricle": {
                    "m": 1734.7777777777778,
                    "s": 329.21985824328465,
                    "values": [2303.9, 1297.8, 1114.0, 1690.6, 1856.3,
                               1897.8, 1893.2, 1817.3, 1742.1]},
            }
        }
        self.kwargs = {
            "individual_stats": individual_stats,
            "cohort_stats": cohort_stats,
            "snapfile": "/my/path/mock_snap",
            "name": "ASEG"
        }

    @mock.patch("pyfreesurfer.plots.polar.plt.savefig")
    def test_normal_execution(self, mock_save):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        polar_plot(**self.kwargs)
        self.assertEqual([
            mock.call(self.kwargs["snapfile"])],
            mock_save.call_args_list)


if __name__ == "__main__":
    unittest.main()
