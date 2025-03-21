# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DeforiskPlugin
                                 A QGIS plugin
 Deforestation risk mapping.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-12-13
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Ghislain Vieilledent (Cirad)
        email                : ghislain.vieilledent@cirad.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Define double undescore variables
# https://peps.python.org/pep-0008/#module-level-dunder-names
__author__ = "Ghislain Vieilledent and Thomas Arsouze"
__email__ = "ghislain.vieilledent@cirad.fr, thomas.arsouze@cirad.fr"
__version__ = "2.0"

import os
import subprocess
import platform
import random
from importlib.metadata import version

from qgis.core import Qgis, QgsApplication, QgsTask, QgsMessageLog

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

import pandas as pd
import geefcc
import pywdpa
import forestatrisk as far
import riskmapjnr as rmj

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .deforisk_plugin_dialog import DeforiskPluginDialog

# Local far functions
from .far_functions import (
    FarCheckArgsTask,
    FarGetFccGridArgsTask,
    FarGetFccTileTask,
    FarGetVariablesTask,
    FarSampleObsTask,
    FarCalibrateTask,
    FarInterpolateRhoTask,
    FarPredictTask,
)

# Local rmj function
from .rmj_functions import (
    BmCalibrateTask,
    BmPredictTask,
    MwCalibrateTask,
    MwPredictTask,
)

# Local val function
from .val_functions import (
    EmptyTask,
    ValidateTask,
    AllocateTask,
)

opj = os.path.join

# Dependencies versions
GEEFCC_VERSION = "0.1.6"
PYWDPA_VERSION = "0.1.6"
FORESTATRISK_VERSION = "1.3.2"
RISKMAPJNR_VERSION = "1.3.2"


class DeforiskPlugin:
    """QGIS Plugin Implementation."""

    OUT = "outputs"
    FAR_MODELS = ["icar", "glm", "rf"]
    MOD_PERIODS = ["calibration", "historical"]
    PRED_PERIODS = ["calibration", "validation",
                    "historical", "forecast"]
    PRED_BM_PERIODS = ["validation", "forecast"]
    VAL_PERIODS = ["calibration", "validation",
                   "historical"]

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            "i18n",
            f"DeforiskPlugin_{locale}.qm")

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr("&Deforisk")
        self.args = None  # GV: arguments for tasks.
        self.task_grid = None  # GV: arguments for fcc tile.

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.dlg = None

        # Task manager
        self.tm = QgsApplication.taskManager()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("DeforiskPlugin", message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ":/plugins/foo/bar.png") or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ":/plugins/deforisk-qgis-plugin/icon.png"
        self.add_action(
            icon_path,
            text=self.tr("Create and compare maps of deforestation risk "
                         "in the tropics"),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr("&Deforisk"),
                action)
            self.iface.removeToolBarIcon(action)

    def check_dependence_version(self, pkg_name, v):
        """Check package version."""
        if version(pkg_name) != v:
            msg = (f"Please install {pkg_name} v{v} "
                   "and restart QGIS")
            QgsMessageLog.logMessage(msg, "Deforisk", Qgis.Critical)

    def print_dependency_version(self):
        """Print package versions."""
        # osmconvert info
        cmd = ["osmconvert", "--help"]
        result = subprocess.run(cmd, capture_output=True, check=True)
        result = result.stdout.splitlines()
        print(result[1].decode())
        # osmfilter info
        cmd = ["osmfilter", "--help"]
        result = subprocess.run(cmd, capture_output=True, check=True)
        result = result.stdout.splitlines()
        print(result[1].decode())
        # geefcc
        print(f"geefcc {geefcc.__version__}")
        self.check_dependence_version(
            "geefcc",
            GEEFCC_VERSION)
        # pywdpa
        print(f"pywdpa {pywdpa.__version__}")
        self.check_dependence_version(
            "pywdpa",
            PYWDPA_VERSION)
        # forestatrisk
        print(f"forestatrisk {far.__version__}")
        self.check_dependence_version(
            "forestatrisk",
            FORESTATRISK_VERSION)
        # riskmapjnr
        print(f"riskmapjnr {rmj.__version__}")
        self.check_dependence_version(
            "riskmapjnr",
            RISKMAPJNR_VERSION)

    def set_exe_path(self):
        """Add folder with windows executables to PATH."""
        is_win = platform.system() == "Windows"
        is_64bit = "PROGRAMFILES(X86)" in list(os.environ.keys())
        if is_win and is_64bit:
            os.environ["PATH"] += os.pathsep + os.path.join(
                self.plugin_dir,
                "winexe"
            )
        self.print_dependency_version()

    def task_description(self, task_name, model=None, period=None,
                         date=None, csize_val=None):
        """Write down task description."""
        get_fcc_args = self.args["get_fcc_args"]
        aoi_abbrev = get_fcc_args["aoi"]
        if os.path.isfile(aoi_abbrev):
            aoi_abbrev = "ownaoi"
        years = get_fcc_args["years"]
        years = years.replace(" ", "").replace(",", "_")
        fcc_abbrev = get_fcc_args["fcc_source"]
        perc = get_fcc_args["perc"]
        if os.path.isfile(fcc_abbrev):
            fcc_abbrev = "ownfcc"
        if fcc_abbrev == "gfc":
            fcc_abbrev = f"gfc{perc}"
        mod_desc = f"_{model}" if model else ""
        period_desc = f"_{period}" if period else ""
        date_desc = f"_{date}" if date else ""
        csize_desc = f"_{csize_val}" if csize_val else ""
        # Description
        desc_base = (f"{task_name}_{aoi_abbrev}_"
                     f"{years}_{fcc_abbrev}")
        description = (desc_base + mod_desc
                       + period_desc + date_desc
                       + csize_desc)
        return description

    def set_workdir(self, iso, years, fcc_source, seed=None):
        """Set working directory."""
        years = years.replace(" ", "").replace(",", "_")
        random.seed(seed)
        rand_int = random.randint(1, 9999)
        fcc_abbrev = fcc_source
        if os.path.isfile(fcc_abbrev):
            fcc_abbrev = "own"
        folder_name = f"{iso}_{years}_{fcc_abbrev}_{rand_int:04}"
        if platform.system() == "Windows":
            workdir = os.path.join(os.environ["HOMEDRIVE"],
                                   os.environ["HOMEPATH"],
                                   "deforisk", folder_name)
        else:
            workdir = os.path.join(os.environ["HOME"],
                                   "deforisk", folder_name)
        return workdir

    def make_get_fcc_args(self, aoi, years, fcc_source, perc,
                          tile_size):
        """Make get_ffc_args dictionary."""
        get_fcc_args = {"aoi": aoi, "years": years, "fcc_source":
                        fcc_source, "perc": perc, "tile_size":
                        tile_size}
        return get_fcc_args

    def get_win_sizes(self):
        """Get window sizes as list."""
        win_sizes = self.args["win_sizes"]
        win_sizes = win_sizes.replace(" ", "").split(",")
        win_sizes = [int(i) for i in win_sizes]
        return win_sizes

    def get_samp_far_periods(self):
        """Get periods for observation sampling."""
        samp_far_periods = []
        sfp = list(self.args["samp_far_periods"].values())
        for (p, samp_period) in enumerate(self.MOD_PERIODS):
            if sfp[p]:
                samp_far_periods.append(samp_period)
        return samp_far_periods

    def get_mod_far_periods(self):
        """Get periods for FAR models."""
        mod_far_periods = []
        mfp = list(self.args["mod_far_periods"].values())
        for (p, mod_period) in enumerate(self.MOD_PERIODS):
            if mfp[p]:
                mod_far_periods.append(mod_period)
        return mod_far_periods

    def get_mod_bm_periods(self):
        """Get periods for Benchmark model."""
        mod_bm_periods = []
        mbp = list(self.args["mod_bm_periods"].values())
        for (p, mod_period) in enumerate(self.MOD_PERIODS):
            if mbp[p]:
                mod_bm_periods.append(mod_period)
        return mod_bm_periods

    def get_mod_mw_periods(self):
        """Get periods for Moving Window model."""
        mod_mw_periods = []
        mbp = list(self.args["mod_mw_periods"].values())
        for (p, mod_period) in enumerate(self.MOD_PERIODS):
            if mbp[p]:
                mod_mw_periods.append(mod_period)
        return mod_mw_periods

    def get_interp_far_periods(self):
        """Get periods for rho interpolation."""
        interp_far_periods = []
        ifp = list(self.args["pred_far_periods"].values())
        for (p, period) in enumerate(self.MOD_PERIODS):
            if any(ifp[(2 * p): (2 * p + 2)]):
                interp_far_periods.append(period)
        return interp_far_periods

    def get_pred_far_models(self):
        """Get list of far models for predictions."""
        pred_far_models = []
        pfm = list(self.args["pred_far_models"].values())
        for (m, far_model) in enumerate(self.FAR_MODELS):
            if pfm[m]:
                pred_far_models.append(far_model)
        return pred_far_models

    def get_pred_far_periods(self):
        """Get periods for far predictions."""
        pred_far_periods = []
        pfp = list(self.args["pred_far_periods"].values())
        for (p, period) in enumerate(self.PRED_PERIODS):
            if pfp[p]:
                pred_far_periods.append(period)
        return pred_far_periods

    def get_pred_bm_periods(self):
        """Get periods for benchmark predictions."""
        pred_bm_periods = []
        pbp = list(self.args["pred_bm_periods"].values())
        for (p, period) in enumerate(self.PRED_BM_PERIODS):
            if pbp[p]:
                pred_bm_periods.append(period)
        return pred_bm_periods

    def get_pred_mw_periods(self):
        """Get periods for mw predictions."""
        pred_mw_periods = []
        pmp = list(self.args["pred_mw_periods"].values())
        for (p, period) in enumerate(self.PRED_PERIODS):
            if pmp[p]:
                pred_mw_periods.append(period)
        return pred_mw_periods

    def get_val_periods(self):
        """Get periods for validation."""
        val_periods = []
        val_dates = [self.args["val_calib"],
                     self.args["val_valid"],
                     self.args["val_histo"]]
        for (p, period) in enumerate(self.VAL_PERIODS):
            if val_dates[p]:
                val_periods.append(period)
        return val_periods

    def get_date(self, period):
        """Get date from period."""
        date = None
        if period in ["calibration", "historical"]:
            date = "t1"
        elif period == "validation":
            date = "t2"
        elif period == "forecast":
            date = "t3"
        return date

    def get_csizes_val(self):
        """Get coarse grid cell sizes as list."""
        csizes_val = self.args["csizes_val"]
        csizes_val = csizes_val.replace(" ", "").split(",")
        csizes_val = [int(i) for i in csizes_val]
        return csizes_val

    def get_val_models(self):
        """Get list of models for validation."""
        val_models = ["bm"]
        win_sizes = self.get_win_sizes()
        val_far_mod = [self.args["val_icar"],
                       self.args["val_glm"],
                       self.args["val_rf"]]
        if self.args["val_mw"]:
            for win_size in win_sizes:
                val_models.append("mw_" + str(win_size))
        for (m, far_model) in enumerate(self.FAR_MODELS):
            if val_far_mod[m]:
                val_models.append(far_model)
        return val_models

    def get_all_models(self):
        """Get list of all models for comparison."""
        all_models = ["bm"]
        all_models.extend(self.FAR_MODELS)
        win_sizes = self.get_win_sizes()
        for win_size in win_sizes:
            all_models.append("mw_" + str(win_size))
        return all_models

    def create_far_directory(self, period):
        """Create MW directories."""
        workdir = self.args["workdir"]
        rmj.make_dir(opj(workdir, "outputs",
                         "far_models",
                         period))

    def create_mw_directory(self, period):
        """Create MW directories."""
        workdir = self.args["workdir"]
        rmj.make_dir(opj(workdir, "outputs",
                         "rmj_moving_window",
                         period))

    def create_validation_directories(self, period):
        """Create validation directories."""
        workdir = self.args["workdir"]
        far.make_dir(opj(workdir, "outputs",
                         "model_validation", period,
                         "figures"))
        far.make_dir(opj(workdir, "outputs",
                         "model_validation", period,
                         "tables"))

    def combine_model_results(self):
        """Combine model results for comparison."""
        workdir = self.args["workdir"]
        os.chdir(workdir)
        indices_list = []
        csizes_val = self.get_csizes_val()
        models = self.get_all_models()
        periods = self.VAL_PERIODS.copy()
        # Loop on periods and models
        for csize_val in csizes_val:
            for period in periods:
                for model in models:
                    ifile = opj(
                        self.OUT, "model_validation",
                        period, "tables",
                        f"indices_{model}_{period}_{csize_val}.csv"
                    )
                    if os.path.isfile(ifile):
                        df = pd.read_csv(ifile)
                        df["model"] = model
                        df["period"] = period
                        indices_list.append(df)
        # Concat indices
        indices = pd.concat(indices_list, axis=0)
        indices.sort_values(by=["csize_coarse_grid", "period", "model"])
        indices = indices[["csize_coarse_grid", "csize_coarse_grid_ha",
                           "ncell", "period", "model",
                           "MedAE", "R2", "RMSE", "wRMSE"]]
        indices.to_csv(
            os.path.join(self.OUT, "model_validation", "indices_all.csv"),
            sep=",", header=True,
            index=False, index_label=False)

    def catch_arguments(self):
        """Catch arguments from UI."""
        # Get variables
        workdir = self.dlg.workdir.filePath()
        aoi = self.dlg.aoi.filePath()
        years = self.dlg.years.text()
        fcc_source = self.dlg.fcc_source.filePath()
        perc = self.dlg.perc.text()
        perc = int(perc) if perc != "" else 50
        tile_size = self.dlg.tile_size.text()
        tile_size = float(tile_size) if tile_size != "" else 1.0
        iso = self.dlg.isocode.text()
        gc_project = self.dlg.gc_project.filePath()
        wdpa_key = self.dlg.wdpa_key.filePath()
        proj = self.dlg.proj.text()
        forest_var_only = self.dlg.forest_var_only.isChecked()
        # Sample observations
        nsamp = int(self.dlg.nsamp.text())
        adapt = self.dlg.adapt.isChecked()
        seed = int(self.dlg.seed.text())
        csize = float(self.dlg.csize.text())
        samp_far_calib = self.dlg.samp_far_calib.isChecked()
        samp_far_hist = self.dlg.samp_far_hist.isChecked()
        # Benchmark model
        defor_thresh = float(self.dlg.defor_thresh.text())
        max_dist = int(self.dlg.max_dist.text())
        mod_bm_calib = self.dlg.mod_bm_calib.isChecked()
        mod_bm_hist = self.dlg.mod_bm_hist.isChecked()
        pred_bm_valid_t2 = self.dlg.pred_bm_valid_t2.isChecked()
        pred_bm_forecast_t3 = self.dlg.pred_bm_forecast_t3.isChecked()
        # FAR models
        variables = self.dlg.variables.text()
        beta_start = float(self.dlg.beta_start.text())
        prior_vrho = int(self.dlg.prior_vrho.text())
        mcmc = int(self.dlg.mcmc.text())
        varselection = self.dlg.varselection.isChecked()
        mod_far_calib = self.dlg.mod_far_calib.isChecked()
        mod_far_hist = self.dlg.mod_far_hist.isChecked()
        # FAR predict
        csize_interp = float(self.dlg.csize_interp.text())
        pred_icar = self.dlg.pred_icar.isChecked()
        pred_glm = self.dlg.pred_glm.isChecked()
        pred_rf = self.dlg.pred_rf.isChecked()
        pred_far_calib_t1 = self.dlg.pred_far_calib_t1.isChecked()
        pred_far_valid_t2 = self.dlg.pred_far_valid_t2.isChecked()
        pred_far_hist_t1 = self.dlg.pred_far_hist_t1.isChecked()
        pred_far_forecast_t3 = self.dlg.pred_far_forecast_t3.isChecked()
        # MW model
        win_sizes = self.dlg.win_sizes.text()
        mod_mw_calib = self.dlg.mod_mw_calib.isChecked()
        mod_mw_hist = self.dlg.mod_mw_hist.isChecked()
        pred_mw_calib_t1 = self.dlg.pred_mw_calib_t1.isChecked()
        pred_mw_valid_t2 = self.dlg.pred_mw_valid_t2.isChecked()
        pred_mw_hist_t1 = self.dlg.pred_mw_hist_t1.isChecked()
        pred_mw_forecast_t3 = self.dlg.pred_mw_forecast_t3.isChecked()
        # Validate
        csizes_val = self.dlg.csizes_val.text()
        val_icar = self.dlg.val_icar.isChecked()
        val_glm = self.dlg.val_glm.isChecked()
        val_rf = self.dlg.val_rf.isChecked()
        val_mw = self.dlg.val_mw.isChecked()
        val_calib = self.dlg.val_calib.isChecked()
        val_valid = self.dlg.val_valid.isChecked()
        val_histo = self.dlg.val_histo.isChecked()
        # Allocate
        riskmap_juris = self.dlg.riskmap_juris.filePath()
        defor_rate_tab = self.dlg.defor_rate_tab.filePath()
        project_borders = self.dlg.project_borders.filePath()
        defor_juris = int(self.dlg.defor_juris.text())
        years_forecast = float(self.dlg.years_forecast.text())
        defor_density_map = self.dlg.defor_density_map.isChecked()
        # Special variables
        if workdir == "":
            # seed = 1234  # Only for tests to get same dir
            fcc_abbrev = fcc_source
            if os.path.isfile(fcc_abbrev):
                fcc_abbrev = "own"
            workdir = self.set_workdir(iso, years, fcc_abbrev, seed)
        get_fcc_args = self.make_get_fcc_args(
            aoi, years, fcc_source, perc, tile_size)
        if variables == "":
            variables = "dist_edge"
        # Dictionary of arguments for far functions
        self.args = {
            # Data
            "workdir": workdir,
            "get_fcc_args": get_fcc_args,
            "isocode": iso,
            "gc_project": gc_project,
            "wdpa_key": wdpa_key,
            "proj": proj,
            "forest_var_only": forest_var_only,
            # Benchmark
            "defor_thresh": defor_thresh,
            "max_dist": max_dist,
            "mod_bm_periods": {
                "mod_bm_calib": mod_bm_calib,
                "mod_bm_hist": mod_bm_hist},
            "pred_bm_periods": {
                "pred_bm_valid_t2": pred_bm_valid_t2,
                "pred_bm_forecast_t3": pred_bm_forecast_t3},
            # FAR sample
            "nsamp": nsamp, "adapt": adapt, "seed": seed,
            "csize": csize,
            "samp_far_periods": {
                "samp_far_calib": samp_far_calib,
                "samp_far_hist": samp_far_hist},
            # FAR models
            "variables": variables,
            "beta_start": beta_start, "prior_vrho": prior_vrho,
            "mcmc": mcmc, "varselection": varselection,
            "mod_far_periods": {
                "mod_far_calib": mod_far_calib,
                "mod_far_hist": mod_far_hist},
            # FAR predict
            "csize_interp": csize_interp,
            "pred_far_models": {
                "pred_icar": pred_icar,
                "pred_glm": pred_glm,
                "pred_rf": pred_rf},
            "pred_far_periods": {
                "pred_far_calib_t1": pred_far_calib_t1,
                "pred_far_valid_t2": pred_far_valid_t2,
                "pred_far_hist_t1": pred_far_hist_t1,
                "pred_far_forecast_t3": pred_far_forecast_t3},
            # Moving Window
            "win_sizes": win_sizes,
            "mod_mw_periods": {
                "mod_mw_calib": mod_mw_calib,
                "mod_mw_hist": mod_mw_hist},
            "pred_mw_periods": {
                "pred_mw_calib_t1": pred_mw_calib_t1,
                "pred_mw_valid_t2": pred_mw_valid_t2,
                "pred_mw_hist_t1": pred_mw_hist_t1,
                "pred_mw_forecast_t3": pred_mw_forecast_t3},
            # Validation
            "csizes_val": csizes_val,
            "val_icar": val_icar,
            "val_glm": val_glm, "val_rf": val_rf,
            "val_mw": val_mw,
            "val_calib": val_calib, "val_valid": val_valid,
            "val_histo": val_histo,
            # Allocate
            "riskmap_juris": riskmap_juris,
            "defor_rate_tab": defor_rate_tab,
            "project_borders": project_borders,
            "defor_juris": defor_juris,
            "years_forecast": years_forecast,
            "defor_density_map": defor_density_map,
        }

    def far_check_args(self):
        """Check arguments."""
        self.catch_arguments()
        description = self.task_description("CheckArgs")
        task_check_args = FarCheckArgsTask(
            description=description,
            iface=self.iface,
            args=self.args)
        task_check_args.taskCompleted.connect(self.far_check_get_fcc)
        # Add task to task manager
        self.tm.addTask(task_check_args)

    def far_check_get_fcc(self):
        """No tiles if forest."""
        self.catch_arguments()
        get_fcc_args = self.args["get_fcc_args"]
        fcc_source = get_fcc_args["fcc_source"]
        if os.path.isfile(fcc_source):
            self.far_get_variables()
        else:
            self.far_get_fcc_grid_args()

    def far_get_fcc_grid_args(self):
        """Get fcc grid arguments."""
        self.catch_arguments()
        description = self.task_description("GetFccGridArgs")
        self.task_grid = FarGetFccGridArgsTask(
            description=description,
            iface=self.iface,
            workdir=self.args["workdir"],
            get_fcc_args=self.args["get_fcc_args"],
            gc_project=self.args["gc_project"],
        )
        self.task_grid.taskCompleted.connect(self.far_get_fcc_tiles)
        # Add task to task manager
        self.tm.addTask(self.task_grid)

    def far_get_fcc_tiles(self):
        """Get fcc."""
        self.catch_arguments()
        # Main empty task
        description = self.task_description("GetFccTiles")
        main_task = EmptyTask(description)
        grid = self.task_grid.grid_args["grid"]
        for (i, ext) in enumerate(grid):
            description = self.task_description(
                f"GetFccTile_{i}")
            task = FarGetFccTileTask(
                description=description,
                index=i,
                ext=ext,
                grid_args=self.task_grid.grid_args,
            )
            main_task.addSubTask(task, [], QgsTask.ParentDependsOnSubTask)
        # Execute far_get_variables after getting the tiles
        main_task.taskCompleted.connect(self.far_get_variables)
        # Add main task to task manager
        self.tm.addTask(main_task)

    def far_get_variables(self):
        """Get variables."""
        self.catch_arguments()
        description = self.task_description("GetVariables")
        task = FarGetVariablesTask(
            description=description,
            iface=self.iface,
            workdir=self.args["workdir"],
            get_fcc_args=self.args["get_fcc_args"],
            isocode=self.args["isocode"],
            gc_project=self.args["gc_project"],
            wdpa_key=self.args["wdpa_key"],
            proj=self.args["proj"],
            forest_var_only=self.args["forest_var_only"])
        # Add task to task manager
        self.tm.addTask(task)

    def far_sample_obs(self):
        """Sample observations."""
        self.catch_arguments()
        samp_far_periods = self.get_samp_far_periods()
        for period in samp_far_periods:
            description = self.task_description(
                "SampleObs", period=period)
            task = FarSampleObsTask(
                description=description,
                iface=self.iface,
                workdir=self.args["workdir"],
                period=period,
                proj=self.args["proj"],
                nsamp=self.args["nsamp"],
                adapt=self.args["adapt"],
                seed=self.args["seed"],
                csize=self.args["csize"])
            # Add task to task manager
            self.tm.addTask(task)

    def far_calibrate(self):
        """Estimate forestatrisk model parameters."""
        self.catch_arguments()
        periods = self.get_mod_far_periods()
        for period in periods:
            description = self.task_description(
                "FarCalibrate", period=period)
            task = FarCalibrateTask(
                description=description,
                iface=self.iface,
                workdir=self.args["workdir"],
                period=period,
                csize=self.args["csize"],
                variables=self.args["variables"],
                beta_start=self.args["beta_start"],
                prior_vrho=self.args["prior_vrho"],
                mcmc=self.args["mcmc"],
                varselection=self.args["varselection"])
            # Add task to task manager
            self.tm.addTask(task)

    def far_predict(self):
        """Predict deforestation risk."""
        # Models and periods
        models = self.get_pred_far_models()
        periods = self.get_pred_far_periods()
        # Tasks with loops on dates and models
        for period in periods:
            self.create_far_directory(period)
            date = self.get_date(period)
            for model in models:
                description = self.task_description(
                    "FarPredict", model=model,
                    period=period, date=date)
                task = FarPredictTask(
                    description=description,
                    iface=self.iface,
                    workdir=self.args["workdir"],
                    years=self.args["get_fcc_args"]["years"],
                    period=period,
                    model=model)
                # Add task to task manager
                self.tm.addTask(task)

    def far_check_interpolate_rho(self):
        """Check if we need to interpolate rho for icar model."""
        self.catch_arguments()
        pred_icar = self.args["pred_far_models"]["pred_icar"]
        if pred_icar:
            self.far_interpolate_rho()
        else:
            self.far_predict()

    def far_interpolate_rho(self):
        """Interpolate rho."""
        self.catch_arguments()
        periods = self.get_interp_far_periods()
        # Main empty task
        description = self.task_description("FarInterpolateRho")
        main_task = EmptyTask(description)
        # Interpolate rho
        for period in periods:
            description = self.task_description(
                "FarInterpolateRho", period=period)
            task = FarInterpolateRhoTask(
                description=description,
                iface=self.iface,
                workdir=self.args["workdir"],
                period=period,
                csize_interpolate=self.args["csize_interp"])
            main_task.addSubTask(task, [], QgsTask.ParentDependsOnSubTask)
        # Execute far_predict after rho interpolation
        main_task.taskCompleted.connect(self.far_predict)
        # Add main task to task manager
        self.tm.addTask(main_task)

    def mw_calibrate(self):
        """Compute distance threshold and local deforestation rate."""
        self.catch_arguments()
        win_sizes = self.get_win_sizes()
        periods = self.get_mod_mw_periods()
        # Loop on window sizes
        for period in periods:
            self.create_mw_directory(period)
            for win_size in win_sizes:
                model = f"mv_{win_size}"
                description = self.task_description(
                    "MwCalibrate", model=model, period=period)
                task = MwCalibrateTask(
                    description=description,
                    workdir=self.args["workdir"],
                    years=self.args["get_fcc_args"]["years"],
                    defor_thresh=self.args["defor_thresh"],
                    max_dist=self.args["max_dist"],
                    win_size=win_size,
                    period=period)
                # Add task to task manager
                self.tm.addTask(task)

    def mw_predict(self):
        """Predict deforestation rate with moving window approach."""
        self.catch_arguments()
        win_sizes = self.get_win_sizes()
        periods = self.get_pred_mw_periods()
        for period in periods:
            self.create_mw_directory(period)
            date = self.get_date(period)
            for wsize in win_sizes:
                model = f"mv_{wsize}"
                description = self.task_description(
                    "MwPredict", model=model, date=date)
                task = MwPredictTask(
                    description=description,
                    workdir=self.args["workdir"],
                    years=self.args["get_fcc_args"]["years"],
                    win_size=wsize,
                    period=period)
                # Add task to task manager
                self.tm.addTask(task)

    def bm_calibrate(self):
        """Compute distance threshold and vulnerability classes with
        deforestation rates.
        """
        self.catch_arguments()
        periods = self.get_mod_bm_periods()
        for period in periods:
            description = self.task_description(
                "BmCalibrate", period=period)
            task = BmCalibrateTask(
                description=description,
                workdir=self.args["workdir"],
                years=self.args["get_fcc_args"]["years"],
                defor_thresh=self.args["defor_thresh"],
                max_dist=self.args["max_dist"],
                period=period)
            # Add task to task manager
            self.tm.addTask(task)

    def bm_predict(self):
        """Predict deforestation rate with the benchmark model."""
        self.catch_arguments()
        periods = self.get_pred_bm_periods()
        for period in periods:
            date = self.get_date(period)
            description = self.task_description(
                "BmPredict", period=period, date=date)
            task = BmPredictTask(
                description=description,
                workdir=self.args["workdir"],
                years=self.args["get_fcc_args"]["years"],
                period=period)
            # Add task to task manager
            self.tm.addTask(task)

    def validate(self):
        """Model validation."""
        # Catch arguments
        self.catch_arguments()
        csizes_val = self.get_csizes_val()
        val_models = self.get_val_models()
        val_periods = self.get_val_periods()
        # Main empty task
        description = self.task_description("Validate_all")
        main_task = EmptyTask(description)
        # Tasks with loop on csizes_val, periods, and models
        for csize_val in csizes_val:
            for period in val_periods:
                self.create_validation_directories(period)
                date = self.get_date(period)
                for model in val_models:
                    description = self.task_description(
                        "Validate", model=model,
                        period=period, date=date,
                        csize_val=csize_val)
                    task = ValidateTask(
                        description=description,
                        iface=self.iface,
                        workdir=self.args["workdir"],
                        years=self.args["get_fcc_args"]["years"],
                        csize_val=csize_val,
                        period=period,
                        model=model)
                    main_task.addSubTask(task)
        # Combine model results
        main_task.taskCompleted.connect(self.combine_model_results)
        # Add first task to task manager
        self.tm.addTask(main_task)

    def allocate(self):
        """Allocating deforestation to project."""
        # Catch arguments
        self.catch_arguments()
        description = self.task_description("Allocate")
        task = AllocateTask(
            description=description,
            iface=self.iface,
            workdir=self.args["workdir"],
            riskmap_juris=self.args["riskmap_juris"],
            defor_rate_tab=self.args["defor_rate_tab"],
            project_borders=self.args["project_borders"],
            defor_juris=self.args["defor_juris"],
            years_forecast=self.args["years_forecast"],
            defor_density_map=self.args["defor_density_map"])
        # Add first task to task manager
        self.tm.addTask(task)

    def run(self):
        """Run method that performs all the real work."""

        # Create the dialog with elements (after translation)
        # and keep reference.
        # Only create GUI ONCE in callback, so that it will only
        # load when the plugin is started
        if self.first_start is True:
            self.first_start = False
            self.dlg = DeforiskPluginDialog()
            # Set executable path
            self.set_exe_path()

        # Action if buttons ares clicked

        # Data
        self.dlg.run_far_get_variable.clicked.connect(
            self.far_check_args)

        # Benchmark model
        self.dlg.run_bm_calibrate.clicked.connect(
            self.bm_calibrate)
        self.dlg.run_bm_predict.clicked.connect(
            self.bm_predict)

        # FAR with icar, glm, and rf models
        self.dlg.run_far_sample.clicked.connect(
            self.far_sample_obs)
        self.dlg.run_far_calibrate.clicked.connect(
            self.far_calibrate)
        self.dlg.run_far_predict.clicked.connect(
            self.far_check_interpolate_rho)

        # Moving window model
        self.dlg.run_mw_calibrate.clicked.connect(
            self.mw_calibrate)
        self.dlg.run_mw_predict.clicked.connect(
            self.mw_predict)

        # Model validation
        self.dlg.run_validate.clicked.connect(
            self.validate)

        # Allocating deforestation
        self.dlg.run_allocate.clicked.connect(
            self.allocate)

        # Show the dialog
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

# End of file
