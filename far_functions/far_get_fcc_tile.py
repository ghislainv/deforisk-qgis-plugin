"""Get forest cover change tile."""

import os

from qgis.core import (
    Qgis, QgsTask,
    QgsMessageLog
)

from geefcc.geeic2geotiff import geeic2geotiff


# Alias
opj = os.path.join
opb = os.path.basename


class FarGetFccTileTask(QgsTask):
    """Get forest cover change tile."""

    # Constants
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 1

    def __init__(self, description, index, ext, grid_args):
        super().__init__(description, QgsTask.CanCancel)
        self.index = index
        self.ext = ext
        self.ntiles = grid_args["ntiles"]
        self.forest = grid_args["forest"]
        self.proj = grid_args["proj"]
        self.scale = grid_args["scale"]
        self.out_dir_tiles = grid_args["out_dir_tiles"]
        self.exception = None
        self.verbose = False

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Get forest cover change."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Download tile
            geeic2geotiff(
                self.index, self.ext, self.ntiles,
                self.forest, self.proj, self.scale,
                self.out_dir_tiles, self.verbose
            )

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
                msg = ('FarGetFccTileTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarGetFccTileTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarGetFccTileTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
