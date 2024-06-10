# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Sample observations.
"""

import os

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsMessageLog
)

import matplotlib.pyplot as plt
import pandas as pd
from patsy.highlevel import dmatrices
import forestatrisk as far

# Local import
from ..utilities import add_layer_to_group

# Alias
opj = os.path.join


class FarSampleObsTask(QgsTask):
    """Sample observations."""

    # Constants
    OUT = opj("outputs", "far_models")
    DATA = "data"
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 2

    def __init__(self, description, iface, workdir, period, proj,
                 nsamp, adapt, seed, csize):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.period = period
        self.proj = proj
        self.nsamp = nsamp
        self.adapt = adapt
        self.seed = seed
        self.csize = csize
        self.dataset = pd.DataFrame()
        self.datadir = f"data_{self.period}"
        self.outdir = opj(self.OUT, self.period)
        self.exception = None

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Sample observations."""

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
            far.make_dir(self.outdir)

            # Check for files
            fcc_file = opj(self.datadir, "fcc.tif")
            if not os.path.isfile(fcc_file):
                msg = ("No forest cover change "
                       "raster in the working directory. "
                       "Run upper box to \"Download and "
                       "compute variables\" first.")
                self.exception = msg
                return False

            # Sample observations
            dataset = far.sample(
                nsamp=self.nsamp, adapt=self.adapt,
                seed=self.seed, csize=self.csize,
                var_dir=self.datadir,
                input_forest_raster="fcc.tif",
                output_file=opj(self.outdir, "sample.txt"),
                blk_rows=0,
                verbose=True)

            # Remove NA from data-set (otherwise scale() and
            # model_binomial_iCAR don't work)
            dataset = dataset.dropna(axis=0)
            # Set number of trials to one for far.model_binomial_iCAR()
            dataset["trial"] = 1
            self.dataset = dataset
            # Print the first five rows
            print("\n"
                  "Dataset of observations (5 first lines):")
            print(self.dataset.head(5))

            # Sample size
            ndefor = sum(self.dataset.fcc == 0)
            nfor = sum(self.dataset.fcc == 1)
            ifile = opj(self.outdir, "sample_size.csv")
            with open(ifile, "w",
                      encoding="utf-8") as file:
                file.write("Var, n\n")
                file.write(f"ndefor, {ndefor}\n")
                file.write(f"nfor, {nfor}\n")
            print("\n"
                  f"Sample size: ndefor = {ndefor}, nfor = {nfor}")

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
            # Correlation formula
            formula_corr = (
                "fcc ~ dist_road + dist_town + dist_river + "
                "dist_edge + altitude + slope - 1"
            )

            # Data
            y, data = dmatrices(formula_corr, data=self.dataset,
                                return_type="dataframe")
            # Plots
            ofile = opj(self.outdir, "correlation.pdf")
            figs = far.plot.correlation(
                y=y, data=data,
                plots_per_page=3,
                figsize=(7, 8),
                dpi=80,
                output_file=ofile)
            for i in figs:
                plt.close(i)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Variables" in group_names:
                var_group = root.findGroup("Variables")
            else:
                var_group = root.addGroup("Variables")

            # Add layer of sampled observations to QGis project
            samp_file = opj(self.workdir, self.outdir,
                            "sample.txt")
            encoding = "UTF-8"
            delimiter = ","
            decimal = "."
            x = "X"
            y = "Y"
            uri = (f"file:///{samp_file}?encoding={encoding}"
                   f"&delimiter={delimiter}&decimalPoint={decimal}"
                   f"&crs={self.proj}&xField={x}&yField={y}")
            samp_layer = QgsVectorLayer(uri, "sampled_obs", "delimitedtext")
            samp_layer.loadNamedStyle(opj("qgis_layer_style",
                                          "sample.qml"))
            add_layer_to_group(far_project, var_group, samp_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarSampleObsTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarSampleObsTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarSampleObsTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
