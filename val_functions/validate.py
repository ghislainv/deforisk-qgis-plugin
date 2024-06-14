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
    OUT = "outputs"
    DATA = "data"
    MESSAGE_CATEGORY = "FAR plugin"
    FAR_MODELS = ["icar", "glm", "rf"]
    N_STEPS = 1

    def __init__(self, description, iface, workdir, years, csize_val,
                 model, period):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.csize_val = csize_val
        self.model = model
        self.period = period
        self.exception = None
        if self.model in self.FAR_MODELS:
            self.resdir = opj(
                self.OUT, "far_models", self.period
            )
        elif self.model == "bm":
            self.resdir = opj(
                self.OUT, "rmj_benchmark", self.period
            )
        else:
            self.resdir = opj(
                self.OUT, "rmj_moving_window", self.period
            )
        self.out_fig = opj(self.OUT, "model_validation",
                           self.period, "figures")
        self.out_tab = opj(self.OUT, "model_validation",
                           self.period, "tables")

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

            # Compute time intervals from years
            time_interval = self.get_time_interval()

            # Date
            date = self.get_date()

            # Validation
            far.validation_udef_arp(
                fcc_file=opj(self.DATA, "fcc123.tif"),
                period=self.period,
                time_interval=time_interval,
                riskmap_file=opj(
                    self.resdir,
                    f"prob_{self.model}_{date}.tif"),
                tab_file_defor=opj(
                    self.resdir,
                    f"defrate_cat_{self.model}_{self.period}.csv"),
                csize_coarse_grid=self.csize_val,
                indices_file_pred=opj(
                    self.out_tab,
                    f"indices_{self.model}_{self.period}_{self.csize_val}.csv"
                ),
                tab_file_pred=opj(
                    self.out_tab,
                    f"pred_obs_{self.model}_{self.period}_{self.csize_val}.csv"
                ),
                fig_file_pred=opj(
                    self.out_fig,
                    f"pred_obs_{self.model}_{self.period}_{self.csize_val}.png"
                ),
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
