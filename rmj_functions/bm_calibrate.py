"""
Get vulnerability map with the benchmark model.
"""

import os
import math

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import riskmapjnr as rmj

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class BmCalibrateTask(QgsTask):
    """Get vulnerability map with the benchmark model."""

    # Constants
    DATA = "data"
    OUT = opj("outputs", "rmj_benchmark")
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 5

    def __init__(self, description, workdir, years,
                 defor_thresh, max_dist):
        """Initialize the class."""
        super().__init__(description, QgsTask.CanCancel)
        self.workdir = workdir
        self.years = years
        self.defor_thresh = defor_thresh
        self.max_dist = max_dist
        self.exception = None

    def get_dist_thresh(self):
        """Get distance to forest edge threshold."""
        ifile = opj(self.OUT, "dist_edge_threshold.csv")
        dist_thresh_data = pd.read_csv(ifile)
        dist_thresh = dist_thresh_data.loc[0, "dist_thresh"]
        return dist_thresh

    def get_time_interval_calibration(self):
        """Get time intervals from years."""
        years = self.years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        time_interval_calibration = years[1] - years[0]
        return time_interval_calibration

    def plot_prob(self, model, date):
        """Plot probability of deforestation."""
        prob_file = opj(self.OUT, f"prob_{model}_{date}.tif")
        png_file = opj(self.OUT, f"prob_{model}_{date}.png")
        border_file = opj(self.DATA, "ctry_PROJ.gpkg")
        fig_prob = rmj.benchmark.plot.vulnerability_map(
            input_map=prob_file,
            maxpixels=1e8,
            output_file=png_file,
            borders=border_file,
            linewidth=0.3,
            figsize=(6, 5), dpi=500)
        plt.close(fig_prob)

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Get vulnerability map with the benchmark model."""

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

            # Compute bins
            dist_bins = rmj.benchmark.compute_dist_bins(
                dist_file=opj(self.DATA, "dist_edge.tif"),
                dist_thresh=self.get_dist_thresh(),
            )
            dist_bins_str = [str(i) for i in dist_bins]

            # Save dist_bins
            ofile = opj(self.OUT, "dist_bins.csv")
            with open(ofile, "w", encoding="utf-8") as f:
                f.write("\n".join(dist_bins_str))

            # Compute vulnerability classes at t1
            rmj.benchmark.vulnerability_map(
                forest_file=opj(self.DATA, "forest", "forest_t1.tif"),
                dist_file=opj(self.DATA, "dist_edge.tif"),
                dist_bins=dist_bins,
                subj_file=opj(self.OUT, "subj.tif"),
                output_file=opj(self.OUT, "prob_bm_t1.tif"),
                blk_rows=128,
                verbose=False)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # Compute time interval from years
            time_interval_calibration = self.get_time_interval_calibration()

            # Compute deforestation rate per vulnerability class
            rmj.benchmark.defrate_per_class(
                fcc_file=opj(self.DATA, "forest", "fcc123.tif"),
                vulnerability_file=opj(
                    self.OUT,
                    "prob_bm_t1.tif"),
                time_interval=time_interval_calibration,
                period="calibration",
                tab_file_defrate=opj(
                    self.OUT,
                    "defrate_cat_bm_t1.csv"),
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
            # Plot
            date = "t1"
            model = "bm"
            self.plot_prob(model=model, date=date)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Benchmark" in group_names:
                mw_group = root.findGroup("Benchmark")
            else:
                mw_group = root.addGroup("Benchmark")

            # Add border layer to QGis project
            border_file = opj(self.DATA, "ctry_PROJ.gpkg")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add prob layers to QGis project
            prob_file = opj(self.OUT, f"prob_bm_{date}.tif")
            prob_layer = QgsRasterLayer(prob_file,
                                        f"prob_bm_{date}")
            prob_layer.loadNamedStyle(opj("qgis_layer_style",
                                          "prob_bm.qml"))
            add_layer_to_group(far_project, mw_group,
                               prob_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

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
