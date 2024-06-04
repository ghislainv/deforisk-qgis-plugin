"""
Estimating the deforestation risk with the benchmark model.
"""

import os

from qgis.core import (
    Qgis, QgsTask,
    QgsMessageLog
)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import riskmapjnr as rmj

# Alias
opj = os.path.join


class BmCalibrateTask(QgsTask):
    """Estimating the deforestation risk with the benchmark model."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_benchmark")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 2

    def __init__(self, description, iface, workdir, years,
                 defor_thresh, max_dist):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.years = years
        self.defor_thresh = defor_thresh
        self.max_dist = max_dist
        self.exception = None

    def get_time_interval(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_interval = years[1] - years[0]
        return time_interval

    def plot_prob(self, prob_file, png_file):
        """Plot probability of deforestation."""
        border_file = opj("data", "ctry_PROJ.shp")
        fig_prob = rmj.plot.riskmap(
            input_risk_map=prob_file,
            maxpixels=1e8,
            output_file=png_file,
            borders=border_file,
            linewidth=0.3,
            figsize=(6, 5), dpi=500)
        plt.close(fig_prob)

    def get_dist_thresh(self):
        """Get distance to forest edge threshold."""
        ifile = opj(self.OUT, "dist_edge_threshold.csv")
        dist_thresh_data = pd.read_csv(ifile)
        dist_thresh = dist_thresh_data.loc[0, "dist_thresh"]
        return dist_thresh

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Estimating the deforestation risk with the benchmark model."""

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

            # Distance to forest edge threshold
            fcc_file = opj(self.DATA, "forest", "fcc123.tif")
            dist_edge_thresh = rmj.dist_edge_threshold(
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
            dist_edge_data = pd.DataFrame(dist_edge_thresh, index=[0])
            dist_edge_data.to_csv(
                opj(self.OUT, "dist_edge_threshold.csv"),
                sep=",", header=True,
                index=False, index_label=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Rasterize subjurisdictions
            rmj.benchmark.rasterize_subjurisdictions(
                input_file=opj(self.DATA, "ctry_PROJ.gpkg"),
                fcc_file=opj(self.DATA, "fcc.tif"),
                output_file=opj(self.OUT, "subj.tif"),
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Distance threshold
            dist_thresh = self.get_dist_thresh()

            # Compute vulnerability classes
            dist_bins = rmj.benchmark.vulnerability_classes(
                dist_file=opj(self.DATA, "dist_edge.tif"),
                dist_thresh=dist_thresh,
                subj_file=opj(self.OUT, "subj.tif"),
                output_file=opj(self.OUT, "vulnerability_classes.tif"),
                blk_rows=128,
                verbose=False)

            # Save dist_bins
            ofile = opj(self.OUT, "dist_bins.csv")
            with open(ofile, "w", encoding="utf-8") as f:
                f.write(dist_bins)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute time interval from years
            time_interval = self.get_time_interval()

            # Compute deforestation rate per vulnerability class
            rmj.benchmark.defrate_per_class(
                fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                vulnerability_file=opj(self.OUT, "vulnerability_classes.tif"),
                time_interval=time_interval[0],
                period="calibration",
                tab_file_defrate=opj(self.OUT, "defrate_per_class.csv"),
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
                msg = ('BmCalibrateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'BmCalibrateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'BmCalibrateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
