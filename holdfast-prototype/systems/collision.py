"""
Collision layer management and helpers.

Uses Panda3D's built-in CollisionTraverser system with sphere-based
collision for gameplay entities. This is simpler and more controllable
than full Bullet physics for a top-down shooter.
"""

from __future__ import annotations
from typing import Callable

from panda3d.core import (
    CollisionTraverser,
    CollisionHandlerEvent,
    CollisionNode,
    CollisionSphere,
    CollisionRay,
    CollisionHandlerQueue,
    NodePath,
    BitMask32,
)

import config


class CollisionSystem:
    """Manages all collision detection and dispatching."""

    def __init__(self, base) -> None:
        self.base = base
        self.traverser = CollisionTraverser("main_traverser")
        self.handler = CollisionHandlerEvent()

        # Pattern: {from_tag}-into-{into_tag}
        self.handler.add_in_pattern("{from_tag}-into-{into_tag}")
        self.handler.add_out_pattern("{from_tag}-out-{into_tag}")

        self.base.cTrav = self.traverser
        self._callbacks: dict[str, list[Callable]] = {}

    def register_collider(
        self,
        node_path: NodePath,
        radius: float,
        from_mask: BitMask32,
        into_mask: BitMask32,
        tag: str,
    ) -> CollisionNode:
        """Attach a collision sphere to a node and register it."""
        col_node = CollisionNode(f"col_{tag}_{id(node_path)}")
        col_node.add_solid(CollisionSphere(0, 0, 0, radius))
        col_node.set_from_collide_mask(from_mask)
        col_node.set_into_collide_mask(into_mask)
        col_np = node_path.attach_new_node(col_node)
        col_np.node().set_tag("tag", tag)

        # Only add as 'from' if it has a from mask
        if from_mask != BitMask32.all_off():
            self.traverser.add_collider(col_np, self.handler)

        return col_node

    def on_collision(self, from_tag: str, into_tag: str, callback: Callable) -> None:
        """Register a callback for when from_tag collides with into_tag."""
        pattern = f"{from_tag}-into-{into_tag}"
        if pattern not in self._callbacks:
            self._callbacks[pattern] = []
            self.base.accept(pattern, self._dispatch, [pattern])
        self._callbacks[pattern].append(callback)

    def _dispatch(self, pattern: str, entry) -> None:
        """Dispatch collision event to registered callbacks."""
        for cb in self._callbacks.get(pattern, []):
            cb(entry)

    def remove_collider(self, node_path: NodePath) -> None:
        """Remove a collider from the traverser."""
        for child in node_path.get_children():
            if isinstance(child.node(), CollisionNode):
                self.traverser.remove_collider(child)
                child.remove_node()
                break
