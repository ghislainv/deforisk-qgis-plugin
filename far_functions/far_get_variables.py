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
import json
import shutil
import platform

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
opb = os.path.basename


def get_default_file(file_path):
    """Get default file."""
    if platform.system() == "Windows":
        home_dir = opj(os.environ["HOMEDRIVE"], os.environ["HOMEPATH"])
    else:
        home_dir = os.environ["HOME"]
    default_file = opj(home_dir, "deforisk", file_path)
    return default_file


def ee_initialize_service_account(json_file):
    """Initialize to EE with service account."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    service_account = data["client_email"]
    credentials = ee.ServiceAccountCredentials(
        service_account, json_file)
    ee.Initialize(credentials=credentials,
                  opt_url=("https://earthengine-highvolume"
                           ".googleapis.com"))


def set_wdpa_env_var(env_file):
    """Set WDPA environmental variable."""
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        [key, value_key] = line.split("=")
        if key == "WDPA_KEY":
            os.environ[key] = value_key.replace("\"", "")


class FarGetVariablesTask(QgsTask):
    """Get variables for modelling and forecasting deforestation."""

    # Constants
    OUT = opj("outputs", "variables")
    DATA = "data"
    DATA_RAW = "data_raw"
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 4

    def __init__(self, description, iface, workdir, get_fcc_args,
                 isocode, gc_project, wdpa_key, proj, forest_var_only):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.get_fcc_args = get_fcc_args
        self.isocode = isocode
        self.gc_project = gc_project
        self.wdpa_key = wdpa_key
        self.proj = proj
        self.forest_var_only = forest_var_only
        self.exception = None

    def ee_initialize(self):
        """Initialize Earth Engine."""
        json_file = os.path.normpath(self.gc_project)
        default_json_file = get_default_file("deforisk-gee.json")
        if os.path.isfile(json_file):
            ee_initialize_service_account(json_file)
        elif len(self.gc_project) > 0:
            ee.Initialize(project=self.gc_project,
                          opt_url=("https://earthengine-highvolume"
                                   ".googleapis.com"))
        elif os.path.isfile(default_json_file):
            ee_initialize_service_account(default_json_file)
        else:
            msg = "No Earth Engine access provided."
            self.iface.messageBar().pushMessage(
                "Error", msg,
                level=Qgis.Critical)

    def set_wdpa_key(self):
        """Set WDPA key."""
        env_file = os.path.normpath(self.wdpa_key)
        default_env_file = get_default_file("env.txt")
        if os.path.isfile(env_file):
            set_wdpa_env_var(env_file)
        elif os.path.isfile(default_env_file):
            set_wdpa_env_var(default_env_file)
        elif len(self.wdpa_key) > 0:
            os.environ["WDPA_KEY"] = self.wdpa_key
        else:
            msg = "No WDPA API key provided."
            self.iface.messageBar().pushMessage(
                "Error", msg,
                level=Qgis.Critical)

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
        # default buffer of ~10km in dd
        gfa["buff"] = 0.08983152841195216
        # parallel (False with QGis)
        gfa["parallel"] = False
        # output_file
        gfa["output_file"] = opj(self.DATA_RAW,
                                 "forest_latlon.tif")
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

            # Copy qml files (layer style)
            src_dir = opj(os.path.dirname(os.path.dirname(__file__)),
                          "qgis_layer_style")
            dst_dir = opj(self.workdir, "qgis_layer_style")
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

            # Check existence of rasters
            fcc_file = opj(self.DATA, "fcc12.tif")
            if not os.path.isfile(fcc_file):

                # Check if we need GADM
                # If aoi is file, copy it to data_raw
                aoi = self.get_fcc_args["aoi"]
                if os.path.isfile(aoi):
                    ofile = opj(self.DATA_RAW, "aoi_latlon.gpkg")
                    # Copy if file does not exist yet
                    if not os.path.isfile(ofile):
                        shutil.copy(aoi, ofile)
                # Else, download from GADM
                else:
                    ofile = opj(self.DATA_RAW,
                                f"gadm41_{self.isocode}_0.gpkg")
                    far.data.download.download_gadm(
                        iso3=self.isocode,
                        output_file=ofile,
                    )

                # Progress
                progress += 1
                self.set_progress(progress, self.N_STEPS)

                # Download data
                if self.forest_var_only is False:
                    # Initialize ee and wdpa
                    self.ee_initialize()
                    self.set_wdpa_key()
                    # Download
                    far.data.country_download(
                        get_fcc_args=self.reformat_get_fcc_args(),
                        iso3=self.isocode,
                        output_dir=self.DATA_RAW,
                        gadm=False,
                        forest=False)  # See task with geefcc

                # Check isCanceled() to handle cancellation
                if self.isCanceled():
                    return False

                # Progress
                progress += 1
                self.set_progress(progress, self.N_STEPS)

                # Compute explanatory variables
                # Compute data_country if "forest_var_only" is False.
                # Always compute data_forest.
                data_country = not self.forest_var_only
                far.data.country_compute(
                    iso3=self.isocode,
                    temp_dir=self.DATA_RAW,
                    output_dir=self.DATA,
                    proj=self.proj,
                    data_country=data_country,
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
            far.create_symbolic_links(self.DATA)

            # Plot
            fcc123_file = opj(self.DATA, "fcc123.tif")
            png_file = opj(self.OUT, "fcc123.png")
            border_file = opj(self.DATA, "aoi_proj.gpkg")
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
            border_file = opj(self.DATA, "aoi_proj.gpkg|layername=aoi")
            border_layer = QgsVectorLayer(border_file, "aoi border", "ogr")
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
