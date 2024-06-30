# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Deriving risk maps with the moving window approach.
"""

import os

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import matplotlib.pyplot as plt
import riskmapjnr as rmj

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class BmPredictTask(QgsTask):
    """Deriving risk maps with the moving window approach."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_benchmark")
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 4

    def __init__(self, description, workdir, years,
                 period):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.workdir = workdir
        self.years = years
        self.period = period
        self.datadir = f"data_{self.period}"
        self.moddir = self.get_moddir()
        self.outdir = opj(self.OUT, self.period)
        self.exception = None

    def get_moddir(self):
        """Get model directory."""
        moddir = None
        if self.period in ["calibration", "validation"]:
            moddir = opj(self.OUT, "calibration")
        elif self.period in ["historical", "forecast"]:
            moddir = opj(self.OUT, "historical")
        return moddir

    def get_time_interval(self):
        """Get time intervals from years and period."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_interval = None
        if self.period == "calibration":
            time_interval = years[1] - years[0]
        elif self.period == "validation":
            time_interval = years[2] - years[1]
        elif self.period in ["historical", "forecast"]:
            time_interval = years[2] - years[0]
        return time_interval

    def get_date(self):
        """Get date from period."""
        date = None
        if self.period in ["calibration", "historical"]:
            date = "t1"
        elif self.period == "validation":
            date = "t2"
        elif self.period == "forecast":
            date = "t3"
        return date

    def get_dist_file(self):
        """Get distance to forest edge file."""
        dist_file = opj(self.datadir, "dist_edge.tif")
        return dist_file

    def get_dist_bins(self, dist_bins_file):
        """Get distance bins."""
        with open(dist_bins_file, "r", encoding="utf-8") as f:
            dist_bins = [float(line.rstrip()) for line in f]
        return dist_bins

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj(self.outdir, f"prob_{model}_{date}.tif")
        png_file = opj(self.outdir, f"prob_{model}_{date}.png")
        border_file = opj(self.DATA, "aoi_proj.gpkg")
        fig_prob = rmj.benchmark.plot.vulnerability_map(
            input_map=prob_file,
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

            # Create directory
            rmj.make_dir(self.outdir)

            # Date
            date = self.get_date()

            # Compute vulnerability classes
            rmj.benchmark.vulnerability_map(
                forest_file=opj(self.DATA,
                                f"forest_{date}.tif"),
                dist_file=self.get_dist_file(),
                dist_bins=self.get_dist_bins(
                    opj(self.moddir, "dist_bins.csv")),
                subj_file=opj(self.moddir, "subj.tif"),
                output_file=opj(self.outdir,
                                f"prob_bm_{date}.tif"),
                blk_rows=128,
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute time interval from years
            time_interval = self.get_time_interval()

            # Deforestation rate on model's period
            deforate_model = None
            if self.period == "validation":
                deforate_model = opj(
                    self.OUT, "calibration",
                    "defrate_cat_bm_calibration.csv")
            elif self.period == "forecast":
                deforate_model = opj(
                    self.OUT, "historical",
                    "defrate_cat_bm_historical.csv")

            # Compute deforestation rate per vulnerability class
            rmj.benchmark.defrate_per_class(
                fcc_file=opj(self.DATA, "fcc123.tif"),
                vulnerability_file=opj(
                    self.outdir,
                    f"prob_bm_{date}.tif"),
                time_interval=time_interval,
                period=self.period,
                deforate_model=deforate_model,
                tab_file_defrate=opj(
                    self.outdir,
                    f"defrate_cat_bm_{self.period}.csv"),
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
            model = "bm"
            self.plot_prob(model=model, date=date)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Benchmark" in group_names:
                mw_group = root.findGroup("Benchmark")
            else:
                mw_group = root.addGroup("Benchmark")

            # Add border layer to QGis project
            border_file = opj(self.DATA, "aoi_proj.gpkg|layername=aoi")
            border_layer = QgsVectorLayer(border_file, "aoi border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            prob_file = opj(self.outdir, f"prob_bm_{date}.tif")
            prob_layer = QgsRasterLayer(
                prob_file,
                f"prob_bm_{date}_{self.period}")
            prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                          "prob_bm.qml"))
            add_layer_to_group(far_project, mw_group,
                               prob_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('BmPredictTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'BmPredictTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'BmPredictTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
