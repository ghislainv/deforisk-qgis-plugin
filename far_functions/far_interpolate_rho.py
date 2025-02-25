# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Interpolate rhos.
"""

import os
import pickle

from qgis.core import (
    Qgis, QgsTask, QgsMessageLog
)

import forestatrisk as far

# Alias
opj = os.path.join


class FarInterpolateRhoTask(QgsTask):
    """Interpolate rhos."""

    # Constants
    OUT = opj("outputs", "far_models")
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 1

    def __init__(self, description, iface, workdir, period,
                 csize_interpolate):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.period = period
        self.csize_interpolate = float(csize_interpolate)
        self.datadir = f"data_{self.period}"
        self.outdir = opj(self.OUT, self.period)
        self.exception = None

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

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Interpolate rhos."""

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

            # Get icar model
            mod_icar_pickle = self.get_icar_model(
                pickle_file=opj(self.outdir, "mod_icar.pickle"))
            if not mod_icar_pickle:
                return False

            # Interpolate the spatial random effects
            csize_file = opj(self.outdir, "csize_icar.txt")
            with open(csize_file, "r", encoding="utf-8") as f:
                csize_icar = f.read()
                csize_icar = float(csize_icar)
            ofile = opj(self.outdir, "rho.tif")
            if not os.path.isfile(ofile):
                rho = mod_icar_pickle["rho"]
                far.interpolate_rho(
                    rho=rho,
                    input_raster=opj(self.datadir, "fcc.tif"),
                    output_file=ofile,
                    csize_orig=csize_icar,
                    csize_new=self.csize_interpolate)

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
            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarInterpolateRhoTask "{name}" not successful '
                       'but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarInterpolateRhoTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarInterpolateRhoTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
