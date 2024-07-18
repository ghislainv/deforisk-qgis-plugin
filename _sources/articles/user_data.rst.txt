===========
User’s data
===========


..
    This case_study.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    case_study.org source file directly.

Forest cover change map
-----------------------

You can use your own forest cover change map with the plugin. To do so, prepare a ``forest_src.tif`` raster file and copy it to the ``data_raw`` folder in your working directory. This files should have the following characteristics:

- It must be a multiple band raster file with each band representing the forest cover at one date.

- Bands must be ordered (first band for t, second band for t+1, etc.).

- Raster values should be 1 for forest pixels and 0 for non-forest pixels (the raster can thus be of type Byte).

- The raster file should be projected in the coordinate reference system of the project.

- The raster must cover at least all the area of the jurisdiction.

.. warning::
    It is much better if the raster is bigger than the jurisdiction (e.g. buffer of 10 km) to reduce edge effects when computing distances to forest edge for example.

While executing the ``Get variables`` step, this raster will be used as the forest data source and all the forest variables (forest cover change and distance to forest edge at the different dates) will be computed from this data.

You can create this multiple band raster using the QGIS tool ``Merge`` available in **Raster > Miscellaneous**.

Additional explicative variables
--------------------------------

Preparing the raster files
^^^^^^^^^^^^^^^^^^^^^^^^^^

To use different or additional explicatives variables for the statistical models, prepare the corresponding raster files in the ``data`` folder of the working directory. These additional raster files should have the following characteristics:

- They should cover at least all the area of the jurisdiction.

- They should be in the projection of the project.

- Resolution should be as close as possible to the forest cover raster resolution.

If some of these variables are changing with time, then create several rasters for t1, t2, and t3.

Create symbolic links
^^^^^^^^^^^^^^^^^^^^^

To avoid copying the same data at several places on disk, create symbolic links in each of the folders ``data_calibration``, ``data_validation``, ``data_historical``, and ``data_forecast``. Symbolic links should points to new rasters in the ``data`` folder.

If using changing variables with time, then use the same file name (e.g. ``variable.tif``) for symbolic links in the four ``data_*`` folders but pointing to different files ``variable_t*.tif`` in the ``data`` folder. For example:

- In the ``data_calibration`` and ``data_historical`` folders (for which we use variables at t1), the file ``variable.tif`` should point to the file ``variable_t1.tif`` in the ``data`` folder.

- In the ``data_validation`` folder (for which we use variables at t2), the file ``variable.tif`` should point to the file ``variable_t2.tif`` in the ``data`` folder.

- In the ``data_forecast`` folder (for which we use variables at t3), the file ``variable.tif`` should point to the file ``variable_t3.tif`` in the ``data`` folder.

  To create symbolic links in Windows, use the command `mklink <https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/mklink>`_. To be able to create symbolic links, the `Developer Mode <https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development>`_ must be activated on your computer.

.. code:: shell

    # Create a symbolic link in Windows
    mklink "C:\Users\me\deforisk\MTQ\data_calibration\variable.tif" "C:\Users\me\deforisk\MTQ\data\variable_t1.tif"

Use these variables in the formula for the statistical models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If raster ``variable.tif`` was added to the list of explicative variables, then add its name ``variable`` to the list of variables names for the FAR statistical models, see detail `here <../plugin_api.html#fit-models-to-data>`_.
