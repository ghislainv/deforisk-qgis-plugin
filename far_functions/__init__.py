"""Importing far functions."""

import matplotlib

from .far_get_variables import FarGetVariablesTask
from .far_sample_obs import FarSampleObsTask
from .far_calibrate import FarCalibrateTask
from .far_interpolate_rho import FarInterpolateRhoTask
from .far_predict import FarPredictTask

# Use agg backend for QGis plugin
matplotlib.use("agg")

# End of file
