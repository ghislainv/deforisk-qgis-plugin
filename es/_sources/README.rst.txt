
..
    This index.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    index.org source file directly.

.. image:: https://deforisk-qgis-plugin.org/\_static/logo-deforisk.png
    :target: https://deforisk-qgis-plugin.org
    :align: right
    :width: 140px
    :alt: Logo riskmapjnr

====================
deforisk QGIS plugin
====================

.. image:: https://img.shields.io/badge/licence-GPLv3-8f10cb.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.html
.. image:: https://img.shields.io/badge/GitHub-repo-green.svg
    :target: https://github.com/ghislainv/deforisk-qgis-plugin
.. image:: https://img.shields.io/badge/web-FAR\_QGIS\_plugin-blue.svg
    :target: https://deforisk-qgis-plugin.org
.. image:: https://img.shields.io/badge/python-forestatrisk-orange?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/forestatrisk
.. image:: https://img.shields.io/badge/python-riskmapjnr-yellow?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/riskmapjnr
.. image:: https://img.shields.io/badge/python-pywdpa-90b478?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/pywdpa
.. image:: https://img.shields.io/badge/python-geefcc-3c8c3c?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/geefcc
.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.12593893.svg
    :target: https://doi.org/10.5281/zenodo.12593893

Languages
---------

.. |icon_en| image:: https://deforisk-qgis-plugin.org/_static/icon_en.png
   :width: 20px
   :target: https://deforisk-qgis-plugin.org/

.. |icon_es| image:: https://deforisk-qgis-plugin.org/_static/icon_es.png
   :width: 20px
   :target: https://deforisk-qgis-plugin.org/es

The ``deforisk`` QGIS plugin website is available in English |icon_en| or Spanish |icon_es|.

Aim
---

The ``deforisk`` QGIS plugin can be used to map the deforestation risk for a country or area of interest. Four models can be used to derive the risk maps: the iCAR, GLM, Random Forest, and Moving Window models. These four models can be compared to a benchmark model which assumes a simple decrease of the deforestation risk with distance to forest edge. All models are calibrated using past deforestation observations for a given period of time between 2000 and 2022. Forest cover change maps can be provided by the user or derived from two global tree/forest cover change products: `Global Forest Change <https://earthenginepartners.appspot.com/science-2013-global-forest>`_ and `Tropical Moist Forests <https://forobs.jrc.ec.europa.eu/TMF>`_.

Deforestation risk maps obtained using this plugin can be used to estimate emission reduction impact of forest conservation projects within the `VCS Jurisdictional and Nested REDD+ Framework <https://verra.org/programs/jurisdictional-nested-redd-framework/>`_.

.. image:: https://deforisk-qgis-plugin.org/\_static/banner.png
    :target: https://deforisk-qgis-plugin.org
    :alt: Banner

Specificities
-------------

**Python based.** The ``deforisk`` plugin relies on four Python packages developed specifically for modelling deforestation: ``geefcc``, ``pywdpa``, ``forestatrisk``, and ``riskmapjnr``. The ``geefcc`` package can be used to make forest cover change maps from Google Earth Engine (GEE) and download them locally using two global tree/forest cover change products: Global Forest Change or Tropical Moist Forests. The ``pywdpa`` package allows downloading vector files of protected areas for any countries using the World Database on Protected Areas (WDPA). The ``forestatrisk`` package provides functions to model deforestation and predict the spatial deforestation risk using various explanatory variables (distance to forest edge, elevation, protected areas, etc.) and various statistical models including iCAR, GLM, and Random Forest models. The ``riskmapjnr`` package allows deriving deforestation risk maps following Verra JNR methodologies which include a moving window model and a benchmark model which assumes a decrease of the deforestation risk with the distance to forest edge.

.. image:: https://deforisk-qgis-plugin.org/\_static/logo-geefcc.png
    :target: https://ecology.ghislainv.fr/geefcc
    :alt: geefc
    :width: 100px

.. image:: https://deforisk-qgis-plugin.org/\_static/logo-pywdpa.png
    :target: https://ecology.ghislainv.fr/pywdpa
    :alt: pywdpa
    :width: 100px

.. image:: https://deforisk-qgis-plugin.org/\_static/logo-far.png
    :target: https://ecology.ghislainv.fr/forestatrisk
    :alt: forestatrisk
    :width: 100px

.. image:: https://deforisk-qgis-plugin.org/\_static/logo-riskmapjnr.png
    :target: https://ecology.ghislainv.fr/riskmapjnr
    :alt: riskmapjnr
    :width: 100px

**Processing raster by blocks.** Raster files of forest cover change and explanatory variables might occupy a space of several gigabytes on disk. Processing such large rasters in memory can be prohibitively intensive on computers with limited RAM. Functions used in the ``deforisk`` plugin process large rasters by blocks of pixels representing subsets of the raster data. This makes computation efficient, with low memory usage. Reading and writing subsets of raster data is done by using functions from GDAL, a dependency of the plugin. Numerical computations on arrays are performed with the NumPy Python package, whose core is mostly made of optimized and compiled C code that runs quickly.

**Running tasks in parallel.** State-of-the-art approach to select the best deforestation risk map and forecast deforestation implies comparing various models, fit the models using forest cover change over different time periods and predict the deforestation risk at several dates. This implies repeating a high number of tasks. To save computation time, the ``deforisk`` plugin use the QGIS task manager which allows running several analysis in parallel.

**OS independent.** Using both computation by block for large rasters and task parallelization, the ``deforisk`` plugin allows selecting the best deforestation risk map and forecast deforestation for large countries or areas of interest in a limited amount of time, even on personal computers with average performance hardware. Because the ``deforisk`` is a QGIS plugin written in Python, it should run on all operating systems able to run QGIS, including Windows (:math:`\geq10`), Linux, and Mac OS.

Installing the ``deforisk`` plugin in QGIS
------------------------------------------

.. note::

    **Dependencies**: `QGIS <https://www.qgis.org/en/site/>`_ and `GDAL <https://gdal.org/index.html>`_ must be installed on your system before using the ``deforisk`` plugin. *On Unix-like systems*, you must also install `osmconvert <https://wiki.openstreetmap.org/wiki/Osmconvert>`_ and `osmfilter <https://wiki.openstreetmap.org/wiki/Osmfilter>`_. *On Windows systems*, these dependencies are already included in the plugin as binary ``.exe`` files so you don’t need to install them. Then, the ``forestatrisk`` and ``riskmapjnr`` Python packages must be installed on your system. Follow the `installation instructions <installation.html>`_ to install these dependencies.

- Download the ``deforisk`` `zip file <https://github.com/ghislainv/deforisk-qgis-plugin/archive/refs/heads/main.zip>`_ from GitHub.

- Open QGIS.

- In QGIS menu bar, go to ``Extensions/Install extensions/Install from ZIP``.

- Select the zip file that has been downloaded.

Funding
-------

The development of the plugin has been funded by `Cirad <https://www.cirad.fr/en/>`_ and `FAO <https://www.fao.org/>`_.

.. image:: https://deforisk-qgis-plugin.org/\_static/logo\_cirad.png
    :target: https://www.cirad.fr/en
    :align: left
    :height: 70px
    :alt: Logo Cirad

.. image:: https://deforisk-qgis-plugin.org/\_static/logo\_fao.png
    :target: https://www.fao.org
    :height: 100px
    :alt: Logo FAO

Contributing
------------

The ``deforisk`` QGIS plugin is Open Source and released under the `GNU GPL version 3 license <https://deforisk-qgis-plugin.org/contributing/license.html>`_. Anybody who is interested can contribute to the package development following our `Community guidelines <https://deforisk-qgis-plugin.org/contributing/community_guidelines.html>`_. Every contributor must agree to follow the project’s `Code of conduct <https://deforisk-qgis-plugin.org/contributing/code_of_conduct.html>`_.
