"""
HOLDFAST — Configuration & Tuning Constants
=============================================
Every gameplay number lives here. Never hardcode tuning values in game code.
Tweak freely; the game reads these at startup and (where noted) at runtime.
"""

from panda3d.core import LVector3f, LColor

# ─── Window / Display ─────────────────────────────────────────────
WINDOW_TITLE = "HOLDFAST — Prototype"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FULLSCREEN = False
TARGET_FPS = 60

# ─── Arena ─────────────────────────────────────────────────────────
ARENA_WIDTH = 40.0          # world units, X axis
ARENA_HEIGHT = 30.0         # world units, Y axis
GRID_CELL_SIZE = 2.0        # tower placement grid resolution
CORE_POSITION = LVector3f(0, -12, 0)   # what you're defending
SPAWN_POINTS = [            # where enemies enter
    LVector3f(-15, 12, 0),
    LVector3f(0, 14, 0),
    LVector3f(15, 12, 0),
]

# ─── Player Movement ──────────────────────────────────────────────
PLAYER_MAX_SPEED = 18.0           # units/sec at full stick
PLAYER_ACCELERATION = 120.0       # how fast you reach max speed
PLAYER_FRICTION = 0.88            # velocity multiplier per frame when not accelerating
PLAYER_MASS = 1.0

# ─── Player Dash ──────────────────────────────────────────────────
DASH_SPEED = 40.0                 # burst speed during dash
DASH_DURATION = 0.12              # seconds of dash
DASH_COOLDOWN = 0.6               # seconds between dashes
DASH_INVINCIBLE = True            # i-frames during dash

# ─── Player Health ────────────────────────────────────────────────
PLAYER_MAX_HP = 100
PLAYER_INVULN_AFTER_HIT = 1.0    # seconds of mercy invulnerability
PLAYER_REGEN_RATE = 0.0           # HP per second (0 = no regen)

# ─── Player Shooting ─────────────────────────────────────────────
DEFAULT_WEAPON = {
    "name": "Pulse Rifle",
    "fire_rate": 8.0,             # shots per second
    "bullet_speed": 30.0,         # units/sec
    "bullet_damage": 10,
    "bullet_mass": 0.3,
    "bullet_drag": 0.01,          # velocity decay per frame
    "spread": 2.0,                # degrees of random spread
    "velocity_inherit": 0.3,      # fraction of player velocity added to bullet
    "bullet_lifetime": 2.5,       # seconds before despawn
    "bullet_radius": 0.15,
    "bullet_color": LColor(0.3, 0.8, 1.0, 1.0),
    "ammo": -1,                   # -1 = infinite
}

SHOTGUN_WEAPON = {
    "name": "Scattergun",
    "fire_rate": 1.8,
    "bullet_speed": 25.0,
    "bullet_damage": 8,
    "bullet_mass": 0.5,
    "bullet_drag": 0.03,
    "spread": 18.0,
    "velocity_inherit": 0.2,
    "bullet_lifetime": 1.5,
    "bullet_radius": 0.12,
    "bullet_color": LColor(1.0, 0.6, 0.2, 1.0),
    "ammo": 40,
    "pellets": 6,                 # shots per trigger pull
}

# ─── Towers ───────────────────────────────────────────────────────
TOWER_PLACEMENT_COST = {
    "turret": 50,
    "mortar": 80,
    "slow_field": 60,
}

TOWER_SELL_REFUND = 0.6           # fraction of cost returned

TURRET_STATS = {
    "range": 8.0,
    "fire_rate": 3.0,             # shots/sec
    "bullet_speed": 28.0,
    "bullet_damage": 12,
    "bullet_mass": 0.2,
    "bullet_drag": 0.005,
    "bullet_radius": 0.12,
    "bullet_color": LColor(0.2, 1.0, 0.3, 1.0),
    "turn_speed": 360.0,          # degrees/sec to track target
    "hp": 200,
    # Manning bonuses
    "manned_fire_rate_mult": 1.8,
    "manned_damage_mult": 1.5,
}

MORTAR_STATS = {
    "range": 14.0,
    "fire_rate": 0.6,
    "bullet_speed": 12.0,
    "bullet_damage": 40,
    "bullet_mass": 2.0,
    "bullet_drag": 0.0,
    "bullet_radius": 0.3,
    "bullet_color": LColor(1.0, 0.3, 0.1, 1.0),
    "splash_radius": 3.0,
    "turn_speed": 120.0,
    "hp": 150,
    "manned_splash_mult": 1.4,
    "manned_damage_mult": 1.3,
}

SLOW_FIELD_STATS = {
    "range": 5.0,
    "slow_factor": 0.4,           # enemy speed multiplied by this
    "hp": 120,
    "manned_range_mult": 1.6,
    "manned_adds_dot": 3.0,       # damage per second when manned
}

# ─── Enemies ──────────────────────────────────────────────────────
GRUNT_STATS = {
    "hp": 40,
    "speed": 4.0,
    "damage_to_core": 10,
    "reward": 10,                  # currency on kill
    "radius": 0.5,
    "color": LColor(0.9, 0.2, 0.2, 1.0),
}

RUSHER_STATS = {
    "hp": 20,
    "speed": 9.0,
    "damage_to_core": 5,
    "reward": 8,
    "radius": 0.35,
    "color": LColor(1.0, 0.8, 0.1, 1.0),
}

FLYER_STATS = {
    "hp": 30,
    "speed": 5.5,
    "damage_to_core": 15,
    "reward": 15,
    "radius": 0.4,
    "color": LColor(0.6, 0.2, 1.0, 1.0),
    "fly_height": 2.0,            # above ground plane
}

BULLET_HELL_EMITTER_STATS = {
    "hp": 80,
    "speed": 2.5,
    "damage_to_core": 20,
    "reward": 25,
    "radius": 0.7,
    "color": LColor(1.0, 0.1, 0.5, 1.0),
    "pattern_fire_rate": 1.5,     # patterns per second
    "bullet_speed": 10.0,
    "bullet_damage": 15,
    "bullet_radius": 0.1,
    "bullet_color": LColor(1.0, 0.2, 0.6, 0.9),
}

# ─── Projectile Pooling ──────────────────────────────────────────
POOL_INITIAL_SIZE = 200           # pre-allocated projectiles
POOL_MAX_SIZE = 800               # hard cap
POOL_GROW_STEP = 50               # allocate this many when pool is empty

# ─── Gravity Wells ────────────────────────────────────────────────
GRAVITY_WELL_STRENGTH = 300.0     # force magnitude
GRAVITY_WELL_RADIUS = 6.0         # max influence range
GRAVITY_WELL_INNER_RADIUS = 1.0   # objects inside this get destroyed
GRAVITY_WELL_AFFECTS_ENEMIES = True
GRAVITY_WELL_AFFECTS_PLAYER = False  # frustrating if True early on

# ─── Wave System ──────────────────────────────────────────────────
PLANNING_PHASE_MIN_TIME = 3.0     # seconds before you can trigger next wave
WAVE_COMPLETE_BONUS = 50          # bonus currency on wave clear
STARTING_CURRENCY = 150           # enough for 2-3 towers
KILL_CURRENCY_PLAYER_MULT = 1.5   # bonus for player kills vs tower kills

# ─── Camera ───────────────────────────────────────────────────────
CAMERA_HEIGHT = 35.0              # Y distance above arena
CAMERA_ANGLE = -75.0              # degrees from horizontal (−90 = straight down)
CAMERA_ZOOM_OUT_THRESHOLD = 10    # active enemies to trigger zoom out
CAMERA_ZOOM_OUT_AMOUNT = 8.0      # additional height when zoomed out
CAMERA_ZOOM_SPEED = 3.0           # lerp speed for zoom transitions
CAMERA_SHAKE_INTENSITY = 0.3      # max offset per explosion
CAMERA_SHAKE_DECAY = 8.0          # decay rate

CAMERA_MANNED_HEIGHT = 15.0       # closer when manning a tower
CAMERA_MANNED_ANGLE = -55.0       # more angled when manning

# ─── Collision Masks ──────────────────────────────────────────────
# BitMask32 values — each category gets a unique bit
from panda3d.core import BitMask32

COL_PLAYER =        BitMask32.bit(0)
COL_PLAYER_BULLET = BitMask32.bit(1)
COL_TOWER_BULLET =  BitMask32.bit(2)
COL_ENEMY =         BitMask32.bit(3)
COL_ENEMY_BULLET =  BitMask32.bit(4)
COL_ENVIRONMENT =   BitMask32.bit(5)
COL_TOWER =         BitMask32.bit(6)
COL_CORE =          BitMask32.bit(7)

# ─── Visual / Effects ────────────────────────────────────────────
BLOOM_INTENSITY = 0.6
AMBIENT_LIGHT_COLOR = LColor(0.15, 0.15, 0.2, 1.0)
DIRECTIONAL_LIGHT_COLOR = LColor(0.7, 0.7, 0.8, 1.0)
LIGHT_TRAIL_LENGTH = 5            # frames of trail history
LIGHT_TRAIL_FADE = 0.7            # opacity decay per trail segment

# ─── Colors (for placeholder geometry) ───────────────────────────
COLOR_PLAYER = LColor(0.2, 0.7, 1.0, 1.0)
COLOR_CORE = LColor(0.1, 0.9, 0.4, 1.0)
COLOR_GRID = LColor(0.3, 0.3, 0.35, 0.5)
COLOR_ARENA_FLOOR = LColor(0.12, 0.12, 0.15, 1.0)
COLOR_WALL = LColor(0.4, 0.4, 0.45, 1.0)
COLOR_GRAVITY_WELL = LColor(0.5, 0.0, 0.8, 0.8)
