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
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class FarPredictTask(QgsTask):
    """Predicting the deforestation risk."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "far_models")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 3

    def __init__(self, description, iface, workdir, years, model,
                 period):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.model = model
        self.period = period
        self.datadir = f"data_{self.period}"
        self.outdir = self.get_outdir()
        self.exception = None

    def get_outdir(self):
        """Get output directory."""
        if self.period in ["calibration", "validation"]:
            outdir = opj(self.OUT, "calibration")
        elif self.period in ["historical", "forecast"]:
            outdir = opj(self.OUT, "historical")
        return outdir

    def get_time_interval(self):
        """Get time intervals from years and period."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        if self.period == "calibration":
            time_interval = years[1] - years[0]
        elif self.period == "validation":
            time_interval = years[2] - years[1]
        elif self.period in ["historical", "forecast"]:
            time_interval = years[2] - years[0]
        return time_interval

    def get_date(self):
        """Get date from period."""
        if self.period in ["calibration", "historical"]:
            date = "t1"
        elif self.period == "validation":
            date = "t2"
        elif self.period == "forecast":
            date = "t3"
        return date

    def get_icar_model(self, pickle_file):
        """Get icar model."""
        try:
            file = open(pickle_file, "rb")
        except FileNotFoundError:
            msg = ("No iCAR model "
                   "in the working directory. "
                   "Run upper box \"iCAR "
                   "model\" first.")
            self.exception = msg
            return False
        with file:
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

    def get_model(self, mod_icar_pickle,
                  y_design_info, x_design_info):
        """Get model."""
        if self.model == "icar":
            # Create icar_model object for predictions
            mod = far.icarModelPred(
                formula=mod_icar_pickle["formula"],
                _y_design_info=y_design_info,
                _x_design_info=x_design_info,
                betas=mod_icar_pickle["betas"],
                rho=mod_icar_pickle["rho"])
        if self.model == "glm":
            ifile = opj(self.outdir, "mod_glm.pickle")
            with open(ifile, "rb") as file:
                mod = pickle.load(file)
        if self.model == "rf":
            ifile = opj(self.outdir, "mod_rf.joblib")
            with open(ifile, "rb") as file:
                mod = joblib.load(file)
        return mod

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj(self.outdir, f"prob_{model}_{date}.tif")
        png_file = opj(self.outdir, f"prob_{model}_{date}.png")
        border_file = opj(self.DATA, "ctry_PROJ.gpkg")
        fig_prob = far.plot.prob(
            input_prob_raster=prob_file,
            maxpixels=1e8,
            output_file=png_file,
            borders=border_file,
            linewidth=0.3,
            figsize=(6, 5), dpi=500)
        plt.close(fig_prob)

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Compute predictions."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Set working directory
            os.chdir(self.workdir)

            # Compute time interval from years
            time_interval = self.get_time_interval()

            # Get design info
            mod_icar_pickle = self.get_icar_model(
                pickle_file=opj(self.outdir, "mod_icar.pickle"))
            if not mod_icar_pickle:
                return False
            (y_design_info, x_design_info) = self.get_design_info(
                mod_icar_pickle, dataset_file=opj(self.outdir, "sample.txt"))

            # Get model
            mod = self.get_model(mod_icar_pickle, y_design_info,
                                 x_design_info)

            # Date
            date = self.get_date()

            # Compute predictions
            if self.model == "icar":
                far.predict_raster_binomial_iCAR(
                    model=mod,
                    var_dir=self.datadir,
                    input_cell_raster=opj(self.outdir, "rho.tif"),
                    input_forest_raster=opj(
                        self.DATA,
                        f"forest_{date}.tif"),
                    output_file=opj(
                        self.outdir,
                        f"prob_icar_{date}.tif"),
                    blk_rows=10,
                    verbose=False)
            elif self.model in ["glm", "rf"]:
                far.predict_raster(
                    model=mod,
                    _x_design_info=x_design_info,
                    var_dir=self.datadir,
                    input_forest_raster=opj(
                        self.DATA,
                        f"forest_{date}.tif"),
                    output_file=opj(
                        self.outdir,
                        f"prob_{self.model}_{date}.tif"),
                    blk_rows=10,
                    verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute deforestation rate per category
            far.defrate_per_cat(
                fcc_file=opj(self.DATA, "fcc123.tif"),
                riskmap_file=opj(
                    self.outdir,
                    f"prob_{self.model}_{date}.tif"),
                time_interval=time_interval,
                period=self.period,
                tab_file_defrate=opj(
                    self.outdir,
                    f"defrate_cat_{self.model}_{self.period}.csv"),
                blk_rows=128,
                verbose=False)

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

        except Exception as exc:
            self.exception = exc
            return False

        return True

    def finished(self, result):
        """Show messages and add layers."""

        if result:
            # Plot
            date = self.get_date()
            self.plot_prob(model=self.model, date=date)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "FAR models" in group_names:
                predict_group = root.findGroup("FAR models")
            else:
                predict_group = root.addGroup("FAR models")

            # Add border layer to QGis project
            border_file = opj(self.DATA, "ctry_PROJ.gpkg")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            prob_file = opj(self.outdir, f"prob_{self.model}_{date}.tif")
            prob_layer = QgsRasterLayer(
                prob_file,
                f"prob_{self.model}_{date}_{self.period}",
            )
            prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                          "prob.qml"))
            add_layer_to_group(far_project, predict_group,
                               prob_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarPredictTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarPredictTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarPredictTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
