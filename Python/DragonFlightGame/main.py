"""A small third-person game about flying a dragon through a forest."""
import math
import random

from ursina import *
from ursina.models.procedural.cone import Cone
from ursina.shaders import lit_with_shadows_shader
from quest import FireClanQuest, HoopQuest, TreeCanopyQuest
from quest import WaterJourneyQuest


GOAL_Z = 270
FOREST_START = 16
FOREST_END = GOAL_Z - 9
FOREST_WIDTH = 23
CANOPY_HEIGHT = 14
FLIGHT_CEILING = 10.5
PLAYER_START = Vec3(0, 5, 0)
HUD_COLOR = color.rgb32(28, 45, 39)


class Forest:
    """A dense, procedurally arranged forest with a clear flying course."""

    def __init__(self, seed=12):
        self.random = random.Random(seed)
        self.tree_colliders = []
        self.root = Entity(name="forest_world")
        self._build_ground()
        self._build_trees()
        self._build_goal()

    def _build_ground(self):
        Entity(parent=self.root, model="plane", position=(0, -.8, GOAL_Z / 2),
               scale=(100, 1, GOAL_Z + 140),
               color=color.rgb32(77, 105, 58),
               texture="white_cube", texture_scale=(48, 150),
               shader=lit_with_shadows_shader)
        # Low ferns and moss add texture to the ground without closing the route.
        for _ in range(190):
            x = self.random.uniform(-FOREST_WIDTH, FOREST_WIDTH)
            z = self.random.uniform(FOREST_START, FOREST_END)
            height = self.random.uniform(.35, .8)
            Entity(parent=self.root, model="sphere", position=(x, -.28 + height / 2, z),
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
                # Crown height varies across the forest. Each trunk grows into
                # its crown so the tree reads as one connected shape.
                canopy_center_y = self.random.uniform(6.8, 12.2)
                trunk_height = canopy_center_y + .3
                trunk_width = self.random.uniform(.65, .95)
                bark = self.random.choice((color.rgb32(101, 69, 48),
                                           color.rgb32(117, 78, 51),
                                           color.rgb32(91, 67, 50)))
                crown_color = self.random.choice((color.rgb32(40, 104, 57),
                                                  color.rgb32(48, 119, 62),
                                                  color.rgb32(63, 130, 68)))
                trunk = Entity(parent=self.root, model=Cylinder(),
                               position=(x, -.8, tree_z),
                               scale=(trunk_width, trunk_height, trunk_width),
                               color=bark, shader=lit_with_shadows_shader)
                # Roots widen the base and make the trunk silhouette readable.
                Entity(parent=self.root, model="sphere", position=(x, -.66, tree_z),
                       scale=(trunk_width * 2.2, .3, trunk_width * 2.2), color=bark)
                crown_y = canopy_center_y
                canopy_colliders = []
                for dx, dy, dz, size in ((0, 1.0, 0, 4.2), (-1.25, .45, .1, 3.25),
                                         (1.2, .35, -.25, 3.35), (.1, .45, 1.1, 3.1)):
                    Entity(parent=self.root, model="sphere",
                           position=(x + dx, crown_y + dy, tree_z + dz),
                           scale=(size, size * .8, size), color=crown_color,
                           shader=lit_with_shadows_shader)
                    canopy_colliders.append((x + dx, crown_y + dy, tree_z + dz,
                                             size * .5, size * .4, size * .5))
                # Collision is intentionally trunk-focused: fly between trunks
                # while staying beneath the leafy canopy.
                self.tree_colliders.append((x, tree_z, trunk_width * .5,
                                            -.8, canopy_center_y - .5,
                                            canopy_colliders))

    def _build_goal(self):
        goal_z = GOAL_Z
        wood = color.rgb32(112, 77, 46)
        for x in (-8, 8):
            Entity(parent=self.root, model=Cylinder(), position=(x, -.8, goal_z),
                   scale=(1.15, 12.2, 1.15), color=wood,
                   shader=lit_with_shadows_shader)
        Entity(parent=self.root, model="cube", position=(0, 11.4, goal_z),
               scale=(17.5, 1.15, 1.5),
               color=color.rgb32(192, 144, 69), shader=lit_with_shadows_shader)
        Entity(parent=self.root, model="cube", position=(0, 6.2, goal_z - .2),
               scale=(.48, 11, .5),
               color=color.rgba32(111, 222, 190, 145), unlit=True)
        Entity(parent=self.root, model=Cone(), position=(0, 6.8, goal_z),
               scale=(1.2, 2.5, 1.2),
               color=color.rgb32(115, 255, 202), unlit=True)
        Entity(parent=self.root, model="sphere", position=(0, 6.2, goal_z), scale=2.8,
               color=color.rgba32(123, 255, 196, 130), unlit=True)
        Text("GOAL", parent=self.root, position=(0, 13.7, goal_z), origin=(0, 0), scale=3,
             color=color.rgb32(255, 235, 155), billboard=True)


class WhiteRoom:
    """An empty white room used as the post-goal destination."""

    def __init__(self):
        self.root = Entity(name="white_room", enabled=False)
        wall_color = color.white
        Entity(parent=self.root, model="cube", position=(0, -.35, 0),
               scale=(24, .7, 24), color=wall_color, unlit=True)
        Entity(parent=self.root, model="cube", position=(0, 10.5, 0),
               scale=(24, .7, 24), color=wall_color, unlit=True)
        for x in (-12, 12):
            Entity(parent=self.root, model="cube", position=(x, 5, 0),
                   scale=(.7, 11, 24), color=wall_color, unlit=True)
        for z in (-12, 12):
            Entity(parent=self.root, model="cube", position=(0, 5, z),
                   scale=(24, 11, .7), color=wall_color, unlit=True)


class HoopStage:
    """An open flight lane with six visible hoops arranged in a 3D path."""

    def __init__(self):
        self.root = Entity(name="hoop_stage", enabled=False)
        Entity(parent=self.root, model="plane", position=(0, -.8, 48),
               scale=(48, 1, 125), color=color.rgb32(184, 222, 224), unlit=True)
        Entity(parent=self.root, model="cube", position=(0, 18, 48),
               scale=(48, .5, 125), color=color.rgb32(198, 229, 229), unlit=True)
        centers = ((-3.5, 4.4), (2.5, 6.0), (4.5, 3.5), (-1.5, 2.8),
                   (-4.0, 6.2), (1.5, 5.0))
        self.hoops = []
        for index, (x, y) in enumerate(centers):
            z = 12 + index * 18
            hoop = Entity(parent=self.root, position=(x, y, z))
            for segment in range(24):
                angle = math.tau * segment / 24
                Entity(parent=hoop, model="sphere",
                       position=(math.cos(angle) * 3.0,
                                 math.sin(angle) * 3.0, 0),
                       scale=.62, color=color.rgb32(255, 205, 35), unlit=True)
            self.hoops.append((Vec3(x, y, z), hoop))


class Dragon:
    """Simple stylized dragon with independently animated wings."""

    def __init__(self, position, palette, scale=1.0, parent=None):
        if parent is None:
            self.entity = Entity(position=position, scale=scale)
        else:
            self.entity = Entity(parent=parent, position=position, scale=scale)
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
    GOAL_Z = GOAL_Z
    FOREST_WIDTH = FOREST_WIDTH
    FLIGHT_CEILING = FLIGHT_CEILING
    PLAYER_START = PLAYER_START

    def __init__(self):
        random.seed(12)
        AmbientLight(color=color.rgb32(168, 190, 162))
        sun = DirectionalLight(color=color.rgb32(255, 239, 205), shadows=True,
                               shadow_map_resolution=(1024, 1024))
        sun.look_at(Vec3(-.3, -.8, -.4))
        self.forest = Forest()
        self.room = WhiteRoom()
        self.hoop_stage = HoopStage()
        self.player = Dragon(PLAYER_START,
                             (color.rgb32(48, 130, 105),
                              color.rgb32(39, 91, 81),
                              color.rgb32(210, 154, 78)))
        self.original_player = self.player
        self.chasers = []
        palettes = [
            (color.rgb32(103, 56, 107), color.rgb32(59, 42, 80), color.rgb32(234, 108, 89)),
            (color.rgb32(135, 67, 54), color.rgb32(87, 49, 46), color.rgb32(247, 165, 69)),
            (color.rgb32(57, 89, 132), color.rgb32(39, 62, 101), color.rgb32(112, 213, 226)),
        ]
        for index, palette in enumerate(palettes):
            self.chasers.append(Dragon(Vec3((-1 if index == 0 else 1) * 3,
                                             5 + index, -8 - index * 4),
                                       palette, scale=.9))
        self.room_dragon = Dragon(
            Vec3(0, 2, 5.5),
            (color.rgb32(216, 142, 59), color.rgb32(154, 80, 47),
             color.rgb32(255, 220, 126)))
        self.room_dragon.entity.rotation_y = 180
        self.room_dragon.entity.enabled = False
        self.water_scene = Entity(parent=self.room.root, name="water_royal_egg_scene",
                                  enabled=False)
        water_palette = (color.rgb32(73, 161, 183), color.rgb32(45, 103, 135),
                         color.rgb32(186, 234, 232))
        self.water_queen = Dragon(Vec3(0, 1.5, 6), water_palette,
                                  scale=1.15, parent=self.water_scene)
        self.water_queen.entity.rotation_y = 180
        crown_gold = color.rgb32(255, 207, 67)
        Entity(parent=self.water_queen.entity, model="cube",
               position=(0, .91, 1.03), scale=(.62, .13, .5), color=crown_gold)
        for crown_x, crown_z, point_scale in (
                (-.24, 1.02, .27), (-.12, 1.08, .34),
                (0, 1.08, .39), (.12, 1.08, .34), (.24, 1.02, .27)):
            Entity(parent=self.water_queen.entity, model=Cone(),
                   position=(crown_x, 1.12, crown_z),
                   scale=(.12, point_scale, .12), color=crown_gold)
        Entity(parent=self.water_queen.entity, model="sphere",
               position=(0, .99, 1.3), scale=.14,
               color=color.rgb32(104, 226, 235), unlit=True)
        self.water_egg = Entity(parent=self.water_scene, model="sphere",
                                position=(0, 1.2, 2.8), scale=(1.55, 2.2, 1.45),
                                color=color.rgb32(115, 201, 216),
                                shader=lit_with_shadows_shader)
        Entity(parent=self.water_egg, model="sphere", position=(0, .02, .48),
               scale=(.72, .78, .25), color=color.rgb32(193, 244, 239), unlit=True)
        self.water_baby = Dragon(Vec3(0, .8, 2.8), water_palette,
                                 scale=.62, parent=self.water_scene)
        self.water_baby.entity.enabled = False
        self.hatching_gender = None
        self.egg_shards = []
        for shard_position, shard_rotation in (
                ((-.7, .18, 2.45), (0, 0, 30)),
                ((.65, .22, 2.52), (0, 0, -35)),
                ((-.35, .08, 3.4), (20, 0, 25)),
                ((.4, .12, 3.35), (-20, 0, -25))):
            shard = Entity(parent=self.water_scene, model=Cone(),
                           position=shard_position, rotation=shard_rotation,
                           scale=(.32, .58, .32),
                           color=color.rgb32(143, 218, 228), unlit=True,
                           enabled=False)
            self.egg_shards.append(shard)
        self.water_quest = WaterJourneyQuest(
            self, self.water_queen, self.water_baby, Dragon)
        self.speed = 11.5
        self.elapsed = 0
        self.lives = 3
        self.invulnerable = 1.5
        self.game_over = False
        self.won = False
        self.hoop_challenge_active = False
        self.hoop_challenge_finished = False
        self.hoop_index = 0
        self.hoop_time_remaining = HoopQuest.TIME_LIMIT
        for _, hoop in self.hoop_stage.hoops:
            hoop.enabled = True
        self._create_hud()
        self.fire_quest = FireClanQuest(self, Dragon)
        self.tree_canopy_quest = TreeCanopyQuest(self, self.forest)
        self.hoop_quest = HoopQuest(self, self.hoop_stage)
        self.active_quest = self.tree_canopy_quest
        self.active_quest.start()

    def _create_hud(self):
        self.hud_items = []
        self.hud_items.append(Text("DRAGON FLIGHT", parent=camera.ui,
                                   position=(-.86, .45), scale=1.3, color=HUD_COLOR))
        self.hud_items.append(Text(
            "WASD / arrows: steer     SPACE: burst of speed     R: restart",
            parent=camera.ui, position=(-.86, .405), scale=.72, color=HUD_COLOR))
        self.hud_items.append(Text(
            "WEAVE BETWEEN TRUNKS  ·  CLIMB AND DIVE THROUGH GAPS  ·  REACH THE BEACON",
            parent=camera.ui, position=(-.86, .375), scale=.64,
            color=color.rgb32(45, 105, 66)))
        self.progress_text = Text("", parent=camera.ui, position=(-.86, .34),
                                  scale=.9, color=HUD_COLOR)
        self.status_text = Text("", parent=camera.ui, origin=(0, 0), position=(0, .31),
                                scale=1.35, color=HUD_COLOR)
        self.lives_text = Text("", parent=camera.ui, position=(.72, .45),
                               scale=1.05, color=HUD_COLOR)
        self.hud_items.extend((self.progress_text, self.status_text, self.lives_text))
        self.room_message = Text("Great job flying!", parent=camera.ui,
                                 position=(0, .34), origin=(0, 0), scale=1.5,
                                 color=color.rgb32(34, 75, 54), enabled=False)
        self.choice_buttons = [
            Button(text="Thank you!", parent=camera.ui, position=(-.15, -.22),
                   scale=(.24, .085), color=color.rgb32(219, 239, 221),
                   text_color=color.rgb32(24, 55, 37),
                   on_click=self.choose_thank_you),
            Button(text="OK", parent=camera.ui, position=(.15, -.22),
                   scale=(.24, .085), color=color.rgb32(219, 239, 221),
                   text_color=color.rgb32(24, 55, 37),
                   on_click=self.choose_ok),
        ]
        for button in self.choice_buttons:
            button.enabled = False
        self.challenge_button = Button(
            text="What is the challenge?", parent=camera.ui, position=(0, -.22),
            scale=(.38, .085), color=color.rgb32(219, 239, 221),
            text_color=color.rgb32(24, 55, 37),
            on_click=self.ask_about_challenge)
        self.challenge_button.enabled = False
        self.ok_challenge_button = Button(
            text="OK", parent=camera.ui, position=(0, -.22),
            scale=(.2, .085), color=color.rgb32(219, 239, 221),
            text_color=color.rgb32(24, 55, 37),
            on_click=self.start_hoop_challenge)
        self.ok_challenge_button.enabled = False
        self.clan_choice_buttons = []
        for clan, position in (("Fire Clan", (-.23, -.16)),
                               ("Water Clan", (.23, -.16)),
                               ("Earth Clan", (-.23, -.29)),
                               ("Sky Clan", (.23, -.29))):
            self.clan_choice_buttons.append(
                Button(text=clan, parent=camera.ui, position=position,
                       scale=(.3, .085), color=color.rgb32(219, 239, 221),
                       text_color=color.rgb32(24, 55, 37),
                       on_click=lambda selected=clan: self.choose_clan(selected))
            )
        for button in self.clan_choice_buttons:
            button.enabled = False
        self.gender_choice_buttons = [
            Button(text="Male", parent=camera.ui, position=(-.17, -.22),
                   scale=(.25, .085), color=color.rgb32(219, 239, 221),
                   text_color=color.rgb32(24, 55, 37),
                   on_click=lambda: self.choose_hatching_gender("male")),
            Button(text="Female", parent=camera.ui, position=(.17, -.22),
                   scale=(.25, .085), color=color.rgb32(219, 239, 221),
                   text_color=color.rgb32(24, 55, 37),
                   on_click=lambda: self.choose_hatching_gender("female")),
        ]
        for button in self.gender_choice_buttons:
            button.enabled = False
        self.hoop_status = Text("", parent=camera.ui, position=(0, .42),
                                origin=(0, 0), scale=1.15,
                                color=color.rgb32(39, 56, 37), enabled=False)

    def _disable_dialogue_buttons(self):
        for button in self.choice_buttons:
            button.enabled = False
        self.challenge_button.enabled = False
        self.ok_challenge_button.enabled = False
        for button in self.clan_choice_buttons:
            button.enabled = False
        for button in self.gender_choice_buttons:
            button.enabled = False

    def _snap_camera(self, offset, look_offset):
        camera.position = self.player.entity.position + offset
        camera.look_at(self.player.entity.position + look_offset)
        camera.rotation_z = 0

    def reset_run(self):
        self.active_quest.restart()

    def handle_input(self, key):
        if key == "r":
            if self.won and self.dialogue_stage in (
                    "clan_choice", "clan_selected", "water_gender_choice",
                    "water_hatched"):
                return
            self.active_quest.restart()

    def update(self):
        dt = min(time.dt, .04)
        if self.active_quest is self.fire_quest:
            self.fire_quest.update(dt)
            return
        if self.active_quest is self.water_quest:
            self.water_quest.update(dt)
            return
        if self.active_quest is self.hoop_quest and not self.hoop_quest.finished:
            self.hoop_quest.update(dt)
            return
        if (self.active_quest is self.hoop_quest and self.hoop_quest.finished
                and not self.won):
            self.elapsed += dt
            self.player.animate(self.elapsed)
            return
        if self.active_quest.finished and not self.won:
            return
        if self.won:
            self.elapsed += dt
            self.player.animate(self.elapsed)
            self.room_dragon.animate(self.elapsed + 1.0)
            if self.dialogue_stage in ("water_gender_choice", "water_hatched"):
                self.water_queen.animate(self.elapsed + 1.5)
            if self.dialogue_stage == "water_hatched":
                self.water_baby.animate(self.elapsed + 2.0)
                if self.elapsed >= self.dialogue_next_time:
                    self.dialogue_stage = "water_journey"
                    self.active_quest = self.water_quest
                    self.water_quest.start()
                    return
            if (self.dialogue_stage == "reply"
                    and self.elapsed >= self.dialogue_next_time):
                self.room_message.text = "I have another challenge for you."
                self.dialogue_stage = "challenge"
                self.challenge_button.enabled = True
            return
        self.active_quest.update(dt)

    def _update_camera(self):
        player = self.player.entity
        dt = min(time.dt, .04)
        camera.position = lerp(camera.position,
                               player.position + Vec3(0, 7.2, -17), dt * 3.2)
        camera.look_at(player.position + Vec3(0, .8, 11))
        camera.fov = 76

    def _enter_white_room(self):
        self.won = True
        self.forest.root.enabled = False
        self.room.root.enabled = True
        self.room_dragon.entity.enabled = True
        for dragon in self.chasers:
            dragon.entity.enabled = False
        self.player.entity.position = Vec3(0, 2, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        camera.position = Vec3(0, 6.2, -9.5)
        camera.look_at(self.player.entity.position + Vec3(0, .4, 1.5))
        window.color = color.white
        for item in self.hud_items:
            item.enabled = False
        self.room_message.enabled = True
        self.dialogue_stage = "choice"
        self.dialogue_next_time = None
        for button in self.choice_buttons:
            button.enabled = True
        for button in self.clan_choice_buttons:
            button.enabled = False

    def _enter_clan_choice_room(self):
        self.won = True
        self.forest.root.enabled = False
        self.hoop_stage.root.enabled = False
        self.room.root.enabled = True
        self.room_dragon.entity.enabled = True
        self.hoop_status.enabled = False
        for dragon in self.chasers:
            dragon.entity.enabled = False
        self.player.entity.position = Vec3(0, 2, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player.entity.alpha = 1
        camera.position = Vec3(0, 6.2, -9.5)
        camera.look_at(self.player.entity.position + Vec3(0, .4, 1.5))
        window.color = color.white
        for item in self.hud_items:
            item.enabled = False
        for button in self.choice_buttons:
            button.enabled = False
        self._disable_dialogue_buttons()
        self.room_message.text = (
            "It is time. You are strong enough to enter the real dragon world.\n"
            "Choose one of the clans."
        )
        self.room_message.scale = .95
        self.room_message.enabled = True
        self.dialogue_stage = "clan_choice"
        self.dialogue_next_time = None
        for button in self.clan_choice_buttons:
            button.enabled = True

    def choose_clan(self, clan):
        if not self.won or self.dialogue_stage != "clan_choice":
            return
        if clan == "Water Clan":
            self._enter_water_egg_scene()
            return
        if clan == "Fire Clan":
            for button in self.clan_choice_buttons:
                button.enabled = False
            self.fire_quest.start()
            return
        self.room_message.text = f"You have chosen the {clan}!"
        self.dialogue_stage = "clan_selected"
        for button in self.clan_choice_buttons:
            button.enabled = False

    def _enter_water_egg_scene(self):
        self.room_dragon.entity.enabled = False
        self.water_scene.enabled = True
        self.water_queen.entity.enabled = True
        self.water_egg.enabled = True
        self.water_baby.entity.enabled = False
        for shard in self.egg_shards:
            shard.enabled = False
        self.original_player.entity.enabled = False
        self.player.entity.position = Vec3(0, .7, -.7)
        self.player.entity.rotation = Vec3(0, 0, 0)
        camera.position = Vec3(0, 5.2, -8.5)
        camera.look_at(Vec3(0, 1.8, 3.8))
        self.room_message.text = (
            "The Water Clan has only one egg for now.\n"
            "The Queen is very protective of it.\n"
            "Will you hatch as male or female?"
        )
        self.room_message.scale = 1.0
        self.room_message.enabled = True
        self.dialogue_stage = "water_gender_choice"
        for button in self.clan_choice_buttons:
            button.enabled = False
        for button in self.gender_choice_buttons:
            button.enabled = True

    def choose_hatching_gender(self, gender):
        if not self.won or self.dialogue_stage != "water_gender_choice":
            return
        self.hatching_gender = gender
        self.water_egg.enabled = False
        for shard in self.egg_shards:
            shard.enabled = True
        self.water_baby.entity.enabled = True
        self.water_baby.entity.rotation = Vec3(0, 180, 0)
        self.player = self.water_baby
        self.room_message.text = (
            f"The egg cracks open! You hatch as a {gender} Water Dragon.\n"
            "The Queen welcomes you into the royal family."
        )
        self.room_message.scale = 1.0
        self.dialogue_stage = "water_hatched"
        self.dialogue_next_time = self.elapsed + 2.5
        for button in self.gender_choice_buttons:
            button.enabled = False

    def choose_thank_you(self):
        self._choose_dialogue("You: Thank you!")

    def choose_ok(self):
        self._choose_dialogue("You: OK!")

    def _choose_dialogue(self, reply):
        if not self.won or self.dialogue_stage != "choice":
            return
        self.room_message.text = reply
        self.dialogue_stage = "reply"
        self.dialogue_next_time = self.elapsed + 1.2
        for button in self.choice_buttons:
            button.enabled = False

    def ask_about_challenge(self):
        if not self.won or self.dialogue_stage != "challenge":
            return
        self.room_message.text = (
            f"Fly through the {len(self.hoop_stage.hoops)} yellow hoops in "
            f"{int(self.hoop_quest.TIME_LIMIT)} seconds!"
        )
        self.dialogue_stage = "challenge_revealed"
        self.challenge_button.enabled = False
        self.ok_challenge_button.enabled = True

    def start_hoop_challenge(self):
        if not self.won or self.dialogue_stage != "challenge_revealed":
            return
        self.won = False
        self.active_quest = self.hoop_quest
        self.hoop_quest.start()


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
