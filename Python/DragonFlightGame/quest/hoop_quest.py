"""Timed flight quest: pass through all hoops before time runs out."""

from ursina import *

from .quest import Quest


class HoopQuest(Quest):
    TIME_LIMIT = 20.0

    def __init__(self, game, hoop_stage):
        super().__init__(game)
        self.hoop_stage = hoop_stage
        self.hoop_index = 0
        self.time_remaining = self.TIME_LIMIT

    def start(self):
        game = self.game
        self.finished = False
        game.elapsed = 0
        game.won = False
        game.game_over = False
        game.dialogue_stage = "hoop_challenge"
        game.room.root.enabled = False
        game.water_scene.enabled = False
        game.room_dragon.entity.enabled = False
        game.forest.root.enabled = False
        self.hoop_stage.root.enabled = True
        game.room_message.enabled = False
        game._disable_dialogue_buttons()
        for item in game.hud_items:
            item.enabled = False
        game.player.entity.position = Vec3(0, 4.5, 0)
        game.player.entity.rotation = Vec3(0, 0, 0)
        game.player.entity.alpha = 1
        self.hoop_index = 0
        self.time_remaining = self.TIME_LIMIT
        for _, hoop in self.hoop_stage.hoops:
            hoop.enabled = True
        game.hoop_index = 0
        game.hoop_time_remaining = self.time_remaining
        game.hoop_challenge_active = True
        game.hoop_challenge_finished = False
        game.hoop_status.text = (
            f"HOOPS 0/{len(self.hoop_stage.hoops)}    "
            f"TIME {self.TIME_LIMIT:.1f}s"
        )
        game.hoop_status.enabled = True
        window.color = color.rgb32(194, 226, 231)
        game._snap_camera(Vec3(0, 6, -13), Vec3(0, .7, 12))

    def restart(self):
        self.start()

    def update(self, dt):
        if self.finished:
            return
        game = self.game
        previous_z = game.player.entity.z
        player = game.player.entity
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        boost = 1.35 if held_keys["space"] else 1.0
        player.x += horizontal * 11 * dt
        player.y += vertical * 9 * dt
        player.z += game.speed * boost * dt
        player.x = max(-11, min(11, player.x))
        player.y = max(1.2, min(10.5, player.y))
        player.rotation_z = lerp(player.rotation_z, -horizontal * 22, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 12, dt * 4)
        game.elapsed += dt
        game.player.animate(game.elapsed)

        if self.hoop_index < len(self.hoop_stage.hoops):
            center, hoop = self.hoop_stage.hoops[self.hoop_index]
            if previous_z < center.z <= player.z:
                if ((player.x - center.x) ** 2 + (player.y - center.y) ** 2) ** .5 <= 2.25:
                    hoop.enabled = False
                    self.hoop_index += 1
                else:
                    self._finish("MISSED A HOOP! Press R to retry")
                    return

        self.time_remaining -= dt
        game.hoop_index = self.hoop_index
        game.hoop_time_remaining = self.time_remaining
        game.hoop_status.text = (
            f"HOOPS {self.hoop_index}/{len(self.hoop_stage.hoops)}    "
            f"TIME {max(0, self.time_remaining):.1f}s"
        )
        camera.position = lerp(camera.position,
                               player.position + Vec3(0, 6, -13), dt * 3)
        camera.look_at(player.position + Vec3(0, .7, 12))
        if self.hoop_index == len(self.hoop_stage.hoops):
            self._finish("ALL HOOPS! Challenge complete!")
        elif self.time_remaining <= 0:
            self._finish("TIME UP! Press R to retry")

    def _finish(self, message):
        self.finished = True
        self.game.hoop_challenge_active = False
        self.game.hoop_challenge_finished = True
        self.game.hoop_status.text = message
        if self.hoop_index == len(self.hoop_stage.hoops):
            self.game._enter_clan_choice_room()
