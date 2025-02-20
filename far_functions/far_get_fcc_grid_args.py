"""Get fcc grid arguments."""

import os
import platform
import json

from qgis.core import (
    Qgis, QgsTask,
    QgsMessageLog
)

import ee
from geefcc.get_extent_from_aoi import get_extent_from_aoi
from geefcc.misc import make_dir
from geefcc.make_grid import make_grid, grid_intersection
from geefcc.ee_tmf import ee_tmf
from geefcc.ee_gfc import ee_gfc

opj = os.path.join
opd = os.path.dirname


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


class FarGetFccGridArgsTask(QgsTask):
    """Get fcc grid arguments."""

    # Constants
    DATA_RAW = "data_raw"
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 1

    def __init__(self, description, iface, workdir, get_fcc_args, gc_project):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.get_fcc_args = get_fcc_args
        self.gc_project = gc_project
        self.exception = None
        self.grid_args = None

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

    def reformat_get_fcc_args(self):
        """Reformat get_fcc_args."""
        # aoi
        gfa = self.get_fcc_args.copy()
        aoi = gfa["aoi"]
        if aoi.startswith("("):
            aoi = aoi.replace("(", "").replace(")", "").split(",")
            aoi = tuple(float(i) for i in aoi)
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
        """Get fcc grid arguments."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY,
                                     Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Create and set working directory
            make_dir(self.workdir)
            os.chdir(self.workdir)

            # Output directories
            make_dir(self.DATA_RAW)

            # Arguments
            get_fcc_args = self.reformat_get_fcc_args()
            aoi = get_fcc_args["aoi"]
            buff = get_fcc_args.get("buff", 0)
            years = get_fcc_args.get("years", [2000, 2010, 2020])
            fcc_source = get_fcc_args.get("fcc_source", "tmf")
            perc = get_fcc_args.get("perc", 75)
            tile_size = get_fcc_args.get("tile_size", 1)
            output_file = get_fcc_args.get("output_file", "fcc.tif")

            # Output dir
            out_dir = opd(output_file)
            make_dir(out_dir)

            # Variables
            proj = "EPSG:4326"
            epsg_code = 4326
            scale = 0.000269494585235856472  # in dd, ~30 m

            # Get aoi
            extent = get_extent_from_aoi(aoi, buff, out_dir)
            aoi_isfile = extent["aoi_isfile"]
            borders_gpkg = extent["borders_gpkg"]
            extent_latlong = extent["extent_latlong"]

            # Make minimal grid
            grid_gpkg = opj(out_dir, "grid.gpkg")
            grid = make_grid(extent_latlong, buff=0, tile_size=tile_size,
                             scale=scale, proj=epsg_code, ofile=grid_gpkg)
            if aoi_isfile:
                min_grid = opj(out_dir, "min_grid.gpkg")
                grid_i = grid_intersection(grid, grid_gpkg, min_grid,
                                           borders_gpkg)
                # Update grid and file
                grid = grid_i
                grid_gpkg = min_grid

            # Number of tiles
            ntiles = len(grid)

            # Initialize EE
            self.ee_initialize()

            # Forest image collection
            forest = None
            if fcc_source == "tmf":
                forest = ee_tmf(years)
            if fcc_source == "gfc":
                forest = ee_gfc(years, perc)

            # Create dir for forest tiles
            out_dir_tiles = opj(out_dir, "forest_tiles")
            make_dir(out_dir_tiles)

            # Return tile args in a dictionary as class attribute
            self.grid_args = {
                "grid": grid, "ntiles": ntiles,
                "forest": forest,
                "proj": proj, "scale": scale,
                "out_dir_tiles": out_dir_tiles,
            }

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
            # Message task successful
            msg = 'Successful task "{name}".'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

            # Message number of tiles
            msg = "A total of {ntiles} tile(s) will be downloaded from GEE."
            msg = msg.format(ntiles=self.grid_args["ntiles"])
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

        else:
            if self.exception is None:
                msg = ('FarGetFccGridArgsTask "{name}" not successful '
                       'but without exception (probably the task was '
                       'manually canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarGetFccGridArgsTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarGetFccGridArgsTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
