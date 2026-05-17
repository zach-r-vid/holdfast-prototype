"""
HOLDFAST — Main Entry Point
============================
Twin-stick shooter × tower defense prototype.

Run with: python main.py

Controls:
  WASD        — Move
  Mouse       — Aim
  Left Click  — Shoot
  Right Click / Shift — Dash
  E           — Enter/exit tower
  Tab         — Toggle build menu
  1/2/3       — Select tower type (when menu open)
  Enter       — Start next wave
  Escape      — Quit
"""

from __future__ import annotations
import sys

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    LVector3f, LPoint3f, LColor,
    WindowProperties, loadPrcFileData,
    AntialiasAttrib,
)

import config
from player.controller import PlayerController
from player.movement import PlayerMovement
from player.dash import DashSystem
from player.shooting import ShootingSystem
from projectiles.pool import ProjectilePool
from environment.arena import Arena
from environment.pathfinding import PathGrid
from environment.gravity_well import GravityWell, GravityWellManager
from enemies.spawner import EnemySpawner
from towers.placement import TowerPlacement
from towers.manning import ManningSystem
from systems.wave_manager import WaveManager, GamePhase
from systems.economy import Economy
from systems.camera import CameraSystem
from systems.collision import CollisionSystem
from ui.hud import HUD
from ui.tower_menu import TowerMenu


# ─── Panda3D config ──────────────────────────────────────────────
loadPrcFileData("", f"win-size {config.WINDOW_WIDTH} {config.WINDOW_HEIGHT}")
loadPrcFileData("", f"window-title {config.WINDOW_TITLE}")
loadPrcFileData("", "sync-video #f")
loadPrcFileData("", "show-frame-rate-meter #t")
loadPrcFileData("", "framebuffer-multisample 1")
loadPrcFileData("", "multisamples 4")


class HoldfastGame(ShowBase):
    """Main game class. Owns all systems and runs the game loop."""

    def __init__(self) -> None:
        super().__init__()
        self.setBackgroundColor(0.02, 0.02, 0.05, 1.0)
        self.render.set_antialias(AntialiasAttrib.M_auto)

        # ── Player HP state ──
        self.player_hp = config.PLAYER_MAX_HP
        self.player_invuln_timer: float = 0.0

        # ── Initialize systems (order matters) ──
        self._init_arena()
        self._init_player()
        self._init_projectiles()
        self._init_economy()
        self._init_pathfinding()
        self._init_gravity_wells()
        self._init_enemies()
        self._init_towers()
        self._init_wave_manager()
        self._init_camera()
        self._init_collision()
        self._init_ui()

        # ── Key bindings ──
        self.accept("escape", sys.exit)

        # ── Start game loop ──
        self.taskMgr.add(self._game_loop, "game_loop")

        print("\n" + "=" * 50)
        print("  HOLDFAST — Prototype")
        print("=" * 50)
        print("  WASD: Move | Mouse: Aim | Click: Shoot")
        print("  Shift: Dash | E: Man Tower | Tab: Build Menu")
        print("  Enter: Start Wave | Escape: Quit")
        print("=" * 50 + "\n")

    # ─── System Initialization ───────────────────────────────────

    def _init_arena(self) -> None:
        self.arena = Arena(self)
        self.arena.show_grid()

    def _init_player(self) -> None:
        # Create player node (simple colored sphere)
        self.player_node = self.render.attach_new_node("player")
        player_model = self.loader.load_model("models/misc/sphere")
        if player_model:
            player_model.reparent_to(self.player_node)
            player_model.set_scale(0.5)
            player_model.set_color(config.COLOR_PLAYER)
        self.player_node.set_pos(0, -8, 0)

        # Aim indicator (small sphere in front of player)
        self.aim_indicator = self.render.attach_new_node("aim_indicator")
        aim_model = self.loader.load_model("models/misc/sphere")
        if aim_model:
            aim_model.reparent_to(self.aim_indicator)
            aim_model.set_scale(0.15)
            aim_model.set_color(LColor(1, 1, 1, 0.6))

        self.controller = PlayerController(self)
        self.movement = PlayerMovement(self.player_node)
        self.dash = DashSystem(self.movement)

    def _init_projectiles(self) -> None:
        self.projectile_parent = self.render.attach_new_node("projectiles")
        self.projectile_pool = ProjectilePool(self.projectile_parent, self)

    def _init_economy(self) -> None:
        self.economy = Economy()

    def _init_pathfinding(self) -> None:
        self.path_grid = PathGrid()

    def _init_gravity_wells(self) -> None:
        self.gravity_manager = GravityWellManager()

        # Place one gravity well in the arena for testing
        well = GravityWell(
            self,
            self.render,
            position=LVector3f(8, 3, 0),
        )
        self.gravity_manager.add(well)

    def _init_enemies(self) -> None:
        self.enemy_parent = self.render.attach_new_node("enemies")
        self.spawner = EnemySpawner(
            self,
            self.enemy_parent,
            self.path_grid,
            self.projectile_pool,
            self.player_node,
        )

    def _init_towers(self) -> None:
        self.tower_parent = self.render.attach_new_node("towers")
        self.tower_placement = TowerPlacement(
            self,
            self.tower_parent,
            self.path_grid,
            self.economy,
        )
        self.shooting = ShootingSystem(self.movement, self.projectile_pool)
        self.manning = ManningSystem(self.movement, self.shooting, self.tower_placement)

    def _init_wave_manager(self) -> None:
        self.wave_manager = WaveManager()

        self.wave_manager.on_phase_change(self._on_phase_change)
        self.wave_manager.on_wave_start(self._on_wave_start)
        self.wave_manager.on_wave_complete(self._on_wave_complete)

    def _init_camera(self) -> None:
        self.camera_system = CameraSystem(self)
        self.camera_system.set_follow_target(self.player_node)

    def _init_collision(self) -> None:
        self.collision_system = CollisionSystem(self)
        # Collision detection is handled via distance checks in update
        # for the prototype. Production would use proper collision nodes.

    def _init_ui(self) -> None:
        self.hud = HUD(self)
        self.tower_menu = TowerMenu(self, self._on_tower_selected)
        self.hud.show_banner("HOLDFAST\nPress ENTER to start", 5.0)

    # ─── Event Callbacks ─────────────────────────────────────────

    def _on_phase_change(self, phase: GamePhase) -> None:
        """Handle game phase transitions."""
        if phase == GamePhase.PLANNING:
            self.arena.show_grid()
        elif phase == GamePhase.ACTION:
            self.arena.hide_grid()
            self.tower_menu.hide()
        elif phase == GamePhase.GAME_OVER:
            self.hud.show_banner("GAME OVER", 999)

    def _on_wave_start(self, wave_number: int) -> None:
        """Start spawning enemies for the wave."""
        self.spawner.start_wave(wave_number - 1)  # 0-indexed
        self.hud.show_banner(f"WAVE {wave_number}", 2.0)

    def _on_wave_complete(self, wave_number: int) -> None:
        """Wave finished — award bonus."""
        bonus = self.economy.on_wave_complete()
        self.hud.show_banner(f"WAVE {wave_number} CLEAR!\n+${bonus}", 2.5)

    def _on_tower_selected(self, tower_type: str) -> None:
        """Tower type chosen from build menu."""
        if self.tower_placement.select_tower_type(tower_type):
            self.hud.show_banner(f"Click to place {tower_type.upper()}", 1.5)

    # ─── Main Game Loop ──────────────────────────────────────────

    def _game_loop(self, task):
        """Called every frame. Orchestrates all systems."""
        dt = globalClock.getDt()  # noqa: F821
        dt = min(dt, 1.0 / 30.0)  # Cap delta time to prevent spiral

        # ── Input ──
        input_state = self.controller.get_input()

        # ── Phase-specific input ──
        if input_state.next_wave_pressed and self.wave_manager.is_planning:
            self.wave_manager.try_start_wave()

        if input_state.tower_menu_toggle and self.wave_manager.is_planning:
            self.tower_menu.toggle()

        if input_state.interact_pressed:
            self.manning.try_toggle()

        # ── Tower placement (during planning) ──
        if self.wave_manager.is_planning and self.tower_placement.selected_type:
            self.tower_placement.update_preview(input_state.aim_world_pos)
            if input_state.shooting:
                placed = self.tower_placement.try_place(input_state.aim_world_pos)
                if placed:
                    self.camera_system.add_shake(0.1)

        # ── Player systems (always update for responsiveness) ──
        if not self.manning.is_manned:
            self.movement.update(input_state, dt)
        self.dash.update(input_state, dt)

        # Only shoot during action phase (or when manned)
        if self.wave_manager.is_action or self.manning.is_manned:
            if not (self.wave_manager.is_planning and self.tower_placement.selected_type):
                self.shooting.update(input_state, dt)

        # ── Update aim indicator ──
        aim_pos = self.movement.get_position() + self.movement.get_facing() * 1.5
        self.aim_indicator.set_pos(aim_pos)

        # ── Manning check ──
        self.manning.update()
        self.camera_system.set_manned(self.manning.is_manned)

        # ── Projectile physics ──
        self.projectile_pool.update(dt)
        self.gravity_manager.update(self.projectile_pool, dt)

        # ── Enemy spawning and movement ──
        self.spawner.update(dt, self.gravity_manager)

        # ── Tower targeting and firing ──
        self.tower_placement.update(
            dt,
            self.spawner.enemies,
            self.projectile_pool,
        )

        # ── Collision checks (distance-based for prototype) ──
        self._check_collisions(dt)

        # ── Process dead enemies and core damage ──
        self._process_enemy_results()

        # ── Wave state ──
        self.wave_manager.update(
            dt,
            wave_complete=self.spawner.is_wave_complete(),
            core_alive=self.arena.is_core_alive(),
        )

        # ── Camera ──
        self.camera_system.update(dt, self.spawner.active_count)

        # ── Player invulnerability ──
        if self.player_invuln_timer > 0:
            self.player_invuln_timer -= dt
            # Blink player model
            visible = int(self.player_invuln_timer * 10) % 2 == 0
            if visible:
                self.player_node.show()
            else:
                self.player_node.hide()
        else:
            self.player_node.show()

        # ── HUD ──
        self.hud.update(
            dt=dt,
            wave_number=self.wave_manager.wave_number,
            phase_name=self.wave_manager.phase.name,
            currency=self.economy.currency,
            player_hp=self.player_hp,
            player_max_hp=config.PLAYER_MAX_HP,
            weapon_name=self.shooting.current_weapon["name"],
            ammo_display=self.shooting.ammo_display,
            dash_fraction=self.dash.cooldown_fraction,
            core_hp=self.arena.core_hp,
            enemy_count=self.spawner.active_count,
        )

        return task.cont

    # ─── Collision Detection ─────────────────────────────────────

    def _check_collisions(self, dt: float) -> None:
        """
        Distance-based collision checks. In production, use proper
        collision nodes / physics engine. For prototype, this is
        fast enough and much simpler to debug.
        """
        player_pos = self.movement.get_position()
        is_invuln = self.player_invuln_timer > 0 or self.dash.is_invincible

        # Player bullets → enemies
        for proj in self.projectile_pool.get_active_by_tag("player_bullet"):
            proj_pos = proj.node.get_pos()
            for enemy in self.spawner.enemies:
                if not enemy.alive:
                    continue
                dist = (proj_pos - enemy.get_position()).length()
                if dist < proj.radius + enemy.radius:
                    enemy.take_damage(proj.damage)
                    self.projectile_pool.kill(proj)
                    if not enemy.alive:
                        self.economy.on_enemy_killed(enemy.reward, killed_by_player=True)
                    break

        # Tower bullets → enemies
        for proj in self.projectile_pool.get_active_by_tag("tower_bullet"):
            proj_pos = proj.node.get_pos()
            for enemy in self.spawner.enemies:
                if not enemy.alive:
                    continue
                dist = (proj_pos - enemy.get_position()).length()
                if dist < proj.radius + enemy.radius:
                    enemy.take_damage(proj.damage)
                    self.projectile_pool.kill(proj)
                    if not enemy.alive:
                        self.economy.on_enemy_killed(enemy.reward, killed_by_player=False)
                    break

        # Enemy bullets → player
        if not is_invuln:
            for proj in self.projectile_pool.get_active_by_tag("enemy_bullet"):
                proj_pos = proj.node.get_pos()
                dist = (proj_pos - player_pos).length()
                if dist < proj.radius + 0.5:
                    self._player_take_damage(proj.damage)
                    self.projectile_pool.kill(proj)
                    break

        # Enemies → player (contact damage)
        if not is_invuln:
            for enemy in self.spawner.enemies:
                if not enemy.alive:
                    continue
                dist = (enemy.get_position() - player_pos).length()
                if dist < enemy.radius + 0.5:
                    self._player_take_damage(10)
                    break

    def _player_take_damage(self, amount: float) -> None:
        """Handle player taking damage."""
        if self.player_invuln_timer > 0 or self.dash.is_invincible:
            return

        self.player_hp -= int(amount)
        self.player_invuln_timer = config.PLAYER_INVULN_AFTER_HIT
        self.camera_system.add_shake(0.4)

        if self.player_hp <= 0:
            self.player_hp = 0
            # Player death — for prototype, just end the game
            self.arena.core_hp = 0  # Trigger game over

    def _process_enemy_results(self) -> None:
        """Handle enemies that reached the core or died."""
        # Core damage from enemies that got through
        for enemy in self.spawner.get_reached_core():
            self.arena.damage_core(enemy.damage_to_core)
            self.camera_system.add_shake(0.2)

        # Cleanup
        self.spawner.cleanup_dead()


# ─── Entry Point ─────────────────────────────────────────────────

if __name__ == "__main__":
    game = HoldfastGame()
    game.run()
