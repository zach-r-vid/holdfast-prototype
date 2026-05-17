"""
Object pool for projectiles.

A bullet hell can spawn hundreds of projectiles per second.
Allocating and deallocating nodes every frame is expensive.
This pool pre-allocates projectile nodes and recycles them.
"""

from __future__ import annotations
from typing import Optional
from collections import deque

from panda3d.core import NodePath, LVector3f, LColor
from direct.showbase.ShowBase import ShowBase

import config


class Projectile:
    """A single pooled projectile with physics state."""

    __slots__ = (
        "node", "velocity", "mass", "drag", "damage",
        "lifetime", "age", "radius", "alive", "owner_tag",
        "col_node", "light_np",
    )

    def __init__(self, node: NodePath) -> None:
        self.node = node
        self.velocity = LVector3f(0, 0, 0)
        self.mass: float = 1.0
        self.drag: float = 0.01
        self.damage: float = 10
        self.lifetime: float = 2.5
        self.age: float = 0.0
        self.radius: float = 0.15
        self.alive: bool = False
        self.owner_tag: str = "player_bullet"
        self.col_node = None
        self.light_np: Optional[NodePath] = None

    def activate(
        self,
        position: LVector3f,
        velocity: LVector3f,
        damage: float,
        mass: float,
        drag: float,
        lifetime: float,
        radius: float,
        color: LColor,
        owner_tag: str,
    ) -> None:
        """Wake this projectile up from the pool."""
        self.velocity = LVector3f(velocity)
        self.damage = damage
        self.mass = mass
        self.drag = drag
        self.lifetime = lifetime
        self.age = 0.0
        self.radius = radius
        self.alive = True
        self.owner_tag = owner_tag

        self.node.set_pos(position)
        self.node.set_scale(radius * 2)
        self.node.set_color(color)
        self.node.show()

    def deactivate(self) -> None:
        """Return this projectile to the pool."""
        self.alive = False
        self.node.hide()
        self.velocity = LVector3f(0, 0, 0)

    def apply_force(self, force: LVector3f, dt: float) -> None:
        """Apply a force (like gravity well pull) for one timestep."""
        acceleration = force / max(self.mass, 0.01)
        self.velocity += acceleration * dt

    def update(self, dt: float) -> bool:
        """
        Step physics forward. Returns False if projectile should despawn.
        """
        if not self.alive:
            return False

        self.age += dt
        if self.age >= self.lifetime:
            return False

        # Apply drag
        self.velocity *= (1.0 - self.drag)

        # Integrate position
        pos = self.node.get_pos()
        pos += self.velocity * dt
        self.node.set_pos(pos)

        # Bounds check
        half_w = config.ARENA_WIDTH / 2 + 5
        half_h = config.ARENA_HEIGHT / 2 + 5
        if abs(pos.x) > half_w or abs(pos.y) > half_h:
            return False

        return True


class ProjectilePool:
    """Pre-allocated pool of reusable projectile objects."""

    def __init__(self, parent: NodePath, base: ShowBase) -> None:
        self.parent = parent
        self.base = base
        self._pool: deque[Projectile] = deque()
        self._active: list[Projectile] = []
        self._bullet_model: Optional[NodePath] = None

        self._create_bullet_model()
        self._grow(config.POOL_INITIAL_SIZE)

    def _create_bullet_model(self) -> None:
        """Create a simple sphere model to instance for all bullets."""
        from panda3d.core import GeomNode
        # Use a simple sphere as the bullet visual
        self._bullet_model = self.base.loader.load_model("models/misc/sphere")
        if self._bullet_model is None:
            # Fallback: create a tiny node (will be scaled)
            self._bullet_model = NodePath("bullet_template")

    def _grow(self, count: int) -> None:
        """Allocate more projectiles into the pool."""
        total = len(self._pool) + len(self._active) + count
        if total > config.POOL_MAX_SIZE:
            count = config.POOL_MAX_SIZE - len(self._pool) - len(self._active)
            if count <= 0:
                return

        for _ in range(count):
            node = self._bullet_model.copy_to(self.parent)
            node.hide()
            node.set_light_off()  # Bullets emit light, don't receive it
            proj = Projectile(node)
            self._pool.append(proj)

    def acquire(
        self,
        position: LVector3f,
        velocity: LVector3f,
        damage: float = 10,
        mass: float = 0.3,
        drag: float = 0.01,
        lifetime: float = 2.5,
        radius: float = 0.15,
        color: LColor = LColor(1, 1, 1, 1),
        owner_tag: str = "player_bullet",
    ) -> Optional[Projectile]:
        """Get a projectile from the pool, activate it, and return it."""
        if not self._pool:
            self._grow(config.POOL_GROW_STEP)
        if not self._pool:
            return None  # Hard cap reached

        proj = self._pool.popleft()
        proj.activate(position, velocity, damage, mass, drag, lifetime, radius, color, owner_tag)
        self._active.append(proj)
        return proj

    def update(self, dt: float) -> None:
        """Update all active projectiles. Return dead ones to pool."""
        still_active = []
        for proj in self._active:
            if proj.update(dt):
                still_active.append(proj)
            else:
                proj.deactivate()
                self._pool.append(proj)
        self._active = still_active

    def kill(self, proj: Projectile) -> None:
        """Immediately deactivate a specific projectile."""
        if proj.alive:
            proj.deactivate()
            if proj in self._active:
                self._active.remove(proj)
            self._pool.append(proj)

    def get_active(self) -> list[Projectile]:
        """Return list of currently active projectiles."""
        return self._active

    def get_active_by_tag(self, tag: str) -> list[Projectile]:
        """Return active projectiles matching a specific owner tag."""
        return [p for p in self._active if p.owner_tag == tag]

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def pool_count(self) -> int:
        return len(self._pool)

    def clear_all(self) -> None:
        """Deactivate everything. Used on wave clear / reset."""
        for proj in self._active:
            proj.deactivate()
            self._pool.append(proj)
        self._active.clear()
