# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Risk map with moving window approach.
"""

import os

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import matplotlib.pyplot as plt
import numpy as np
import riskmapjnr as rmj
import forestatrisk as far

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class RmjCalibrateTask(QgsTask):
    """Risk map with moving window approach for calibration period."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_moving_window")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 5

    def __init__(self, description, iface, defor_thresh, max_dist,
                 win_size, workdir, years):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.defor_thresh = defor_thresh
        self.max_dist = max_dist
        self.win_size = win_size
        self.workdir = workdir
        self.years = years
        self.exception = None

    def get_time_interval(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_interval = years[1] - years[0]
        return time_interval

    def plot_prob(self, prob_file, png_file):
        """Plot probability of deforestation."""
        border_file = opj("data", "ctry_PROJ.shp")
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
        """Risk map with moving window approach for calibration
        period.
        """

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

            # Create output directory for rmj
            rmj.make_dir(self.OUT)

            # Distance to forest edge threshold
            fcc_file = opj(self.DATA, "forest", "fcc123.tif")
            dist_edge_thresh = rmj.dist_edge_threshold(
                fcc_file=fcc_file,
                defor_values=1,
                defor_threshold=self.defor_thresh,
                dist_file=opj(self.DATA, "dist_edge.tif"),
                dist_bins=np.arange(0, self.max_dist, step=30),
                tab_file_dist=opj(self.OUT, "tab_dist.csv"),
                fig_file_dist=opj(self.OUT, "perc_dist.png"),
                blk_rows=128,
                dist_file_available=True,
                check_fcc=False,
                verbose=True)
            dist_thresh = dist_edge_thresh["dist_thresh"]

            # Print result
            print(dist_edge_thresh)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute time interval from years
            time_interval = self.get_time_interval()

            # Compute local deforestation rate
            rmj.local_defor_rate(
                fcc_file=fcc_file,
                defor_values=1,
                ldefrate_file=opj(self.OUT, "ldefrate.tif"),
                win_size=self.win_size,
                time_interval=time_interval,
                rescale_min_val=2,
                rescale_max_val=65535,
                blk_rows=128,
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Derive riskmap at t1
            rmj.set_defor_cat_zero(
                ldefrate_file=opj(self.OUT, "ldefrate.tif"),
                dist_file=opj(self.DATA, "dist_edge.tif"),
                dist_thresh=dist_thresh,
                ldefrate_with_zero_file=opj(
                    self.OUT,
                    f"prob_mv_{self.win_size}_t1.tif"),
                blk_rows=128,
                verbose=False)

            # Compute deforestation rate per category
            rmj.defrate_per_cat(
                fcc_file=opj("data", "forest", "fcc123.tif"),
                riskmap_file=opj(self.OUT, f"prob_mv_{self.win_size}_t1.tif"),
                time_interval=time_interval,
                period="calibration",
                tab_file_defrate=opj(
                    self.OUT,
                    f"defrate_cat_mv_{self.win_size}_t1.csv"),
                verbose=False)

            # Validation
            far.validation_udef_arp(
                fcc_file=opj("data", "forest", "fcc123.tif"),
                period="calibration",
                time_interval=time_interval,
                riskmap_file=opj(
                    self.OUT,
                    f"prob_mv_{self.win_size}_t1.tif"),
                tab_file_defor=opj(
                    self.OUT,
                    f"defrate_cat_mv_{self.win_size}_t1.csv"),
                csize_coarse_grid=50,
                indices_file_pred=opj(
                    self.OUT,
                    f"indices_mv_{self.win_size}_t1.csv"),
                tab_file_pred=opj(
                    self.OUT,
                    f"pred_obs_mv_{self.win_size}_t1.csv"),
                fig_file_pred=opj(
                    self.OUT,
                    f"pred_obs_mv_{self.win_size}_t1.png"),
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Derive riskmap at t2
            rmj.get_ldefz_v(
                ldefrate_file=opj(self.OUT, "ldefrate.tif"),
                dist_v_file=opj(self.DATA, "validation", "dist_edge_t2.tif"),
                dist_thresh=dist_thresh,
                ldefrate_with_zero_v_file=opj(
                    self.OUT,
                    f"prob_mv_{self.win_size}_t2.tif"),
                verbose=False)

            # Compute deforestation rate per category
            rmj.defrate_per_cat(
                fcc_file=opj("data", "forest", "fcc123.tif"),
                riskmap_file=opj(self.OUT, f"prob_mv_{self.win_size}_t2.tif"),
                time_interval=time_interval,
                period="validation",
                tab_file_defrate=opj(
                    self.OUT,
                    f"defrate_cat_mv_{self.win_size}_t2.csv"),
                verbose=False)

            # Validation
            far.validation_udef_arp(
                fcc_file=opj("data", "forest", "fcc123.tif"),
                period="validation",
                time_interval=time_interval,
                riskmap_file=opj(
                    self.OUT,
                    f"prob_mv_{self.win_size}_t2.tif"),
                tab_file_defor=opj(
                    self.OUT,
                    f"defrate_cat_mv_{self.win_size}_t2.csv"),
                csize_coarse_grid=50,
                indices_file_pred=opj(
                    self.OUT,
                    f"indices_mv_{self.win_size}_t2.csv"),
                tab_file_pred=opj(
                    self.OUT,
                    f"pred_obs_mv_{self.win_size}_t2.csv"),
                fig_file_pred=opj(
                    self.OUT,
                    f"pred_obs_mv_{self.win_size}_t2.png"),
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

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
            prob_file = opj(self.OUT, f"prob_mv_{self.win_size}_t1.tif")
            png_file = opj(self.OUT, f"prob_mv_{self.win_size}_t1.png")
            self.plot_prob(prob_file, png_file)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Moving window" in group_names:
                mv_group = root.findGroup("Moving window")
            else:
                mv_group = root.addGroup("Moving window")

            # Add border layer to QGis project
            border_file = opj("data", "ctry_PROJ.shp")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            for d in ["t1", "t2"]:
                prob_file = opj(self.OUT, f"prob_mv_{self.win_size}_{d}.tif")
                prob_layer = QgsRasterLayer(prob_file,
                                            f"prob_mv_{self.win_size}_{d}")
                prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                              "prob_mv.qml"))
                add_layer_to_group(far_project, mv_group,
                                   prob_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('RmjCalibrateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'RmjCalibrateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'RmjCalibrateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
