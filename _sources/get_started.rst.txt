===========
Get started
===========


..
    This get_started.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    get_started.org source file directly.

Introduction
------------

To test the plugin installation and have a first look at its functionalities, try it on a small area of interest (AOI) such as the `Martinique <https://en.wikipedia.org/wiki/Martinique>`_ island (1128 km\ :sup:`2`\) which as the MTQ iso code. Testing the plugin on a small AOI has the advantage of making computations faster so that you can directly see the outputs, interpret the results, and understand the functioning of the plugin.

Get variables
-------------

.. image:: _static/interface_MTQ-tuto.png
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

Click the run button and you should get the following layer on QGIS:

.. image:: _static/qgis-variables.png
    :width: 650px
    :alt: QGIS variables

Benchmark model
---------------

Forestatrisk models
-------------------

Moving window models
--------------------

Validation
----------

Conclusion
----------
