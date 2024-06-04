"""Importing rmj functions."""

import matplotlib

from .mw_calibrate import MwCalibrateTask
from .mw_predict import MwPredictTask

# Use agg backend for QGis plugin
matplotlib.use("agg")

# End of file
