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

from qgis.core import Qgis, QgsProject, QgsVectorLayer

import matplotlib.pyplot as plt
from patsy import dmatrices
import forestatrisk as far

# Local import
from ..utilities import add_layer


# far_sample_obs
def far_sample_obs(iface,
                   workdir,
                   proj,
                   nsamp,
                   adapt,
                   seed,
                   csize):
    """Sample observations."""

    # Set working directory
    os.chdir(workdir)

    # Check for files
    fcc23_file = os.path.join(workdir, "data", "fcc23.tif")
    if not os.path.isfile(fcc23_file):
        msg = ("No forest cover change "
               "raster in the working directory. "
               "Run upper box to \"Download and "
               "compute variables\" first.")
        iface.messageBar().pushMessage(
            "Error", msg,
            level=Qgis.Critical)

    # Sample observations
    dataset = far.sample(nsamp=nsamp, adapt=adapt,
                         seed=seed, csize=csize,
                         var_dir="data",
                         input_forest_raster="fcc23.tif",
                         output_file="outputs/sample.txt",
                         blk_rows=0,
                         verbose=False)

    # Remove NA from data-set (otherwise scale() and
    # model_binomial_iCAR doesn't work)
    dataset = dataset.dropna(axis=0)
    # Set number of trials to one for far.model_binomial_iCAR()
    dataset["trial"] = 1
    # Print the first five rows
    print("\n"
          "Dataset of observations:")
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
    print("\n"
          f"Sample size: ndefor = {ndefor}, nfor = {nfor}")

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

    # Qgis project
    far_project = QgsProject.instance()

    # Add layer of sampled observations to QGis project
    samp_file = os.path.join(workdir, "outputs", "sample.txt")
    encoding = "UTF-8"
    delimiter = ","
    decimal = "."
    x = "X"
    y = "Y"
    uri = (f"file:///{samp_file}?encoding={encoding}"
           f"&delimiter={delimiter}&decimalPoint={decimal}"
           f"&crs={proj}&xField={x}&yField={y}")
    samp_layer = QgsVectorLayer(uri, "sampled_obs", "delimitedtext")
    samp_layer.loadNamedStyle(os.path.join("qgis_layer_style",
                                           "sample.qml"))
    add_layer(far_project, samp_layer)

# End of file
