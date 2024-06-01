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
import pandas as pd
import riskmapjnr as rmj

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class RmjPredictTask(QgsTask):
    """Deriving risk maps with the moving window approach."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_moving_window")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 4

    def __init__(self, description, iface, workdir, years,
                 win_size, period):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.win_size = win_size
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

    def get_dist_thresh(self):
        """Get distance to forest edge threshold."""
        ifile = opj(self.OUT, "dist_edge_threshold.csv")
        dist_thresh_data = pd.read_csv(ifile)
        dist_thresh = dist_thresh_data.loc[0, "dist_thresh"]
        return dist_thresh

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj(self.OUT, f"prob_{model}_{date}.tif")
        png_file = opj(self.OUT, f"prob_{model}_{date}.png")
        border_file = opj(self.DATA, "ctry_PROJ.gpkg")
        fig_prob = rmj.plot.riskmap(
            input_risk_map=prob_file,
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

            # Date
            date = "t1" if self.period == "calibration" else "t2"

            # Model
            model = f"mw_{self.win_size}"

            # Distance threshold
            dist_thresh = self.get_dist_thresh()

            # Compute predictions
            rmj.set_defor_cat_zero(
                ldefrate_file=opj(self.OUT, f"ldefrate_{model}.tif"),
                dist_file=self.get_dist_file(),
                dist_thresh=dist_thresh,
                ldefrate_with_zero_file=opj(
                    self.OUT,
                    f"prob_{model}_{date}.tif"),
                blk_rows=128,
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute deforestation rate per category
            rmj.defrate_per_cat(
                fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                riskmap_file=opj(self.OUT,
                                 f"prob_{model}_{date}.tif"),
                time_interval=time_interval,
                period=self.period,
                tab_file_defrate=opj(
                    self.OUT,
                    f"defrate_cat_{model}_{date}.csv"),
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
            model = f"mw_{self.win_size}"
            self.plot_prob(model=model, date=date)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Moving window" in group_names:
                mw_group = root.findGroup("Moving window")
            else:
                mw_group = root.addGroup("Moving window")

            # Add border layer to QGis project
            border_file = opj(self.DATA, "ctry_PROJ.gpkg")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            prob_file = opj(self.OUT, f"prob_{model}_{date}.tif")
            prob_layer = QgsRasterLayer(prob_file,
                                        f"prob_{model}_{date}")
            prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                          "prob_mw.qml"))
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
                msg = ('RmjPredictTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'RmjPredictTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'RmjPredictTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
