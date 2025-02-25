"""Allocate deforestation to projects."""

import os

from qgis.core import (
    Qgis, QgsTask, QgsProject,
    QgsVectorLayer, QgsRasterLayer, QgsMessageLog
)

import forestatrisk as far

# Local import
from ..utilities import add_layer, add_layer_to_group

# Alias
opj = os.path.join


class AllocateTask(QgsTask):
    """Allocate deforestation to project."""

    # Constants
    OUT = "outputs"
    DATA = "data"
    MESSAGE_CATEGORY = "Deforisk"
    N_STEPS = 1

    def __init__(self, description, iface, workdir, riskmap_juris,
                 defor_rate_tab, project_borders, defor_juris, years_forecast,
                 defor_density_map):
        super().__init__(description, QgsTask.CanCancel)
        self.iface = iface
        self.workdir = workdir
        self.riskmap_juris = riskmap_juris
        self.defor_rate_tab = defor_rate_tab
        self.project_borders = project_borders
        self.defor_juris = defor_juris
        self.years_forecast = years_forecast
        self.defor_density_map = defor_density_map
        self.exception = None
        self.out_dir = opj(self.OUT, "allocating_deforestation")

    def set_progress(self, progress, n_steps):
        """Set progress."""
        if progress == 0:
            self.setProgress(1)
        else:
            prog_perc = progress / n_steps
            prog_perc = int(prog_perc * 100)
            self.setProgress(prog_perc)

    def run(self):
        """Allocating deforestation to project."""

        try:
            # Starting message
            msg = 'Started task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Info)

            # Progress
            progress = 0
            self.set_progress(progress, self.N_STEPS)

            # Set working directory
            os.chdir(self.workdir)

            # Create output directory
            far.make_dir(self.out_dir)

            # Validation
            far.allocate_deforestation(
                riskmap_juris_file=self.riskmap_juris,
                defor_rate_tab=self.defor_rate_tab,
                defor_juris_ha=self.defor_juris,
                years_forecast=self.years_forecast,
                project_borders=self.project_borders,
                output_file=opj(self.out_dir, "defor_project.csv"),
                defor_density_map=self.defor_density_map,
                blk_rows=128,
                verbose=False)

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

            if self.defor_density_map:

                # Qgis project and group
                far_project = QgsProject.instance()
                root = far_project.layerTreeRoot()
                group_names = [i.name() for i in root.children()]
                if "Allocation" in group_names:
                    var_group = root.findGroup("Allocation")
                else:
                    var_group = root.addGroup("Allocation")

                # Add border layer to QGis project
                border_file = opj(self.DATA, "aoi_proj.gpkg|layername=aoi")
                border_layer = QgsVectorLayer(border_file, "aoi border", "ogr")
                border_layer.loadNamedStyle(
                    opj("qgis_layer_style", "border.qml"))
                add_layer(far_project, border_layer)

                # Add defor density map layer to QGis project
                defor_density_file = opj(self.OUT, "allocating_deforestation",
                                         "deforestation_density_map.tif")
                defor_density_layer = QgsRasterLayer(defor_density_file,
                                                     "defor_density")
                add_layer_to_group(far_project, var_group, defor_density_layer)

                # Progress
                self.set_progress(self.N_STEPS, self.N_STEPS)

            msg = 'Successful task "{name}"'
            msg = msg.format(name=self.description())
            QgsMessageLog.logMessage(msg, self.MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                msg = ('AllocateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'AllocateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'AllocateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
