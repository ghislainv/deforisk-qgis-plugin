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

from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer

import matplotlib.pyplot as plt
from patsy import dmatrices
import pandas as pd
import joblib
import forestatrisk as far

# Local import
from ..utilities import add_layer


# icar_model class for predictions
class icarModel():
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
                     csize=10,
                     csize_interpolate=1,
                     model_icar=True,
                     model_glm=False,
                     model_rf=False):
    """Predicting the deforestation risk."""

    # Set working directory
    os.chdir(workdir)

    # # -------------------------------------
    # # Update dist_edge and dist_defor at t3
    # # -------------------------------------

    # # Rename and copy files
    # vfiles = ["edge", "defor"]
    # for v in vfiles:
    #     ifile = os.path.join("data", f"dist_{v}.tif.bak")
    #     if not os.path.isfile(ifile):
    #         os.rename(os.path.join("data", f"dist_{v}.tif"),
    #                   ifile)
    #         copy2(os.path.join("data", "forecast", f"dist_{v}_forecast.tif"),
    #               os.path.join("data", f"dist_{v}.tif"))

    # ------------------------------------
    # Get base formula
    # ------------------------------------

    # Get iCAR model and formula
    ifile = os.path.join("outputs", "mod_icar.pickle")
    if not os.path.isfile(ifile):
        msg = ("No iCAR model "
               "in the working directory. "
               "Run upper box \"iCAR "
               "model\" first.")
        iface.messageBar().pushMessage(
            "Error", msg,
            level=Qgis.Critical)

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

    if model_icar:

        # Create icar_model object for predictions
        mod_icar = icarModel(
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
            input_raster=os.path.join("data", "fcc.tif"),
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
                "forest_t1.tif"),
            output_file=os.path.join("outputs", "prob_icar.tif"),
            blk_rows=10)

        # Compute deforestation rate per category
        far.defrate_per_cat(
            fcc_file=os.path.join("data", "forest", "fcc123.tif"),
            defor_values=1,
            riskmap_file=os.path.join("outputs", "prob_icar.tif"),
            time_interval=10,
            tab_file_defrate=os.path.join(
                "outputs",
                "defrate_cat_icar.csv"),
            blk_rows=128,
            verbose=False)

    # ------------------------------------
    # GLM model
    # ------------------------------------

    if model_glm:
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
            blk_rows=10)

    # ------------------------------------
    # RF model
    # ------------------------------------

    if model_rf:
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
            blk_rows=10)

    # # -----------------
    # # Reinitialize data
    # # -----------------

    # vfiles = ["edge", "defor"]
    # for v in vfiles:
    #     ifile = os.path.join("data", f"dist_{v}.tif.bak")
    #     if os.path.isfile(ifile):
    #         os.remove(os.path.join("data", f"dist_{v}.tif"))
    #         os.rename(ifile, os.path.join("data", f"dist_{v}.tif"))

    # -------------------
    # Message and rasters
    # -------------------

    # Message
    msg = f"Prediction raster files can be found in {workdir}"
    iface.messageBar().pushMessage(
        "Success", msg,
        level=Qgis.Success)

    # Plot
    mod = ["icar", "glm", "rf"]
    cond = [model_icar, model_glm, model_rf]
    for (i, m) in enumerate(mod):
        if cond[i]:
            prob_file = os.path.join("outputs", f"prob_{m}.tif")
            png_file = os.path.join("outputs", f"prob_{m}.png")
            border_file = os.path.join("data", "ctry_PROJ.shp")
            fig_prob = far.plot.prob(
                input_prob_raster=prob_file,
                maxpixels=1e8,
                output_file=png_file,
                borders=border_file,
                linewidth=0.3,
                figsize=(6, 5), dpi=500)
            plt.close(fig_prob)

    # Qgis project
    far_project = QgsProject.instance()

    # Add border layer to QGis project
    border_file = os.path.join("data", "ctry_PROJ.shp")
    border_layer = QgsVectorLayer(border_file, "border", "ogr")
    border_layer.loadNamedStyle(os.path.join("qgis_layer_style", "border.qml"))
    add_layer(far_project, border_layer)

    # Add prob layers to QGis project
    for (i, m) in enumerate(mod):
        if cond[i]:
            prob_file = os.path.join("outputs", f"prob_{m}.tif")
            prob_layer = QgsRasterLayer(prob_file, f"prob_{m}")
            prob_layer.loadNamedStyle(os.path.join("qgis_layer_style",
                                                   "prob.qml"))
            add_layer(far_project, prob_layer)

# End of file
