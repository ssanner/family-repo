"""Object-oriented version of the BirdFlight island-hopping game."""
from abc import ABC, abstractmethod
import math
import random

from ursina import *
from ursina.models.procedural.cone import Cone
from ursina.models.procedural.cylinder import Cylinder


ROUTE = [(-5, 7, 0), (4, 10, 38), (10, 5, 79), (0, 12, 122),
         (-10, 7, 165), (3, 11, 208)]
NEST_RADIUS = 5.0
HUD_COLOR = color.rgb32(20, 44, 64)


class LandscapeFeatures(ABC):
    """Contract for a feature that adds scenery to the Ursina scene."""

    @abstractmethod
    def build(self):
        """Create the feature in the active scene."""


class WaterFeature(LandscapeFeatures):
    def build(self):
        return Entity(model="plane", scale=(1600, 1, 1800), y=-7,
                      color=color.rgb32(47, 151, 174))


class IslandFeature(LandscapeFeatures):
    def __init__(self, position, index):
        self.position = position
        self.index = index

    def build(self):
        root = Entity(position=self.position)
        radius = 7.8 if self.index == 0 else 6.5
        rock = color.rgb32(114, 105, 96)
        for layer in range(4):
            width = radius * (1.0 - layer * .075)
            Entity(parent=root, model=Cylinder(), position=(0, -1.2 - layer * 1.35, 0),
                   scale=(width * 2, 2.5, width * 2), color=rock.tint(-layer * .035))
        Entity(parent=root, model=Cylinder(), y=.05, scale=(radius * 2, .65, radius * 2),
               color=color.rgb32(112, 159, 92))

        for _ in range(9):
            angle = random.random() * math.tau
            distance_from_center = random.uniform(4.3, radius - 1.0)
            x = math.cos(angle) * distance_from_center
            z = math.sin(angle) * distance_from_center
            Entity(parent=root, model="sphere", position=(x, .42, z), scale=(.36, .65, .36),
                   color=random.choice([color.rgb32(66, 118, 76), color.rgb32(83, 135, 80)]))

        Entity(parent=root, model="sphere", position=(0, .52, 0), scale=(1.9, .23, 1.9),
               color=color.rgb32(241, 205, 116))
        for marker in range(16):
            angle = marker * math.tau / 16
            Entity(parent=root, model="sphere",
                   position=(math.cos(angle) * 3.15, .38, math.sin(angle) * 3.15),
                   scale=(.15, .12, .15), color=color.rgb32(255, 227, 145))
        return root


class EnvelopingIslandFeature(LandscapeFeatures):
    """Build a broad island shelf bordered by high, broken cliff walls."""

    def __init__(self):
        self.colliders = []

    def build(self):
        rock = color.rgb32(91, 86, 83)
        Entity(model=Cylinder(), position=(0, -13.5, 104), scale=(82, 7, 252),
               color=color.rgb32(103, 99, 89))

        # Staggered cliff mesas create an enclosing canyon while leaving the
        # center of the route open for flight.
        for side in (-1, 1):
            for index, z in enumerate(range(-3, 225, 19)):
                x = side * random.uniform(23, 26)
                width = random.uniform(12, 17)
                depth = random.uniform(15, 21)
                height = random.uniform(12, 19)
                center_y = -6.5 + height / 2
                cliff_color = rock.tint(random.uniform(-.08, .06))
                Entity(model=Cylinder(), position=(x, -6.5, z),
                       scale=(width, height, depth), color=cliff_color)
                Entity(model=Cylinder(), position=(x - side * .4, -6.5 + height * .62, z + 1),
                       scale=(width * .78, height * .38, depth * .82),
                       color=cliff_color.tint(.035))
                self.colliders.append((Vec3(x, center_y, z),
                                       Vec3(width * .42, height * .5, depth * .42)))
        return self.colliders


class RockArchFeature(LandscapeFeatures):
    """A stone gate with a low opening and a route over its crown."""

    def __init__(self, center_x, z, spring_y=7.6, radius=4.7):
        self.center = Vec3(center_x, 0, z)
        self.spring_y = spring_y
        self.radius = radius
        self.colliders = []

    def build(self):
        stone_colors = [color.rgb32(122, 111, 100), color.rgb32(139, 126, 111),
                        color.rgb32(105, 101, 96)]
        pier_x = self.radius + .9
        pier_bottom = -6.5
        pier_height = self.spring_y - pier_bottom
        pier_center_y = pier_bottom + pier_height / 2
        for side in (-1, 1):
            Entity(model=Cylinder(),
                   position=(self.center.x + side * pier_x, pier_bottom, self.center.z),
                   scale=(2.8, pier_height, 3.8), color=random.choice(stone_colors))
            self.colliders.append((Vec3(self.center.x + side * pier_x, pier_center_y, self.center.z),
                                   Vec3(1.35, pier_height / 2, 1.9)))

        for degrees in range(10, 171, 20):
            angle = math.radians(degrees)
            x = self.center.x + math.cos(angle) * self.radius
            stone_width, stone_height, stone_depth = 1.75, 1.2, 3.8
            tangent_angle = degrees + 90
            radians = math.radians(tangent_angle)
            half_x = (abs(math.cos(radians)) * stone_width
                      + abs(math.sin(radians)) * stone_height) / 2
            half_y = (abs(math.sin(radians)) * stone_width
                      + abs(math.cos(radians)) * stone_height) / 2
            arc_y = self.spring_y + math.sin(angle) * self.radius
            # Keep the underside of the two end stones flush with the support tops.
            y = max(arc_y, self.spring_y + half_y)
            Entity(model="cube", position=(x, y, self.center.z),
                   scale=(stone_width, stone_height, stone_depth),
                   rotation_z=tangent_angle, color=random.choice(stone_colors))

            # Use the rotated block's approximate axis-aligned bounds for hits.
            self.colliders.append((Vec3(x, y, self.center.z),
                                   Vec3(half_x + .08, half_y + .08, stone_depth / 2)))
        return self.colliders


class WindGust(LandscapeFeatures):
    """A visible spherical wind volume that pushes anything flying through it."""

    def __init__(self, center, radius, direction, speed, particle_count=24):
        self.center = Vec3(*center)
        self.radius = radius
        self.direction = Vec3(*direction).normalized()
        self.wind_velocity = self.direction * speed
        self.particle_count = particle_count
        self.particles = []
        self.region_motes = []
        self.elapsed = 0
        self.stream_speed = max(7.0, speed * 2.2)
        reference = Vec3(0, 1, 0) if abs(self.direction.y) < .9 else Vec3(1, 0, 0)
        self.side = self.direction.cross(reference).normalized()
        self.up = self.direction.cross(self.side).normalized()

    def build(self):
        # A loose, drifting veil marks the gust's approximate edge without a
        # hard geometric shell. Faster streaks inside it reveal wind direction.
        for _ in range(48):
            mote = Entity(model="sphere",
                          scale=random.uniform(.18, .34),
                          color=color.rgb32(160, 218, 222), unlit=True)
            mote.alpha = random.uniform(.16, .3)
            mote.position = self._spawn_mote_position()
            self.region_motes.append((mote, random.uniform(0, math.tau)))

        streak_color = color.rgb32(255, 235, 157)
        for _ in range(self.particle_count):
            particle = Entity(model="sphere", scale=(.075, .075, .62),
                              color=streak_color, unlit=True)
            particle.position = self._spawn_position()
            particle.look_at(particle.position + self.direction)
            self.particles.append(particle)
        return self.particles

    def _spawn_mote_position(self):
        direction = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                         random.uniform(-1, 1))
        while direction.length() < .01:
            direction = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                             random.uniform(-1, 1))
        return self.center + direction.normalized() * random.uniform(
            self.radius * .78, self.radius * .99)

    def _spawn_position(self):
        along = random.uniform(-self.radius * .82, -self.radius * .25)
        radial_limit = math.sqrt(max(0, self.radius ** 2 - along ** 2)) * .72
        radial = math.sqrt(random.random()) * radial_limit
        angle = random.random() * math.tau
        offset = (self.direction * along
                  + self.side * (math.cos(angle) * radial)
                  + self.up * (math.sin(angle) * radial))
        return self.center + offset

    def velocity_at(self, position):
        distance_from_center = distance(position, self.center)
        if distance_from_center >= self.radius:
            return Vec3(0, 0, 0)
        falloff = 1 - distance_from_center / self.radius
        return self.wind_velocity * falloff

    def update(self, dt):
        self.elapsed += dt
        for mote, phase in self.region_motes:
            drift = (self.direction * .55
                     + self.side * (math.sin(self.elapsed * .8 + phase) * .18)
                     + self.up * (math.cos(self.elapsed * .65 + phase) * .18))
            mote.position += drift * dt
            if distance(mote.position, self.center) >= self.radius:
                mote.position = self._spawn_mote_position()

        for particle in self.particles:
            particle.position += self.direction * self.stream_speed * dt
            if distance(particle.position, self.center) >= self.radius - .3:
                particle.position = self._spawn_position()
            particle.look_at(particle.position + self.direction)


class MainAvatar(ABC):
    """Contract for the avatar controlled by the player."""

    @abstractmethod
    def build(self, position):
        """Create and return the avatar's scene entity."""

    @abstractmethod
    def animate(self, elapsed_time):
        """Update the avatar's idle or flight animation."""


class BirdAvatar(MainAvatar):
    def __init__(self, position):
        self.entity = self.build(position)

    def build(self, position):
        bird = Entity(position=position)
        Entity(parent=bird, model="sphere", scale=(1.25, .78, 1.65),
               color=color.rgb32(247, 164, 67))
        Entity(parent=bird, model="sphere", position=(0, .48, .95), scale=(.62, .62, .65),
               color=color.rgb32(255, 193, 93))
        Entity(parent=bird, model=Cone(), position=(0, .34, 1.68), rotation_x=90,
               scale=(.32, .68, .32), color=color.rgb32(230, 103, 53))
        for side in (-1, 1):
            Entity(parent=bird, model="sphere", position=(side * .28, .58, 1.2),
                   scale=.13, color=color.white)
            Entity(parent=bird, model="sphere", position=(side * .32, .59, 1.3),
                   scale=.07, color=color.black)
        self.wings = []
        for side in (-1, 1):
            wing = Entity(parent=bird, model="sphere", position=(side * .95, .02, -.05),
                          scale=(.32, .16, 1.1), rotation_z=side * -12,
                          color=color.rgb32(212, 115, 52))
            self.wings.append((wing, side))
        Entity(parent=bird, model="sphere", position=(0, .04, -1.0),
               scale=(.42, .25, .68), color=color.rgb32(255, 204, 115))
        return bird

    def animate(self, elapsed_time):
        flap = math.sin(elapsed_time * 15) * 34
        for wing, side in self.wings:
            wing.rotation_z = side * (-12 + flap)


class GameAvatars(ABC):
    """Contract for non-player avatars in the game world."""

    @abstractmethod
    def build(self, position):
        """Create and return the avatar's scene entity."""

    @abstractmethod
    def animate(self, phase):
        """Update the avatar's movement animation."""


class PredatorAvatar(GameAvatars):
    def __init__(self, position):
        self.entity = self.build(position)

    def build(self, position):
        body = Entity(model="sphere", scale=1.35, color=color.rgb32(83, 44, 104))
        Entity(parent=body, model="sphere", position=(0, .38, .67), scale=(.58, .54, .58),
               color=color.rgb32(119, 59, 125))
        Entity(parent=body, model=Cone(), position=(0, .22, 1.2), rotation_x=90,
               scale=(.3, .58, .3), color=color.rgb32(255, 151, 55))
        for side in (-1, 1):
            Entity(parent=body, model="sphere", position=(side * .28, .61, .99),
                   scale=.13, color=color.white)
            Entity(parent=body, model="sphere", position=(side * .31, .62, 1.08),
                   scale=.065, color=color.rgb32(25, 20, 35))
        self.wings = []
        for side in (-1, 1):
            wing = Entity(parent=body, model="sphere", position=(side * .78, .02, -.12),
                          scale=(.34, .18, 1.25), rotation_z=side * -18,
                          color=color.rgb32(48, 35, 83))
            Entity(parent=wing, model="sphere", position=(0, 0, .55), scale=(1, 1, .3),
                   color=color.rgb32(220, 104, 119))
            self.wings.append((wing, side))
        body.position = position
        return body

    def animate(self, phase):
        for wing, side in self.wings:
            wing.rotation_z = side * (-18 + math.sin(phase * 5) * 38)


class FlockingBird(GameAvatars):
    """A small, non-hostile bird steered by its flock's boid rules."""

    def __init__(self, position):
        self.entity = self.build(position)
        self.entity.scale = .68
        self.velocity = 4.0 *Vec3(random.uniform(-1, 1), random.uniform(-.5, .5),
                             random.uniform(-.8, .8))
        self.phase = random.uniform(0, math.tau)

    def build(self, position):
        body = Entity(position=position)
        Entity(parent=body, model="sphere", scale=(1.2, .7, 1.5),
               color=color.rgb32(39, 151, 168))
        Entity(parent=body, model="sphere", position=(0, .38, .83), scale=(.58, .56, .58),
               color=color.rgb32(91, 198, 184))
        Entity(parent=body, model=Cone(), position=(0, .25, 1.4), rotation_x=90,
               scale=(.26, .5, .26), color=color.rgb32(244, 181, 75))
        for side in (-1, 1):
            Entity(parent=body, model="sphere", position=(side * .25, .56, 1.02),
                   scale=.11, color=color.white)
            Entity(parent=body, model="sphere", position=(side * .28, .57, 1.1),
                   scale=.055, color=color.rgb32(20, 45, 55))
        self.wings = []
        for side in (-1, 1):
            wing = Entity(parent=body, model="sphere", position=(side * .73, .02, -.08),
                          scale=(.32, .14, 1.0), rotation_z=side * -14,
                          color=color.rgb32(29, 112, 139))
            self.wings.append((wing, side))
        body.position = position
        return body

    def animate(self, phase):
        for wing, side in self.wings:
            wing.rotation_z = side * (-14 + math.sin(phase + self.phase) * 32)


class BirdFlock:
    """A wandering obstacle group with cohesion, alignment, and separation."""

    def __init__(self, center, bird_count=6):
        self.anchor = Vec3(*center)
        self.birds = []
        self.wander_target = Vec3(0, 0, 0)
        self.wander_timer = 0
        for _ in range(bird_count):
            offset = Vec3(random.uniform(-2.4, 2.4), random.uniform(-1.4, 1.4),
                          random.uniform(-2.4, 2.4))
            self.birds.append(FlockingBird(self.anchor + offset))

    @staticmethod
    def _limit(vector, maximum):
        length = vector.length()
        return vector.normalized() * maximum if length > maximum else vector

    def update(self, dt, elapsed_time, wind_at=None):
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_timer = random.uniform(1.0, 2.2)
            self.wander_target = Vec3(random.uniform(-5.0, 5.0),
                                      random.uniform(-3.0, 3.0),
                                      random.uniform(-2.5, 2.5))

        positions = [bird.entity.position for bird in self.birds]
        center = Vec3(0, 0, 0)
        average_velocity = Vec3(0, 0, 0)
        for bird, position in zip(self.birds, positions):
            center += position
            average_velocity += bird.velocity
        center /= len(self.birds)
        average_velocity /= len(self.birds)
        for index, bird in enumerate(self.birds):
            cohesion = (center - bird.entity.position) * .34
            alignment = (average_velocity - bird.velocity) * .55
            separation = Vec3(0, 0, 0)
            for other_index, other in enumerate(self.birds):
                if other_index == index:
                    continue
                away = bird.entity.position - other.entity.position
                gap = away.length()
                if .001 < gap < 2.1:
                    separation += away.normalized() * ((2.1 - gap) * .95)

            desired = self.anchor + self.wander_target
            wander = (desired - bird.entity.position) * .16
            velocity = bird.velocity + (cohesion + alignment + separation + wander) * dt
            bird.velocity = self._limit(velocity, 2.8)
            wind_velocity = wind_at(bird.entity.position) if wind_at else Vec3(0, 0, 0)
            bird.entity.position += (bird.velocity + wind_velocity) * dt
            bird.entity.x = max(self.anchor.x - 8, min(self.anchor.x + 8, bird.entity.x))
            bird.entity.y = max(1, min(20, bird.entity.y))
            bird.entity.z = max(self.anchor.z - 5, min(self.anchor.z + 5, bird.entity.z))
            if bird.velocity.length() > .1:
                bird.entity.look_at(bird.entity.position + bird.velocity)
            bird.animate(elapsed_time * 7)

    def collides_with(self, position, radius=1.55):
        return any(distance(bird.entity.position, position) < radius for bird in self.birds)


class BirdFlightGame:
    def __init__(self):
        random.seed(12)
        WaterFeature().build()
        self.terrain_colliders = EnvelopingIslandFeature().build()
        for index, position in enumerate(ROUTE):
            IslandFeature(position, index).build()

        AmbientLight(color=color.rgba32(170, 190, 210, 255))
        sun = DirectionalLight(color=color.rgb32(255, 239, 207))
        sun.look_at(Vec3(1, -2, -1))

        start = Vec3(ROUTE[0][0], ROUTE[0][1] + 2.0, ROUTE[0][2] - 3)
        self.bird = BirdAvatar(start)
        self.predators = [
            PredatorAvatar(start + Vec3(-9, random.uniform(-1.5, 1.5), -8)),
            PredatorAvatar(start + Vec3(10, random.uniform(-1.5, 1.5), -8)),
        ]
        self.flocks = []
        for index in range(len(ROUTE) - 1):
            x1, y1, z1 = ROUTE[index]
            x2, y2, z2 = ROUTE[index + 1]
            fraction = .35
            center = (x1 + (x2 - x1) * fraction,
                      y1 + (y2 - y1) * fraction + 1.5,
                      z1 + (z2 - z1) * fraction)
            self.flocks.append(BirdFlock(center, bird_count=6))
        self.arches = []
        for index in (0, 2, 4):
            x1, y1, z1 = ROUTE[index]
            x2, y2, z2 = ROUTE[index + 1]
            fraction = .75
            arch = RockArchFeature(x1 + (x2 - x1) * fraction,
                                   z1 + (z2 - z1) * fraction)
            self.terrain_colliders.extend(arch.build())
            self.arches.append(arch)
        self.wind_gusts = []
        gust_specs = [
            (1, .72, (1.0, .22, .32), 4.6),
            (3, .72, (-.9, .3, .38), 4.8),
        ]
        for index, fraction, direction, speed in gust_specs:
            x1, y1, z1 = ROUTE[index]
            x2, y2, z2 = ROUTE[index + 1]
            center = (x1 + (x2 - x1) * fraction,
                      y1 + (y2 - y1) * fraction + 1.4,
                      z1 + (z2 - z1) * fraction)
            gust = WindGust(center, radius=7.5, direction=direction, speed=speed)
            gust.build()
            self.wind_gusts.append(gust)
        self._create_hud()
        self.speed_z = 8.6
        self.reset_run()

    def _create_hud(self):
        Text("BIRDFLIGHT", parent=camera.ui, position=(-.86, .45), scale=1.3,
             color=HUD_COLOR)
        Text("WASD / arrows: steer     SPACE: flap boost     R: restart",
             parent=camera.ui, position=(-.86, .405), scale=.75, color=HUD_COLOR)
        Text("TEAL: DODGE  |  ARCHES: LOW/HIGH  |  WIND CLOUD: AREA / GOLD: FLOW",
             parent=camera.ui, position=(-.86, .375), scale=.65,
             color=color.rgb32(19, 112, 125))
        self.progress_text = Text("", parent=camera.ui, position=(-.86, .34),
                                  scale=.9, color=HUD_COLOR)
        self.status_text = Text("", parent=camera.ui, origin=(0, 0), position=(0, .34),
                                scale=1.5, color=HUD_COLOR)
        self.heart_text = Text("", parent=camera.ui, position=(.67, .45),
                               scale=1.1, color=HUD_COLOR)

    def reset_run(self):
        self.checkpoint = 0
        self.lives = 3
        self.landed_count = 0
        self.invulnerable = 1.5
        self.game_over = False
        self.won = False
        bird = self.bird.entity
        bird.position = Vec3(ROUTE[0][0], ROUTE[0][1] + 2.0, ROUTE[0][2] - 3)
        bird.rotation = Vec3(0, 0, 0)
        camera.position = bird.position + Vec3(0, 9.5, -23)
        camera.rotation = Vec3(0, 0, 0)
        camera.look_at(bird.position + Vec3(0, 1.5, 12))
        for index, predator in enumerate(self.predators):
            predator.entity.position = bird.position + Vec3((-5, 5)[index], 0, -6)
        self.status_text.text = ""

    def lose_life(self, reason="Flight setback"):
        self.lives -= 1
        self.invulnerable = 2.2
        if self.lives <= 0:
            self.game_over = True
            self.status_text.text = f"FLIGHT OVER — {reason.upper()}  ·  Press R to try again"
            self.status_text.color = HUD_COLOR
            return

        x, y, z = ROUTE[self.checkpoint]
        self.bird.entity.position = Vec3(x, y + 2.4, z + 3.5)
        self.status_text.text = f"{reason} — back at your last nest; steer for the next marker!"
        for index, predator in enumerate(self.predators):
            predator.entity.position = self.bird.entity.position + Vec3((-5, 5)[index], 0, -7 - index)

    def handle_input(self, key):
        bird = self.bird.entity
        if key == "r":
            self.reset_run()
        elif key in ("a", "left"):
            bird.x = max(-25, bird.x - 1.4)
        elif key in ("d", "right"):
            bird.x = min(25, bird.x + 1.4)
        elif key in ("w", "up"):
            bird.y = min(25, bird.y + 1.2)
        elif key in ("s", "down"):
            bird.y = max(-1, bird.y - 1.2)

    def update(self):
        dt = min(time.dt, .04)
        if self.game_over or self.won:
            return

        for gust in self.wind_gusts:
            gust.update(dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        bird = self.bird.entity
        horizontal = held_keys["d"] + held_keys["right"] - held_keys["a"] - held_keys["left"]
        vertical = held_keys["w"] + held_keys["up"] - held_keys["s"] - held_keys["down"]
        boost = 1.55 if held_keys["space"] else 1.0
        wind_velocity = self._wind_velocity_at(bird.position)
        bird.x += (horizontal * 10.0 + wind_velocity.x) * dt
        bird.y += (vertical * 8.2 + wind_velocity.y) * dt
        bird.z += (self.speed_z * boost + wind_velocity.z) * dt
        bird.y = max(-1.0, min(25.0, bird.y))
        bird.x = max(-25.0, min(25.0, bird.x))
        bird.rotation_z = lerp(bird.rotation_z, -horizontal * 20, dt * 5)
        bird.rotation_x = lerp(bird.rotation_x, vertical * 12, dt * 4)
        self.bird.animate(time.time())

        if not self._check_checkpoint():
            return
        self._update_terrain_collisions()
        self._update_flocks(dt)
        self._update_predators(dt)
        self._update_camera_and_hud()

    def _check_checkpoint(self):
        if self.checkpoint + 1 >= len(ROUTE):
            return True

        bird = self.bird.entity
        nx, ny, nz = ROUTE[self.checkpoint + 1]
        if abs(bird.z - nz) < 3.5 and math.hypot(bird.x - nx, bird.y - (ny + 1.4)) < NEST_RADIUS:
            self.checkpoint += 1
            self.landed_count += 1
            self.status_text.text = "SAFE NEST REACHED!  +1 heart"
            self.status_text.color = HUD_COLOR
            if self.lives < 3:
                self.lives += 1
            for index, predator in enumerate(self.predators):
                predator.entity.position = bird.position + Vec3(
                    (-5, 5)[index], random.uniform(-1, 1), -7 - index)
            if self.checkpoint == len(ROUTE) - 1:
                self.won = True
                self.status_text.text = "HOME AT LAST!  ·  Press R to fly again"
            return True

        if bird.z > nz + 5:
            self.lose_life("Missed the nest")
            return False
        return True

    def _update_predators(self, dt):
        bird = self.bird.entity
        for index, predator in enumerate(self.predators):
            phase = time.time() * 1.35 + index * math.pi
            target = bird.position + Vec3(
                math.cos(phase) * 2.5,
                .65 + math.sin(phase * 1.6) * 1.0,
                -1.0 + math.sin(phase * .8) * 1.8,
            )
            enemy = predator.entity
            enemy.position = lerp(enemy.position, target, min(1, dt * 1.5))
            enemy.position += self._wind_velocity_at(enemy.position) * dt
            enemy.look_at(bird.position)
            enemy.rotation_x = math.sin(phase * 2) * 12
            predator.animate(phase)
            if self.invulnerable <= 0 and distance(enemy.position, bird.position) < 2.35:
                self.lose_life("Predator strike")
                break

    def _update_flocks(self, dt):
        bird_position = self.bird.entity.position
        for flock in self.flocks:
            flock.update(dt, time.time(), self._wind_velocity_at)
            if self.invulnerable <= 0 and flock.collides_with(bird_position):
                self.lose_life("Flock collision")
                return

    def _update_terrain_collisions(self):
        position = self.bird.entity.position
        bird_radius = Vec3(.8, .65, 1.0)
        for center, half_extents in self.terrain_colliders:
            if (abs(position.x - center.x) < half_extents.x + bird_radius.x
                    and abs(position.y - center.y) < half_extents.y + bird_radius.y
                    and abs(position.z - center.z) < half_extents.z + bird_radius.z):
                self.lose_life("Rock collision")
                return

    def _wind_velocity_at(self, position):
        wind = Vec3(0, 0, 0)
        for gust in self.wind_gusts:
            wind += gust.velocity_at(position)
        return wind

    def _update_camera_and_hud(self):
        bird = self.bird.entity
        dt = min(time.dt, .04)
        camera.position = lerp(camera.position, bird.position + Vec3(0, 9.5, -23), dt * 2.8)
        camera.look_at(bird.position + Vec3(0, 1.5, 12))
        camera.fov = 72
        remaining = max(0, int((ROUTE[-1][2] - bird.z) / 10))
        self.progress_text.text = (
            f"NEST {self.checkpoint + 1}/{len(ROUTE)}     Distance {remaining}"
        )
        self.heart_text.text = f"LIVES: {self.lives}"
        if self.invulnerable > 0 and not self.won:
            bird.alpha = .45 if int(time.time() * 12) % 2 else 1
        else:
            bird.alpha = 1


game = None


def input(key):
    if game is not None:
        game.handle_input(key)


def update():
    if game is not None:
        game.update()


def main():
    global game
    application = Ursina(title="BirdFlight OOP", borderless=False, fullscreen=False,
                         development_mode=False, editor_ui_enabled=False)
    window.color = color.rgb32(125, 194, 220)
    window.fps_counter.enabled = False
    game = BirdFlightGame()
    bird = game.bird.entity
    camera.position = bird.position + Vec3(0, 9.5, -23)
    camera.look_at(bird.position + Vec3(0, 1.5, 12))
    application.run()


if __name__ == "__main__":
    main()
