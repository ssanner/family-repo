"""Fire Clan origin story and the search for the missing Earth Gem piece."""

import math

from ursina import *

from .quest import Quest


class FireClanQuest(Quest):
    """Play the Fire Clan family story, then fly with a royal companion."""

    EARTH_GOAL_Z = 72

    def __init__(self, game, dragon_factory):
        super().__init__(game)
        self.dragon_factory = dragon_factory
        self.fire_scene = Entity(name="fire_clan_home", enabled=False)
        self.water_scene = Entity(name="water_kingdom_visit", enabled=False)
        self.sky_scene = Entity(name="sky_kingdom_visit", enabled=False)
        self.earth_scene = Entity(name="earth_gem_search", enabled=False)
        self._build_fire_home()
        self._build_kingdoms()
        self._build_earth_search()

        fire_palette = (color.rgb32(210, 92, 49), color.rgb32(132, 53, 47),
                        color.rgb32(255, 177, 72))
        mother_palette = (color.rgb32(170, 72, 54), color.rgb32(113, 48, 51),
                          color.rgb32(251, 167, 73))
        self.player = self.dragon_factory(
            Vec3(0, .8, 0), fire_palette, scale=.62, parent=self.fire_scene)
        self.player_crown = Entity(parent=self.player.entity,
                                   position=(0, .92, 1.02), enabled=False)
        crown_gold = color.rgb32(255, 211, 78)
        Entity(parent=self.player_crown, model="cube", position=(0, 0, 0),
               scale=(.72, .14, .52), color=crown_gold, unlit=True)
        for x, height in ((-.26, .3), (-.13, .4), (0, .48),
                          (.13, .4), (.26, .3)):
            Entity(parent=self.player_crown, model=Cone(),
                   position=(x, .12, 0), scale=(.14, height, .14),
                   color=crown_gold, unlit=True)
        self.mother = self.dragon_factory(
            Vec3(-3, 1.4, -3), mother_palette, scale=1.25,
            parent=self.fire_scene)
        self.mother.entity.rotation_y = 25
        self.egg = Entity(parent=self.fire_scene, model="sphere",
                          position=(0, 1.2, 0), scale=(1.7, 2.25, 1.55),
                          color=color.rgb32(232, 105, 53), unlit=True)
        Entity(parent=self.egg, model="sphere", position=(0, .04, .48),
               scale=(.72, .88, .22), color=color.rgb32(255, 202, 105),
               unlit=True)
        self.egg_shards = []
        for position, rotation in (((-1.0, .5, .1), (0, 0, 30)),
                                   ((1.05, .3, -.2), (0, 0, -38)),
                                   ((-.5, .1, 1.0), (20, 0, 25)),
                                   ((.65, .15, 1.0), (-20, 0, -28))):
            shard = Entity(parent=self.fire_scene, model=Cone(),
                           position=position, rotation=rotation,
                           scale=(.38, .68, .38),
                           color=color.rgb32(246, 156, 75), unlit=True,
                           enabled=False)
            self.egg_shards.append(shard)

        self.siblings = []
        for index in range(17):
            row, column = divmod(index, 6)
            x = (column - 2.5) * 2.3
            z = 4.5 + row * 3.0
            sibling = self.dragon_factory(
                Vec3(x, .8, z),
                (color.rgb32(175 + index % 3 * 15, 70, 45),
                 color.rgb32(111, 49 + index % 2 * 8, 46),
                 color.rgb32(248, 162 + index % 3 * 12, 67)),
                scale=.66, parent=self.fire_scene)
            sibling.entity.rotation_y = 180
            sibling.entity.enabled = False
            self.siblings.append(sibling)
        self.leash = Entity(parent=self.fire_scene, model="cube",
                            scale=(.09, .09, 1), color=color.rgb32(220, 182, 91),
                            unlit=True, enabled=False)

        water_palette = (color.rgb32(79, 166, 192), color.rgb32(45, 105, 145),
                         color.rgb32(196, 239, 236))
        self.water_prince = self.dragon_factory(
            Vec3(0, 1.5, 9), water_palette, scale=1.15,
            parent=self.water_scene)
        self.water_prince.entity.rotation_y = 180
        princess_palettes = (
            (color.rgb32(156, 115, 198), color.rgb32(103, 75, 157),
             color.rgb32(255, 218, 149)),
            (color.rgb32(223, 137, 182), color.rgb32(164, 91, 151),
             color.rgb32(255, 226, 162)),
            (color.rgb32(110, 190, 197), color.rgb32(64, 132, 159),
             color.rgb32(255, 216, 144)))
        self.water_princesses = []
        for index, palette in enumerate(princess_palettes):
            princess = self.dragon_factory(
                Vec3((index - 1) * 4, 1.5, 12), palette,
                scale=1.0, parent=self.water_scene)
            princess.entity.rotation_y = 180
            self.water_princesses.append(princess)
        self.sky_companion = self.dragon_factory(
            Vec3(0, 1.5, 10), princess_palettes[1], scale=1.05,
            parent=self.sky_scene)
        self.sky_companion.entity.rotation_y = 180
        self.companion = None

        self.phase = "idle"
        self.gender = None
        self.story_timer = 0
        self.story_step = 0
        self.mission_z = 0
        self.gender_buttons = [
            Button(text="Male", parent=camera.ui, position=(-.16, -.22),
                   scale=(.25, .085), color=color.rgb32(252, 219, 189),
                   text_color=color.rgb32(86, 42, 31),
                   on_click=lambda: self.choose_gender("male")),
            Button(text="Female", parent=camera.ui, position=(.16, -.22),
                   scale=(.25, .085), color=color.rgb32(252, 219, 189),
                   text_color=color.rgb32(86, 42, 31),
                   on_click=lambda: self.choose_gender("female")),
        ]
        for button in self.gender_buttons:
            button.enabled = False

    def _build_fire_home(self):
        scene = self.fire_scene
        Entity(parent=scene, model="plane", position=(0, -.4, 5),
               scale=(60, 1, 70), color=color.rgb32(111, 63, 48), unlit=True)
        for x, z, height in ((-20, 12, 12), (20, 12, 15),
                             (-23, -13, 9), (23, -13, 11)):
            Entity(parent=scene, model=Cylinder(), position=(x, 0, z),
                   scale=(3, height, 3), color=color.rgb32(122, 72, 49),
                   unlit=True)
            Entity(parent=scene, model=Cone(), position=(x, height / 2, z),
                   scale=(5, 5, 5), color=color.rgb32(174, 78, 49), unlit=True)
        Entity(parent=scene, model="cube", position=(0, .05, -7),
               scale=(11, .5, 5), color=color.rgb32(115, 72, 62), unlit=True)
        Entity(parent=scene, model="cube", position=(0, .35, -7),
               scale=(10, .25, 4.4), color=color.rgb32(180, 113, 91), unlit=True)
        for x in (-5, 5):
            Entity(parent=scene, model="sphere", position=(x, 5, 19),
                   scale=(5, 1.5, 4), color=color.rgb32(240, 136, 73),
                   unlit=True)

    def _build_kingdoms(self):
        Entity(parent=self.water_scene, model="plane", position=(0, -.4, 8),
               scale=(55, 1, 50), color=color.rgb32(31, 114, 143), unlit=True)
        Entity(parent=self.water_scene, model="cube", position=(0, 4, 22),
               scale=(24, 10, 5), color=color.rgb32(57, 138, 160), unlit=True)
        for x in (-10, 10):
            Entity(parent=self.water_scene, model=Cylinder(),
                   position=(x, 0, 22), scale=(3, 17, 3),
                   color=color.rgb32(105, 184, 188), unlit=True)
            Entity(parent=self.water_scene, model=Cone(),
                   position=(x, 10, 22), scale=(5, 6, 5),
                   color=color.rgb32(38, 111, 149), unlit=True)
        for index in range(9):
            x = -22 + index * 5.5
            Entity(parent=self.water_scene, model="sphere", position=(x, 3, 3),
                   scale=(1.2, 4.5, .35), color=color.rgb32(88, 218, 224),
                   unlit=True)

        Entity(parent=self.sky_scene, model="plane", position=(0, -.5, 10),
               scale=(65, 1, 65), color=color.rgb32(175, 220, 235), unlit=True)
        for x, z, size in ((-19, 8, 10), (19, 12, 12), (-22, 35, 13),
                           (22, 38, 13), (-5, 53, 11), (13, 56, 12)):
            Entity(parent=self.sky_scene, model="sphere", position=(x, 1, z),
                   scale=(size, size * .42, size * .7),
                   color=color.rgb32(239, 250, 255), unlit=True)
        Entity(parent=self.sky_scene, model="cube", position=(0, 5, 37),
               scale=(20, 10, 8), color=color.rgb32(129, 181, 216), unlit=True)
        for x in (-8, 8):
            Entity(parent=self.sky_scene, model=Cylinder(),
                   position=(x, 0, 37), scale=(2.8, 18, 2.8),
                   color=color.rgb32(160, 204, 228), unlit=True)
            Entity(parent=self.sky_scene, model=Cone(),
                   position=(x, 11, 37), scale=(4.5, 6, 4.5),
                   color=color.rgb32(103, 148, 198), unlit=True)
        Text("SKY KINGDOM", parent=self.sky_scene, position=(0, 17, 37),
             origin=(0, 0), scale=2, color=color.rgb32(255, 247, 213),
             billboard=True)

    def _build_earth_search(self):
        scene = self.earth_scene
        Entity(parent=scene, model="plane", position=(0, -.5, 35),
               scale=(60, 1, 90), color=color.rgb32(105, 115, 83), unlit=True)
        for index, z in enumerate(range(12, 69, 12)):
            for x in (-13, 13):
                Entity(parent=scene, model=Cylinder(), position=(x, 0, z),
                       scale=(2.1, 11 + index % 3 * 2, 2.1),
                       color=color.rgb32(109, 110, 83), unlit=True)
            Entity(parent=scene, model="cube", position=(0, 7 + index % 3, z),
                   scale=(27, 1.2, 1.5), color=color.rgb32(147, 139, 94),
                   unlit=True)
        self.earth_shard_position = Vec3(0, 3, 72)
        self.earth_shard = Entity(parent=scene,
                                  position=self.earth_shard_position)
        Entity(parent=self.earth_shard, model=Cone(), position=(0, .5, 0),
               scale=(1.2, 2, 1.2), color=color.rgb32(171, 230, 112),
               unlit=True)
        Entity(parent=self.earth_shard, model=Cone(), position=(0, -.5, 0),
               rotation_z=180, scale=(1.2, 2, 1.2),
               color=color.rgb32(93, 178, 93), unlit=True)
        Entity(parent=scene, model="sphere", position=self.earth_shard_position,
               scale=3.5, color=color.rgba32(169, 255, 127, 65), unlit=True)
        Text("MISSING EARTH GEM PIECE", parent=scene,
             position=(0, 7, 72), origin=(0, 0), scale=1.5,
             color=color.rgb32(240, 255, 204), billboard=True)

    def start(self):
        game = self.game
        self.finished = False
        self.phase = "gender_choice"
        self.gender = None
        self.story_step = 0
        self.story_timer = 0
        self.companion = None
        game.active_quest = self
        game.player = self.player
        game.won = False
        game.game_over = False
        game.elapsed = 0
        game.room.root.enabled = False
        game.forest.root.enabled = False
        game.hoop_stage.root.enabled = False
        game.water_scene.enabled = False
        for quest_scene in (self.fire_scene, self.water_scene, self.sky_scene,
                            self.earth_scene):
            quest_scene.enabled = False
        self.fire_scene.enabled = True
        self.player.entity.parent = self.fire_scene
        self.water_prince.entity.parent = self.water_scene
        for princess in self.water_princesses:
            princess.entity.parent = self.water_scene
        self.sky_companion.entity.parent = self.sky_scene
        game.original_player.entity.enabled = False
        game.water_baby.entity.enabled = False
        game.room_dragon.entity.enabled = False
        game.water_queen.entity.enabled = False
        for chaser in game.chasers:
            chaser.entity.enabled = False
        self.player.entity.enabled = True
        self.player.entity.scale = .62
        self.player.entity.position = Vec3(0, .8, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player_crown.enabled = False
        self.mother.entity.enabled = True
        self.mother.entity.alpha = 1
        self.mother.entity.position = Vec3(-3, 1.4, -3)
        self.mother.entity.rotation = Vec3(0, 25, 0)
        self.egg.enabled = True
        self.leash.enabled = False
        for shard in self.egg_shards:
            shard.enabled = False
        for sibling in self.siblings:
            sibling.entity.enabled = False
        self.water_prince.entity.enabled = False
        for princess in self.water_princesses:
            princess.entity.enabled = False
        self.sky_companion.entity.enabled = False
        self.earth_shard.enabled = True
        game._disable_dialogue_buttons()
        for item in game.hud_items:
            item.enabled = False
        game.room_message.text = (
            "You have chosen the Fire Clan.\n"
            "You begin as a dragon egg.\n"
            "Will you hatch as male or female?"
        )
        game.room_message.position = (0, .34)
        game.room_message.scale = 1.0
        game.room_message.color = color.rgb32(255, 242, 214)
        game.room_message.enabled = True
        for button in self.gender_buttons:
            button.enabled = True
        window.color = color.rgb32(128, 72, 56)
        camera.position = Vec3(0, 7, -16)
        camera.look_at(Vec3(0, 1.5, 4))

    def choose_gender(self, gender):
        if self.phase != "gender_choice":
            return
        self.gender = gender
        self.game.hatching_gender = gender
        self.phase = "hatching"
        self.story_timer = 2.5
        self.egg.enabled = False
        for button in self.gender_buttons:
            button.enabled = False
        for shard in self.egg_shards:
            shard.enabled = True
        self.player.entity.enabled = True
        self.player.entity.position = Vec3(0, 1.1, 0)
        self.player.entity.rotation = Vec3(0, 180, 0)
        for sibling in self.siblings:
            sibling.entity.enabled = True
        self.mother.entity.position = Vec3(-4, 1.4, -4)
        self.mother.entity.rotation_y = 20
        self.game.room_message.text = (
            f"The egg hatches! You are a {gender} Fire Dragon.\n"
            "You join a family with 17 siblings."
        )

    def _update_leash(self):
        player_position = self.player.entity.position + Vec3(0, .35, 0)
        mother_position = self.mother.entity.position + Vec3(0, .45, .5)
        difference = player_position - mother_position
        self.leash.position = (player_position + mother_position) / 2
        self.leash.look_at(player_position)
        self.leash.scale = Vec3(.09, .09, max(.2, difference.length()))

    def update(self, dt):
        game = self.game
        if self.phase in ("gender_choice", "finished"):
            if self.phase == "finished":
                self.player.animate(game.elapsed)
                if self.companion:
                    self.companion.animate(game.elapsed + 1)
            return

        game.elapsed += dt
        if self.phase == "hatching":
            self._update_family(dt)
        elif self.phase == "family_dialogue":
            self._update_family(dt)
            self.story_timer -= dt
            if self.story_timer <= 0:
                self._begin_time_jump()
        elif self.phase == "time_jump":
            self.player.animate(game.elapsed)
            self.story_timer -= dt
            if self.story_timer <= 0:
                self._begin_water_visit()
        elif self.phase == "water_meeting":
            self._update_meeting(dt)
            self.story_timer -= dt
            if self.story_timer <= 0:
                if self.gender == "male":
                    self._follow_princess_to_sky()
                else:
                    self._ask_companion_for_help()
        elif self.phase == "sky_travel":
            self._update_sky_travel(dt)
        elif self.phase == "partner_dialogue":
            self._update_meeting(dt)
            self.story_timer -= dt
            if self.story_timer <= 0:
                self._partner_agrees()
        elif self.phase == "partner_agrees":
            self._update_meeting(dt)
            self.story_timer -= dt
            if self.story_timer <= 0:
                self._begin_earth_flight()
        elif self.phase == "earth_flight":
            self._update_earth_flight(dt)
        elif self.phase == "earth_search":
            self._update_earth_search(dt)

    def _update_family(self, dt):
        self.player.animate(self.game.elapsed)
        self.mother.animate(self.game.elapsed + .7)
        for index, sibling in enumerate(self.siblings):
            if sibling.entity.enabled:
                sibling.animate(self.game.elapsed + index * .2)
        if self.phase == "hatching":
            self._update_leash()
            self.story_timer -= dt
            if self.story_timer <= 0:
                sibling_word = "brothers" if self.gender == "female" else "sisters"
                heir_word = "daughter" if self.gender == "female" else "son"
                self.phase = "family_dialogue"
                self.story_timer = 5.8
                self.game.room_message.text = (
                    "Mother: I love you, my dear.\n"
                    f"You are my only {heir_word}, in a family with 17 "
                    f"{sibling_word}.\n"
                    "Your siblings are too rough, so you cannot play with them."
                )
                self.leash.enabled = True
                self.game.status_text.text = "Your mother keeps you close with a golden leash."

    def _begin_time_jump(self):
        self.phase = "time_jump"
        self.story_timer = 5.0
        self.player.entity.scale = 1.25
        self.player_crown.enabled = True
        self.player.entity.position = Vec3(0, 1.6, 4)
        self.player.entity.rotation = Vec3(0, 180, 0)
        for sibling in self.siblings:
            sibling.entity.enabled = False
        self.leash.enabled = False
        self.mother.entity.position = Vec3(0, .65, -6.5)
        self.mother.entity.rotation = Vec3(0, 0, 90)
        self.mother.entity.alpha = .6
        self.game.room_message.text = (
            "17 YEARS LATER\n"
            "Your mother has become very sick.\n"
            "As the only heir, you become "
            f"the Fire {'King' if self.gender == 'male' else 'Queen'}."
        )
        self.game.room_message.scale = 1.15
        self.game.status_text.text = ""
        camera.position = Vec3(0, 7, -15)
        camera.look_at(Vec3(0, 2, -4))

    def _begin_water_visit(self):
        self.phase = "water_meeting"
        self.story_timer = 4.2
        self.fire_scene.enabled = False
        self.water_scene.enabled = True
        self.player.entity.parent = self.water_scene
        self.player.entity.position = Vec3(0, 1.4, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player.entity.scale = 1.25
        if self.gender == "male":
            for princess in self.water_princesses:
                princess.entity.enabled = True
            self.water_prince.entity.enabled = False
            self.game.room_message.text = (
                "As the Fire King, you travel to the Water Kingdom\n"
                "to meet its princesses."
            )
        else:
            self.water_prince.entity.enabled = True
            for princess in self.water_princesses:
                princess.entity.enabled = False
            self.game.room_message.text = (
                "As the Fire Queen, you travel to the Water Kingdom\n"
                "and meet its prince."
            )
        self.game.room_message.scale = .95
        self.game.room_message.enabled = True
        window.color = color.rgb32(42, 129, 157)
        camera.position = Vec3(0, 7, -24)
        camera.look_at(Vec3(0, 2, 10))

    def _update_meeting(self, dt):
        self.player.animate(self.game.elapsed)
        if self.companion:
            target = self.player.entity.position + Vec3(3, .3, 5)
            self.companion.entity.position = lerp(
                self.companion.entity.position, target, min(1, dt * 2))
            self.companion.entity.look_at(self.player.entity.position)
            self.companion.animate(self.game.elapsed + 1)
        camera.position = lerp(
            camera.position, self.player.entity.position + Vec3(0, 6, -14), dt * 2)
        camera.look_at(self.player.entity.position + Vec3(0, .3, 10))

    def _follow_princess_to_sky(self):
        self.phase = "sky_travel"
        self.story_timer = 3.4
        self.water_scene.enabled = False
        self.sky_scene.enabled = True
        self.player.entity.parent = self.sky_scene
        self.player.entity.position = Vec3(0, 2.5, -18)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.sky_companion.entity.enabled = True
        self.companion = self.sky_companion
        self.game.room_message.text = (
            "Princess Coral went to the Sky Kingdom to look for a clue\n"
            "about the missing Earth Gem piece.\n"
            "You follow her through the clouds."
        )
        window.color = color.rgb32(153, 207, 232)
        camera.position = Vec3(0, 9, -30)
        camera.look_at(Vec3(0, 2, 12))

    def _update_sky_travel(self, dt):
        self.player.entity.z += 6 * dt
        self.player.entity.y = lerp(self.player.entity.y, 1.7, dt * 2)
        self.player.animate(self.game.elapsed)
        self.sky_companion.animate(self.game.elapsed + .8)
        camera.position = lerp(
            camera.position, self.player.entity.position + Vec3(0, 6, -12), dt * 2)
        camera.look_at(Vec3(0, 2, 12))
        self.story_timer -= dt
        if self.story_timer <= 0:
            self.player.entity.position = Vec3(0, 1.5, 0)
            self.game.room_message.text = (
                "You catch up with Princess Coral at the Sky Kingdom.\n"
                "You: Could you help me find the missing piece of the Earth Gem?"
            )
            self.phase = "partner_dialogue"
            self.story_timer = 4.0

    def _ask_companion_for_help(self):
        self.companion = self.water_prince
        self.companion.entity.position = self.player.entity.position + Vec3(3, .3, 5)
        self.phase = "partner_dialogue"
        self.story_timer = 4.0
        self.game.room_message.text = (
            "You: Prince Tide, could you help me find the missing piece "
            "of the Earth Gem?"
        )

    def _partner_agrees(self):
        self.phase = "partner_agrees"
        self.story_timer = 3.0
        companion_name = "Princess Coral" if self.gender == "male" else "Prince Tide"
        self.game.room_message.text = (
            f"{companion_name}: Yes! The missing piece is hidden\n"
            "in the Earth Temple. Let's find it together."
        )

    def _begin_earth_flight(self):
        self.phase = "earth_flight"
        self.story_timer = 3.0
        self.water_scene.enabled = False
        self.sky_scene.enabled = False
        self.earth_scene.enabled = True
        self.player.entity.parent = self.earth_scene
        self.player.entity.position = Vec3(0, 2.5, -18)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.companion.entity.parent = self.earth_scene
        self.companion.entity.position = Vec3(3, 2.4, -24)
        self.game.room_message.text = "Together, you fly to the Earth Temple."
        window.color = color.rgb32(123, 151, 101)
        camera.position = Vec3(0, 9, -30)
        camera.look_at(Vec3(0, 2.5, 12))

    def _update_earth_flight(self, dt):
        self.player.entity.z += 6 * dt
        self.player.entity.y = lerp(self.player.entity.y, 2.0, dt * 2)
        self.player.animate(self.game.elapsed)
        self.companion.entity.z = self.player.entity.z - 6
        self.companion.entity.x = lerp(self.companion.entity.x, 3, dt * 2)
        self.companion.animate(self.game.elapsed + 1)
        camera.position = lerp(
            camera.position, self.player.entity.position + Vec3(0, 6, -12), dt * 2)
        camera.look_at(self.player.entity.position + Vec3(0, .3, 14))
        self.story_timer -= dt
        if self.story_timer <= 0:
            self.phase = "earth_search"
            self.player.entity.position = Vec3(0, 2.5, 0)
            self.companion.entity.position = Vec3(3, 2.5, -6)
            self.mission_z = 0
            self.game.room_message.text = "Find the missing piece of the Earth Gem!"
            self.story_timer = 4.5
            self.game.status_text.text = "Fly through the temple halls to reach the green shard."
            self.game.progress_text.text = "EARTH GEM SEARCH  72 m"
            self.game.status_text.enabled = True
            self.game.progress_text.enabled = True

    def _update_earth_search(self, dt):
        player = self.player.entity
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        player.x = max(-18, min(18, player.x + horizontal * 10 * dt))
        player.y = max(.5, min(9, player.y + vertical * 7 * dt))
        player.z += 11 * dt
        player.rotation_z = lerp(player.rotation_z, -horizontal * 18, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 10, dt * 4)
        self.player.animate(self.game.elapsed)
        self.companion.entity.position = lerp(
            self.companion.entity.position,
            player.position + Vec3(3, .3, -5), min(1, dt * 2))
        self.companion.entity.look_at(player.position)
        self.companion.animate(self.game.elapsed + .8)
        self.earth_shard.rotation_y += 55 * dt
        camera.position = lerp(camera.position, player.position + Vec3(0, 6, -13), dt * 3)
        camera.look_at(player.position + Vec3(0, .2, 14))
        remaining = max(0, int(self.EARTH_GOAL_Z - player.z))
        self.game.progress_text.text = f"EARTH GEM SEARCH  {remaining} m"
        if self.game.room_message.enabled:
            self.story_timer -= dt
            if self.story_timer <= 0:
                self.game.room_message.enabled = False
        if distance(player.position, self.earth_shard.position) < 2.6:
            self.phase = "finished"
            self.finished = True
            self.earth_shard.enabled = False
            self.game.room_message.text = (
                "You and your companion found the missing piece!\n"
                "The Earth Gem is whole again."
            )
            self.game.room_message.enabled = True
            self.game.status_text.text = "QUEST COMPLETE! Press R to begin again."

    def restart(self):
        self.start()
