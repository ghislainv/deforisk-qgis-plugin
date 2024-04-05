"""Importing rmj functions."""

import matplotlib

from .rmj_calibrate import RmjCalibrateTask
from .rmj_predict import RmjPredictTask

# Use agg backend for QGis plugin
matplotlib.use("agg")

# End of file
