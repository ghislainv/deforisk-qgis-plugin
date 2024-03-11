# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Predicting the deforestation risk.
"""

import os
import pickle
from shutil import copy2

from qgis.core import Qgis

import numpy as np
import matplotlib.pyplot as plt
from patsy import dmatrices
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import forestatrisk as far


# icar_model class for predictions
class icar_model():
    """Small mod_icar class."""

    def __init__(
            self,
            formula,
            _y_design_info,
            _x_design_info,
            betas,
            rho
    ):
        self.formula = formula
        self._y_design_info = _y_design_info
        self._x_design_info = _x_design_info
        self.betas = betas
        self.rho = rho

    def __repr__(self):
        """Summary of model_binomial_iCAR model."""
        summary = (
            "Binomial logistic regression with iCAR process\n"
            "  Model: %s ~ %s\n"
            % (self._y_design_info.describe(), self._x_design_info.describe())
        )
        return summary

# far_predict_risk
def far_predict_risk(iface,
                     workdir,
                     csize,
                     csize_interpolate=1,
                     icar_model=True,
                     glm_model=False,
                     rf_model=False):
    """Predicting the deforestation risk."""

    # -------------------------------------
    # Update dist_edge and dist_defor at t3
    # -------------------------------------

    # Set working directory
    os.chdir(workdir)

    # Rename and copy files
    os.rename(os.path.join("data", "dist_edge.tif"),
              os.path.join("data", "dist_edge.tif.bak"))
    os.rename(os.path.join("data", "dist_defor.tif"),
              os.path.join("data", "dist_defor.tif.bak"))
    copy2(os.path.join("data", "forecast", "dist_edge_forecast.tif"),
          os.path.join("data", "dist_edge.tif"))
    copy2(os.path.join("data", "forecast", "dist_defor_forecast.tif"),
          os.path.join("data", "dist_defor.tif"))

    # ------------------------------------
    # Get base formula
    # ------------------------------------

    # Get iCAR model and formula
    ifile = os.path.join("outputs", "mod_icar.pickle")
    with open(ifile, "rb") as file:
        mod_icar_pickle = pickle.load(file)
    formula_icar = mod_icar_pickle["formula"]

    # Get model info from patsy
    dataset_file = os.path.join(workdir, "outputs", "sample.txt")
    dataset = pd.read_csv(dataset_file)
    dataset = dataset.dropna(axis=0)
    dataset["trial"] = 1
    y, x = dmatrices(formula_icar, dataset, 0, "drop")

    # ------------------------------------
    # iCAR model
    # ------------------------------------

    if icar_model:

        # Create icar_model object for predictions
        mod_icar = icar_model(
            formula=formula_icar,
            _y_design_info=y.design_info,
            _x_design_info=x.design_info,
            betas=mod_icar_pickle["betas"],
            rho=mod_icar_pickle["rho"]
        )

        # Interpolate the spatial random effects
        rho = mod_icar_pickle["rho"]
        far.interpolate_rho(
            rho=rho,
            input_raster=os.path.join("data", "fcc23.tif"),
            output_file=os.path.join("outputs", "rho.tif"),
            csize_orig=csize,
            csize_new=csize_interpolate
        )

        # Compute predictions
        far.predict_raster_binomial_iCAR(
            mod_icar,
            var_dir="data",
            input_cell_raster=os.path.join("outputs", "rho.tif"),
            input_forest_raster=os.path.join(
                "data",
                "forest",
                "forest_t3.tif"),
            output_file=os.path.join("outputs", "prob_icar.tif"),
            blk_rows=10  # Reduced number of lines to avoid memory problems
        )

    # ------------------------------------
    # GLM model
    # ------------------------------------

    if glm_model:
        # Get glm model
        ifile = os.path.join("outputs", "mod_glm.pickle")
        with open(ifile, "rb") as file:
            mod_glm = pickle.load(file)
        # Compute predictions
        far.predict_raster(
            model=mod_glm,
            _x_design_info=x.design_info,
            var_dir="data",
            input_forest_raster=os.path.join(
                "data",
                "forest",
                "forest_t3.tif"
            ),
            output_file=os.path.join("outputs", "prob_glm.tif"),
            blk_rows=10  # Reduced number of lines to avoid memory problems
        )

    # ------------------------------------
    # RF model
    # ------------------------------------

    if rf_model:
        # Get rf model
        ifile = os.path.join("outputs", "mod_rf.joblib")
        with open(ifile, "rb") as file:
            mod_rf = joblib.load(file)
        # Compute predictions
        far.predict_raster(
            model=mod_rf,
            _x_design_info=x.design_info,
            var_dir="data",
            input_forest_raster=os.path.join(
                "data",
                "forest",
                "forest_t3.tif"
            ),
            output_file=os.path.join("outputs", "prob_rf.tif"),
            blk_rows=10  # Reduced number of lines to avoid memory problems
        )

    # -----------------
    # Reinitialize data
    # -----------------

    os.remove("data/dist_edge.tif")
    os.remove("data/dist_defor.tif")
    os.rename("data/dist_edge.tif.bak", "data/dist_edge.tif")
    os.rename("data/dist_defor.tif.bak", "data/dist_defor.tif")

# End of file
