"""Importing far functions."""

import matplotlib

from .far_get_variables import FarGetVariablesTask
from .far_sample_obs import FarSampleObsTask
from .far_models import FarModelsTask
from .far_predict import FarPredictTask
from .far_validate import FarValidateTask, combine_model_results
from .far_empty_task import FarEmptyTask

# Use agg backend for QGis plugin
matplotlib.use("agg")
