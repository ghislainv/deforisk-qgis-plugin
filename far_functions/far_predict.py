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

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import matplotlib.pyplot as plt
from patsy.highlevel import dmatrices
import pandas as pd
import joblib
import forestatrisk as far

# Local import
from ..utilities import add_layer

# Alias
opj = os.path.join

MESSAGE_CATEGORY = 'FarPredictTask'


class FarPredictTask(QgsTask):
    """Predicting the deforestation risk."""

    def __init__(self, description, iface, workdir, years,
                 csize, csize_interpolate, run_models):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.csize = csize
        self.csize_interpolate = csize_interpolate
        self.run_models = run_models
        self.exception = None

    def get_time_interval(self, years):
        """Get time intervals from years."""
        years = years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_intervals = [years[1] - years[0], years[2] - years[1]]
        return time_intervals

    def get_icar_model(self, iface, pickle_file):
        """Get icar model."""
        if not os.path.isfile(pickle_file):
            msg = ("No iCAR model "
                   "in the working directory. "
                   "Run upper box \"iCAR "
                   "model\" first.")
            iface.messageBar().pushMessage(
                "Error", msg,
                level=Qgis.Critical)
        with open(pickle_file, "rb") as file:
            mod_icar_pickle = pickle.load(file)
        return mod_icar_pickle

    def get_design_info(self, mod_icar_pickle, dataset_file):
        """Get design info from patsy."""
        formula_icar = mod_icar_pickle["formula"]
        dataset = pd.read_csv(dataset_file)
        dataset = dataset.dropna(axis=0)
        dataset["trial"] = 1
        y, x = dmatrices(formula_icar, dataset, 0, "drop")
        y_design_info = y.design_info
        x_design_info = x.design_info
        return (y_design_info, x_design_info)

    def get_models(self, run_models,
                   mod_icar_pickle, csize, csize_interpolate,
                   y_design_info, x_design_info):
        """Get models."""
        mod = {}
        if run_models[0]:
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
                formula=mod_icar_pickle["formula"],
                _y_design_info=y_design_info,
                _x_design_info=x_design_info,
                betas=mod_icar_pickle["betas"],
                rho=mod_icar_pickle["rho"])
        if run_models[1]:
            ifile = opj("outputs", "mod_glm.pickle")
            with open(ifile, "rb") as file:
                mod["glm"] = pickle.load(file)
        if run_models[2]:
            ifile = opj("outputs", "mod_rf.joblib")
            with open(ifile, "rb") as file:
                mod["rf"] = joblib.load(file)
        return mod

    def clean_data_repository(self, vfiles):
        """Clean the data repository."""
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

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj("outputs", f"prob_{model}_{date}.tif")
        png_file = opj("outputs", f"prob_{model}_{date}.png")
        border_file = opj("data", "ctry_PROJ.shp")
        fig_prob = far.plot.prob(
            input_prob_raster=prob_file,
            maxpixels=1e8,
            output_file=png_file,
            borders=border_file,
            linewidth=0.3,
            figsize=(6, 5), dpi=500)
        plt.close(fig_prob)

    def run(self):
        """Compute predictions."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, Qgis.Info)

            # Set working directory
            os.chdir(self.workdir)

            # Compute time intervals from years
            time_intervals = self.get_time_interval(self.years)

            # Get design info
            mod_icar_pickle = self.get_icar_model(
                self.iface, pickle_file=opj("outputs", "mod_icar.pickle"))
            (y_design_info, x_design_info) = self.get_design_info(
                mod_icar_pickle, dataset_file=opj("outputs", "sample.txt"))

            # Get models
            mod = self.get_models(
                self.run_models,
                mod_icar_pickle, self.csize, self.csize_interpolate,
                y_design_info, x_design_info)

            # Clean the data repository (if necessary)
            self.clean_data_repository(vfiles=["edge"])

            # Indices for loops
            dates = ["t1", "t2"]
            periods = ["calibration", "validation"]
            models = ["icar", "glm", "rf"]
            n_dates = len(dates)
            n_models = self.run_models.count(True)
            progress = 0
            self.setProgress(1)

            # Loop on periods
            for (d, period, ti) in zip(dates, periods, time_intervals):

                # Update dist files for t2
                if d == "t2":
                    self.update_dist_files(vfiles=["edge"])

                # Loop on models
                for (m, run_model) in zip(models, self.run_models):

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
                                output_file=opj("outputs",
                                                f"prob_icar_{d}.tif"),
                                blk_rows=10)
                        elif m in ["glm", "rf"]:
                            far.predict_raster(
                                model=mod[m],
                                _x_design_info=x_design_info,
                                var_dir="data",
                                input_forest_raster=opj(
                                    "data",
                                    "forest",
                                    f"forest_{d}.tif"),
                                output_file=opj("outputs",
                                                f"prob_{m}_{d}.tif"),
                                blk_rows=10)

                        # Check isCanceled() to handle cancellation
                        if self.isCanceled():
                            return False

                        # Progress
                        progress += 1
                        set_progress = progress / (n_dates * n_models * 2)
                        set_progress = int(set_progress * 100)
                        self.setProgress(set_progress)

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

                        # Check isCanceled() to handle cancellation
                        if self.isCanceled():
                            return False

                        # Plot probability of deforestation
                        self.plot_prob(model=m, date=d)

                        # Progress
                        progress += 1
                        set_progress = progress / (n_dates * n_models * 2)
                        set_progress = int(set_progress * 100)
                        self.setProgress(set_progress)

                # Clean the data repository
                self.clean_data_repository(vfiles=["edge"])

        except Exception as exc:
            self.exception = exc
            return False

        return True

    def finished(self, result):
        """Show messages and add layers."""

        if result:
            # Message
            msg = f"Prediction raster files can be found in {self.workdir}"
            self.iface.messageBar().pushMessage(
                "Success", msg,
                level=Qgis.Success)

            # Qgis project
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            predict_group = root.addGroup("Predictions")

            # Add border layer to QGis project
            border_file = opj("data", "ctry_PROJ.shp")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            dates = ["t1", "t2"]
            models = ["icar", "glm", "rf"]
            for (i, m) in enumerate(models):
                if self.run_models[i]:
                    for d in dates:
                        prob_file = opj("outputs", f"prob_{m}_{d}.tif")
                        prob_layer = QgsRasterLayer(prob_file, f"prob_{m}_{d}")
                        prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                                      "prob.qml"))
                        far_project.addMapLayer(prob_layer, False)
                        predict_group.addLayer(prob_layer)
        else:
            if self.exception is None:
                msg = ('FarPredictTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarPredictTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarPredictTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
