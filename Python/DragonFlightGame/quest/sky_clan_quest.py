"""Sky Clan hatchling story and its mother's three membership trials."""

from ursina import *

from .quest import Quest


class SkyClanQuest(Quest):
    """Hatch into the Sky Clan and prove yourself in three flying trials."""

    GATES = (Vec3(-6, 4, 20), Vec3(6, 7, 40),
             Vec3(-5, 2.5, 60), Vec3(5, 6, 80))
    FEATHERS = (Vec3(-7, 3, 22), Vec3(6, 7, 46), Vec3(-4, 5, 70))
    SUMMIT = Vec3(0, 7, 94)

    def __init__(self, game, dragon_factory):
        super().__init__(game)
        self.dragon_factory = dragon_factory
        self.scene = Entity(name="sky_clan_trials", enabled=False)
        self._build_scene()
        sky_palette = (color.rgb32(121, 178, 210), color.rgb32(83, 119, 174),
                       color.rgb32(242, 231, 176))
        mother_palette = (color.rgb32(164, 198, 222), color.rgb32(104, 142, 197),
                          color.rgb32(255, 221, 142))
        self.player = dragon_factory(Vec3(0, .8, 0), sky_palette,
                                    scale=.64, parent=self.scene)
        self.mother = dragon_factory(Vec3(0, 1.5, -5), mother_palette,
                                    scale=1.25, parent=self.scene)
        self.mother.entity.rotation_y = 180
        self.egg = Entity(parent=self.scene, model="sphere", position=(0, 1, 0),
                          scale=(1.65, 2.1, 1.55),
                          color=color.rgb32(156, 190, 222), unlit=True)
        Entity(parent=self.egg, model="sphere", position=(0, .04, .49),
               scale=(.76, .86, .23), color=color.rgb32(244, 231, 177),
               unlit=True)
        self.gates = []
        for position in self.GATES:
            gate = Entity(parent=self.scene, position=position, enabled=False)
            for offset in ((-1.35, 0, 0), (1.35, 0, 0),
                           (0, -1.35, 0), (0, 1.35, 0)):
                Entity(parent=gate, model="sphere", position=offset,
                       scale=(.65, .65, .55),
                       color=color.rgb32(239, 228, 151), unlit=True)
            self.gates.append(gate)
        self.feathers = []
        for position in self.FEATHERS:
            feather = Entity(parent=self.scene, position=position, enabled=False)
            Entity(parent=feather, model=Cone(), rotation_z=-90,
                   scale=(.55, 1.9, .28), color=color.rgb32(255, 231, 119),
                   unlit=True)
            Entity(parent=feather, model="sphere", scale=1.6,
                   color=color.rgba32(255, 231, 119, 55), unlit=True)
            self.feathers.append(feather)
        self.storm_clouds = []
        for index, position in enumerate((
                Vec3(0, 4, 31), Vec3(7, 3, 53), Vec3(-7, 8, 65),
                Vec3(1, 8, 77), Vec3(-8, 3, 87), Vec3(8, 6, 89))):
            cloud = Entity(parent=self.scene, model="sphere", position=position,
                           scale=(4.5, 3.2, 3.7),
                           color=color.rgb32(101, 119, 152), unlit=True,
                           enabled=False)
            for offset in ((-1.1, .18, 0), (.9, .25, .2)):
                Entity(parent=cloud, model="sphere", position=offset,
                       scale=(.7, .65, .7), color=color.rgb32(121, 139, 170),
                       unlit=True)
            self.storm_clouds.append(cloud)
        self.beacon = Entity(parent=self.scene, position=self.SUMMIT,
                             enabled=False)
        Entity(parent=self.beacon, model=Cylinder(), position=(0, 2.4, 0),
               scale=(.55, 4.8, .55), color=color.rgb32(202, 212, 224),
               unlit=True)
        Entity(parent=self.beacon, model="sphere", position=(0, 5.1, 0),
               scale=2.4, color=color.rgb32(255, 235, 130), unlit=True)
        self.phase = "idle"
        self.gender = None
        self.trial_index = 0
        self.target_index = 0
        self.lives = 3
        self.invulnerability = 0
        self.timer = 0
        self.gender_buttons = [
            Button(text="Male", parent=camera.ui, position=(-.16, -.22),
                   scale=(.25, .085), color=color.rgb32(226, 236, 250),
                   text_color=color.rgb32(35, 52, 77),
                   on_click=lambda: self.choose_gender("male")),
            Button(text="Female", parent=camera.ui, position=(.16, -.22),
                   scale=(.25, .085), color=color.rgb32(226, 236, 250),
                   text_color=color.rgb32(35, 52, 77),
                   on_click=lambda: self.choose_gender("female")),
        ]
        for button in self.gender_buttons:
            button.enabled = False
        self.lives_text = Text(parent=camera.ui, position=(-.86, .43), scale=1.1,
                               color=color.rgb32(255, 244, 205), enabled=False)

    def _build_scene(self):
        Entity(parent=self.scene, model="plane", position=(0, -2.2, 49),
               scale=(64, 1, 130), color=color.rgb32(181, 216, 232), unlit=True)
        for x, y, z, size in ((-20, 1, 9, 13), (19, 2, 18, 16),
                              (21, -1, 47, 15), (-22, 2, 58, 18),
                              (19, 1, 82, 17), (-18, 0, 94, 18)):
            Entity(parent=self.scene, model="sphere", position=(x, y, z),
                   scale=(size, size * .35, size * .65),
                   color=color.rgb32(248, 252, 255), unlit=True)
        for x, z in ((-15, 10), (15, 29), (-18, 41), (17, 68), (-16, 79)):
            Entity(parent=self.scene, model=Cylinder(), position=(x, -5, z),
                   scale=(4, 13, 4), color=color.rgb32(132, 160, 186),
                   unlit=True)
            Entity(parent=self.scene, model=Cone(), position=(x, 3, z),
                   scale=(9, 10, 9), color=color.rgb32(166, 195, 216),
                   unlit=True)
        Entity(parent=self.scene, model="sphere", position=(0, -8, 105),
               scale=(28, 12, 25), color=color.rgb32(146, 177, 199), unlit=True)
        Text("SKY SUMMIT", parent=self.scene, position=(0, 16, 99),
             origin=(0, 0), scale=2, color=color.rgb32(255, 246, 207),
             billboard=True)

    def start(self):
        self.finished = False
        self.phase = "gender_choice"
        self.gender = None
        self.trial_index = 0
        self.target_index = 0
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
        self.player.entity.enabled = False
        self.player.entity.position = Vec3(0, .8, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player.entity.scale = .64
        self.mother.entity.enabled = True
        self.egg.enabled = True
        for gate in self.gates:
            gate.enabled = False
        for feather in self.feathers:
            feather.enabled = False
        for cloud in self.storm_clouds:
            cloud.enabled = False
        self.beacon.enabled = False
        self.lives_text.enabled = False
        for button in self.gender_buttons:
            button.enabled = True
        game.room_message.position = (0, .34)
        game.room_message.scale = .98
        game.room_message.color = color.rgb32(43, 58, 77)
        game.room_message.text = (
            "You have chosen the Sky Clan.\n"
            "You begin as an egg. Will you hatch as male or female?"
        )
        game.room_message.enabled = True
        window.color = color.rgb32(206, 230, 242)
        camera.position = Vec3(0, 7, -15)
        camera.look_at(Vec3(0, 1.5, 0))

    def choose_gender(self, gender):
        if self.phase != "gender_choice":
            return
        self.gender = gender
        self.phase = "hatching"
        self.timer = 3.5
        self.egg.enabled = False
        self.player.entity.enabled = True
        self.player.entity.position = Vec3(0, 1, 0)
        self.player.entity.rotation = Vec3(0, 180, 0)
        for button in self.gender_buttons:
            button.enabled = False
        self.game.room_message.text = (
            f"Your egg hatches! You are a {gender} Sky Dragon.\n"
            "Your mother welcomes you to the Sky Clan."
        )

    def _begin_mother_trials(self):
        self.phase = "mother_intro"
        self.timer = 6
        self.game.room_message.text = (
            "Mother: Welcome home, little one. To prove you are ready\n"
            "to join the Sky Clan, you must complete three flying trials."
        )

    def _start_trial(self, index):
        self.trial_index = index
        self.target_index = 0
        self.lives = 3
        self.invulnerability = 0
        self.finished = False
        self.phase = "trial_intro"
        self.player.entity.position = Vec3(0, 3, 0)
        self.player.entity.rotation = Vec3(0, 0, 0)
        self.player.entity.rotation_x = 0
        self.player.entity.rotation_z = 0
        for gate in self.gates:
            gate.enabled = index == 0
        for feather in self.feathers:
            feather.enabled = index == 1
        for cloud in self.storm_clouds:
            cloud.enabled = index in (1, 2)
        self.beacon.enabled = index == 2
        self.lives_text.text = "HEARTS: 3"
        self.lives_text.enabled = True
        if index == 0:
            text = "TRIAL 1: Fly through all four golden wind gates."
            status = "Steer with WASD or the arrow keys."
            progress = "WIND GATES  0 / 4"
        elif index == 1:
            text = "TRIAL 2: Gather three sun feathers and dodge storm clouds."
            status = "Touch each feather; avoid the dark storm clouds."
            progress = "SUN FEATHERS  0 / 3"
        else:
            text = "TRIAL 3: Fly through the storm and reach the summit beacon."
            status = "Watch your altitude and steer around the storm clouds."
            progress = "SKY SUMMIT  94 m"
        self.game.room_message.text = text
        self.game.room_message.enabled = True
        self.timer = 4
        self.game.status_text.text = status
        self.game.status_text.enabled = True
        self.game.progress_text.text = progress
        self.game.progress_text.enabled = True
        camera.position = Vec3(0, 9, -14)
        camera.look_at(Vec3(0, 3, 14))

    def update(self, dt):
        if self.phase == "idle":
            return
        self.game.elapsed += dt
        if self.phase in ("gender_choice", "finished"):
            self.player.animate(self.game.elapsed)
            if self.phase == "finished":
                self.mother.animate(self.game.elapsed + 1)
            return
        if self.phase == "hatching":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + 1)
            self.timer -= dt
            if self.timer <= 0:
                self._begin_mother_trials()
            return
        if self.phase == "mother_intro":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + 1)
            self.timer -= dt
            if self.timer <= 0:
                self._start_trial(0)
            return
        if self.phase == "trial_intro":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + 1)
            self.timer -= dt
            if self.timer <= 0:
                self.game.room_message.enabled = False
                self.phase = f"trial_{self.trial_index + 1}"
            return
        if self.phase == "trial_transition":
            self.player.animate(self.game.elapsed)
            self.mother.animate(self.game.elapsed + 1)
            self.timer -= dt
            if self.timer <= 0:
                if self.trial_index < 2:
                    self._start_trial(self.trial_index + 1)
                else:
                    self._finish_trials()
            return
        if self.phase == "trial_failed":
            self.player.animate(self.game.elapsed)
            return
        if self.phase in ("trial_1", "trial_2", "trial_3"):
            self._update_trial(dt)

    def _update_trial(self, dt):
        player = self.player.entity
        self.invulnerability = max(0, self.invulnerability - dt)
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        player.x = max(-17, min(17, player.x + horizontal * 10 * dt))
        player.y = max(.5, min(11, player.y + vertical * 7 * dt))
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
            for cloud in self.storm_clouds:
                if (cloud.enabled and abs(player.z - cloud.z) < 3.5
                        and (player.x - cloud.x) ** 2 + (player.y - cloud.y) ** 2 < 4.0 ** 2):
                    self._take_hit()
                    if self.phase == "trial_failed":
                        return
                    break
        if self.trial_index == 0:
            self._check_targets(self.gates, "WIND GATES", 4)
        elif self.trial_index == 1:
            self._check_targets(self.feathers, "SUN FEATHERS", 3)
        elif distance(player.position, self.beacon.position) < 3.5:
            self._complete_trial()

    def _check_targets(self, targets, label, target_count):
        if self.target_index >= target_count:
            self._complete_trial()
            return
        target = targets[self.target_index]
        target.rotation_y += 55 * time.dt
        if distance(self.player.entity.position, target.position) < 3.1:
            target.enabled = False
            self.target_index += 1
            self.game.progress_text.text = f"{label}  {self.target_index} / {target_count}"
            if self.target_index >= target_count:
                self._complete_trial()

    def _take_hit(self):
        self.lives -= 1
        self.lives_text.text = f"HEARTS: {self.lives}"
        self.invulnerability = 1.4
        if self.lives <= 0:
            self.phase = "trial_failed"
            self.finished = True
            self.game.room_message.text = (
                "Mother: Take a breath and try that trial again.\n"
                "Press R to retry this Sky Clan trial."
            )
            self.game.room_message.enabled = True
            self.game.status_text.text = "OUT OF HEARTS — Press R to retry this trial."
            return
        self.player.entity.z = max(0, self.player.entity.z - 8)
        self.game.room_message.text = "A storm cloud caught you! Keep flying."
        self.game.room_message.enabled = True
        self.timer = 1.2

    def _complete_trial(self):
        self.phase = "trial_transition"
        self.timer = 4.5
        if self.trial_index == 0:
            self.game.room_message.text = (
                "Mother: Well flown! You found the wind through the clouds.\n"
                "Your next trial is to gather three sun feathers in a storm."
            )
        elif self.trial_index == 1:
            self.game.room_message.text = (
                "Mother: Excellent! You gathered the sun feathers.\n"
                "For your final trial, reach the Sky Summit beacon."
            )
        self.game.room_message.enabled = True
        self.game.status_text.text = "TRIAL COMPLETE"

    def _finish_trials(self):
        self.phase = "finished"
        self.finished = True
        self.mother.entity.position = Vec3(0, 1.5, -4)
        self.player.entity.position = Vec3(0, 2, -1)
        self.player.entity.rotation = Vec3(0, 180, 0)
        self.lives_text.enabled = False
        self.game.progress_text.enabled = False
        self.game.status_text.text = "SKY CLAN TRIALS COMPLETE — Press R to begin again."
        self.game.room_message.text = (
            "Mother: You passed all three trials. You are a true member\n"
            "of the Sky Clan, and I am proud of you!"
        )
        self.game.room_message.enabled = True
        camera.position = Vec3(0, 7, -15)
        camera.look_at(Vec3(0, 2, 1))

    def restart(self):
        if self.phase == "trial_failed":
            self._start_trial(self.trial_index)
            return
        self.start()
