
..
    This index.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    index.org source file directly.

.. image:: https://ecology.ghislainv.fr/deforisk-qgis-plugin/\_images/logo-deforisk.svg
    :target: https://ecology.ghislainv.fr/deforisk-qgis-plugin
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
    :target: https://ecology.ghislainv.fr/deforisk-qgis-plugin
.. image:: https://img.shields.io/badge/python-forestatrisk-orange?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/forestatrisk
.. image:: https://img.shields.io/badge/python-riskmapjnr-yellow?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/riskmapjnr
.. image:: https://img.shields.io/badge/python-pywdpa-90b478?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/pywdpa
.. image:: https://img.shields.io/badge/python-geefcc-3c8c3c?logo=python&logoColor=ffd43b&.svg
    :target: https://ecology.ghislainv.fr/geefcc

Aim
---

The ``deforisk`` QGis plugin can be used to map the deforestation risk for a country or area of interest. Four models can be used to derive the risk maps: the iCAR, GLM, Random Forest, and Moving Window models. These four models can be compared to a benchmark model which assumes a simple decrease of the deforestation risk with distance to forest edge. All models are calibrated using past deforestation observations for a given period of time between 2000 and 2022. Forest cover change maps can be provided by the user or derived from two global tree/forest cover change products: `Global Forest Change <https://earthenginepartners.appspot.com/science-2013-global-forest>`_ and `Tropical Moist Forests <https://forobs.jrc.ec.europa.eu/TMF>`_.

Deforestation risk maps obtained using this plugin can be used to estimate emission reduction impact of forest conservation projects within the `VCS Jurisdictional and Nested REDD+ Framework <https://verra.org/programs/jurisdictional-nested-redd-framework/>`_.

.. image:: https://ecology.ghislainv.fr/deforisk-qgis-plugin/\_images/banner.png
    :target: https://ecology.ghislainv.fr/deforisk-qgis-plugin
    :alt: Banner

Installing the ``deforisk`` plugin in Qgis
------------------------------------------

.. note::

    **Dependencies**: `Qgis <https://www.qgis.org/en/site/>`_ and `GDAL <https://gdal.org/index.html>`_ must be installed on your system before using the ``deforisk`` plugin. *On Unix-like systems*, you must also install `osmconvert <https://wiki.openstreetmap.org/wiki/Osmconvert>`_ and `osmfilter <https://wiki.openstreetmap.org/wiki/Osmfilter>`_. *On Windows systems*, these dependencies are already included in the plugin as binary ``.exe`` files so you don’t need to install them. Then, the ``forestatrisk`` and ``riskmapjnr`` Python packages must be installed on your system. Follow the `installation instructions <installation.html>`_ to install these dependencies.

- Download the ``deforisk`` `zip file <https://github.com/ghislainv/deforisk-qgis-plugin/archive/refs/heads/main.zip>`_ from GitHub.

- Open Qgis.

- In Qgis menu bar, go to ``Extensions/Install extensions/Install from ZIP``.

- Select the zip file that has been downloaded.

Funding
-------

The development of the plugin has been funded by `Cirad <https://www.cirad.fr/en/>`_ and `FAO <https://www.fao.org/>`_.

.. image:: https://ecology.ghislainv.fr/deforisk-qgis-plugin/\_images/logo\_cirad.png
    :target: https://www.cirad.fr/en
    :align: left
    :height: 70px
    :alt: Logo Cirad

.. image:: https://ecology.ghislainv.fr/deforisk-qgis-plugin/\_images/logo\_fao.png
    :target: https://www.fao.org
    :height: 100px
    :alt: Logo FAO

Contributing
------------

The ``deforisk`` QGIS plugin is Open Source and released under the `GNU GPL version 3 license <https://ecology.ghislainv.fr/deforisk-qgis-plugin/license.html>`_. Anybody who is interested can contribute to the package development following our `Community guidelines <https://ecology.ghislainv.fr/deforisk-qgis-plugin/contributing.html>`_. Every contributor must agree to follow the project’s `Code of conduct <https://ecology.ghislainv.fr/deforisk-qgis-plugin/code_of_conduct.html>`_.
