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

    def update(self, dt, elapsed_time):
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
            bird.entity.position += bird.velocity * dt
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
            center = ((x1 + x2) / 2, (y1 + y2) / 2 + 1.5, (z1 + z2) / 2)
            self.flocks.append(BirdFlock(center, bird_count=6))
        self._create_hud()
        self.speed_z = 8.6
        self.reset_run()

    def _create_hud(self):
        Text("BIRDFLIGHT", parent=camera.ui, position=(-.86, .45), scale=1.3,
             color=HUD_COLOR)
        Text("WASD / arrows: steer     SPACE: flap boost     R: restart",
             parent=camera.ui, position=(-.86, .405), scale=.75, color=HUD_COLOR)
        Text("DODGE THE TEAL FLOCKS",
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

    def lose_life(self):
        self.lives -= 1
        self.invulnerable = 2.2
        if self.lives <= 0:
            self.game_over = True
            self.status_text.text = "THE WIND CAUGHT YOU  ·  Press R to try again"
            self.status_text.color = HUD_COLOR
            return

        x, y, z = ROUTE[self.checkpoint]
        self.bird.entity.position = Vec3(x, y + 2.4, z + 3.5)
        self.status_text.text = "Back to your last nest — steer for the next marker!"
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

        self.invulnerable = max(0, self.invulnerable - dt)
        bird = self.bird.entity
        horizontal = held_keys["d"] + held_keys["right"] - held_keys["a"] - held_keys["left"]
        vertical = held_keys["w"] + held_keys["up"] - held_keys["s"] - held_keys["down"]
        boost = 1.55 if held_keys["space"] else 1.0
        bird.x += horizontal * 10.0 * dt
        bird.y += vertical * 8.2 * dt
        bird.z += self.speed_z * boost * dt
        bird.y = max(-1.0, min(25.0, bird.y))
        bird.x = max(-25.0, min(25.0, bird.x))
        bird.rotation_z = lerp(bird.rotation_z, -horizontal * 20, dt * 5)
        bird.rotation_x = lerp(bird.rotation_x, vertical * 12, dt * 4)
        self.bird.animate(time.time())

        if not self._check_checkpoint():
            return
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
            self.lose_life()
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
            enemy.look_at(bird.position)
            enemy.rotation_x = math.sin(phase * 2) * 12
            predator.animate(phase)
            if self.invulnerable <= 0 and distance(enemy.position, bird.position) < 2.35:
                self.lose_life()
                break

    def _update_flocks(self, dt):
        bird_position = self.bird.entity.position
        for flock in self.flocks:
            flock.update(dt, time.time())
            if self.invulnerable <= 0 and flock.collides_with(bird_position):
                self.lose_life()
                if not self.game_over:
                    self.status_text.text = "Flock collision — back at your last nest"
                    self.status_text.color = HUD_COLOR
                return

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
