"""
Check arguments.
"""

import os
import shutil

from qgis.core import (
    Qgis, QgsTask,
    QgsMessageLog
)

import forestatrisk as far

# Alias
opj = os.path.join
opb = os.path.basename


def check_fcc_source(fcc_source):
    """Check fcc source."""
    cond1 = fcc_source not in ["tmf", "gfc"]
    cond2 = not os.path.isfile(fcc_source)
    if cond1 and cond2:
        msg = ("Forest data source should be "
               "either a raster file, 'tmf', "
               "or 'gfc'")
        raise ValueError(msg)


def check_aoi(aoi):
    """Check aoi."""
    cond_string = [isinstance(aoi, str),
                   len(aoi) == 3]
    cond_file = os.path.isfile(aoi)
    if not (all(cond_string) or cond_file):
        msg = ("Area of interest should be "
               "either a path to a vector file "
               "or a country iso code of three "
               "letters (e.g. MTQ)")
        raise ValueError(msg)


class FarCheckArgsTask(QgsTask):
    """Check arguments."""

    # Constants
    DATA_RAW = "data_raw"
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 2

    def __init__(self, description, iface, args):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.args = args
        self.exception = None
        self.get_fcc_args = args["get_fcc_args"]

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Check arguments."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Check fcc_source
            fcc_source = self.get_fcc_args["fcc_source"]
            check_fcc_source(fcc_source)
            # If file, check file properties
            if os.path.isfile(fcc_source):
                proj = self.args["proj"]
                far.check_fcc(fcc_source, proj=proj, nbands_min=3,
                              blk_rows=128, verbose=False)
                # If no error, copy file to data_raw directory
                workdir = self.args["workdir"]
                ofile = opj(workdir, self.DATA_RAW, "forest_src.tif")
                if not os.path.isfile(ofile):
                    far.make_dir(opj(workdir, self.DATA_RAW))
                    shutil.copy(fcc_source, ofile)

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Check aoi
            aoi = self.get_fcc_args["aoi"]
            check_aoi(aoi)

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
                msg = ('FarCheckArgsTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarCheckArgsTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarCheckArgsTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
