# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Get forestatrisk variables.
"""

import os
import shutil
from glob import glob

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import ee
import matplotlib.pyplot as plt
import forestatrisk as far

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class FarGetVariablesTask(QgsTask):
    """Get variables for modelling and forecasting deforestation."""

    # Constants
    OUT = opj("outputs", "far_models")
    DATA = "data"
    DATA_RAW = "data_raw"
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 3

    def __init__(self, description, iface, workdir, get_fcc_args,
                 isocode, proj):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.get_fcc_args = get_fcc_args
        self.isocode = isocode
        self.proj = proj
        self.exception = None

    def create_symbolic_links(self):
        """Create symbolic links for predictions."""
        var_tif = self.DATA + "/*.tif"
        raster_list = glob(var_tif)
        dates = ["t2", "t3"]
        periods = ["validation", "forecast"]
        for (date, period) in zip(dates, periods):
            far.make_dir(f"data_{date}")
            for r in raster_list:
                src_file = os.path.abspath(r)
                r_basename = os.path.basename(r)
                dst_file = opj(f"data_{date}", r_basename)
                if os.path.isfile(dst_file):
                    os.remove(dst_file)
                os.symlink(src_file, dst_file)
            for v in ["edge", "defor"]:
                src_file = opj(self.DATA, period, f"dist_{v}_{date}.tif")
                src_file = os.path.abspath(src_file)
                dst_file = opj(f"data_{date}", f"dist_{v}.tif")
                if os.path.isfile(dst_file):
                    os.remove(dst_file)
                os.symlink(src_file, dst_file)

    def reformat_get_fcc_args(self):
        """Reformat get_fcc_args."""
        # aoi
        gfa = self.get_fcc_args.copy()
        aoi = gfa["aoi"]
        if aoi.startswith("("):
            aoi = aoi.replace("(", "").replace(")", "").split(",")
            aoi = tuple([float(i) for i in aoi])
        # years
        years = gfa["years"]
        years = years.replace(" ", "").split(",")
        years = [int(i) for i in years]
        gfa["years"] = years
        # output_file
        gfa["output_file"] = opj(self.DATA_RAW, "forest_latlon.tif")
        return gfa

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Get forestatrisk variables."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Create and set working directory
            far.make_dir(self.workdir)
            os.chdir(self.workdir)

            # Output directories
            far.make_dir(self.DATA_RAW)
            far.make_dir(self.DATA)
            far.make_dir(self.OUT)

            # Initialize Earth Engine
            # service_account = "far-qgis@forestatrisk.iam.gserviceaccount.com"
            # json_key = opj(workdir, ".forestatrisk-gee.json")
            # credentials = ee.ServiceAccountCredentials(
            # service_account, json_key)
            ee.Initialize(project="forestatrisk")

            # Copy qml files (layer style)
            src_dir = opj(os.path.dirname(os.path.dirname(__file__)),
                          "qgis_layer_style")
            dst_dir = opj(self.workdir, "qgis_layer_style")
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

            # Check existence of rasters
            fcc_file = opj(self.DATA, "fcc.tif")
            if not os.path.isfile(fcc_file):
                # Download data
                far.data.country_download(
                    get_fcc_args=self.reformat_get_fcc_args(),
                    iso3=self.isocode,
                    output_dir=self.DATA_RAW)

                # Check isCanceled() to handle cancellation
                if self.isCanceled():
                    return False

                # Progress
                progress += 1
                self.set_progress(progress, self.N_STEPS)

                # Compute explanatory variables
                far.data.country_compute(
                    iso3=self.isocode,
                    temp_dir=self.DATA_RAW,
                    output_dir=self.DATA,
                    proj=self.proj,
                    data_country=True,
                    data_forest=True,
                    keep_temp_dir=True)

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
            # Create symbolic links
            self.create_symbolic_links()

            # Plot
            fcc123_file = opj(self.DATA, "forest", "fcc123.tif")
            png_file = opj(self.OUT, "fcc123.png")
            border_file = opj(self.DATA, "ctry_PROJ.shp")
            fig_fcc123 = far.plot.fcc123(
                input_fcc_raster=fcc123_file,
                maxpixels=1e8,
                output_file=png_file,
                borders=border_file,
                linewidth=0.3,
                figsize=(6, 5), dpi=500)
            plt.close(fig_fcc123)

            # Qgis project and group
            far_project = QgsProject.instance()
            root = far_project.layerTreeRoot()
            group_names = [i.name() for i in root.children()]
            if "Variables" in group_names:
                var_group = root.findGroup("Variables")
            else:
                var_group = root.addGroup("Variables")

            # Add border layer to QGis project
            border_file = opj(self.DATA, "ctry_PROJ.shp")
            border_layer = QgsVectorLayer(border_file, "border", "ogr")
            border_layer.loadNamedStyle(opj("qgis_layer_style", "border.qml"))
            add_layer(far_project, border_layer)

            # Add fcc123 layer to QGis project
            fcc123_layer = QgsRasterLayer(fcc123_file, "fcc123")
            fcc123_layer.loadNamedStyle(opj("qgis_layer_style", "fcc123.qml"))
            add_layer_to_group(far_project, var_group, fcc123_layer)

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarGetVariablesTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarGetVariablesTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarGetVariablesTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
