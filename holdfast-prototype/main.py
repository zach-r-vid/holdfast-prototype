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
  X           — Toggle sell mode (click near tower to sell)
  Enter       — Start next wave
  Escape      — Pause (Resume / Restart / Quit)
  `           — Toggle debug mode (K:Kill all, Shift+N:Skip, Shift+R:Restart wave)
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
from enemies.slug import Slug
from enemies.hunter import Hunter
from towers.placement import TowerPlacement
from towers.manning import ManningSystem
from towers.mortar import Mortar
from towers.arc_preview import ArcPreview
from systems.wave_manager import WaveManager, GamePhase
from systems.economy import Economy
from systems.camera import CameraSystem
from systems.collision import CollisionSystem
from systems.crystals import CrystalManager
from systems.power_meter import PowerMeter, PowerAbility
from systems.debug import DebugSystem
from ui.hud import HUD
from ui.tower_menu import TowerMenu
from ui.pause_menu import PauseMenu
from ui.dev_menu import DevMenu
from utils.color import apply_color


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
        self.paused: bool = False

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
        self._init_crystals()
        self._init_ui()

        self._init_debug()

        # ── Key bindings ──
        self.accept("escape", self._toggle_pause)
        self.accept("`", self._toggle_debug_or_dev_menu)

        # ── Start game loop ──
        self.taskMgr.add(self._game_loop, "game_loop")

        print("\n" + "=" * 50)
        print("  HOLDFAST — Prototype")
        print("=" * 50)
        print("  WASD: Move | Mouse: Aim | Click: Shoot")
        print("  Shift: Dash | 1-4: Weapon/Tower | Scroll: Zoom")
        print("  E: Man Tower | Tab: Build Menu | X: Sell")
        print("  F: Activate Power | R: Cycle Power | G: Grav Well")
        print("  Enter: Start Wave | Esc: Pause | `: Debug")
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
            apply_color(player_model, config.COLOR_PLAYER)
        self.player_node.set_pos(0, -8, 0)

        # Aim indicator (small sphere in front of player)
        self.aim_indicator = self.render.attach_new_node("aim_indicator")
        aim_model = self.loader.load_model("models/misc/sphere")
        if aim_model:
            aim_model.reparent_to(self.aim_indicator)
            aim_model.set_scale(0.15)
            apply_color(aim_model, LColor(1, 1, 1, 0.6))

        self.controller = PlayerController(self)
        self.movement = PlayerMovement(self.player_node)
        self.movement._path_grid = None  # Set after pathfinding init
        self.dash = DashSystem(self.movement)

        # Dash-ready glow light
        from panda3d.core import PointLight
        dash_light = PointLight("dash_ready_light")
        dash_light.set_color(LColor(0.3, 0.6, 1.0, 1.0))
        dash_light.set_attenuation((1, 0.5, 0.2))
        self.dash_light_np = self.player_node.attach_new_node(dash_light)
        self.render.set_light(self.dash_light_np)
        self.dash_light_np.hide()

        # Dash afterimages
        self._dash_afterimages: list[tuple[NodePath, float]] = []

    def _init_projectiles(self) -> None:
        self.projectile_parent = self.render.attach_new_node("projectiles")
        self.projectile_pool = ProjectilePool(self.projectile_parent, self)

    def _init_economy(self) -> None:
        self.economy = Economy()

    def _init_pathfinding(self) -> None:
        self.path_grid = PathGrid()
        self.movement._path_grid = self.path_grid

    def _init_gravity_wells(self) -> None:
        self.gravity_manager = GravityWellManager()

        if not config.GRAVITY_WELLS_ENABLED:
            return

        # Place one gravity well in the arena for testing
        well = GravityWell(
            self,
            self.render,
            position=LVector3f(1, 2, 0),  # Near center lane path
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
        self.arc_preview = ArcPreview(self, self.render)

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

    def _init_crystals(self) -> None:
        self.crystal_parent = self.render.attach_new_node("crystals")
        self.crystal_manager = CrystalManager(self, self.crystal_parent)
        self.power_meter = PowerMeter()
        self.shooting._power_meter = self.power_meter

    def _init_ui(self) -> None:
        self.hud = HUD(self)
        self.tower_menu = TowerMenu(self, self._on_tower_selected)
        self.pause_menu = PauseMenu(
            self,
            on_resume=self._resume,
            on_restart=self._restart,
            on_quit=sys.exit,
        )
        self.hud.show_banner("HOLDFAST\nPress ENTER to start", 5.0)

    def _init_debug(self) -> None:
        self.debug = DebugSystem(
            self, self.economy, self.wave_manager,
            self.spawner, self.projectile_pool,
        )
        self.dev_menu = DevMenu(self)

    # ─── Pause / Restart ─────────────────────────────────────────

    def _toggle_pause(self) -> None:
        if self.paused:
            self._resume()
        else:
            self.paused = True
            self.pause_menu.show()

    def _toggle_debug_or_dev_menu(self) -> None:
        """Backtick key: first press enables debug, second toggles dev menu."""
        if not self.debug.active:
            self.debug.toggle()
        elif self.dev_menu.visible:
            self.dev_menu.hide()
            self.paused = False
        else:
            self.dev_menu.show()
            self.paused = True

    def _resume(self) -> None:
        self.paused = False
        self.pause_menu.hide()

    def _restart(self) -> None:
        """Reset all game state to initial values."""
        self.paused = False
        self.pause_menu.hide()

        # Clear entities
        self.spawner.clear_all()
        self.projectile_pool.clear_all()

        # Remove all towers and unblock grid
        for tower in list(self.tower_placement.towers):
            self.tower_placement.sell_tower(tower)
        self.tower_placement.cancel_selection()
        self.tower_placement.sell_mode = False
        self.tower_placement._clear_sell_highlight()

        # Reset path grid
        self.path_grid._path_cache.clear()

        # Reset economy
        self.economy.currency = config.STARTING_CURRENCY
        self.economy.total_earned = config.STARTING_CURRENCY
        self.economy.total_spent = 0

        # Reset player
        self.player_hp = config.PLAYER_MAX_HP
        self.player_invuln_timer = 0.0
        self.player_node.set_pos(0, -8, 0)
        self.player_node.show()
        self.movement.velocity = LVector3f(0, 0, 0)

        # Reset manning
        if self.manning.is_manned:
            self.manning.try_toggle()
        self.arc_preview.hide()

        # Reset arena core
        self.arena.core_hp = 500
        if self.arena.core_node:
            apply_color(self.arena.core_node, config.COLOR_CORE)

        # Reset wave manager
        self.wave_manager.phase = GamePhase.PLANNING
        self.wave_manager.wave_number = 0
        self.wave_manager.planning_timer = 0.0

        # Reset crystals and power
        self.crystal_manager.clear_all()
        self.power_meter.reset()

        # Reset shooting
        self.shooting.weapons = [
            dict(config.DEFAULT_WEAPON),
            dict(config.SHOTGUN_WEAPON),
            dict(config.SMG_WEAPON),
            dict(config.NOVA_WEAPON),
        ]
        self.shooting.weapon_index = 0
        self.shooting.current_weapon = self.shooting.weapons[0]

        # UI
        self.arena.show_grid()
        self.tower_menu.hide()
        self.dev_menu.hide()
        self.hud.show_banner("HOLDFAST\nPress ENTER to start", 5.0)

    # ─── Event Callbacks ─────────────────────────────────────────

    def _on_phase_change(self, phase: GamePhase) -> None:
        """Handle game phase transitions."""
        if phase == GamePhase.PLANNING:
            self.arena.show_grid()
        elif phase == GamePhase.ACTION:
            self.arena.hide_grid()
            self.tower_menu.hide()
            self.tower_placement.sell_mode = False
            self.tower_placement._clear_sell_highlight()
            self.tower_placement.cancel_selection()
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

        if self.paused:
            return task.cont

        # ── Input ──
        input_state = self.controller.get_input()

        # ── Camera zoom (scroll wheel) ──
        if input_state.scroll_zoom != 0:
            self.camera_system.scroll_zoom(input_state.scroll_zoom)

        # ── Phase-specific input ──
        if input_state.next_wave_pressed and self.wave_manager.is_planning:
            self.wave_manager.try_start_wave()

        if input_state.tower_menu_toggle and self.wave_manager.is_planning:
            self.tower_menu.toggle()

        if input_state.interact_pressed:
            self.manning.try_toggle()

        if input_state.sell_mode_toggle and self.wave_manager.is_planning:
            self.tower_placement.toggle_sell_mode()
            if self.tower_placement.sell_mode:
                self.hud.show_banner("SELL MODE — Click a tower", 1.5)

        # Power-up controls
        if input_state.power_cycle:
            self.power_meter.cycle_ability()
            name = "SUPER SHOT" if self.power_meter.selected == PowerAbility.SUPER_SHOT else "BOMB"
            self.hud.show_banner(f"Power: {name}", 1.0)

        # Gravity well activation
        if input_state.gravity_activate:
            if self.gravity_manager.try_activate_nearest(self.movement.get_position()):
                self.hud.show_banner("GRAVITY SURGE!", 1.5)
                self.camera_system.add_shake(0.5)

        if input_state.power_activate:
            ability = self.power_meter.try_activate()
            if ability == PowerAbility.SUPER_SHOT:
                self.hud.show_banner("SUPER SHOT!", 1.5)
                self.camera_system.add_shake(0.3)
            elif ability == PowerAbility.BOMB:
                self._detonate_bomb()
                self.hud.show_banner("BOMB!", 2.0)

        # ── Tower selling (during planning) ──
        if self.wave_manager.is_planning and self.tower_placement.sell_mode:
            self.tower_placement.update_sell_preview(input_state.aim_world_pos)
            if input_state.shooting:
                refund = self.tower_placement.try_sell_at(input_state.aim_world_pos)
                if refund is not None:
                    self.hud.show_banner(f"SOLD +${refund}", 1.5)
                    self.camera_system.add_shake(0.1)

        # ── Tower placement (during planning) ──
        elif self.wave_manager.is_planning and self.tower_placement.selected_type:
            self.tower_placement.update_preview(input_state.aim_world_pos)
            if input_state.shooting:
                placed = self.tower_placement.try_place(input_state.aim_world_pos)
                if placed:
                    self.camera_system.add_shake(0.1)

        # ── Player systems (always update for responsiveness) ──
        if not self.manning.is_manned:
            self.movement.update(input_state, dt)
        else:
            self.movement.update_facing_only(input_state)
        self.dash.update(input_state, dt)

        # Weapon cycling (Q key)
        if input_state.weapon_cycle != 0:
            self.shooting.cycle_weapon(input_state.weapon_cycle)
            self.hud.show_banner(
                f"[{self.shooting.weapon_index + 1}] {self.shooting.current_weapon['name']}",
                1.0,
            )

        # Number keys — tower select when build menu open, weapon select otherwise
        if input_state.number_key > 0:
            if self.tower_menu.visible:
                if input_state.number_key == 5:
                    # Repair option
                    self._try_repair()
                else:
                    self.tower_menu.select_by_number(input_state.number_key)
            else:
                if self.shooting.select_weapon(input_state.number_key - 1):
                    self.hud.show_banner(
                        f"[{self.shooting.weapon_index + 1}] {self.shooting.current_weapon['name']}",
                        1.0,
                    )

        # Only shoot during action phase (or when manned)
        manned_mortar = self._get_manned_mortar()
        if self.wave_manager.is_action or self.manning.is_manned:
            if not (self.wave_manager.is_planning and self.tower_placement.selected_type):
                if manned_mortar:
                    self._update_manned_mortar(input_state, dt, manned_mortar)
                else:
                    self.shooting.update(input_state, dt)

        # ── Arc preview ──
        if manned_mortar:
            self._update_arc_preview(input_state, manned_mortar)
        else:
            self.arc_preview.hide()

        # ── Update aim indicator ──
        aim_pos = self.movement.get_position() + self.movement.get_facing() * 1.5
        self.aim_indicator.set_pos(aim_pos)

        # ── Manning check ──
        self.manning.update()
        self.camera_system.set_manned(self.manning.is_manned)

        # ── Arc projectile splash impacts (before pool update deactivates them) ──
        self._check_arc_impacts(dt)

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

        # ── Gravity well player pull & DPS ──
        grav_player_force = self.gravity_manager.get_player_force(
            self.movement.get_position(), dt
        )
        if grav_player_force.length_squared() > 0.01 and not self.manning.is_manned:
            self.movement.velocity += grav_player_force * dt

        grav_player_dps = self.gravity_manager.get_player_dps_at(
            self.movement.get_position()
        )
        if grav_player_dps > 0 and self.player_invuln_timer <= 0:
            self._player_take_damage(grav_player_dps * dt)

        # ── Gravity well enemy DPS ──
        for enemy in self.spawner.enemies:
            if not enemy.alive:
                continue
            dps = self.gravity_manager.get_enemy_dps_at(enemy.get_position())
            if dps > 0:
                enemy.take_damage(dps * dt)
                if not enemy.alive:
                    self.economy.on_enemy_killed(enemy.reward, killed_by_player=False)

        # ── Collision checks (distance-based for prototype) ──
        self._check_collisions(dt)

        # ── Process dead enemies and core damage ──
        self._process_enemy_results()

        # ── Crystals & power meter ──
        player_pos = self.movement.get_position()
        power_collected, health_collected = self.crystal_manager.update(dt, player_pos)
        if power_collected > 0:
            self.power_meter.add_crystals(power_collected)
        if health_collected > 0:
            heal = health_collected * config.HEALTH_CRYSTAL_RESTORE
            self.player_hp = min(self.player_hp + heal, config.PLAYER_MAX_HP)
        self.power_meter.update(dt)

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

        # ── Dash visual feedback ──
        if self.dash.can_dash:
            self.dash_light_np.show()
        else:
            self.dash_light_np.hide()

        # Spawn afterimage during dash
        if self.dash.is_dashing:
            ghost = self.loader.load_model("models/misc/sphere")
            if ghost:
                ghost.reparent_to(self.render)
                ghost.set_pos(self.player_node.get_pos())
                ghost.set_scale(0.5)
                ghost.set_color(LColor(0.2, 0.5, 1.0, 0.5))
                from panda3d.core import TransparencyAttrib
                ghost.set_transparency(TransparencyAttrib.M_alpha)
                self._dash_afterimages.append((ghost, 0.3))

        # Fade and remove afterimages
        still_visible = []
        for ghost, timer in self._dash_afterimages:
            timer -= dt
            if timer <= 0:
                ghost.remove_node()
            else:
                alpha = timer / 0.3
                ghost.set_color_scale(1, 1, 1, alpha)
                still_visible.append((ghost, timer))
        self._dash_afterimages = still_visible

        # ── Spawn indicators ──
        if self.wave_manager.is_planning:
            self.arena.pulse_spawn_indicators()

        # ── Debug ──
        self.debug.update()

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
            weapon_slot=self.shooting.weapon_index + 1,
            dash_fraction=self.dash.cooldown_fraction,
            core_hp=self.arena.core_hp,
            enemy_count=self.spawner.active_count,
            power_display=self.power_meter.display_text,
            power_ready=self.power_meter.is_full,
            power_active=self.power_meter.super_shot_active,
        )

        return task.cont

    # ─── Manned Mortar ──────────────────────────────────────────

    def _get_manned_mortar(self):
        """Return the Mortar instance if the player is manning one, else None."""
        if not self.manning.is_manned:
            return None
        tower = self.manning.current_tower
        if isinstance(tower, Mortar):
            return tower
        return None

    def _update_arc_preview(self, input_state, mortar):
        """Show trajectory arc and splash ring at the clamped aim point."""
        start = mortar.get_position()
        end = mortar.get_manned_target(input_state.aim_world_pos)
        dist = (end - start).length()
        arc_height = 1.5 + dist * 0.4
        self.arc_preview.update(start, end, arc_height, mortar.splash_radius)

    def _update_manned_mortar(self, input_state, dt, mortar):
        """Handle fire rate and firing for manned mortar."""
        self.shooting._fire_cooldown -= dt
        if input_state.shooting and self.shooting._fire_cooldown <= 0:
            fire_rate = mortar.stats["fire_rate"] * mortar.stats.get("manned_fire_rate_mult", 1.5)
            self.shooting._fire_cooldown = 1.0 / fire_rate
            end = mortar.get_manned_target(input_state.aim_world_pos)
            mortar.fire_at_position(
                self.projectile_pool,
                end,
                damage_mult=mortar.stats.get("manned_damage_mult", 1.3),
            )

    # ─── Collision Detection ─────────────────────────────────────

    def _check_arc_impacts(self, dt: float) -> None:
        """Check if any arc projectiles will hit the ground this frame and apply splash."""
        for proj in self.projectile_pool.get_active():
            if not proj.uses_arc or not proj.alive:
                continue
            pos = proj.node.get_pos()
            next_z = pos.z + proj.z_velocity * dt - 10.0 * dt * dt
            if next_z > 0 or proj.age < 0.1:
                continue
            impact = LVector3f(pos.x, pos.y, 0)
            killed_by_player = proj.owner_tag == "player_bullet"
            for enemy in self.spawner.enemies:
                if not enemy.alive:
                    continue
                dist = (enemy.get_position() - impact).length()
                if dist < proj.splash_radius:
                    falloff = 1.0 - (dist / proj.splash_radius) * 0.5
                    enemy.take_damage(proj.damage * falloff)
                    if not enemy.alive:
                        self.economy.on_enemy_killed(enemy.reward, killed_by_player=killed_by_player)
            self.camera_system.add_shake(0.3)
            self.projectile_pool.kill(proj)

    def _check_collisions(self, dt: float) -> None:
        """
        Distance-based collision checks. In production, use proper
        collision nodes / physics engine. For prototype, this is
        fast enough and much simpler to debug.
        """
        player_pos = self.movement.get_position()
        is_invuln = self.player_invuln_timer > 0 or self.dash.is_invincible

        # Player bullets → enemies
        piercing = self.power_meter.is_piercing
        for proj in self.projectile_pool.get_active_by_tag("player_bullet"):
            proj_pos = proj.node.get_pos()
            hit = False
            for enemy in self.spawner.enemies:
                if not enemy.alive:
                    continue
                dist = (proj_pos - enemy.get_position()).length()
                if dist < proj.radius + enemy.radius:
                    enemy.take_damage(proj.damage)
                    if not enemy.alive:
                        self.economy.on_enemy_killed(enemy.reward, killed_by_player=True)
                    if not piercing:
                        self.projectile_pool.kill(proj)
                        hit = True
                        break
            if hit:
                continue

        # Tower bullets → enemies (skip arc projectiles — they use splash on impact)
        for proj in self.projectile_pool.get_active_by_tag("tower_bullet"):
            if proj.uses_arc:
                continue
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
                    dmg = getattr(enemy, "damage_to_player", 10)
                    self._player_take_damage(dmg)
                    break

        # Slug slime → player (DoT + slow effect on movement)
        for enemy in self.spawner.enemies:
            if not isinstance(enemy, Slug):
                continue
            for slime in enemy.slime_nodes:
                if not slime.alive:
                    continue
                dist = (slime.node.get_pos() - player_pos).length()
                if dist < slime.radius + 0.4:
                    if not is_invuln:
                        self._player_take_damage(slime.damage * dt)
                    self.movement.velocity *= slime.slow_factor

    def _try_repair(self) -> None:
        """Spend currency to restore player HP during planning phase."""
        if self.player_hp >= config.PLAYER_MAX_HP:
            self.hud.show_banner("HP already full", 1.0)
            return
        if not self.economy.spend(config.REPAIR_COST):
            self.hud.show_banner("Not enough $", 1.0)
            return
        self.player_hp = min(self.player_hp + config.REPAIR_AMOUNT, config.PLAYER_MAX_HP)
        self.hud.show_banner(f"REPAIRED +{config.REPAIR_AMOUNT} HP", 1.5)

    def _detonate_bomb(self) -> None:
        """Power-up bomb: radial blast from player, clears hostile bullets."""
        player_pos = self.movement.get_position()
        radius = config.POWER_BOMB_RADIUS
        damage = config.POWER_BOMB_DAMAGE

        # Damage all enemies in radius
        for enemy in self.spawner.enemies:
            if not enemy.alive:
                continue
            dist = (enemy.get_position() - player_pos).length()
            if dist < radius:
                falloff = 1.0 - (dist / radius) * 0.5
                enemy.take_damage(damage * falloff)
                if not enemy.alive:
                    self.economy.on_enemy_killed(enemy.reward, killed_by_player=True)

        # Clear enemy bullets in radius
        if config.POWER_BOMB_CLEARS_BULLETS:
            for proj in list(self.projectile_pool.get_active_by_tag("enemy_bullet")):
                dist = (proj.node.get_pos() - player_pos).length()
                if dist < radius:
                    self.projectile_pool.kill(proj)

        self.camera_system.add_shake(0.8)

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

        # Drop crystals from dead enemies (before cleanup removes them)
        for enemy in self.spawner.enemies:
            if not enemy.alive and hasattr(enemy, "_crystal_dropped"):
                continue
            if not enemy.alive:
                enemy._crystal_dropped = True  # type: ignore[attr-defined]
                self.crystal_manager.spawn(enemy.get_position())

        # Cleanup
        self.spawner.cleanup_dead()


# ─── Entry Point ─────────────────────────────────────────────────

if __name__ == "__main__":
    game = HoldfastGame()
    game.run()
