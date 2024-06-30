# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Empty task.
"""

from qgis.core import (
    Qgis, QgsTask, QgsMessageLog
)


class EmptyTask(QgsTask):
    """Empty task.

    This class is used as main task with subTasks. A global
    description can be used.

    """

    # Constants
    MESSAGE_CATEGORY = "Deforisk"

    def __init__(self, description):
        super().__init__(description, QgsTask.CanCancel)
        self.exception = None

    def run(self):
        """Model validation."""
        try:
            # Check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

        except Exception as exc:
            self.exception = exc
            return False

        return True

    def finished(self, result):
        """Show messages and add layers."""

        if result:
            pass

        else:
            if self.exception is None:
                msg = ('FarValidateTask "{name}" not successful but without '
                       'exception (probably the task was manually '
                       'canceled by the user)')
                msg = msg.format(name=self.description())
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Warning)
            else:
                msg = 'FarValidateTask "{name}" Exception: {exception}'
                msg = msg.format(
                        name=self.description(),
                        exception=self.exception)
                QgsMessageLog.logMessage(
                    msg, self.MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        """Cancelation message."""
        msg = 'FarValidateTask "{name}" was canceled'
        msg = msg.format(name=self.description())
        QgsMessageLog.logMessage(
            msg, self.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

# End of file
