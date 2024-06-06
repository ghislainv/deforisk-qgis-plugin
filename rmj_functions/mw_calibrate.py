# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Estimating the local deforestation risk with the moving window approach.
"""

import os

from qgis.core import (
    Qgis, QgsTask,
    QgsMessageLog
)

import numpy as np
import pandas as pd
import riskmapjnr as rmj

# Alias
opj = os.path.join


class MwCalibrateTask(QgsTask):
    """Estimating the local deforestation risk with the moving window
    approach."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_moving_window")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 2

    def __init__(self, description, workdir, years,
                 defor_thresh, max_dist, win_size):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.workdir = workdir
        self.years = years
        self.defor_thresh = defor_thresh
        self.max_dist = max_dist
        self.win_size = win_size
        self.exception = None

    def get_time_interval_calibration(self):
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

            # Output directory
            rmj.make_dir(self.OUT)

            # Distance to forest edge threshold
            fcc_file = opj(self.DATA, "forest", "fcc123.tif")
            ofile = opj(self.OUT, "dist_edge_threshold.csv")
            if not os.path.isfile(ofile):
                dist_thresh = rmj.dist_edge_threshold(
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

                # Save result
                dist_edge_data = pd.DataFrame(dist_thresh, index=[0])
                dist_edge_data.to_csv(
                    ofile,
                    sep=",", header=True,
                    index=False, index_label=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute time interval from years
            time_interval = self.get_time_interval_calibration()

            # Model
            model = f"mw_{self.win_size}"

            # Compute local deforestation rate
            rmj.local_defor_rate(
                fcc_file=fcc_file,
                defor_values=1,
                ldefrate_file=opj(self.OUT, f"ldefrate_{model}.tif"),
                win_size=self.win_size,
                time_interval=time_interval,
                rescale_min_val=2,
                rescale_max_val=65535,
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
            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('MwCalibrateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'MwCalibrateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'MwCalibrateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
