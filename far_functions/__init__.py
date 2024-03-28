"""Importing far functions."""

import matplotlib

from .far_get_variables import FarGetVariablesTask
from .far_sample_obs import far_sample_obs
from .far_models import far_models
from .far_predict import FarPredictTask
from .far_validate import FarValidateTask, combine_model_results

# Use agg backend for QGis plugin
matplotlib.use("agg")
