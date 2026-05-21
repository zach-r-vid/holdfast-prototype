"""
Color utility for Panda3D models.

Panda3D's built-in models (rgbCube, sphere) have baked materials that
override set_color() when scene lighting is active. This helper clears
the baked material and sets up a proper diffuse/ambient material so
the color actually shows up under lights.
"""

from __future__ import annotations

from panda3d.core import LColor, Material, NodePath


def apply_color(node: NodePath, color: LColor) -> None:
    """Apply a visible color to a model node under lit conditions.

    Clears any baked material, creates a new material with diffuse +
    ambient set to the desired color, and also sets the flat color
    as a fallback. Works with rgbCube, sphere, and any other model.
    """
    node.clear_material()
    mat = Material()
    mat.set_diffuse(color)
    mat.set_ambient(color)
    # Slight emission so entities are visible even in shadow
    emit = LColor(color.x * 0.15, color.y * 0.15, color.z * 0.15, color.w)
    mat.set_emission(emit)
    node.set_material(mat, 1)
    node.set_color(color)


def apply_color_unlit(node: NodePath, color: LColor) -> None:
    """Apply color to a node that ignores lighting (HUD elements, overlays)."""
    node.set_light_off()
    node.set_color(color)
