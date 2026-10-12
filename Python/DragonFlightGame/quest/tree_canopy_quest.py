"""Forest flight quest: weave through trees and reach the beacon."""

import math

from ursina import *

from .quest import Quest


class TreeCanopyQuest(Quest):
    def __init__(self, game, forest):
        super().__init__(game)
        self.forest = forest

    def start(self):
        game = self.game
        self.finished = False
        game.elapsed = 0
        game.forest.root.enabled = True
        game.room.root.enabled = False
        game.water_scene.enabled = False
        game.hoop_stage.root.enabled = False
        game.room_dragon.entity.enabled = False
        game.room_message.enabled = False
        game._disable_dialogue_buttons()
        game.hoop_status.enabled = False
        game.hoop_challenge_active = False
        game.hoop_challenge_finished = False
        game.hoop_index = 0
        game.hoop_time_remaining = game.hoop_quest.TIME_LIMIT
        game.dialogue_stage = None
        game.dialogue_next_time = None
        for item in game.hud_items:
            item.enabled = True
        window.color = color.rgb32(132, 184, 177)
        game.player.entity.position = Vec3(game.PLAYER_START)
        game.player.entity.rotation = Vec3(0, 0, 0)
        game.lives = 3
        game.invulnerable = 1.5
        game.game_over = False
        game.won = False
        game.status_text.text = ""
        for index, dragon in enumerate(game.chasers):
            dragon.entity.enabled = True
            dragon.entity.position = Vec3((-1 if index == 0 else 1) * 3,
                                          5 + index, -8 - index * 4)
        game._snap_camera(Vec3(0, 7.2, -17), Vec3(0, .8, 11))
        game._update_camera()

    def restart(self):
        self.start()

    def update(self, dt):
        if self.finished:
            return
        game = self.game
        game.elapsed += dt
        game.invulnerable = max(0, game.invulnerable - dt)
        player = game.player.entity
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        boost = 1.35 if held_keys["space"] else 1.0
        player.x += horizontal * 10.5 * dt
        player.y += vertical * 8.0 * dt
        player.z += game.speed * boost * dt
        player.x = max(-game.FOREST_WIDTH + 1.5,
                       min(game.FOREST_WIDTH - 1.5, player.x))
        player.y = max(1.3, min(game.FLIGHT_CEILING, player.y))
        player.rotation_z = lerp(player.rotation_z, -horizontal * 22, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 12, dt * 4)
        game.player.animate(game.elapsed)

        if game.invulnerable <= 0:
            collision_reason = self._collision_reason()
            if collision_reason:
                self._lose_life(collision_reason)
        self._update_chasers(dt)
        if game.lives <= 0:
            return
        if player.z >= game.GOAL_Z - 2:
            if abs(player.x) <= 8.0 and abs(player.y - 6.0) <= 5.2:
                self.finished = True
                game._enter_white_room()
            else:
                self._lose_life("MISSED THE BEACON")
        game._update_camera()
        distance_left = max(0, int(game.GOAL_Z - player.z))
        game.progress_text.text = f"DISTANCE TO GOAL  {distance_left} m"
        game.lives_text.text = f"HEARTS: {game.lives}"
        player.alpha = ((.45 if int(game.elapsed * 12) % 2 else 1)
                        if game.invulnerable > 0 else 1)

    def _collision_reason(self):
        game = self.game
        player = game.player.entity
        for (x, z, trunk_radius, trunk_bottom, trunk_top,
             canopy_colliders) in self.forest.tree_colliders:
            trunk_distance = math.hypot(player.x - x, player.z - z)
            trunk_hit = (
                trunk_distance < trunk_radius + .7
                and player.y + .4 > trunk_bottom
                and player.y - .85 < trunk_top
            )
            if trunk_hit:
                return "TREE STRIKE"
            for cx, cy, cz, rx, ry, rz in canopy_colliders:
                dx = (player.x - cx) / (rx + .55)
                dy = (player.y + .2 - cy) / (ry + .7)
                dz = (player.z - cz) / (rz + .65)
                if dx * dx + dy * dy + dz * dz < 1:
                    return "CANOPY STRIKE"
        return None

    def _lose_life(self, reason):
        game = self.game
        game.lives -= 1
        game.invulnerable = 2.0
        if game.lives <= 0:
            self.finished = True
            game.game_over = True
            game.status_text.text = f"FLIGHT OVER — {reason}  ·  Press R to try again"
            return
        game.status_text.text = f"{reason} — shake them off and keep flying!"
        game.player.entity.position = Vec3(0, 5, max(0, game.player.entity.z - 9))
        game.player.entity.rotation = Vec3(0, 0, 0)
        game.player.entity.alpha = 1
        for index, dragon in enumerate(game.chasers):
            dragon.entity.position = game.player.entity.position + Vec3(
                (-1 if index == 0 else 1) * 4, 1 + index, -9 - index * 3)

    def _update_chasers(self, dt):
        game = self.game
        player = game.player.entity
        for index, dragon in enumerate(game.chasers):
            phase = game.elapsed * 1.2 + index * math.pi
            enemy = dragon.entity
            target = player.position + Vec3(math.sin(phase) * 2.2,
                                            .9 + math.sin(phase * 1.6) * .8,
                                            -2.4 - index * 1.5)
            enemy.position = lerp(enemy.position, target, min(1, dt * 8))
            enemy.x = max(-game.FOREST_WIDTH + 1,
                          min(game.FOREST_WIDTH - 1, enemy.x))
            enemy.y = max(1.5, min(game.FLIGHT_CEILING, enemy.y))
            enemy.look_at(player.position)
            dragon.animate(game.elapsed + index * .5)
            if (game.invulnerable <= 0
                    and distance(enemy.position, player.position) < 3.0):
                self._lose_life("CHASER HIT")
                break
