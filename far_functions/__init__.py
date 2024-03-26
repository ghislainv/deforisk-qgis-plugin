"""Importing far functions."""

import matplotlib

from .far_get_variables import far_get_variables
from .far_sample_obs import far_sample_obs
from .far_models import far_models
from .far_predict import FarPredictTask
from .far_validate import FarValidateTask

# Use agg backend for QGis plugin
matplotlib.use("agg")
