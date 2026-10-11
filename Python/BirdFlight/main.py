"""BirdFlight: a small, procedural 3D island-hopping flight game."""
import math
import random
from ursina import *
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone

app = Ursina(title="BirdFlight", borderless=False, fullscreen=False,
             development_mode=False, editor_ui_enabled=False)
window.color = color.rgb32(125, 194, 220)
window.fps_counter.enabled = False
random.seed(12)

# Warm, low-poly scenery built entirely from Ursina's primitive models.
water = Entity(model="plane", scale=(1600, 1, 1800), y=-7, color=color.rgb32(47, 151, 174))
water.rotation_x = 0
AmbientLight(color=color.rgba32(170, 190, 210, 255))
sun = DirectionalLight(color=color.rgb32(255, 239, 207))
sun.look_at(Vec3(1, -2, -1))

ROUTE = [(-5, 7, 0), (4, 10, 38), (10, 5, 79), (0, 12, 122), (-10, 7, 165), (3, 11, 208)]
NEST_RADIUS = 5.0


def make_island(x, y, z, index):
    """Layered rock stacks with a grassy crown and a visible nest marker."""
    root = Entity(position=(x, y, z))
    radius = 7.8 if index == 0 else 6.5
    rock = color.rgb32(114, 105, 96)
    for layer in range(4):
        width = radius * (1.0 - layer * .075)
        Entity(parent=root, model=Cylinder(), position=(0, -1.2 - layer * 1.35, 0),
               scale=(width * 2, 2.5, width * 2), color=rock.tint(-layer * .035))
    Entity(parent=root, model=Cylinder(), y=.05, scale=(radius * 2, .65, radius * 2),
           color=color.rgb32(112, 159, 92))
    # Tiny trees, pebbles, and tufts give scale to the landing platform.
    for _ in range(9):
        angle = random.random() * math.tau
        distance = random.uniform(4.3, radius - 1.0)
        px, pz = math.cos(angle) * distance, math.sin(angle) * distance
        Entity(parent=root, model="sphere", position=(px, .42, pz), scale=(.36, .65, .36),
               color=random.choice([color.rgb32(66, 118, 76), color.rgb32(83, 135, 80)]))
    Entity(parent=root, model="sphere", position=(0, .52, 0), scale=(1.9, .23, 1.9),
           color=color.rgb32(241, 205, 116))
    # A softly visible approach ring floats around each safe landing.
    for marker in range(16):
        angle = marker * math.tau / 16
        Entity(parent=root, model="sphere", position=(math.cos(angle) * 3.15, .38, math.sin(angle) * 3.15),
               scale=(.15, .12, .15), color=color.rgb32(255, 227, 145))
    return root


islands = [make_island(x, y, z, i) for i, (x, y, z) in enumerate(ROUTE)]

# Player bird, assembled as a compact little creature from spheres and cones.
bird = Entity(position=(ROUTE[0][0], ROUTE[0][1] + 2.0, ROUTE[0][2] - 3))
Entity(parent=bird, model="sphere", scale=(1.25, .78, 1.65), color=color.rgb32(247, 164, 67))
Entity(parent=bird, model="sphere", position=(0, .48, .95), scale=(.62, .62, .65), color=color.rgb32(255, 193, 93))
beak = Entity(parent=bird, model=Cone(), position=(0, .34, 1.68), rotation_x=90,
              scale=(.32, .68, .32), color=color.rgb32(230, 103, 53))
for side in (-1, 1):
    Entity(parent=bird, model="sphere", position=(side * .28, .58, 1.2), scale=.13, color=color.white)
    Entity(parent=bird, model="sphere", position=(side * .32, .59, 1.3), scale=.07, color=color.black)
wings = []
for side in (-1, 1):
    wing = Entity(parent=bird, model="sphere", position=(side * .95, .02, -.05),
                  scale=(.32, .16, 1.1), rotation_z=side * -12, color=color.rgb32(212, 115, 52))
    wings.append((wing, side))
Entity(parent=bird, model="sphere", position=(0, .04, -1.0), scale=(.42, .25, .68),
       color=color.rgb32(255, 204, 115))


def make_predator(offset):
    # Larger plum-colored hunters with bright faces and broad, flapping wings.
    body = Entity(model="sphere", scale=1.35, color=color.rgb32(83, 44, 104))
    Entity(parent=body, model="sphere", position=(0, .38, .67), scale=(.58, .54, .58),
           color=color.rgb32(119, 59, 125))
    Entity(parent=body, model=Cone(), position=(0, .22, 1.2), rotation_x=90,
           scale=(.3, .58, .3), color=color.rgb32(255, 151, 55))
    for side in (-1, 1):
        Entity(parent=body, model="sphere", position=(side * .28, .61, .99), scale=.13,
               color=color.white)
        Entity(parent=body, model="sphere", position=(side * .31, .62, 1.08), scale=.065,
               color=color.rgb32(25, 20, 35))
    body.flap_wings = []
    for side in (-1, 1):
        wing = Entity(parent=body, model="sphere", position=(side * .78, .02, -.12),
                      scale=(.34, .18, 1.25), rotation_z=side * -18,
                      color=color.rgb32(48, 35, 83))
        Entity(parent=wing, model="sphere", position=(0, 0, .55), scale=(1, 1, .3),
               color=color.rgb32(220, 104, 119))
        body.flap_wings.append((wing, side))
    body.position = bird.position + Vec3(offset, random.uniform(-1.5, 1.5), -random.uniform(6, 9))
    return body


predators = [make_predator(-9), make_predator(10)]

# Heads-up display.
HUD_COLOR = color.rgb32(20, 44, 64)
Text("BIRDFLIGHT", parent=camera.ui, position=(-.86, .45), scale=1.3, color=HUD_COLOR)
help_text = Text("WASD / arrows: steer     SPACE: flap boost     R: restart",
                 parent=camera.ui, position=(-.86, .405), scale=.75, color=HUD_COLOR)
progress_text = Text("", parent=camera.ui, position=(-.86, .34), scale=.9, color=HUD_COLOR)
status_text = Text("", parent=camera.ui, origin=(0, 0), position=(0, .34), scale=1.5,
                   color=HUD_COLOR)
heart_text = Text("", parent=camera.ui, position=(.67, .45), scale=1.1, color=HUD_COLOR)

checkpoint = 0
lives = 3
landed_count = 0
invulnerable = 0.0
game_over = False
won = False
speed_z = 8.6


def reset_run():
    global checkpoint, lives, landed_count, invulnerable, game_over, won
    checkpoint, lives, landed_count = 0, 3, 0
    invulnerable = 1.5
    game_over = won = False
    bird.position = Vec3(ROUTE[0][0], ROUTE[0][1] + 2.0, ROUTE[0][2] - 3)
    for i, predator in enumerate(predators):
        predator.position = bird.position + Vec3((-5, 5)[i], 0, -6)
    status_text.text = ""


def lose_life():
    global lives, invulnerable, game_over
    lives -= 1
    invulnerable = 2.2
    if lives <= 0:
        game_over = True
        status_text.text = "THE WIND CAUGHT YOU  ·  Press R to try again"
        status_text.color = HUD_COLOR
    else:
        x, y, z = ROUTE[checkpoint]
        bird.position = Vec3(x, y + 2.4, z + 3.5)
        status_text.text = "Back to your last nest — steer for the next marker!"
        for i, predator in enumerate(predators):
            predator.position = bird.position + Vec3((-5, 5)[i], 0, -7 - i)


def input(key):
    """A tap nudges the bird; holding a key continues smooth steering."""
    if key == "r":
        reset_run()
    elif key in ("a", "left"):
        bird.x = max(-25, bird.x - 1.4)
    elif key in ("d", "right"):
        bird.x = min(25, bird.x + 1.4)
    elif key in ("w", "up"):
        bird.y = min(25, bird.y + 1.2)
    elif key in ("s", "down"):
        bird.y = max(-1, bird.y - 1.2)


def update():
    global checkpoint, landed_count, invulnerable, won, lives
    dt = min(time.dt, .04)
    if game_over or won:
        return

    invulnerable = max(0, invulnerable - dt)
    horizontal = held_keys["d"] + held_keys["right"] - held_keys["a"] - held_keys["left"]
    vertical = held_keys["w"] + held_keys["up"] - held_keys["s"] - held_keys["down"]
    boost = 1.55 if held_keys["space"] else 1.0
    bird.x += horizontal * 10.0 * dt
    bird.y += vertical * 8.2 * dt
    bird.z += speed_z * boost * dt
    bird.y = max(-1.0, min(25.0, bird.y))
    bird.x = max(-25.0, min(25.0, bird.x))
    bird.rotation_z = lerp(bird.rotation_z, -horizontal * 20, dt * 5)
    bird.rotation_x = lerp(bird.rotation_x, vertical * 12, dt * 4)
    flap = math.sin(time.time() * 15) * 34
    for wing, side in wings:
        wing.rotation_z = side * (-12 + flap)

    # Safe nests advance the route and restore one heart.
    if checkpoint + 1 < len(ROUTE):
        nx, ny, nz = ROUTE[checkpoint + 1]
        if abs(bird.z - nz) < 3.5 and math.hypot(bird.x - nx, bird.y - (ny + 1.4)) < NEST_RADIUS:
            checkpoint += 1
            landed_count += 1
            status_text.text = "SAFE NEST REACHED!  +1 heart"
            status_text.color = HUD_COLOR
            if lives < 3:
                lives += 1
            for i, predator in enumerate(predators):
                predator.position = bird.position + Vec3((-5, 5)[i], random.uniform(-1, 1), -7 - i)
            if checkpoint == len(ROUTE) - 1:
                won = True
                status_text.text = "HOME AT LAST!  ·  Press R to fly again"
                status_text.color = HUD_COLOR
        elif bird.z > nz + 5:
            # Keep missed targets from leaving the player stranded beyond the route.
            lose_life()
            return

    # Hunters stay in view, circle close, and swoop across the bird's path.
    for i, predator in enumerate(predators):
        phase = time.time() * 1.35 + i * math.pi
        target = bird.position + Vec3(
            math.cos(phase) * 2.5,
            .65 + math.sin(phase * 1.6) * 1.0,
            -1.0 + math.sin(phase * .8) * 1.8,
        )
        predator.position = lerp(predator.position, target, min(1, dt * 1.5))
        predator.look_at(bird.position)
        predator.rotation_x = math.sin(phase * 2) * 12
        for wing, side in predator.flap_wings:
            wing.rotation_z = side * (-18 + math.sin(phase * 5) * 38)
        if invulnerable <= 0 and distance(predator.position, bird.position) < 2.35:
            lose_life()
            break

    # Camera follows from behind, looking slightly downward along the island chain.
    camera.position = lerp(camera.position, bird.position + Vec3(0, 9.5, -23), dt * 2.8)
    camera.look_at(bird.position + Vec3(0, 1.5, 12))
    camera.fov = 72
    progress_text.text = f"NEST {checkpoint + 1}/{len(ROUTE)}     Distance {max(0, int((ROUTE[-1][2] - bird.z) / 10))}"
    heart_text.text = f"LIVES: {lives}"
    if invulnerable > 0 and not won:
        bird.alpha = .45 if int(time.time() * 12) % 2 else 1
    else:
        bird.alpha = 1


# Overhead scenic fly-in camera placement.
camera.position = bird.position + Vec3(0, 9.5, -23)
camera.look_at(bird.position + Vec3(0, 1.5, 12))
app.run()

















