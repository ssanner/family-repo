"""A small third-person game about flying a dragon through a forest."""
import math
import random

from ursina import *
from ursina.models.procedural.cone import Cone
from ursina.shaders import lit_with_shadows_shader


GOAL_Z = 270
FOREST_START = 16
FOREST_END = GOAL_Z - 9
FOREST_WIDTH = 23
CANOPY_HEIGHT = 14
FLIGHT_CEILING = 6.2
PLAYER_START = Vec3(0, 5, 0)
HUD_COLOR = color.rgb32(28, 45, 39)


class Forest:
    """A dense, procedurally arranged forest with a clear flying course."""

    def __init__(self, seed=12):
        self.random = random.Random(seed)
        self.tree_colliders = []
        self._build_ground()
        self._build_trees()
        self._build_goal()

    def _build_ground(self):
        Entity(model="plane", position=(0, -.8, GOAL_Z / 2),
               scale=(100, 1, GOAL_Z + 140),
               color=color.rgb32(77, 105, 58),
               texture="white_cube", texture_scale=(48, 150),
               shader=lit_with_shadows_shader)
        # Low ferns and moss add texture to the ground without closing the route.
        for _ in range(190):
            x = self.random.uniform(-FOREST_WIDTH, FOREST_WIDTH)
            z = self.random.uniform(FOREST_START, FOREST_END)
            height = self.random.uniform(.35, .8)
            Entity(model="sphere", position=(x, -.28 + height / 2, z),
                   scale=(.35, height, .45),
                   color=self.random.choice((color.rgb32(58, 113, 66),
                                             color.rgb32(83, 130, 65),
                                             color.rgb32(105, 139, 74))),
                   unlit=True)

    def _build_trees(self):
        # Staggered rows leave several broad gaps in every section of the run.
        lanes = [-20, -14, -8, -2, 4, 10, 16, 22]
        for row, z in enumerate(range(FOREST_START, FOREST_END, 13)):
            missing = set(self.random.sample(range(len(lanes)),
                                             self.random.choice((2, 3))))
            for lane_index, lane_x in enumerate(lanes):
                if lane_index in missing:
                    continue
                x = lane_x + self.random.uniform(-1.0, 1.0)
                tree_z = z + (6.0 if row % 2 else 0) + self.random.uniform(-1, 1)
                trunk_height = self.random.uniform(8.2, 10.5)
                trunk_width = self.random.uniform(.65, .95)
                bark = self.random.choice((color.rgb32(101, 69, 48),
                                           color.rgb32(117, 78, 51),
                                           color.rgb32(91, 67, 50)))
                crown_color = self.random.choice((color.rgb32(40, 104, 57),
                                                  color.rgb32(48, 119, 62),
                                                  color.rgb32(63, 130, 68)))
                trunk = Entity(model=Cylinder(), position=(x, trunk_height / 2 - .8, tree_z),
                               scale=(trunk_width, trunk_height, trunk_width),
                               color=bark, shader=lit_with_shadows_shader)
                # Roots widen the base and make the trunk silhouette readable.
                Entity(parent=trunk, model="sphere", y=-.43,
                       scale=(1.9, .28, 1.9), color=bark)
                crown_y = trunk_height - .8
                for dx, dy, dz, size in ((0, 1.0, 0, 4.2), (-1.25, .45, .1, 3.25),
                                         (1.2, .35, -.25, 3.35), (.1, .45, 1.1, 3.1)):
                    Entity(model="sphere", position=(x + dx, crown_y + dy, tree_z + dz),
                           scale=(size, size * .8, size), color=crown_color,
                           shader=lit_with_shadows_shader)
                # Collision is intentionally trunk-focused: fly between trunks
                # while staying beneath the leafy canopy.
                self.tree_colliders.append((x, tree_z, trunk_width + .85,
                                            trunk_height - .1))

    def _build_goal(self):
        goal_z = GOAL_Z
        wood = color.rgb32(112, 77, 46)
        for x in (-8, 8):
            Entity(model=Cylinder(), position=(x, 5.7, goal_z),
                   scale=(1.15, 12.2, 1.15), color=wood,
                   shader=lit_with_shadows_shader)
        Entity(model="cube", position=(0, 11.4, goal_z), scale=(17.5, 1.15, 1.5),
               color=color.rgb32(192, 144, 69), shader=lit_with_shadows_shader)
        Entity(model="cube", position=(0, 6.2, goal_z - .2), scale=(.48, 11, .5),
               color=color.rgba32(111, 222, 190, 145), unlit=True)
        Entity(model=Cone(), position=(0, 6.8, goal_z), scale=(1.2, 2.5, 1.2),
               color=color.rgb32(115, 255, 202), unlit=True)
        Entity(model="sphere", position=(0, 6.2, goal_z), scale=2.8,
               color=color.rgba32(123, 255, 196, 130), unlit=True)
        Text("GOAL", position=(0, 13.7, goal_z), origin=(0, 0), scale=3,
             color=color.rgb32(255, 235, 155), billboard=True)


class Dragon:
    """Simple stylized dragon with independently animated wings."""

    def __init__(self, position, palette, scale=1.0):
        self.entity = Entity(position=position, scale=scale)
        body_color, wing_color, accent_color = palette
        Entity(parent=self.entity, model="sphere", scale=(.86, .68, 1.55),
               color=body_color)
        Entity(parent=self.entity, model="sphere", position=(0, .33, .98),
               scale=(.58, .5, .65), color=body_color)
        Entity(parent=self.entity, model="sphere", position=(0, .2, 1.48),
               scale=(.4, .3, .57), color=accent_color)
        for side in (-1, 1):
            Entity(parent=self.entity, model=Cone(),
                   position=(side * .28, .68, .93),
                   rotation_z=side * -18, scale=(.16, .55, .16),
                   color=accent_color)
            Entity(parent=self.entity, model="sphere",
                   position=(side * .22, .43, 1.2), scale=.09, color=color.white)
            Entity(parent=self.entity, model="sphere",
                   position=(side * .23, .43, 1.27), scale=.045, color=color.black)
        self.wings = []
        for side in (-1, 1):
            wing = Entity(parent=self.entity, model="sphere",
                          position=(side * .88, .05, -.1),
                          scale=(1.55, .15, .95), rotation_z=side * -12,
                          color=wing_color)
            # Raised spars give each wing a bat-like dragon silhouette.
            Entity(parent=wing, model="cube", position=(side * .28, .05, .16),
                   scale=(.055, .08, 1.25), rotation_y=-18, color=accent_color)
            self.wings.append((wing, side))
        tail = Entity(parent=self.entity, model=Cone(), position=(0, .03, -1.28),
                      rotation_x=-90, scale=(.23, 1.2, .23), color=body_color)
        Entity(parent=tail, model="sphere", position=(0, .38, 0),
               scale=(1.7, .42, .65), color=accent_color)

    def animate(self, phase, amount=1):
        flap = math.sin(phase * 13) * 38 * amount
        for wing, side in self.wings:
            wing.rotation_z = side * (-12 + flap)


class DragonFlightGame:
    def __init__(self):
        random.seed(12)
        AmbientLight(color=color.rgb32(168, 190, 162))
        sun = DirectionalLight(color=color.rgb32(255, 239, 205), shadows=True,
                               shadow_map_resolution=(1024, 1024))
        sun.look_at(Vec3(-.3, -.8, -.4))
        self.forest = Forest()
        self.player = Dragon(PLAYER_START,
                             (color.rgb32(48, 130, 105),
                              color.rgb32(39, 91, 81),
                              color.rgb32(210, 154, 78)))
        self.chasers = []
        palettes = [
            (color.rgb32(103, 56, 107), color.rgb32(59, 42, 80), color.rgb32(234, 108, 89)),
            (color.rgb32(135, 67, 54), color.rgb32(87, 49, 46), color.rgb32(247, 165, 69)),
        ]
        for index, palette in enumerate(palettes):
            self.chasers.append(Dragon(Vec3((-1 if index == 0 else 1) * 3,
                                             5 + index, -8 - index * 4),
                                       palette, scale=.9))
        self.speed = 11.5
        self.elapsed = 0
        self.lives = 3
        self.invulnerable = 1.5
        self.game_over = False
        self.won = False
        self._create_hud()
        self.reset_run()

    def _create_hud(self):
        Text("DRAGON FLIGHT", parent=camera.ui, position=(-.86, .45), scale=1.3,
             color=HUD_COLOR)
        Text("WASD / arrows: steer     SPACE: burst of speed     R: restart",
             parent=camera.ui, position=(-.86, .405), scale=.72, color=HUD_COLOR)
        Text("WEAVE BETWEEN TRUNKS  ·  STAY BELOW THE CANOPY  ·  REACH THE BEACON",
             parent=camera.ui, position=(-.86, .375), scale=.64,
             color=color.rgb32(45, 105, 66))
        self.progress_text = Text("", parent=camera.ui, position=(-.86, .34),
                                  scale=.9, color=HUD_COLOR)
        self.status_text = Text("", parent=camera.ui, origin=(0, 0), position=(0, .31),
                                scale=1.35, color=HUD_COLOR)
        self.lives_text = Text("", parent=camera.ui, position=(.72, .45),
                               scale=1.05, color=HUD_COLOR)

    def reset_run(self):
        self.player.entity.position = Vec3(PLAYER_START)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.lives = 3
        self.invulnerable = 1.5
        self.game_over = False
        self.won = False
        self.status_text.text = ""
        for index, dragon in enumerate(self.chasers):
            dragon.entity.position = Vec3((-1 if index == 0 else 1) * 3,
                                          5 + index, -8 - index * 4)
        self._update_camera()

    def handle_input(self, key):
        if key == "r":
            self.reset_run()

    def update(self):
        dt = min(time.dt, .04)
        if self.game_over or self.won:
            return
        self.elapsed += dt
        self.invulnerable = max(0, self.invulnerable - dt)
        player = self.player.entity
        horizontal = held_keys["d"] + held_keys["right"] - held_keys["a"] - held_keys["left"]
        vertical = held_keys["w"] + held_keys["up"] - held_keys["s"] - held_keys["down"]
        boost = 1.35 if held_keys["space"] else 1.0
        player.x += horizontal * 10.5 * dt
        player.y += vertical * 8.0 * dt
        player.z += self.speed * boost * dt
        player.x = max(-FOREST_WIDTH + 1.5, min(FOREST_WIDTH - 1.5, player.x))
        player.y = max(1.3, min(FLIGHT_CEILING, player.y))
        player.rotation_z = lerp(player.rotation_z, -horizontal * 22, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 12, dt * 4)
        self.player.animate(self.elapsed)

        if self.invulnerable <= 0 and self._hits_tree():
            self._lose_life("TREE STRIKE")
        self._update_chasers(dt)
        if self.lives <= 0:
            return
        if player.z >= GOAL_Z - 2:
            if abs(player.x) <= 8.0 and abs(player.y - 6.0) <= 5.2:
                self.won = True
                self.status_text.text = "FOREST CLEARED!  ·  Press R to fly again"
            else:
                self._lose_life("MISSED THE BEACON")
        self._update_camera()
        distance_left = max(0, int(GOAL_Z - player.z))
        self.progress_text.text = f"DISTANCE TO GOAL  {distance_left} m"
        self.lives_text.text = f"HEARTS: {self.lives}"
        player.alpha = (.45 if int(self.elapsed * 12) % 2 else 1) if self.invulnerable > 0 else 1

    def _hits_tree(self):
        player = self.player.entity
        for x, z, radius, height in self.forest.tree_colliders:
            if (abs(player.z - z) < 1.35
                    and abs(player.x - x) < radius + .55
                    and player.y < height - .4):
                return True
        return False

    def _lose_life(self, reason):
        self.lives -= 1
        self.invulnerable = 2.0
        if self.lives <= 0:
            self.game_over = True
            self.status_text.text = f"FLIGHT OVER — {reason}  ·  Press R to try again"
            return
        self.status_text.text = f"{reason} — shake them off and keep flying!"
        self.player.entity.position = Vec3(0, 5, max(0, self.player.entity.z - 9))
        for index, dragon in enumerate(self.chasers):
            dragon.entity.position = self.player.entity.position + Vec3(
                (-1 if index == 0 else 1) * 4, 1 + index, -9 - index * 3)

    def _update_chasers(self, dt):
        player = self.player.entity
        for index, dragon in enumerate(self.chasers):
            phase = self.elapsed * 1.2 + index * math.pi
            enemy = dragon.entity
            target = player.position + Vec3(math.sin(phase) * 3.1,
                                            1.2 + math.sin(phase * 1.6) * 1.1,
                                            -5.5 - index * 2.0)
            enemy.position = lerp(enemy.position, target, min(1, dt * 1.25))
            enemy.x = max(-FOREST_WIDTH + 1, min(FOREST_WIDTH - 1, enemy.x))
            enemy.y = max(1.5, min(FLIGHT_CEILING, enemy.y))
            enemy.look_at(player.position)
            dragon.animate(self.elapsed + index * .5)
            if self.invulnerable <= 0 and distance(enemy.position, player.position) < 2.1:
                self._lose_life("CHASER HIT")
                break

    def _update_camera(self):
        player = self.player.entity
        dt = min(time.dt, .04)
        camera.position = lerp(camera.position,
                               player.position + Vec3(0, 7.2, -17), dt * 3.2)
        camera.look_at(player.position + Vec3(0, .8, 11))
        camera.fov = 76


game = None


def input(key):
    if game is not None:
        game.handle_input(key)


def update():
    if game is not None:
        game.update()


def main():
    global game
    application = Ursina(title="DragonFlight", borderless=False, fullscreen=False,
                         development_mode=False, editor_ui_enabled=False)
    window.color = color.rgb32(132, 184, 177)
    window.fps_counter.enabled = False
    game = DragonFlightGame()
    application.run()


if __name__ == "__main__":
    main()
