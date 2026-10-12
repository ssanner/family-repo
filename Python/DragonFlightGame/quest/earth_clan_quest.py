"""Earth Clan origin story and Dragon Island rescue quest."""

from ursina import *

from .quest import Quest


class EarthClanQuest(Quest):
    """A mixed Earth and Sea dragon grows up to defend Dragon Island."""

    SIGILS = (Vec3(-8, 3, 24), Vec3(7, 6, 48), Vec3(-5, 8, 72),
              Vec3(8, 4, 96))

    def __init__(self, game, dragon_factory):
        super().__init__(game)
        self.dragon_factory = dragon_factory
        self.scene = Entity(name="earth_clan_story", enabled=False)
        self._build_world()
        earth_palette = (color.rgb32(112, 157, 89), color.rgb32(69, 111, 72),
                         color.rgb32(218, 195, 121))
        sea_palette = (color.rgb32(66, 158, 191), color.rgb32(43, 99, 143),
                       color.rgb32(198, 237, 236))
        self.player = dragon_factory(Vec3(0, .8, 1), earth_palette,
                                    scale=.64, parent=self.scene)
        self.mother = dragon_factory(Vec3(-3, 1.4, -3), earth_palette,
                                    scale=1.2, parent=self.scene)
        self.father = dragon_factory(Vec3(3, 1.4, -3), sea_palette,
                                    scale=1.2, parent=self.scene)
        self.mother.entity.rotation_y = 25
        self.father.entity.rotation_y = -25
        self.egg = Entity(parent=self.scene, model="sphere", position=(0, 1, 1),
                          scale=(1.6, 2, 1.5), color=color.rgb32(133, 170, 103),
                          unlit=True)
        self.egg_mark = Entity(parent=self.egg, model="sphere",
                               position=(0, .04, .48), scale=(.75, .8, .23),
                               color=color.rgb32(91, 193, 195), unlit=True)
        self.obstacles = []
        for index, (x, y, z, radius) in enumerate((
                (-3, 2.2, 18, 2.1), (4, 5, 31, 2.2), (0, 7, 43, 2.0),
                (-5, 3.5, 56, 2.2), (3, 2, 68, 2.1), (-1, 6, 81, 2.2),
                (5, 4.2, 91, 2.0), (-4, 2.4, 103, 2.1))):
            rock = Entity(parent=self.scene, model="sphere", position=(x, y, z),
                          scale=radius * 2,
                          color=color.rgb32(103 + index % 3 * 10, 114, 88),
                          unlit=True)
            Entity(parent=rock, model="sphere", position=(.2, .22, .1),
                   scale=.32, color=color.rgb32(151, 146, 111), unlit=True)
            self.obstacles.append((rock, radius))
        self.sigils = []
        for position in self.SIGILS:
            rune = Entity(parent=self.scene, position=position)
            Entity(parent=rune, model=Cone(), scale=(1.4, 2, .55),
                   color=color.rgb32(130, 234, 133), unlit=True)
            Entity(parent=rune, model=Cone(), rotation_z=180,
                   scale=(1.4, 2, .55), color=color.rgb32(130, 234, 133),
                   unlit=True)
            Entity(parent=rune, model="sphere", scale=3.3,
                   color=color.rgba32(147, 255, 135, 55), unlit=True)
            self.sigils.append(rune)
        self.island_core = Entity(parent=self.scene, model="sphere",
                                  position=(0, 4, 116), scale=(8, 8, 8),
                                  color=color.rgb32(64, 169, 91), unlit=True)
        Entity(parent=self.island_core, model="sphere", position=(0, .1, 0),
               scale=(.62, .62, .62), color=color.rgb32(205, 245, 131),
               unlit=True)
        self.phase = "idle"
        self.gender = None
        self.timer = 0
        self.lives = 3
        self.invulnerability = 0
        self.collected = 0
        self.gender_buttons = [
            Button(text="Male", parent=camera.ui, position=(-.16, -.22),
                   scale=(.25, .085), color=color.rgb32(234, 238, 212),
                   text_color=color.rgb32(45, 63, 42),
                   on_click=lambda: self.choose_gender("male")),
            Button(text="Female", parent=camera.ui, position=(.16, -.22),
                   scale=(.25, .085), color=color.rgb32(234, 238, 212),
                   text_color=color.rgb32(45, 63, 42),
                   on_click=lambda: self.choose_gender("female")),
        ]
        for button in self.gender_buttons:
            button.enabled = False
        self.lives_text = Text(parent=camera.ui, position=(-.86, .43), scale=1.1,
                               color=color.rgb32(255, 238, 190), enabled=False)

    def _build_world(self):
        Entity(parent=self.scene, model="plane", position=(0, -.45, 52),
               scale=(58, 1, 148), color=color.rgb32(104, 139, 94), unlit=True)
        for x, z, height in ((-24, 13, 12), (24, 19, 16), (-23, 48, 14),
                             (23, 57, 12), (-22, 88, 16), (22, 102, 14)):
            Entity(parent=self.scene, model=Cylinder(), position=(x, 0, z),
                   scale=(3, height, 3), color=color.rgb32(102, 91, 67),
                   unlit=True)
            Entity(parent=self.scene, model="sphere", position=(x, height, z),
                   scale=(8, 5, 8), color=color.rgb32(67, 126, 76), unlit=True)
        Entity(parent=self.scene, model="sphere", position=(0, -10, 120),
               scale=(43, 17, 37), color=color.rgb32(70, 125, 81), unlit=True)
        Entity(parent=self.scene, model="plane", position=(0, -1, 118),
               scale=(55, 1, 50), color=color.rgb32(107, 153, 87), unlit=True)
        for x, z in ((-19, 106), (-15, 127), (17, 110), (20, 131), (0, 143)):
            Entity(parent=self.scene, model="sphere", position=(x, 1, z),
                   scale=(5, 5, 6), color=color.rgb32(72, 138, 84), unlit=True)
        Text("DRAGON ISLAND", parent=self.scene, position=(0, 17, 118),
             origin=(0, 0), scale=2, color=color.rgb32(255, 243, 196),
             billboard=True)

    def start(self):
        self.finished = False
        self.phase = "gender_choice"
        self.gender = None
        self.timer = 0
        self.collected = 0
        self.lives = 3
        self.invulnerability = 0
        game = self.game
        game.active_quest = self
        game.player = self.player
        game.won = False
        game.game_over = False
        game.elapsed = 0
        game.room.root.enabled = False
        game.forest.root.enabled = False
        game.hoop_stage.root.enabled = False
        game.water_scene.enabled = False
        game.original_player.entity.enabled = False
        game.room_dragon.entity.enabled = False
        game.water_queen.entity.enabled = False
        game.water_baby.entity.enabled = False
        for chaser in game.chasers:
            chaser.entity.enabled = False
        game._disable_dialogue_buttons()
        for item in game.hud_items:
            item.enabled = False
        self.scene.enabled = True
        self.player.entity.enabled = True
        self.player.entity.position = Vec3(0, .8, 1)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player.entity.scale = .64
        self.player.entity.enabled = False
        self.mother.entity.enabled = True
        self.father.entity.enabled = True
        self.mother.entity.position = Vec3(-3, 1.4, -3)
        self.father.entity.position = Vec3(3, 1.4, -3)
        self.egg.enabled = True
        for button in self.gender_buttons:
            button.enabled = True
        for rock, _ in self.obstacles:
            rock.enabled = True
        for rune in self.sigils:
            rune.enabled = True
        self.island_core.enabled = True
        self.lives_text.enabled = False
        game.room_message.position = (0, .34)
        game.room_message.scale = .98
        game.room_message.color = color.rgb32(49, 68, 42)
        game.room_message.text = (
            "You have chosen the Earth Clan.\n"
            "You are the child of an Earth dragon and a Sea prince.\n"
            "You are not part of the Earth royal family.\nWill you hatch as male or female?"
        )
        game.room_message.enabled = True
        window.color = color.rgb32(153, 180, 132)
        camera.position = Vec3(0, 7, -16)
        camera.look_at(Vec3(0, 1.5, 2))

    def choose_gender(self, gender):
        if self.phase != "gender_choice":
            return
        self.gender = gender
        self.phase = "hatching"
        self.timer = 3.8
        self.egg.enabled = False
        self.player.entity.enabled = True
        for button in self.gender_buttons:
            button.enabled = False
        self.player.entity.position = Vec3(0, 1, 1)
        self.player.entity.rotation = Vec3(0, 180, 0)
        self.game.room_message.text = (
            f"The egg hatches! You are a {gender} Earth and Sea dragon.\n"
            "Your father is the Sea Prince, so you are a Sea Prince/Princess."
        )

    def update(self, dt):
        if self.phase == "idle":
            return
        self.game.elapsed += dt
        if self.phase in ("gender_choice", "finished"):
            self.player.animate(self.game.elapsed)
            if self.phase == "finished":
                self.mother.animate(self.game.elapsed + .7)
                self.father.animate(self.game.elapsed + 1.2)
            return
        if self.phase == "hatching":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + .7)
            self.father.animate(self.game.elapsed + 1.2)
            self.timer -= dt
            if self.timer <= 0:
                self.phase = "time_jump"
                self.timer = 4.5
                self.player.entity.scale = 1.25
                self.player.entity.position = Vec3(0, 2, 4)
                self.game.room_message.text = (
                    "17 YEARS LATER\n"
                    f"You have grown into a Sea {'Prince' if self.gender == 'male' else 'Princess'},\n"
                    "with the strength of both Earth and Sea clans."
                )
                camera.position = Vec3(0, 8, -16)
                camera.look_at(Vec3(0, 2, 4))
            return
        if self.phase == "time_jump":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + .7)
            self.father.animate(self.game.elapsed + 1.2)
            self.timer -= dt
            if self.timer <= 0:
                self.phase = "rescue_flight"
                self.player.entity.position = Vec3(0, 3, 0)
                self.player.entity.rotation = Vec3(0, 0, 0)
                self.lives_text.text = "HEARTS: 3"
                self.lives_text.enabled = True
                self.game.room_message.text = (
                    "Dragon Island is in danger! Fly through the four green sigils\n"
                    "to restore its ancient shield and save every dragon."
                )
                self.timer = 4
                self.game.status_text.text = "WASD / arrow keys: fly. Reach all four sigils."
                self.game.status_text.enabled = True
                self.game.progress_text.enabled = True
                self.game.progress_text.text = "ISLAND SHIELD  0 / 4"
                camera.position = Vec3(0, 9, -14)
                camera.look_at(Vec3(0, 3, 14))
            return
        if self.phase == "rescue_failed":
            self.player.animate(self.game.elapsed)
            return
        if self.phase == "rescue_flight":
            self._update_rescue(dt)

    def _update_rescue(self, dt):
        player = self.player.entity
        self.invulnerability = max(0, self.invulnerability - dt)
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        player.x = max(-18, min(18, player.x + horizontal * 10 * dt))
        player.y = max(.5, min(10, player.y + vertical * 7 * dt))
        player.z += 10 * dt
        player.rotation_z = lerp(player.rotation_z, -horizontal * 18, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 10, dt * 4)
        self.player.animate(self.game.elapsed)
        camera.position = lerp(camera.position, player.position + Vec3(0, 6, -13), dt * 3)
        camera.look_at(player.position + Vec3(0, .2, 14))
        self.timer -= dt
        if self.timer <= 0 and self.game.room_message.enabled:
            self.game.room_message.enabled = False
        if self.invulnerability <= 0:
            for rock, radius in self.obstacles:
                if (rock.enabled and abs(player.z - rock.z) < radius + .8
                        and ((player.x - rock.x) ** 2
                             + (player.y - rock.y) ** 2) < (radius + .6) ** 2):
                    self.lives -= 1
                    self.lives_text.text = f"HEARTS: {self.lives}"
                    self.invulnerability = 1.3
                    if self.lives <= 0:
                        self.phase = "rescue_failed"
                        self.finished = True
                        self.game.room_message.text = "The island is still in danger. Press R to retry."
                        self.game.room_message.enabled = True
                        self.game.status_text.text = "OUT OF HEARTS — Press R to retry."
                        return
                    else:
                        player.z = max(0, player.z - 8)
                        player.x = max(-16, min(16, player.x + (2 if player.x < 0 else -2)))
                        self.game.room_message.text = "A falling rock hit you! Keep flying."
                        self.game.room_message.enabled = True
                        self.timer = 1.1
                    break
        for index in range(self.collected, len(self.sigils)):
            rune = self.sigils[index]
            rune.rotation_y += 65 * dt
            if distance(player.position, rune.position) < 2.8:
                rune.enabled = False
                self.collected += 1
                self.game.progress_text.text = f"ISLAND SHIELD  {self.collected} / 4"
                break
        if self.collected >= len(self.sigils) and player.z > 106:
            self.phase = "finished"
            self.finished = True
            self.island_core.color = color.rgb32(159, 255, 159)
            self.game.room_message.text = (
                "The island shield is restored!\n"
                "You saved the whole island and every dragon who lives here."
            )
            self.game.room_message.enabled = True
            self.game.status_text.text = "EARTH CLAN QUEST COMPLETE — Press R to begin again."

    def restart(self):
        if self.phase == "rescue_failed":
            self.finished = False
            self.phase = "rescue_flight"
            self.collected = 0
            self.lives = 3
            self.invulnerability = 0
            self.player.entity.position = Vec3(0, 3, 0)
            self.player.entity.rotation = Vec3(0, 0, 0)
            self.player.entity.rotation_x = 0
            self.player.entity.rotation_z = 0
            for rock, _ in self.obstacles:
                rock.enabled = True
            for rune in self.sigils:
                rune.enabled = True
            self.island_core.color = color.rgb32(64, 169, 91)
            self.lives_text.text = "HEARTS: 3"
            self.lives_text.enabled = True
            self.game.elapsed = 0
            self.game.room_message.enabled = False
            self.game.status_text.text = "Reach all four sigils and save the island."
            self.game.progress_text.text = "ISLAND SHIELD  0 / 4"
            self.game.progress_text.enabled = True
            return
        self.start()
