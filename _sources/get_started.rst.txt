===========
Get started
===========


..
    This get_started.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    get_started.org source file directly.

Introduction
------------

.. |ico_py| image:: _static/icon_python_console_toolbar.png
   :class: no-scaled-link
.. |ico_deforisk| image:: _static/icon_deforisk_toolbar.png
   :class: no-scaled-link   

Open QGIS on your computer. To have access to log messages, activate the “Log Messages” panel in QGIS going to ``View > Panel > Log Messages`` in the Menu. When using a plugin, it is also a good habit to open the Python console in QGIS to have access to Python messages returned in the console. To open it, click on the Python icon |ico_py| in the “Plugins Toolbar”. If the toolbar is not visible, activate it going to ``View > Toolbars > Plugins Toolbar`` in the Menu.

Once the plugin has been installed (see `Installation <installation.html>`_ instructions), open the plugin clicking on its icon |ico_deforisk|. You should see the versions of the dependencies installed in your environment written in the Python console. Check that these version numbers correspond to the last version for each dependency. Otherwise upgrade the dependencies.

.. code:: python

    osmconvert 0.8.10
    osmfilter 1.4.4
    geefcc 0.1.3
    pywdpa 0.1.6
    forestatrisk 1.2
    riskmapjnr 1.3

To test the plugin and have a first look at its functionalities, try it on a small area of interest (AOI) such as the `Martinique <https://en.wikipedia.org/wiki/Martinique>`_ island (1128 km\ :sup:`2`\) which has the MTQ iso code. Testing the plugin on a small AOI has the advantage of making computations fast so that you can directly see the outputs, interpret the results, and understand the functioning of the plugin.

Get variables
-------------

.. image:: _static/interface_MTQ-tuto-variables.png
    :alt: MTQ variables

- ``Working directory``: Select your working directory. Here ``/home/<username>/deforisk/MTQ-tuto``, but it could be ``C:\Users\<username>\deforisk\MTQ-tuto`` on Windows for example.

- ``Area Of Interest``: MTQ

- ``Years``: 2000, 2010, 2020

- ``Forest data source``: tmf

- ``Tree cover threshold (%)``: 50 (could be left empty, not useful here for tmf data source)

- ``Tile size (dd)``: 1

- ``Country/state ISO code``: MTQ

- ``Earth Engine access``: Google Cloud project name with Earth Engine access or path to a JSON private key file for service account.

- ``WDPA access``: Personal WDPA API Token or path to text file with WDPA\_KEY environmental variable.

- ``Projection EPSG code``: EPSG:5490

Click the run button. A forest cover change map appears in the list of QGIS layers (see image below and click to enlarge) and a plot of the forest cover change ``fcc123.png`` is created in folder ``outputs/variables``. New folders are created in the working directory among which the ``data_raw`` folder which includes raw data with intermediary files and the ``data`` folder which includes processed data used for models and plots. You can visualize the road network for example adding the ``roads_proj.shp`` vector file, which is located in the ``data_raw`` directory, in QGIS.

.. image:: _static/qgis-variables-results.png
    :width: 650px
    :alt: QGIS variables

Benchmark model
---------------

.. image:: _static/interface_MTQ-tuto-benchmark.png
    :alt: MTQ variables

Fit model to data
~~~~~~~~~~~~~~~~~

- ``Deforestation threshold (%)``: 99.5%

- ``Max. distance to forest edge (m)``: 2500

- ``calib. period``: Checked, the model is fitted over the calibration period (t1--t2).

- ``hist. period``: Checked, the model is fitted over the historical period (t1--t3).

Click the ``Run`` button to estimate the deforestation risk with the benchmark model and predict the deforestation risk at t1 using both data on the calibration and historical periods. Maps with classes of deforestation risk are added to the list of QGIS layers (see image below) and new folders with results are created in the ``outputs/rmj_benchmark/`` directory including the ``<period>/defrate_cat_bm_<period>.csv`` tables with deforestation rates for each class of deforestation risk (see details `here <plugin_api.html#defrate-table>`_).

.. image:: _static/qgis-benchmark-results.png
    :width: 650px
    :alt: QGIS variables

Predict the deforestation risk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``t2 validation``: Checked, computes predictions at t2 for validation (using the benchmark model fitted over the calibration period).

- ``t3 forecast``: Checked, computes predictions at t3 for forecasting (using the benchmark model fitted over the historical period).

Click the ``Run`` button to predict the deforestation risk at t2 and t3 using the benchmark model. Maps with classes of deforestation risk are added to the list of QGIS layers (see image below) and new folders with results are created in the ``outputs/rmj_benchmark/`` directory.

Forestatrisk models
-------------------

Moving window models
--------------------

Validation
----------

Conclusion
----------
