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

import pandas as pd
import forestatrisk as far

# Alias
opj = os.path.join


class FarValidateTask(QgsTask):
    """Validating the deforestation risk maps."""

    # Constants
    OUT = "outputs"
    DATA = "data"
    MESSAGE_CATEGORY = "FarValidateTask"
    DATES = ["t1", "t2"]
    N_DATES = len(DATES)
    PERIODS = ["calibration", "validation"]
    MODELS = ["icar", "glm", "rf"]

    def __init__(self, description, iface, workdir, years, run_models):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.run_models = run_models
        self.n_models = run_models.count(True)
        self.indices_list = []
        self.exception = None

    def get_time_intervals(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_intervals = [years[1] - years[0], years[2] - years[1]]
        return time_intervals

    def set_progress_validate(self, progress):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / (self.N_DATES * self.n_models)
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Model validation."""

        try:
            # Set working directory
            os.chdir(self.workdir)

            # Compute time intervals from years
            time_intervals = self.get_time_intervals()

            # Progress
            progress = 0
            self.set_progress_validate(progress)

            # Loop on periods and models
            for (d, period, ti) in zip(self.DATES, self.PERIODS,
                                       time_intervals):
                for (m, run_model) in zip(self.MODELS, self.run_models):
                    # Check isCanceled() to handle cancellation
                    if self.isCanceled():
                        return False
                    # Check model
                    if run_model:
                        # Validation
                        far.validation_udef_arp(
                            fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                            period=period,
                            time_interval=ti,
                            riskmap_file=opj(self.OUT, f"prob_{m}_{d}.tif"),
                            tab_file_defor=opj(self.OUT,
                                               f"defrate_cat_{m}_{d}.csv"),
                            csize_coarse_grid=50,
                            indices_file_pred=opj(self.OUT,
                                                  f"indices_{m}_{d}.csv"),
                            tab_file_pred=opj(self.OUT,
                                              f"pred_obs_{m}_{d}.csv"),
                            fig_file_pred=opj(self.OUT,
                                              f"pred_obs_{m}_{d}.png"),
                            verbose=False)
                        # Indices
                        df = pd.read_csv(opj(self.OUT,
                                             f"indices_{m}_{d}.csv"))
                        df["model"] = m
                        df["period"] = period
                        self.indices_list.append(df)
                        # Progress
                        progress += 1
                        self.set_progress_validate(progress)

        except Exception as exc:
            self.exception = exc
            return False

        return True

    def finished(self, result):
        """Show messages and add layers."""

        if result:

            # Concat indices
            indices = pd.concat(self.indices_list, axis=0)
            indices.sort_values(by=["period", "model"])
            indices = indices[["model", "period", "MedAE", "R2", "wRMSE",
                               "ncell", "csize_coarse_grid",
                               "csize_coarse_grid_ha"]]
            indices.to_csv(
                opj(self.OUT, "indices_all.csv"),
                sep=",", header=True,
                index=False, index_label=False)

            # Message
            msg = f"Validation results can be found in {self.workdir}"
            self.iface.messageBar().pushMessage(
                "Success", msg,
                level=Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarValidateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarValidateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarValidateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
