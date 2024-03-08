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
import shutil

from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer

import ee
import numpy as np
import matplotlib.pyplot as plt
from patsy import dmatrices
import pandas as pd
import pickle
import forestatrisk as far

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
    #service_account = "far-qgis@forestatrisk.iam.gserviceaccount.com"
    #json_key = os.path.join(workdir, ".forestatrisk-gee.json")
    #credentials = ee.ServiceAccountCredentials(service_account, json_key)
    ee.Initialize(project="forestatrisk")

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
    """Sample observations."""

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


# ========================================
# far_model_icar
# ========================================
def far_model_icar(iface,
                   workdir,
                   csize,
                   variables,
                   beta_start,
                   prior_vrho,
                   mcmc,
                   varselection):
    """Estimate iCAR model parameters."""

    # -------------------
    # Get the dataset
    # -------------------

    # Set working directory
    os.chdir(workdir)

    # Dataset
    dataset_file = os.path.join(workdir, "outputs", "sample.txt")
    if not os.path.isfile(dataset_file):
        msg = ("No data file in the outputs folder "
               "of the working directory. "
               "Sample observations first.")
        iface.messageBar().pushMessage(
            "Error", msg,
            level=Qgis.Critical)
    else:
        dataset = pd.read_csv(dataset_file)
        dataset = dataset.dropna(axis=0)
        dataset["trial"] = 1

    # -------------------
    # Model preparation
    # -------------------

    # Neighborhood for spatial-autocorrelation
    ifile = os.path.join("data", "fcc23.tif")
    nneigh, adj = far.cellneigh(raster=ifile, csize=csize, rank=1)

    # List of variables
    var = variables.replace(" ", "")
    var = var.split(",")
    # Order variable and place pa first
    if "pa" in var:
        var.remove("pa")
        var = ["pa"] + var
    # Categorical variables and scaled continuous variables
    var = ["C(pa)" if v == "pa" else f"scale({v})" for v in var]
    # Transform into numpy array
    # (to select with var_keep afterwards)
    variables = np.array(var)

    # -------------------
    # Variable selection
    # -------------------

    if varselection:
        # Run model while there is non-significant variables
        var_remove = True
        while np.any(var_remove):
            # Formula
            right_part = " + ".join(variables) + " + cell"
            left_part = "I(1-fcc23) + trial ~ "
            formula = left_part + right_part
            # Model
            mod_icar = far.model_binomial_iCAR(
                # Observations
                suitability_formula=formula,
                data=dataset,
                # Spatial structure
                n_neighbors=nneigh, neighbors=adj,
                # Priors
                priorVrho=prior_vrho,
                # Chains
                burnin=1000, mcmc=1000, thin=1,
                # Starting values
                beta_start=beta_start)
            # Ecological and statistical significance
            effects = mod_icar.betas[1:]
            positive_effects = effects >= 0
            var_remove = positive_effects
            var_keep = np.logical_not(var_remove)
            variables = variables[var_keep]

    # -------------------
    # Final model
    # -------------------

    # Formula
    right_part = " + ".join(variables) + " + cell"
    left_part = "I(1-fcc23) + trial ~ "
    formula = left_part + right_part

    # Initial values for beta_start
    beta_start = mod_icar.betas if varselection else beta_start

    # Re-run the model with longer MCMC and estimated initial values
    mod_icar = far.model_binomial_iCAR(
        # Observations
        suitability_formula=formula, data=dataset,
        # Spatial structure
        n_neighbors=nneigh, neighbors=adj,
        # Priors
        priorVrho=prior_vrho,
        # Chains
        burnin=mcmc, mcmc=mcmc, thin=int(mcmc / 1000),
        # Starting values
        beta_start=beta_start)

    # -------------------
    # Model summary
    # -------------------

    # Summary
    print(mod_icar)

    # Write summary in file
    ofile = os.path.join("outputs", "summary_icar.txt")
    with open(ofile, "w", encoding="utf-8") as file:
        file.write(str(mod_icar))

    # Traces
    figs = mod_icar.plot(
        output_file=os.path.join("outputs", "mcmc.pdf"),
        plots_per_page=3,
        figsize=(10, 6),
        dpi=80
    )
    for i in figs:
        plt.close(i)

    # -------------------
    # Model backup
    # -------------------

    # Save model's main specifications with pickle
    mod_icar_pickle = {
        "formula": mod_icar.suitability_formula,
        "rho": mod_icar.rho,
        "betas": mod_icar.betas,
        "Vrho": mod_icar.Vrho,
        "deviance": mod_icar.deviance}
    ofile = os.path.join("outputs", "mod_icar.pickle")
    with open(ofile, "wb") as file:
        pickle.dump(mod_icar_pickle, file)

# End of file
