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

from qgis.core import Qgis, QgsTask, QgsProject, QgsVectorLayer, QgsRasterLayer

import matplotlib.pyplot as plt
from patsy.highlevel import dmatrices
import pandas as pd
import joblib
import forestatrisk as far

# Local import
from ..utilities import add_layer

# Alias
opj = os.path.join


class FarPredict(QgsTask):
    """Predicting the deforestation risk."""

    def __init__(self, description):
        super().__init__(description, QgsTask.CanCancel)
        self.exception = None

    def get_base_formula(self, iface, workdir):
        """Get base formula."""
        ifile = opj("outputs", "mod_icar.pickle")
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
        return (mod_icar_pickle, formula_icar)

    def get_model_info(self, workdir, mod_icar_pickle, formula_icar):
        """Get model info from patsy."""
        dataset_file = opj(workdir, "outputs", "sample.txt")
        dataset = pd.read_csv(dataset_file)
        dataset = dataset.dropna(axis=0)
        dataset["trial"] = 1
        y, x = dmatrices(formula_icar, dataset, 0, "drop")
        return (dataset, y, x)

    def get_models(self, model_icar, model_glm, model_rf,
                   mod_icar_pickle, csize, csize_interpolate,
                   formula_icar, y, x):
        """Get models."""
        mod = {}
        rho = None
        if model_icar:
            # Interpolate the spatial random effects
            rho = mod_icar_pickle["rho"]
            far.interpolate_rho(
                rho=rho,
                input_raster=opj("data", "fcc.tif"),
                output_file=opj("outputs", "rho.tif"),
                csize_orig=csize,
                csize_new=csize_interpolate)
            # Create icar_model object for predictions
            mod["icar"] = far.icarModelPred(
                formula=formula_icar,
                _y_design_info=y.design_info,
                _x_design_info=x.design_info,
                betas=mod_icar_pickle["betas"],
                rho=mod_icar_pickle["rho"])
        if model_glm:
            ifile = opj("outputs", "mod_glm.pickle")
            with open(ifile, "rb") as file:
                mod["glm"] = pickle.load(file)
        if model_rf:
            ifile = opj("outputs", "mod_rf.joblib")
            with open(ifile, "rb") as file:
                mod["rf"] = joblib.load(file)
        return (mod, rho)

    def clean_data_repository(self):
        """Clean the data repostiory."""
        vfiles = ["edge"]  # ["edge", "defor"]
        for v in vfiles:
            ifile = opj("data", f"dist_{v}.tif.bak")
            if os.path.isfile(ifile):
                os.remove(opj("data", f"dist_{v}.tif"))
                os.rename(ifile, opj("data", f"dist_{v}.tif"))

    def reinitialize_data_repository(self, vfiles):
        """Reinitialize the data repository."""
        for v in vfiles:
            ifile = opj("data", f"dist_{v}.tif.bak")
            if os.path.isfile(ifile):
                os.remove(opj("data", f"dist_{v}.tif"))
                os.rename(ifile, opj("data", f"dist_{v}.tif"))

    def update_dist_files(self, vfiles):
        """Update distance files."""
        for v in vfiles:
            ifile = opj("data", f"dist_{v}.tif.bak")
            if not os.path.isfile(ifile):
                os.rename(opj("data", f"dist_{v}.tif"), ifile)
                copy2(opj("data", "validation", f"dist_{v}_t2.tif"),
                      opj("data", f"dist_{v}.tif"))

    def run(self,
            iface,
            workdir,
            years,
            csize=10,
            csize_interpolate=1,
            model_icar=True,
            model_glm=False,
            model_rf=False):
        """Compute predictions."""

        # Set working directory
        os.chdir(workdir)

        # Compute time intervals from years
        years = years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_intervals = [years[1] - years[0], years[2] - years[1]]

        # Get base formula
        (mod_icar_pickle, formula_icar) = self.get_base_formula(iface, workdir)

        # Get model info
        (dataset, y, x) = self.get_model_info(
            workdir, mod_icar_pickle, formula_icar)

        # Get models
        (mod, rho) = self.get_models(
            model_icar, model_glm, model_rf,
            mod_icar_pickle, csize, csize_interpolate,
            formula_icar, y, x)

        # Clean the data repository (if necessary)
        self.clean_data_repository(vfiles=["edge"])

        # Indices for loops
        dates = ["t1", "t2"]
        periods = ["calibration", "validation"]
        models = ["icar", "glm", "rf"]
        run_models = [model_icar, model_glm, model_rf]

        # Loop on periods
        for (d, period, ti) in zip(dates, periods, time_intervals):

            # Update dist files for t2
            if d == "t2":
                self.update_dist_files(vfiles=["edge"])

            # Loop on models
            for (m, run_model) in zip(models, run_models):

                # Check isCanceled() to handle cancellation
                if self.isCanceled():
                    return False

                # Check model
                if run_model:
                    # Compute predictions
                    if m == "icar":
                        far.predict_raster_binomial_iCAR(
                            mod["icar"],
                            var_dir="data",
                            input_cell_raster=opj("outputs", "rho.tif"),
                            input_forest_raster=opj(
                                "data",
                                "forest",
                                f"forest_{d}.tif"),
                            output_file=opj("outputs", f"prob_icar_{d}.tif"),
                            blk_rows=10)
                    elif m in ["glm", "rf"]:
                        far.predict_raster(
                            model=mod[m],
                            _x_design_info=x.design_info,
                            var_dir="data",
                            input_forest_raster=opj(
                                "data",
                                "forest",
                                f"forest_{d}.tif"),
                            output_file=opj("outputs", f"prob_{m}_{d}.tif"),
                            blk_rows=10)

                    # Check isCanceled() to handle cancellation
                    if self.isCanceled():
                        return False

                    # Compute deforestation rate per category
                    far.defrate_per_cat(
                        fcc_file=opj("data", "forest", "fcc123.tif"),
                        riskmap_file=opj("outputs", f"prob_{m}_{d}.tif"),
                        time_interval=ti,
                        period=period,
                        tab_file_defrate=opj(
                            "outputs",
                            f"defrate_cat_{m}_{d}.csv"),
                        verbose=False)

            # Clean the data repository
            self.clean_data_repository(vfiles=["edge"])

        return True

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
            for d in dates:
                # Plot
                prob_file = opj("outputs", f"prob_{m}_{d}.tif")
                png_file = opj("outputs", f"prob_{m}_{d}.png")
                border_file = opj("data", "ctry_PROJ.shp")
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
    border_file = opj("data", "ctry_PROJ.shp")
    border_layer = QgsVectorLayer(border_file, "border", "ogr")
    border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
    add_layer(far_project, border_layer)

    # Add prob layers to QGis project
    for (i, m) in enumerate(mod):
        if cond[i]:
            for d in dates:
                prob_file = opj("outputs", f"prob_{m}_{d}.tif")
                prob_layer = QgsRasterLayer(prob_file, f"prob_{m}_{d}")
                prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                              "prob.qml"))
                add_layer(far_project, prob_layer)

# End of file
