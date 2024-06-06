"""Importing rmj functions."""

import matplotlib

from .bm_calibrate import BmCalibrateTask
from .bm_predict import BmPredictTask
from .mw_calibrate import MwCalibrateTask
from .mw_predict import MwPredictTask

# Use agg backend for QGis plugin
matplotlib.use("agg")

# End of file
