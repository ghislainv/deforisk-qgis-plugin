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

# import matplotlib.pyplot as plt
# import pandas as pd
import numpy as np
import riskmapjnr as rmj

# Local import
# from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class RmjCalibrateTask(QgsTask):
    """Risk map with moving window approach for calibration period."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_moving_window")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 1

    def __init__(self, description, iface, defor_thresh, max_dist,
                 workdir, years):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.defor_thresh = defor_thresh
        self.max_dist = max_dist
        self.workdir = workdir
        self.years = years
        self.exception = None

    def get_time_interval(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_interval = years[1] - years[0]
        return time_interval

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

            # Compute time interval from years
            # time_interval = self.get_time_interval()

            # Distance to forest edge threshold
            dist_edge_thres = rmj.dist_edge_threshold(
                fcc_file=opj(self.DATA, "fcc.tif"),
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

            # Print result
            print(dist_edge_thres)

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
