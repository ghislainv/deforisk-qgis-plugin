# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Model validation.
"""

import os

from qgis.core import (
    Qgis, QgsTask, QgsMessageLog
)

import forestatrisk as far

# Alias
opj = os.path.join


class ValidateTask(QgsTask):
    """Validating deforestation risk map."""

    # Constants
    OUT = opj("outputs", "validation")
    DATA = "data"
    MESSAGE_CATEGORY = "FAR plugin"
    FAR_MODELS = ["icar", "glm", "rf"]
    N_STEPS = 1

    def __init__(self, description, iface, workdir, years, csize_val,
                 period, model):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.csize_val = csize_val
        self.period = period
        self.model = model
        self.exception = None
        if self.model in self.FAR_MODELS:
            self.resdir = opj("outputs", "far_models")
        else:
            self.resdir = opj("outputs", "rmj_moving_window")

    def get_time_interval(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        if self.period == "calibration":
            time_interval = years[1] - years[0]
        else:
            time_interval = years[2] - years[1]
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
        """Model validation."""

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
            far.make_dir(self.OUT)

            # Compute time intervals from years
            time_interval = self.get_time_interval()

            # Date
            date = "t1" if self.period == "calibration" else "t2"

            # Validation
            far.validation_udef_arp(
                fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                period=self.period,
                time_interval=time_interval,
                riskmap_file=opj(
                    self.resdir,
                    f"prob_{self.model}_{date}.tif"),
                tab_file_defor=opj(
                    self.resdir,
                    f"defrate_cat_{self.model}_{date}.csv"),
                csize_coarse_grid=self.csize_val,
                indices_file_pred=opj(
                    self.OUT,
                    f"indices_{self.model}_{date}_{self.csize_val}.csv"),
                tab_file_pred=opj(
                    self.OUT,
                    f"pred_obs_{self.model}_{date}_{self.csize_val}.csv"),
                fig_file_pred=opj(
                    self.OUT,
                    f"pred_obs_{self.model}_{date}_{self.csize_val}.png"),
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
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('ValidateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'ValidateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'ValidateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
