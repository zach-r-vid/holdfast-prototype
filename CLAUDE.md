# HOLDFAST — Claude Code Instructions

## Project Context
Twin-stick shooter / tower defense hybrid game.
Prototype is Python + Panda3D + Bullet physics.
Goal: prove the core gameplay loop is fun, not build a finished game.

## Source of Truth
- Design intent: `GAME_DESIGN_DOCUMENT.md`
- All tuning values: `holdfast-prototype/config.py` — never hardcode gameplay numbers

## Working Style
- Use object pooling for any spawned entity (projectiles, enemies, effects)
- Keep the prototype playable at all times — never break the game loop to add a feature
- Placeholder art is fine (colored cubes, spheres, cylinders with emissive materials)
- Test each feature in isolation before integrating

## Architecture Rules
- Base classes for towers, enemies, projectiles — composed via overrides, not deep inheritance
- Collision layers: PLAYER_BULLET, TOWER_BULLET, ENEMY_BULLET, PLAYER, ENEMY, ENVIRONMENT
- State machine for game phase: PLANNING, ACTION, WAVE_CLEAR
- Projectiles are physics bodies with velocity, mass, drag — not raycasts
- Enemy pathing via A* on grid; recalculate when towers are placed

## Code Style
- Python type hints everywhere
- Docstrings on public methods
- Keep files under 300 lines; split when they grow
- Name things for what they DO, not what they ARE

## Running
```bash
cd holdfast-prototype
python main.py
```
