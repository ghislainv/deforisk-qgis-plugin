===============================
Advices for large jurisdictions
===============================


..
    This case_study.rst file is automatically generated. Please do not
    modify it. If you want to make changes to this file, modify the
    case_study.org source file directly.

Some advices for large jurisdictions
------------------------------------

It could be necessary to change the default parameters of the plugin for large jurisdictions (e.g. country scale).

1. Use a larger ``Max. distance to forest egde (m)``, e.g. **6000 m** in the ``Benchmark`` and ``MW models``.

2. If you want to save computation time and look at the most important results, only:

   - Calibrate the models on the **calibration period**, checking ``calib. period`` in the box ``Fit model to data``.

   - Predict for the **validation period**, checking ``t2 validation`` in the box ``Predict the deforestation risk``.

3. For FAR models:

   - Use a larger ``Spatial cell size (km)`` for sampling, e.g. **10 km** to avoid estimating a too large number of parameters for spatial random effects.

   - Use a larger ``Spatial cell size interpolation (km)``, e.g. **1 km**.

4. For the MW models, use only one ``Window sizes (# pixels)``, e.g. **21**. This should correspond to about 630 m for a resolution of 30 m.

5. For the validation step, use only one ``Coarse grid cell sizes (# pixels)`` and increase its size, using e.g. **300**. This should correspond to about 9 km for a resolution of 30 m.
