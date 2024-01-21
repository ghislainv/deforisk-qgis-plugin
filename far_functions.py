# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Get variables
"""

import os
import sys
import shutil

from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer

# Import the forestatrisk package
try:
    import forestatrisk as far
except ImportError:
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    far_dir = os.path.join(plugin_dir, "forestatrisk")
    sys.path.append(far_dir)
    import forestatrisk as far

# Then import far dependencies
import matplotlib.pyplot as plt
import ee
from patsy import dmatrices

# Local import
from .utilities import add_layer


# ========================================
# far_get_variables()
# ========================================
def far_get_variables(iface,
                      workdir,
                      isocode,
                      proj,
                      fcc_source,
                      perc,
                      remote_rclone,
                      gdrive_folder,
                      wdpa_key):
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

    # Print far doc and version
    print(far.__doc__)
    print(f"version: {far.__version__}")

    # Initialize Earth Engine
    service_account = "far-qgis@forestatrisk.iam.gserviceaccount.com"
    json_key = os.path.join(workdir, ".forestatrisk-gee.json")
    credentials = ee.ServiceAccountCredentials(service_account, json_key)
    ee.Initialize(credentials)

    # Get WDPA API key
    env_file = os.path.join(workdir, ".env")
    if wdpa_key == "":
        if os.path.isfile(env_file):
            with open(env_file, encoding="utf-8") as f:
                lines = f.readlines
                for line in lines:
                    [key, value_key] = line.split("=")
                    if key == "WDPA_KEY":
                        os.environ[key] = value_key.replace("\"", "")
        else:
            msg = ("No WDPA API key provided "
                   "(plugin or WDPA_KEY in workdir/.env)")
            raise ValueError(msg)

    # Copy qml files (layer style)
    src_dir = os.path.join(os.path.dirname(__file__), "qgis_layer_style")
    dst_dir = os.path.join(workdir, "qgis_layer_style")
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

    # Qgis project
    far_project = QgsProject.instance()

    # Check raster existence
    fcc123_file = os.path.join(data_dir, "forest", "fcc123.tif")
    if not os.path.isfile(fcc123_file):
        # Compute gee forest data
        far.data.country_forest_run(
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
        msg = f"Raster files can be found in {workdir}"
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

    # Add border layer to QGis project
    border_file = os.path.join(data_dir, "ctry_PROJ.shp")
    border_layer = QgsVectorLayer(border_file, "border", "ogr")
    border_layer.loadNamedStyle(os.path.join("qgis_layer_style", "border.qml"))
    add_layer(far_project, border_layer)

    # Add fcc123 layer to QGis project
    fcc123_layer = QgsRasterLayer(fcc123_file, "fcc123")
    fcc123_layer.loadNamedStyle(os.path.join("qgis_layer_style", "fcc123.qml"))
    add_layer(far_project, fcc123_layer)


# ========================================
# far_sample_obs
# ========================================
def far_sample_obs(iface,
                   workdir,
                   proj,
                   nsamp,
                   adapt,
                   seed,
                   csize):
    """Sample observations"""

    # Set working directory
    os.chdir(workdir)

    # Qgis project
    far_project = QgsProject.instance()

    # Check for files
    fcc23_file = os.path.join(workdir, "data", "fcc23.tif")
    if not os.path.isfile(fcc23_file):
        msg = ("No forest cover change "
               "raster in the working directory. "
               "Run upper block to \"Download and "
               "compute variables\" first.")
        iface.messageBar().pushMessage(
            "Error", msg,
            level=Qgis.Critical)
    else:
        # Sample observations
        dataset = far.sample(nsamp=nsamp, adapt=adapt,
                             seed=seed, csize=csize,
                             var_dir="data",
                             input_forest_raster="fcc23.tif",
                             output_file="outputs/sample.txt",
                             blk_rows=0)

        # Remove NA from data-set (otherwise scale() and
        # model_binomial_iCAR doesn't work)
        dataset = dataset.dropna(axis=0)
        # Set number of trials to one for far.model_binomial_iCAR()
        dataset["trial"] = 1
        # Print the first five rows
        print(dataset.head(5))

        # Sample size
        ndefor = sum(dataset.fcc23 == 0)
        nfor = sum(dataset.fcc23 == 1)
        with open("outputs/sample_size.csv",
                  "w",
                  encoding="utf-8") as file:
            file.write("Var, n\n")
            file.write(f"ndefor, {ndefor}\n")
            file.write(f"nfor, {nfor}\n")
        print(f"Sample size: ndefor = {ndefor}, nfor = {nfor}")

        # Correlation formula
        formula_corr = "fcc23 ~ dist_road + dist_town + dist_river + \
        dist_defor + dist_edge + altitude + slope - 1"

        # Output file
        of = "outputs/correlation.pdf"
        # Data
        y, data = dmatrices(formula_corr, data=dataset,
                            return_type="dataframe")
        # Plots
        figs = far.plot.correlation(
            y=y, data=data,
            plots_per_page=3,
            figsize=(7, 8),
            dpi=80,
            output_file=of)
        for i in figs:
            plt.close(i)

        # Message
        msg = f"Sampled observations can be found in {workdir}"
        iface.messageBar().pushMessage(
            "Success", msg,
            level=Qgis.Success)

        # Add layer of sampled observations to QGis project
        samp_file = os.path.join(workdir, "outputs", "sample.txt")
        encoding = "UTF-8"
        delimiter = ","
        decimal = "."
        x = "X"
        y = "Y"
        uri = (f"file://{samp_file}?encoding={encoding}"
               f"&delimiter={delimiter}&decimalPoint={decimal}"
               f"&crs={proj}&xField={x}&yField={y}")
        samp_layer = QgsVectorLayer(uri, "sampled_obs", "delimitedtext")
        samp_layer.loadNamedStyle(os.path.join("qgis_layer_style",
                                               "sample.qml"))
        add_layer(far_project, samp_layer)

# End of file
