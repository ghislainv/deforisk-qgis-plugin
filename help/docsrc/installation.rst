
..
    This installation.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    installation.org source file directly.

Installation
------------

.. note::

    `QGIS <https://www.qgis.org/en/site/>`_ and `GDAL <https://gdal.org/index.html>`_ must be installed on your system. The ``forestatrisk`` and ``riskmapjnr`` Python packages must also be installed on your system before using the QGIS plugin. Follow the instructions below to install these dependencies on your system.

On Windows
~~~~~~~~~~

Turn on the developer mode
^^^^^^^^^^^^^^^^^^^^^^^^^^

To be able to use the ``deforisk`` QGis plugin, you need to activate the developer mode on Windows. The developer mode allows creating symbolic links (symlinks) which are used by the plugin and necessary to avoid copying large files on disk. To activate the developer mode, follow `these instructions <https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development>`_. In summary:

- Enter “for developers” into the search box in the taskbar to go to the “For developers” settings page.

- Toggle the Developer Mode setting, at the top of the “For developers” page.

- Read the disclaimer for the setting you choose. Click “Yes” to accept the change.

Install QGIS and GDAL on Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install QGIS and GDAL on Windows, use the `OSGeo4W <https://trac.osgeo.org/osgeo4w/>`_ network installer. OSGeo4W is a binary distribution of a broad set of open source geospatial software for Windows environments (Windows 11 down to 7). Select *Express Install* and install both QGIS and GDAL. Several Gb of space will be needed on disk to install these programs. This will also install *OSGeo4W Shell* to execute command lines.

Install the ``forestatrisk`` and ``riskmapjnr`` Python packages on Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install the ``forestatrisk`` and ``riskmapjnr`` Python packages, open *OSGeo4W Shell*, upgrade ``pip`` and ``setuptools``, and install ``forestatrisk`` and ``riskmapjnr`` with ``pip``.

.. code:: shell

    python3.exe -m pip install --upgrade pip setuptools
    python3.exe -m pip install forestatrisk riskmapjnr

Note: In case of problems, you can check the version of Python used by OSGeo4W using *OSGeo Shell* and that the package wheels for ``forestatrisk`` and ``riskmapjnr`` are available on `PyPI <https://pypi.org/project/forestatrisk/#files>`_ for your Windows and Python versions. Currently, PyPI provides wheels for Python 3.9 to 3.11 for Windows, Linux, and macOS 64-bit systems.

.. code:: shell

    python3.exe --version

On Unix-like systems (Linux and macOS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install QGIS and GDAL on Unix-like systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install QGIS and GDAL on your system, for example using ``apt-get`` for Debian/Ubuntu Linux distributions.

.. code:: shell

    sudo apt-get update
    sudo apt-get install qgis gdal-bin libgdal-dev

After installing GDAL, you can test the installation by running ``gdalinfo --version`` in the command prompt or terminal, which should display the installed GDAL version.

Install the ``forestatrisk`` and ``riskmapjnr`` Python packages on Unix-like systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On recent systems, you cannot use pip to install Python packages system-wide. As a consequence, we need to create a virtual environment and install the ``forestatrisk`` and ``riskmapjnr`` packages in it. Make sure to also install the appropriate GDAL bindings using ``gdal==$(gdal-config --version)``. Once the package and its dependencies have been installed, you can deactivate the virtual environment.

.. code:: shell

    python3 -m venv /path/to/venv
    source  /path/to/venv/bin/activate
    python3 -m pip install forestatrisk riskmapjnr gdal==$(gdal-config --version)
    deactivate

Then, in the ``setup.py`` `Python file <https://docs.qgis.org/3.4/en/docs/pyqgis_developer_cookbook/intro.html#running-python-code-when-qgis-starts>`_, add the following two lines, adapting the path to your specific case (check the Python version). These two lines will be executed when QGIS starts and will add the path to the packages installed in the virtual environment to ``sys.path``.

.. code:: python

    import sys
    sys.path.append("/path/to/venv/lib/python3.11/site-packages/")

Installing the ``deforisk`` plugin in QGIS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Download the ``deforisk`` `zip file <https://github.com/ghislainv/deforisk-qgis-plugin/archive/refs/heads/main.zip>`_ from GitHub.

- Open QGIS.

- In QGIS menu bar, go to ``Extensions/Install extensions/Install from ZIP``.

- Select the zip file that has been downloaded.