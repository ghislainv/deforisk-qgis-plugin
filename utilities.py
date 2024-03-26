# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""Useful functions."""


def add_layer(project, layer):
    """Add layer after removal if its name exists."""
    for lay in project.mapLayers().values():
        if lay.name() == layer.name():
            project.removeMapLayers([lay.id()])
    project.addMapLayer(layer, False)
    project.layerTreeRoot().addLayer(layer)


def add_layer_to_group(project, group, layer):
    """Add layer to group after removal if its name exists."""
    for lay in project.mapLayers().values():
        if lay.name() == layer.name():
            project.removeMapLayers([lay.id()])
    project.addMapLayer(layer, False)
    group.addLayer(layer)

# End of file
