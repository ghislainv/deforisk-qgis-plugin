# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Model validation.
"""

import os

from qgis.core import Qgis

import pandas as pd
import forestatrisk as far

# Alias
opj = os.path.join


# far_validate
def far_validate(iface,
                 workdir,
                 years,
                 model_icar=True,
                 model_glm=False,
                 model_rf=False):
    """Model validation."""

    # Set working directory
    os.chdir(workdir)

    # Compute time intervals from years
    years = years.replace(" ", "").split(",")
    years = [int(i) for i in years]
    time_intervals = [years[1] - years[0], years[2] - years[1]]

    # Synthesize results for all models and periods
    indices_list = []

    # -------------------------------
    # Loop on dates/periods and model
    # -------------------------------

    dates = ["t1", "t2"]
    periods = ["calibration", "validation"]
    models = ["icar", "glm", "rf"]
    run_models = [model_icar, model_glm, model_rf]
    for (d, period, ti) in zip(dates, periods, time_intervals):
        for (m, run_model) in zip(models, run_models):
            if run_model:
                # Validation
                far.validation_udef_arp(
                    fcc_file=opj("data", "forest", "fcc123.tif"),
                    period=period,
                    time_interval=ti,
                    riskmap_file=opj("outputs", f"prob_{m}_{d}.tif"),
                    tab_file_defor=opj("outputs", f"defrate_cat_{m}_{d}.csv"),
                    csize_coarse_grid=50,
                    indices_file_pred=opj("outputs", f"indices_{m}_{d}.csv"),
                    tab_file_pred=opj("outputs", f"pred_obs_{m}_{d}.csv"),
                    fig_file_pred=opj("outputs", f"pred_obs_{m}_{d}.png"),
                    verbose=False)
                # Indices
                df = pd.read_csv(opj("outputs", f"indices_{m}_{d}.csv"))
                df["model"] = m
                df["period"] = period
                indices_list.append(df)

    # Concat indices
    indices = pd.concat(indices_list, axis=0)
    indices.sort_values(by=["period", "model"])
    indices = indices[["model", "period", "MedAE", "R2", "wRMSE",
                       "ncell", "csize_coarse_grid",
                       "csize_coarse_grid_ha"]]
    indices.to_csv(
        opj("outputs", "indices_all.csv"),
        sep=",", header=True,
        index=False, index_label=False)

    # -------------------
    # Message
    # -------------------

    # Message
    msg = f"Validation results can be found in {workdir}"
    iface.messageBar().pushMessage(
        "Success", msg,
        level=Qgis.Success)

# End of file
