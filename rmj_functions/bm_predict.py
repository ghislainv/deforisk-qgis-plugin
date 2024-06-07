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
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 4

    def __init__(self, description, workdir, years,
                 period):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.workdir = workdir
        self.years = years
        self.period = period
        self.exception = None

    def get_time_interval(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        if self.period == "calibration":
            time_interval = years[1] - years[0]
        else:
            time_interval = years[2] - years[1]
        return time_interval

    def get_dist_file(self):
        """Get distance to forest edge file."""
        if self.period == "calibration":
            dist_file = opj(self.DATA, "dist_edge.tif")
        else:
            dist_file = opj(self.DATA, "validation",
                            "dist_edge_t2.tif")
        return dist_file

    def get_dist_bins(self, dist_bins_file):
        """Get distance bins."""
        with open(dist_bins_file, "r", encoding="utf-8") as f:
            dist_bins = [float(line.rstrip()) for line in f]
        return dist_bins

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj(self.OUT, f"prob_{model}_{date}.tif")
        png_file = opj(self.OUT, f"prob_{model}_{date}.png")
        border_file = opj(self.DATA, "ctry_PROJ.gpkg")
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

            # Date
            date = "t1" if self.period == "calibration" else "t2"

            # Compute vulnerability classes
            rmj.benchmark.vulnerability_map(
                forest_file=opj(self.DATA, "forest", f"forest_{date}.tif"),
                dist_file=self.get_dist_file(),
                dist_bins=self.get_dist_bins(
                    opj(self.OUT, "dist_bins.csv")),
                subj_file=opj(self.OUT, "subj.tif"),
                output_file=opj(self.OUT, f"prob_bm_{date}.tif"),
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

            # Rate on calibration period
            if self.period == "calibration":
                rate_calibration = None
            else:
                rate_calibration = opj(self.OUT, "defrate_cat_bm_t1.csv")

            # Compute deforestation rate per vulnerability class
            rmj.benchmark.defrate_per_class(
                fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                vulnerability_file=opj(
                    self.OUT,
                    f"prob_bm_{date}.tif"),
                time_interval=time_interval,
                period=self.period,
                rate_calibration=rate_calibration,
                tab_file_defrate=opj(
                    self.OUT,
                    f"defrate_cat_bm_{date}.csv"),
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
            date = "t1" if self.period == "calibration" else "t2"
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
            border_file = opj(self.DATA, "ctry_PROJ.gpkg")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            prob_file = opj(self.OUT, f"prob_bm_{date}.tif")
            prob_layer = QgsRasterLayer(prob_file,
                                        f"prob_bm_{date}")
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
