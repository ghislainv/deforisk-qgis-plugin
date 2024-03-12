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

from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer

import ee
import matplotlib.pyplot as plt
import forestatrisk as far

# Local import
from ..utilities import add_layer


# far_get_variables()
def far_get_variables(iface,
                      workdir,
                      isocode,
                      proj,
                      fcc_source,
                      perc,
                      remote_rclone,
                      gdrive_folder):
    """Get forestatrisk variables."""

    # Create and set working directory
    far.make_dir(workdir)
    os.chdir(workdir)

    # Output directories
    data_raw_dir = "data_raw"
    data_dir = "data"
    output_dir = "outputs"
    far.make_dir(data_raw_dir)
    far.make_dir(data_dir)
    far.make_dir(output_dir)

    # Initialize Earth Engine
    # service_account = "far-qgis@forestatrisk.iam.gserviceaccount.com"
    # json_key = os.path.join(workdir, ".forestatrisk-gee.json")
    # credentials = ee.ServiceAccountCredentials(service_account, json_key)
    ee.Initialize(project="forestatrisk")

    # Copy qml files (layer style)
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "qgis_layer_style")
    dst_dir = os.path.join(workdir, "qgis_layer_style")
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

    # Check raster existence
    fcc123_file = os.path.join(data_dir, "forest", "fcc123.tif")
    if not os.path.isfile(fcc123_file):
        # Run gee for forest data
        far.data.run_gee_forest(
            iso3=isocode,
            proj="EPSG:4326",
            output_dir=data_raw_dir,
            keep_dir=True,
            fcc_source=fcc_source,
            perc=perc,
            gdrive_remote_rclone=remote_rclone,
            gdrive_folder=gdrive_folder)

        # Download data
        far.data.country_download(
            iso3=isocode,
            gdrive_remote_rclone=remote_rclone,
            gdrive_folder=gdrive_folder,
            output_dir=data_raw_dir)

        # Compute explanatory variables
        far.data.country_compute(
            iso3=isocode,
            temp_dir=data_raw_dir,
            output_dir=data_dir,
            proj=proj,
            data_country=True,
            data_forest=True,
            keep_temp_dir=True)

        # Message
        msg = f"Variable raster files can be found in {workdir}"
        iface.messageBar().pushMessage(
            "Success", msg,
            level=Qgis.Success)

    # Plot
    fcc123_file = os.path.join(data_dir, "forest", "fcc123.tif")
    png_file = os.path.join(output_dir, "fcc123.png")
    border_file = os.path.join(data_dir, "ctry_PROJ.shp")
    fig_fcc123 = far.plot.fcc123(
        input_fcc_raster=fcc123_file,
        maxpixels=1e8,
        output_file=png_file,
        borders=border_file,
        linewidth=0.3,
        figsize=(6, 5), dpi=500)
    plt.close(fig_fcc123)

    # Qgis project
    far_project = QgsProject.instance()

    # Add border layer to QGis project
    border_file = os.path.join(data_dir, "ctry_PROJ.shp")
    border_layer = QgsVectorLayer(border_file, "border", "ogr")
    border_layer.loadNamedStyle(os.path.join("qgis_layer_style", "border.qml"))
    add_layer(far_project, border_layer)

    # Add fcc123 layer to QGis project
    fcc123_layer = QgsRasterLayer(fcc123_file, "fcc123")
    fcc123_layer.loadNamedStyle(os.path.join("qgis_layer_style", "fcc123.qml"))
    add_layer(far_project, fcc123_layer)

# End of file
