# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Estimate forestatrisk model parameters.
"""

import os
import pickle

from qgis.core import Qgis, QgsTask, QgsMessageLog

import numpy as np
import matplotlib.pyplot as plt
from patsy.highlevel import dmatrices
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss
import forestatrisk as far

# Alias
opj = os.path.join


class FarModelsTask(QgsTask):
    """Estimate forestatrisk model parameters."""

    # Constants
    OUT = "outputs"
    DATA = "data"
    MESSAGE_CATEGORY = "FAR plugin"
    N_STEPS = 6

    def __init__(self, description, iface, workdir, csize, variables,
                 beta_start, prior_vrho, mcmc, varselection):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.csize = csize
        self.variables = variables
        self.beta_start = beta_start
        self.prior_vrho = prior_vrho
        self.mcmc = mcmc
        self.varselection = varselection
        self.exception = None

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Estimate forestatrisk model parameters."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # -------------------
            # Get the dataset
            # -------------------

            # Set working directory
            os.chdir(self.workdir)

            # Dataset
            dataset_file = opj(self.OUT, "sample.txt")
            if not os.path.isfile(dataset_file):
                msg = ("No data file in the outputs folder "
                       "of the working directory. "
                       "Sample observations first.")
                self.exception = msg
                return False

            dataset = pd.read_csv(dataset_file)
            dataset = dataset.dropna(axis=0)
            dataset["trial"] = 1

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # -------------------
            # Model preparation
            # -------------------

            # Neighborhood for spatial-autocorrelation
            ifile = opj(self.DATA, "fcc.tif")
            nneigh, adj = far.cellneigh(raster=ifile,
                                        csize=self.csize, rank=1)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # List of variables
            var = self.variables.replace(" ", "")
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

            if self.varselection:
                # Run model while there is non-significant variables
                var_remove = True
                while np.any(var_remove):
                    # Formula
                    right_part = " + ".join(variables) + " + cell"
                    left_part = "I(1-fcc) + trial ~ "
                    formula = left_part + right_part
                    # Model
                    mod_icar = far.model_binomial_iCAR(
                        # Observations
                        suitability_formula=formula,
                        data=dataset,
                        # Spatial structure
                        n_neighbors=nneigh, neighbors=adj,
                        # Priors
                        priorVrho=self.prior_vrho,
                        # Chains
                        burnin=1000, mcmc=1000, thin=1,
                        # Starting values
                        beta_start=self.beta_start)
                    # Ecological and statistical significance
                    effects = mod_icar.betas[1:]
                    positive_effects = effects >= 0
                    var_remove = positive_effects
                    var_keep = np.logical_not(var_remove)
                    variables = variables[var_keep]
                    # Check isCanceled() to handle cancellation
                    if self.isCanceled():
                        return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # -------------------
            # Final model
            # -------------------

            # Formula
            right_part = " + ".join(variables) + " + cell"
            left_part = "I(1-fcc) + trial ~ "
            formula = left_part + right_part

            # Initial values for beta_start
            if self.varselection:
                beta_start = mod_icar.betas
            else:
                beta_start = self.beta_start

            # Re-run the model with longer MCMC and estimated initial values
            mod_icar = far.model_binomial_iCAR(
                # Observations
                suitability_formula=formula, data=dataset,
                # Spatial structure
                n_neighbors=nneigh, neighbors=adj,
                # Priors
                priorVrho=self.prior_vrho,
                # Chains
                burnin=self.mcmc,
                mcmc=self.mcmc,
                thin=int(self.mcmc / 1000),
                # Starting values
                beta_start=beta_start)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

            # -------------------
            # Model summary
            # -------------------

            # Summary
            print(mod_icar)

            # Write summary in file
            ofile = opj(self.OUT, "summary_icar.txt")
            with open(ofile, "w", encoding="utf-8") as file:
                file.write(str(mod_icar))

            # Traces
            figs = mod_icar.plot(
                output_file=opj(self.OUT, "mcmc.pdf"),
                plots_per_page=3,
                figsize=(10, 6),
                dpi=80
            )
            for i in figs:
                plt.close(i)

            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            # Progress
            progress += 1
            self.set_progress(progress, self.N_STEPS)

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
            ofile = opj(self.OUT, "mod_icar.pickle")
            with open(ofile, "wb") as file:
                pickle.dump(mod_icar_pickle, file)

            # -------------------
            # Model comparison
            # -------------------

            # Null model
            formula_null = "I(1-fcc) ~ 1"
            y, x = dmatrices(formula_null, data=dataset, NA_action="drop")
            Y = y[:, 0]
            X_null = x[:, :]
            mod_null = LogisticRegression(solver="lbfgs")
            mod_null = mod_null.fit(X_null, Y)
            pred_null = mod_null.predict_proba(X_null)
            ofile = opj(self.OUT, "mod_null.pickle")
            with open(ofile, "wb") as file:
                pickle.dump(mod_null, file)

            # Simple glm with no spatial random effects
            formula_glm = formula
            y, x = dmatrices(formula_glm, data=dataset, NA_action="drop")
            Y = y[:, 0]
            # We remove the last column (cells)
            X_glm = x[:, :-1]
            mod_glm = LogisticRegression(solver="lbfgs")
            mod_glm = mod_glm.fit(X_glm, Y)
            pred_glm = mod_glm.predict_proba(X_glm)
            ofile = opj(self.OUT, "mod_glm.pickle")
            with open(ofile, "wb") as file:
                pickle.dump(mod_glm, file)

            # Random forest model
            formula_rf = formula
            y, x = dmatrices(formula_rf, data=dataset, NA_action="drop")
            Y = y[:, 0]
            # We remove the first (intercept, 0 col) and last column (cells)
            X_rf = x[:, 1:-1]
            mod_rf = RandomForestClassifier(n_estimators=500,
                                            n_jobs=3)
            mod_rf = mod_rf.fit(X_rf, Y)
            pred_rf = mod_rf.predict_proba(X_rf)
            # Use joblib for persistence
            # https://scikit-learn.org/stable/model_persistence.html
            ofile = opj(self.OUT, "mod_rf.joblib")
            with open(ofile, "wb") as file:
                joblib.dump(mod_rf, file, compress=True)

            # Deviances
            deviance_null = 2*log_loss(Y, pred_null, normalize=False)
            deviance_glm = 2*log_loss(Y, pred_glm, normalize=False)
            deviance_rf = 2*log_loss(Y, pred_rf, normalize=False)
            deviance_icar = mod_icar.deviance
            deviance_full = 0
            dev = [deviance_null, deviance_glm, deviance_rf,
                   deviance_icar, deviance_full]

            # Result table
            mod_dev = pd.DataFrame(
                {"model": ["null", "glm", "rf", "icar", "full"],
                 "deviance": dev})
            perc = 100*(1-mod_dev.deviance/deviance_null)
            mod_dev["perc"] = perc
            mod_dev = mod_dev.round(0)
            ofile = opj(self.OUT, "model_deviances.csv")
            mod_dev.to_csv(ofile, header=True, index=False)

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

            # Progress
            self.set_progress(self.N_STEPS, self.N_STEPS)

            # Message
            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('FarModelsTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarModelsTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarModelsTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
