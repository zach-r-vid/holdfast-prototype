"""
Slug — slow, tanky enemy that leaves damaging slime trails.

Creates area denial: the inverse of what towers do to enemies.
Slime damages and slows the player but does not affect towers.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
import config
from utils.color import apply_color

if TYPE_CHECKING:
    from environment.gravity_well import GravityWellManager


class SlimeNode:
    """A persistent ground hazard left by slugs."""

    __slots__ = ("node", "timer", "radius", "damage", "slow_factor", "alive")

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        position: LVector3f,
        duration: float,
        radius: float,
        damage: float,
        slow_factor: float,
    ) -> None:
        self.radius = radius
        self.damage = damage
        self.slow_factor = slow_factor
        self.timer = duration
        self.alive = True

        self.node = parent.attach_new_node(f"slime_{id(self)}")
        self.node.set_pos(position)

        model = base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            model.set_scale(radius, radius, 0.05)
            apply_color(model, LColor(0.2, 0.7, 0.0, 0.4))
            model.set_transparency(TransparencyAttrib.M_alpha)
            model.set_pos(0, 0, 0.03)

    def update(self, dt: float) -> bool:
        """Returns False when expired."""
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False
            self.node.remove_node()
            return False
        alpha = min(0.4, self.timer / 2.0)
        self.node.set_color_scale(1, 1, 1, alpha)
        return True

    def cleanup(self) -> None:
        if self.alive:
            self.node.remove_node()
            self.alive = False


class Slug(BaseEnemy):
    """Very slow, very tough. Leaves slime behind as it walks."""

    def __init__(self, base: ShowBase, parent: NodePath, spawn_pos: LVector3f) -> None:
        super().__init__(base, parent, config.SLUG_STATS, spawn_pos)
        self._slime_timer: float = 0.0
        self._slime_parent = parent
        self.slime_nodes: list[SlimeNode] = []

    def _build_visual(self, stats: dict) -> None:
        """Wide, flat rectangle — reads as a heavy crawling slab."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            model.set_scale(self.radius * 1.0, self.radius * 1.4, self.radius * 0.4)
            model.set_pos(0, 0, self.radius * 0.2)
            apply_color(model, stats.get("color", LColor(0.3, 0.8, 0.1, 1)))

        # Darker dorsal stripe
        stripe = self.base.loader.load_model("models/misc/rgbCube")
        if stripe:
            stripe.reparent_to(self.node)
            stripe.set_scale(self.radius * 0.4, self.radius * 1.2, self.radius * 0.5)
            stripe.set_pos(0, 0, self.radius * 0.35)
            apply_color(stripe, LColor(0.15, 0.5, 0.05, 1))

    def update(self, dt: float, gravity_wells=None) -> None:
        super().update(dt, gravity_wells)

        if not self.alive:
            return

        self._slime_timer -= dt
        if self._slime_timer <= 0:
            self._slime_timer = self.stats["slime_interval"]
            self._drop_slime()

        still_alive = []
        for slime in self.slime_nodes:
            if slime.update(dt):
                still_alive.append(slime)
        self.slime_nodes = still_alive

    def _drop_slime(self) -> None:
        pos = self.node.get_pos()
        slime = SlimeNode(
            self.base,
            self._slime_parent,
            LVector3f(pos),
            duration=self.stats["slime_duration"],
            radius=self.stats["slime_radius"],
            damage=self.stats["slime_damage"],
            slow_factor=self.stats["slime_slow_factor"],
        )
        self.slime_nodes.append(slime)

    def cleanup(self) -> None:
        for slime in self.slime_nodes:
            slime.cleanup()
        self.slime_nodes.clear()
        super().cleanup()
