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

from qgis.core import Qgis

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


# ========================================
# far_get_variables()
# ========================================
def far_get_variables(iface,
                      workdir,
                      isocode,
                      proj,
                      fcc_source="jrc",
                      perc=50,
                      gdrive_remote_rclone="gdrive_gv",
                      gdrive_folder="GEE/GEE-far-qgis-plugin"):
    """Get forestatrisk variables."""

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
    ee.Initialize()

    # Set WDPA API key
    with open(os.path.join(workdir, ".env"), encoding="utf-8") as f:
        [_, value_key] = f.read().split("=")
        os.environ["WDPA_KEY"] = value_key.replace("\"", "")

    # Set working directory
    os.chdir(workdir)

    # Compute gee forest data
    far.data.country_forest_run(
        iso3=isocode,
        proj="EPSG:4326",
        output_dir=data_raw_dir,
        keep_dir=True,
        fcc_source=fcc_source,
        perc=perc,
        gdrive_remote_rclone=gdrive_remote_rclone,
        gdrive_folder=gdrive_folder)

    # Download data
    far.data.country_download(
        iso3=isocode,
        gdrive_remote_rclone=gdrive_remote_rclone,
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

    # Plot
    ifile = os.path.join(data_dir, "forest/fcc123.tif")
    ofile = os.path.join(output_dir, "fcc123.png")
    bfile = os.path.join(data_dir, "ctry_PROJ.shp")
    fig_fcc123 = far.plot.fcc123(
        input_fcc_raster=ifile,
        maxpixels=1e8,
        output_file=ofile,
        borders=bfile,
        linewidth=0.3,
        figsize=(6, 5), dpi=500)
    plt.close(fig_fcc123)

    # Message
    msg = f"Raster files can be found in {workdir}"
    iface.messageBar().pushMessage(
        "Success", msg,
        level=Qgis.Success)

    # Add fcc layer to QGis (to be done)


# ========================================
# far_sample_obs
# ========================================
def far_sample_obs(iface,
                   workdir,
                   nsamp,
                   adapt,
                   seed,
                   csize):
    """Sample observations"""

    # Set working directory
    os.chdir(workdir)

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

# End of file
