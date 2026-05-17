# HOLDFAST — Prototype

Twin-stick shooter × tower defense hybrid. Panda3D prototype.

## Setup

```bash
# Requires Python 3.10+
pip install panda3d

# Run the game
cd holdfast-prototype
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Aim |
| Left Click | Shoot |
| Right Click / Shift | Dash |
| E | Enter/exit tower |
| Tab | Toggle build menu (planning phase) |
| 1 / 2 / 3 | Select tower type |
| Enter | Start next wave |
| Escape | Quit |

## Game Flow

1. **Planning Phase** — Place towers using Tab menu. Towers snap to the grid and affect enemy pathing.
2. **Press Enter** — Wave begins. Enemies spawn and follow paths to the core.
3. **Action Phase** — Shoot enemies, dodge bullet patterns, man towers for boosted damage.
4. **Wave Clear** — Earn currency bonus. Return to planning.
5. **Repeat** — Waves escalate in enemy count and variety.

## Project Structure

```
holdfast-prototype/
├── main.py              # Entry point — ties all systems together
├── config.py            # ALL tuning constants (speeds, damage, costs)
├── player/
│   ├── controller.py    # Input handling (keyboard + mouse)
│   ├── movement.py      # Physics-based movement with momentum
│   ├── shooting.py      # Weapon firing and ammo management
│   └── dash.py          # Dash/dodge with i-frames
├── towers/
│   ├── base_tower.py    # Abstract tower with targeting
│   ├── turret.py        # Single-target DPS tower
│   ├── mortar.py        # AoE splash tower
│   ├── slow_field.py    # Area slow debuff tower
│   ├── placement.py     # Grid placement and build/sell
│   └── manning.py       # Player-enters-tower mechanic
├── enemies/
│   ├── base_enemy.py    # Path-following enemy base
│   ├── grunt.py         # Basic walker
│   ├── rusher.py        # Fast, fragile
│   ├── bullet_hell_emitter.py  # Fires patterns at player
│   └── spawner.py       # Wave composition and spawn timing
├── projectiles/
│   ├── pool.py          # Object-pooled projectile system
│   ├── base_projectile.py  # Spawning helpers
│   └── patterns.py      # Bullet-hell pattern generators
├── environment/
│   ├── arena.py         # Floor, walls, core, lighting
│   ├── pathfinding.py   # A* grid pathfinding
│   └── gravity_well.py  # Physics hazard
├── systems/
│   ├── wave_manager.py  # Planning/Action/Clear state machine
│   ├── economy.py       # Currency tracking
│   ├── camera.py        # Dynamic zoom and shake
│   └── collision.py     # Collision layer management
└── ui/
    ├── hud.py           # On-screen status display
    └── tower_menu.py    # Tower build selection menu
```

## Tuning

All gameplay numbers are in `config.py`. Change anything there and restart. Key values to experiment with:

- `PLAYER_MAX_SPEED` / `PLAYER_ACCELERATION` / `PLAYER_FRICTION` — movement feel
- `DASH_SPEED` / `DASH_DURATION` / `DASH_COOLDOWN` — dodge responsiveness
- `DEFAULT_WEAPON["velocity_inherit"]` — how much player momentum transfers to bullets
- `GRAVITY_WELL_STRENGTH` — how aggressively the gravity well pulls
- `WAVE_DEFINITIONS` in `enemies/spawner.py` — enemy composition per wave

## Architecture Notes

- **Config-driven**: No hardcoded gameplay numbers. Everything tuneable from `config.py`.
- **Object pooling**: Projectiles are pooled from startup. Supports 800 simultaneous bullets.
- **Modular**: Each system (player, towers, enemies, projectiles) is independent. Systems communicate through the main game loop, not direct references.
- **Placeholder art**: Everything is colored primitives. The game design doesn't depend on art — if it's fun with cubes, it'll be fun with models.

## Known Prototype Limitations

- Collision detection is distance-based (no spatial partitioning). Fine for <100 enemies.
- No mortar splash damage implementation yet (direct hit only).
- Tower range indicators only show on slow field.
- No sound.
- No save/load.
- Single map only.

## Next Steps (Post-Prototype)

See `GAME_DESIGN_DOCUMENT.md` for the full production plan including Godot 4 migration.
