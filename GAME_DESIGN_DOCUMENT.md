# HOLDFAST
## Twin-Stick Shooter × Tower Defense

*Working title — rename freely*

---

## 1. Vision

A top-down semi-3D twin-stick shooter bullet hell fused with tower defense. You are both the architect and the soldier. Place towers, design kill corridors, then drop into the action to fight alongside your defenses as waves of enemies push toward your core. Towers handle the grind; you handle the crises.

**The pitch:** "What if you could jump inside a Defense Grid level and fight?"

**Target platform:** Steam (Windows/Mac/Linux)
**Development workflow:** Panda3D prototype → Godot 4 production
**Team:** Solo developer + Claude Code as AI pair programmer

---

## 2. Core Loop

```
PLANNING PHASE (between waves)
  │
  ├── Place / upgrade / reposition towers
  ├── Spend currency earned from last wave
  ├── Survey the map, plan coverage
  ├── Trigger next wave when ready
  │
  ▼
ACTION PHASE (during waves)
  │
  ├── Enemies spawn and follow paths/lanes toward the core
  ├── Towers fire autonomously
  ├── Player moves freely as twin-stick shooter character
  ├── Player shoots, dodges bullet-hell patterns from enemies
  ├── Player can man towers directly for boosted damage/accuracy
  ├── Wave complete → currency reward → return to planning
  │
  ▼
ESCALATION
  │
  ├── Later waves force more player intervention
  ├── Enemy types counter specific tower strategies
  ├── Boss waves introduce bullet-hell set pieces
  └── Player must balance builder role and fighter role under pressure
```

The tension between "I need to place this tower optimally" and "I need to physically be over THERE right now" is the emotional engine of the game.

---

## 3. Player Character

### Movement
- Twin-stick controls: left stick moves, right stick aims
- Movement feel target: **Geometry Wars** — buttery smooth, instant response, slight momentum on stop (not floaty, just *satisfying*)
- Dash/dodge: short invincibility-frame dash on a cooldown, essential for bullet-hell survival
- Movement speed should feel fast but not uncontrollable; the player needs to cross the map quickly to respond to threats but also thread through bullet patterns

### Shooting
- Right stick aims continuously; fire button shoots (or auto-fire option)
- Weapons have Enter the Gungeon-style variety: different fire rates, spread patterns, projectile behaviors
- **Bullets have physics momentum** (Binding of Isaac style): projectiles inherit some player velocity, arc slightly, interact with gravity wells and environmental forces
- Weapon pickups drop from enemies or unlock between stages
- Limited ammo for special weapons; default weapon has infinite ammo but modest damage

### Manning Towers
- Player can walk up to any placed tower and interact to "enter" it
- While manning: camera tightens, player directly controls aim/fire, damage and fire rate boosted significantly
- Tradeoff: you're stationary and not covering other areas
- Some tower types gain unique abilities when manned (e.g., sniper tower gets a charged shot; mortar tower lets you manually aim splash zones)

---

## 4. Tower Defense Systems

### Tower Placement
- Grid-based placement on designated build zones (Defense Grid style)
- Towers placed during planning phase; limited repositioning during action phase (at a cost)
- Placement affects enemy pathing: enemies follow shortest path to core, so tower placement can create mazes/corridors (Bloons-style pathing manipulation where the map allows it)
- Some maps have fixed paths (Defense Grid style); others have open fields where tower placement defines the path (Bloons style); best maps mix both

### Tower Types (Starter Set — Expand in Production)

| Tower | Role | Manned Bonus |
|-------|------|-------------|
| **Turret** | Steady single-target DPS, medium range | Increased fire rate + precision aim |
| **Mortar** | Slow AoE splash, long range | Manual targeting of splash zone |
| **Tesla Coil** | Chain lightning to nearby clustered enemies | Extended chain range + damage |
| **Slow Field** | Area that reduces enemy speed, no damage | Field expands + adds damage-over-time |
| **Wall / Barrier** | Blocks pathing, absorbs damage, no offense | Player takes cover behind it, reduced incoming damage |
| **Launcher** | Fires physics-driven projectiles that bounce off walls | Trick shot mode: manually aim ricochets |

### Economy
- Currency earned per enemy killed (bonus for player kills vs tower kills to incentivize action)
- Wave completion bonus
- Tower costs scale; upgrades cheaper than new towers to reward commitment
- Selling towers refunds partial cost
- Between-stage shop for player weapon upgrades, new tower blueprints, passive abilities

---

## 5. Enemy Design

### Pathing
- Enemies follow paths toward the **core** (a structure the player must protect)
- Ground enemies follow walkable paths influenced by tower placement
- Some enemies ignore pathing (flyers, phasing enemies) — these are the "oh no" moments that force player intervention
- Enemy variety forces hybrid strategy: you can't just tower everything, you can't just shoot everything

### Enemy Types (Starter Set)

**Grunts** — Basic walkers. Fodder. Test your tower coverage.
**Rushers** — Fast, fragile. Punish gaps in your maze.
**Tanks** — Slow, high HP. Absorb tower fire, need player focus.
**Flyers** — Ignore ground pathing, beeline for core. Only certain towers + player can hit them.
**Shielded** — Front-facing shield blocks tower fire from one direction. Player must flank.
**Splitters** — Die and split into smaller enemies (Bloons-style).
**Bullet Hell Emitters** — Enemies that fire complex bullet patterns at the player (not the core). They exist to distract you from defending.
**Disruptors** — Target and disable your towers temporarily. Priority kill targets.

### Bosses
- End-of-stage bosses are bullet-hell set pieces
- Large enemies with patterned attacks, multiple phases
- Towers contribute chip damage but the player must engage directly
- Boss arenas may limit or rearrange tower placement to force adaptation

---

## 6. Physics System

### Bullet Physics
- All projectiles (player, tower, enemy) are physics objects with velocity, mass, and drag
- Player bullets inherit partial player velocity (moving right and shooting forward = bullets angle right)
- Heavier projectiles (mortar shells) arc with gravity
- Light projectiles (laser bolts) travel fast with minimal physics influence
- This creates emergent behavior: strafing while firing fans your shots; charging forward tightens your spread

### Environmental Interactions
- **Gravity wells**: pull bullets and enemies toward them (Geometry Wars black holes). Strategic tower placement near wells creates kill zones where projectiles orbit and shred clustered enemies
- **Bounce surfaces**: walls and barriers that reflect projectiles. Launcher tower + bounce surfaces = trick shot corridors
- **Wind zones**: areas that push projectiles laterally. Towers firing through wind zones need the player to compensate or exploit the drift
- **Explosive barrels / chain objects**: environmental props that detonate when shot, creating area damage and physics impulse that scatters enemies

### Semi-3D Physics
- World is 3D but gameplay is primarily on a 2D plane (top-down)
- Height differences exist: ramps, elevated platforms, sunken trenches
- Towers on high ground get range bonus
- Some projectiles can arc over walls; others are line-of-sight blocked
- Enemies can be knocked back or launched vertically by explosions (visual flair + brief CC)
- Player jump is limited/contextual — used for dodging certain ground-level bullet patterns, not platforming

---

## 7. Visual Direction

### Aesthetic
- **Retro 3D**: Xbox Live Arcade / GameCube era. Clean geometry, bold lighting, readable silhouettes
- Low-to-mid poly models with strong specular highlights and rim lighting
- Bloom and glow on projectiles, explosions, energy effects — every bullet should *read* clearly against the battlefield
- Color-coded factions: player/tower projectiles one palette, enemy projectiles another. Readability is survival in a bullet hell
- Inspired by: Metroid Prime's visor glow and light interaction, Geometry Wars' neon-on-dark contrast, Wario World's chunky colorful geometry

### Lighting
- Dynamic point lights on every projectile (performance-managed via LOD and pooling)
- Light trails on fast-moving objects: dashing player leaves a streak, missiles leave comet tails
- Towers emit ambient glow matching their type (blue for tesla, orange for mortar, etc.)
- Environmental lighting shifts per stage: industrial stages are warm/orange; alien stages are cool/purple; etc.
- Specular "pops" on metallic surfaces when explosions occur nearby

### Camera
- Fixed top-down perspective, slightly angled (not pure orthographic — slight perspective for depth)
- Camera height adjusts based on action density: zooms out slightly during intense waves for readability
- Subtle camera shake on explosions (intensity-scaled, with option to disable)
- When manning a tower: camera drops closer, narrows FOV, creates an intimate shift in feel

---

## 8. Audio Direction (Notes)

- Retro-inspired but not chiptune; think synthesized orchestral + electronic
- Each tower type has a distinct audio signature (you should be able to hear which towers are active without looking)
- Bullet-hell sections get rhythmic, almost musical enemy fire patterns
- Bass-heavy impacts on explosions; high-frequency sizzle on energy weapons
- Dynamic music: planning phase is ambient/strategic; action phase layers in intensity; boss fights go full throttle

---

## 9. Map / Level Design Principles

- Each map is a contained arena with a core to defend and spawn points at edges
- Maps mix fixed-path corridors (Defense Grid DNA) with open zones (Bloons DNA)
- Environmental hazards and physics objects are placed to reward creative tower placement
- Maps have verticality: bridges, elevated sniper perches, sunken kill boxes
- 3–5 maps for vertical slice; 12–20 for full release
- Maps should be replayable: randomized enemy wave compositions on repeat plays

---

## 10. Progression Systems

### Within a Run (Single Stage)
- Tower unlocks and upgrades via currency
- Weapon drops from enemies
- Escalating wave difficulty

### Between Runs (Meta-Progression)
- Unlock new tower blueprints permanently
- Unlock new player weapons for the starting pool
- Cosmetic unlocks (player skin, tower skins, projectile effects)
- Challenge modifiers for replayability (e.g., "no turrets allowed," "double enemy speed," "bullet hell intensity +50%")

### Difficulty Scaling
- Early waves: towers can handle most enemies; player mops up stragglers
- Mid waves: specific enemy types counter your towers; player must intervene tactically
- Late waves: overwhelming volume + bullet-hell boss patterns; player is constantly moving, manning towers, repositioning, surviving
- This arc should feel like going from "relaxed architect" to "desperate action hero" within a single stage

---

## 11. Technical Architecture

### Panda3D Prototype Phase

**Goal:** Prove the core loop feels good. Not a vertical slice — a *feeling* slice.

**Prototype deliverables (in priority order):**

1. **Player movement** — Twin-stick controls. Get the Geometry Wars feel: responsive, smooth, slight momentum. Dash mechanic. This must feel perfect before anything else matters.

2. **Shooting with physics** — Player fires projectiles that are physics objects. Implement velocity inheritance from player movement. Test: strafing while shooting should visibly angle your bullet stream. This should feel kinetically satisfying.

3. **Basic tower placement** — Grid-based placement of a single turret type on a flat arena. Tower auto-targets and fires at enemies. Enemy walks a fixed path. Prove that player-as-shooter and towers-as-autonomous-defense can coexist without either feeling redundant.

4. **Tower manning** — Player enters a turret. Camera shifts. Player controls aim. Damage increases. Exiting returns to twin-stick mode. This transition must be seamless and fast.

5. **Bullet-hell enemy** — One enemy type that fires patterned projectiles at the player (concentric rings, spiral arms, aimed bursts). Player must dodge while also managing tower defense. This is where the genre fusion either sings or falls apart.

6. **Gravity well** — Place one gravity well on the map. Projectiles (player, tower, and enemy) curve around it. Enemies passing near it get pulled. Test: does this create interesting emergent gameplay? Can you exploit it with tower placement?

7. **One complete wave sequence** — Planning phase → action phase → wave clear → reward → planning. Loop it. Play it 20 times. Is it fun?

**Prototype tech stack:**
```
Python 3.11+
Panda3D (latest stable)
panda3d-bullet (Bullet physics integration)
```

**Prototype file structure:**
```
holdfast-prototype/
├── main.py                  # Entry point, game loop, state management
├── player/
│   ├── controller.py        # Twin-stick input handling
│   ├── movement.py          # Physics-based movement with momentum
│   ├── shooting.py          # Weapon firing, projectile spawning
│   └── dash.py              # Dash/dodge mechanic
├── towers/
│   ├── base_tower.py        # Abstract tower class
│   ├── turret.py            # Basic turret implementation
│   ├── placement.py         # Grid placement logic
│   └── manning.py           # Player-enters-tower mechanic
├── enemies/
│   ├── base_enemy.py        # Abstract enemy class
│   ├── grunt.py             # Basic pathing enemy
│   ├── bullet_hell_emitter.py # Enemy that fires patterns at player
│   └── spawner.py           # Wave composition and spawn timing
├── projectiles/
│   ├── base_projectile.py   # Physics-driven projectile base
│   ├── patterns.py          # Bullet-hell pattern generators
│   └── pool.py              # Object pooling for performance
├── environment/
│   ├── gravity_well.py      # Gravity well physics
│   ├── arena.py             # Map/arena definition
│   └── pathfinding.py       # Enemy pathing (A* or flow field)
├── systems/
│   ├── wave_manager.py      # Planning/action phase state machine
│   ├── economy.py           # Currency and scoring
│   ├── camera.py            # Camera control and transitions
│   └── collision.py         # Collision layers and responses
├── ui/
│   ├── hud.py               # Health, currency, wave info
│   └── tower_menu.py        # Tower selection during planning
├── assets/                  # Placeholder art (colored primitives are fine)
│   ├── models/
│   ├── textures/
│   └── sounds/
├── config.py                # Tuning constants (speeds, damage, costs)
└── README.md                # Setup instructions
```

**Key architectural decisions for prototype:**
- **Entity-component style**: Enemies, towers, and projectiles share a common base with composable behaviors. Don't over-engineer this — just base classes with overridable methods is fine for the prototype.
- **Object pooling for projectiles**: A bullet hell can spawn hundreds of projectiles per second. Pool them from the start, even in the prototype. Despawn on collision or leaving the arena bounds.
- **Config-driven tuning**: All gameplay numbers (player speed, dash cooldown, tower damage, enemy HP, wave timing) live in `config.py`. You will be tweaking these constantly. Never hardcode them.
- **State machine for game phases**: `PLANNING → ACTION → WAVE_CLEAR → PLANNING`. Clean transitions. The wave manager owns this state.
- **Physics layers**: Player bullets, tower bullets, enemy bullets, and physical entities all need distinct collision layers so towers don't shoot each other and enemy bullets don't kill enemies.

### Godot 4 Production Phase

**Migrate after the prototype proves the loop is fun.** Not before.

**Why Godot 4 for production:**
- GDScript and scene files are text-based → Claude Code can read, generate, and modify them directly
- Built-in physics (Godot Physics or Jolt) handles bullet physics, gravity areas, collision layers
- Visual shader editor for the retro 3D lighting effects
- Steam export via official GDExtension (Steamworks integration via GodotSteam)
- Area3D nodes are perfect for gravity wells, slow fields, tower ranges
- Godot's signal system maps cleanly to the event-driven nature of TD games (enemy_entered_range, wave_complete, tower_placed, etc.)

**Production file structure (Godot):**
```
holdfast/
├── project.godot
├── scenes/
│   ├── main.tscn                # Root scene
│   ├── player/
│   │   ├── player.tscn
│   │   └── player.gd
│   ├── towers/
│   │   ├── base_tower.tscn
│   │   ├── turret.tscn / .gd
│   │   ├── mortar.tscn / .gd
│   │   └── tesla.tscn / .gd
│   ├── enemies/
│   │   ├── base_enemy.tscn
│   │   ├── grunt.tscn / .gd
│   │   └── bullet_emitter.tscn / .gd
│   ├── projectiles/
│   │   ├── bullet.tscn / .gd
│   │   └── patterns.gd
│   ├── environment/
│   │   ├── gravity_well.tscn / .gd
│   │   ├── bounce_wall.tscn / .gd
│   │   └── arena_01.tscn
│   └── ui/
│       ├── hud.tscn / .gd
│       ├── tower_menu.tscn / .gd
│       └── wave_banner.tscn / .gd
├── scripts/
│   ├── autoload/
│   │   ├── game_manager.gd      # Global state, phase transitions
│   │   ├── wave_manager.gd      # Wave definitions and spawning
│   │   └── economy.gd           # Currency singleton
│   ├── components/
│   │   ├── health.gd
│   │   ├── physics_projectile.gd
│   │   └── target_acquisition.gd
│   └── data/
│       ├── tower_data.gd        # Tower stats as resources
│       ├── enemy_data.gd        # Enemy stats as resources
│       └── wave_data.gd         # Wave compositions as resources
├── resources/
│   ├── tower_definitions/       # .tres files for tower stats
│   ├── enemy_definitions/       # .tres files for enemy stats
│   └── wave_definitions/        # .tres files for wave compositions
├── shaders/
│   ├── projectile_trail.gdshader
│   ├── bloom_post.gdshader
│   └── retro_lighting.gdshader
├── assets/
│   ├── models/
│   ├── textures/
│   ├── audio/
│   └── fonts/
├── addons/
│   └── godotsteam/              # Steam integration
└── export_presets.cfg
```

---

## 12. Claude Code Handoff Instructions

### For Prototype Phase (Panda3D)

```
PROJECT CONTEXT:
You are helping build a twin-stick shooter / tower defense hybrid game.
The prototype is in Python using Panda3D + Bullet physics.
The goal is to prove the core gameplay loop is fun, not to build a finished game.

WORKING STYLE:
- Consult this GDD (GAME_DESIGN_DOCUMENT.md) as the source of truth for design intent
- All tuning values go in config.py, never hardcoded
- Use object pooling for any spawned entity (projectiles, enemies, effects)
- Keep the prototype playable at all times — never break the game loop to add a feature
- Placeholder art is fine (colored cubes, spheres, cylinders with emissive materials)
- Test each feature in isolation before integrating

PRIORITY ORDER:
1. Player movement (must feel great before anything else)
2. Shooting with physics projectiles
3. One enemy type walking a fixed path
4. One tower type auto-targeting enemies
5. Tower manning mechanic
6. Bullet-hell enemy patterns
7. Gravity well environmental physics
8. Wave loop (planning → action → clear → planning)
9. Basic UI (health, currency, wave counter)
10. Second tower type and second enemy type

ARCHITECTURE RULES:
- Base classes for towers, enemies, projectiles — composed via overrides, not deep inheritance
- Collision layers: PLAYER_BULLET, TOWER_BULLET, ENEMY_BULLET, PLAYER, ENEMY, ENVIRONMENT
- State machine for game phase: PLANNING, ACTION, WAVE_CLEAR
- Projectiles are physics bodies with velocity, mass, drag — not raycasts
- Enemy pathing via A* on a navmesh or grid; recalculate when towers are placed

CODE STYLE:
- Python type hints everywhere
- Docstrings on public methods
- Keep files under 300 lines; split when they grow
- Name things for what they DO, not what they ARE
```

### For Production Phase (Godot 4)

```
PROJECT CONTEXT:
Migrating a proven prototype into Godot 4 for Steam release.
The core loop is validated — now we need polish, content, and performance.

WORKING STYLE:
- Consult this GDD for design intent
- Use Godot's node/scene composition — prefer scenes over scripts for reusable entities
- Gameplay data (tower stats, enemy stats, wave compositions) as Godot Resource files (.tres)
- Autoload singletons for global managers (GameManager, WaveManager, Economy)
- Signals for inter-system communication — avoid direct references between unrelated systems
- Use Godot's built-in physics (or Jolt plugin) — do not write custom physics

GODOT-SPECIFIC RULES:
- Scenes are self-contained: a tower scene includes its model, collision, range indicator, and script
- Use AnimationPlayer for visual feedback (hit flash, placement confirmation, damage shake)
- Shader-based effects for projectile trails, bloom, retro lighting
- Export hints on script variables for in-editor tuning
- Use Godot's TileMap or GridMap for tower placement grids
- Area3D nodes for gravity wells, slow fields, tower detection ranges
- Object pooling via a global pool manager autoload

PERFORMANCE RULES:
- Projectile pooling is mandatory — target 500+ simultaneous projectiles at 60fps
- LOD on projectile lights: full lights for nearby, simplified for distant, culled for off-screen
- Enemy pathfinding cached and only recalculated on tower placement changes
- Use servers (PhysicsServer3D, RenderingServer) directly for mass-spawned entities if node overhead becomes a bottleneck

STEAM INTEGRATION:
- GodotSteam plugin for achievements, cloud saves, overlay
- Build pipeline: Godot export → Steam build upload via steamcmd
```

---

## 13. Vertical Slice Definition

The vertical slice is the first "this is a real game" milestone. It should be a single complete stage that demonstrates every core system.

**Vertical slice contains:**
- 1 complete map with mixed fixed-path and open-build zones
- 1 environmental hazard (gravity well)
- 3 tower types (Turret, Mortar, Slow Field)
- 4 enemy types (Grunt, Rusher, Flyer, Bullet Hell Emitter)
- 1 boss encounter
- Full planning → action → wave clear loop for 5-8 waves
- Tower manning mechanic for all 3 tower types
- Player with 2 weapons (default + 1 pickup)
- Dash/dodge mechanic
- Physics-driven projectiles with momentum
- Basic economy (currency, tower costs, upgrades)
- HUD (health, currency, wave counter, minimap)
- Retro 3D visual style with bloom, light trails, color-coded projectiles
- Dynamic camera (zoom-out on intensity, tighten on tower manning)
- One music track with planning/action intensity layers
- Sound effects for all weapons, towers, and enemies
- Steam integration (launch, overlay, one test achievement)

**Vertical slice does NOT need:**
- Meta-progression
- Multiple stages
- Full tower roster
- Story/narrative
- Settings menu (hardcode sensible defaults)
- Controller rebinding (use standard twin-stick mapping)

---

## 14. Open Design Questions

These are decisions to make during or after prototyping, not before:

1. **How much pathing manipulation?** Pure Defense Grid (fixed paths, towers beside them) vs pure Bloons (you build the maze) vs hybrid. Prototype both, see what's fun.

2. **Permadeath or checkpoint?** Roguelike runs where death resets the stage? Or checkpoint per wave? Affects meta-progression design heavily.

3. **Co-op?** This genre fusion screams for 2-player co-op (one builds, one fights; or both do both). But scope it for solo first.

4. **How many weapons?** Enter the Gungeon has hundreds. This game probably needs 10–20 that feel distinct. Quality over quantity.

5. **Tower upgrade depth?** Simple linear upgrades (Turret Mk1 → Mk2 → Mk3) or branching paths (Turret → Sniper OR Minigun)? Branching is more interesting but harder to balance.

6. **Narrative framing?** Does this game need a story, or is it a pure arcade experience? A light narrative frame (you're defending a base, waves are an invasion) costs little and adds motivation.

---

*This is a living document. Update it as the prototype reveals what works and what doesn't. The prototype exists to answer the open questions — don't design on paper what you can test in code.*
