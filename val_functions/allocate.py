"""Allocate deforestation to projects."""

import os

from qgis.core import (
    Qgis, QgsTask, QgsMessageLog
)

import forestatrisk as far

# Alias
opj = os.path.join


class AllocateTask(QgsTask):
    """Allocate deforestation to project."""

    # Constants
    OUT = "outputs"
    DATA = "data"
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 1

    def __init__(self, description, iface, workdir, riskmap_juris,
                 defor_rate_tab, project_borders, defor_juris, years_forecast):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.riskmap_juris = riskmap_juris
        self.defor_rate_tab = defor_rate_tab
        self.project_borders = project_borders
        self.defor_juris = defor_juris
        self.years_forecast = years_forecast
        self.exception = None
        self.out_dir = opj(self.OUT, "allocating_deforestation")

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Allocating deforestation to project."""

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

            # Create output directory
            far.make_dir(self.out_dir)

            # Validation
            far.allocate_deforestation(
                riskmap_juris_file=self.riskmap_juris,
                defor_rate_tab=self.defor_rate_tab,
                defor_juris_ha=self.defor_juris,
                years_forecast=self.years_forecast,
                project_borders=self.project_borders,
                output_file=opj(self.out_dir, "defor_project.csv"),
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
                msg = ('AllocateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'AllocateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'AllocateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
