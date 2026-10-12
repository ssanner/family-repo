"""Fly beside the Water Queen, dive, avoid fish, and reach the palace."""

import math

from ursina import *

from .quest import Quest


class WaterJourneyQuest(Quest):
    GOAL_Z = 182
    SURFACE_Y = 5.5
    DIVE_Z = 24

    def __init__(self, game, queen, hatchling, dragon_factory):
        super().__init__(game)
        self.queen = queen
        self.hatchling = hatchling
        self.dragon_factory = dragon_factory
        self.world = Entity(name="underwater_journey", enabled=False)
        self.sleep_room = Entity(name="underwater_palace_bedroom", enabled=False)
        self._build_ocean()
        self._build_palace()
        self._build_bedroom()
        self.fish = []
        self._build_fish()
        self.palace_dragon = self.dragon_factory(
            Vec3(0, 1.5, 7),
            (color.rgb32(177, 105, 71), color.rgb32(107, 70, 65),
             color.rgb32(245, 201, 120)),
            scale=1.05, parent=self.sleep_room)
        self.palace_dragon.entity.rotation_y = 180
        self.phase = "flight"
        self.story_timer = 0
        self.lives = 3
        self.invulnerable = 0
        self.dived = False

    def _build_ocean(self):
        Entity(parent=self.world, model="plane", position=(0, -5, 90),
               scale=(110, 1, 230), color=color.rgb32(22, 72, 96), unlit=True)
        Entity(parent=self.world, model="plane",
               position=(0, self.SURFACE_Y, 90), scale=(110, 1, 230),
               color=color.rgba32(47, 147, 184, 105), unlit=True)
        # Rocky columns and coral make the underwater route visible at a glance.
        for index, z in enumerate(range(18, self.GOAL_Z, 14)):
            for side in (-1, 1):
                x = side * (17 + (index % 3) * 2)
                height = 2.5 + (index % 4) * .65
                Entity(parent=self.world, model=Cylinder(),
                       position=(x, -5, z + side * 3),
                       scale=(1.1, height, 1.1),
                       color=color.rgb32(40 + index % 3 * 8, 105, 111),
                       unlit=True)
                for branch in (-1, 1):
                    Entity(parent=self.world, model=Cone(),
                           position=(x + branch * .55, -2.3, z + side * 3),
                           rotation_z=branch * 9,
                           scale=(.65, 1.8, .65),
                           color=color.rgb32(50, 143 + index % 3 * 10, 137),
                           unlit=True)

    def _build_palace(self):
        z = self.GOAL_Z
        palace_color = color.rgb32(71, 155, 168)
        trim_color = color.rgb32(239, 206, 120)
        for x in (-7, 7):
            Entity(parent=self.world, model=Cylinder(), position=(x, -4, z),
                   scale=(2.6, 15, 2.6), color=palace_color, unlit=True)
            Entity(parent=self.world, model="sphere", position=(x, 10.8, z),
                   scale=3.2, color=trim_color, unlit=True)
        Entity(parent=self.world, model="cube", position=(0, 8.8, z),
               scale=(17, 2, 4), color=trim_color, unlit=True)
        Entity(parent=self.world, model="cube", position=(0, 2.5, z + 1),
               scale=(9, 7, 2), color=color.rgb32(31, 100, 129), unlit=True)
        Entity(parent=self.world, model="sphere", position=(0, 3, z - 1),
               scale=5.2, color=color.rgba32(89, 210, 224, 90), unlit=True)
        Text("UNDERWATER PALACE", parent=self.world,
             position=(0, 12.8, z), origin=(0, 0), scale=2.2,
             color=color.rgb32(240, 231, 187), billboard=True)

    def _build_fish(self):
        positions = ((-5, 3.2, 34), (3.5, 1.6, 49), (7, 5.4, 65),
                     (-1.5, 4.4, 81), (-7, 2.2, 98), (4.5, 3.4, 116),
                     (-4.0, 5.5, 134), (6, 1.8, 151), (0, 4, 169))
        palettes = (color.rgb32(255, 171, 86), color.rgb32(121, 224, 213),
                    color.rgb32(244, 117, 117))
        for index, (x, y, z) in enumerate(positions):
            fish = Entity(parent=self.world, position=(x, y, z))
            tint = palettes[index % len(palettes)]
            Entity(parent=fish, model="sphere", scale=(.8, .5, 1.25), color=tint)
            Entity(parent=fish, model=Cone(), position=(0, 0, -.82),
                   rotation_x=90, scale=(.3, .7, .3), color=tint)
            Entity(parent=fish, model="sphere", position=(0, .12, .42),
                   scale=.12, color=color.white, unlit=True)
            Entity(parent=fish, model="sphere", position=(0, .12, .49),
                   scale=.06, color=color.black, unlit=True)
            self.fish.append((fish, Vec3(x, y, z), index * .9))

    def _build_bedroom(self):
        wall_color = color.rgb32(32, 84, 108)
        Entity(parent=self.sleep_room, model="cube", position=(0, -.35, 0),
               scale=(28, .7, 30), color=color.rgb32(21, 60, 79), unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 8, 14),
               scale=(28, 16, .7), color=wall_color, unlit=True)
        for x in (-14, 14):
            Entity(parent=self.sleep_room, model="cube", position=(x, 4, 0),
                   scale=(.7, 8, 30), color=wall_color, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, .2, 0),
               scale=(4.5, .5, 6), color=color.rgb32(87, 151, 162), unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, .55, -1.4),
               scale=(4, .25, 1.3), color=color.rgb32(202, 225, 219), unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 1.0, 0),
               scale=(4.8, .16, 6.3), color=color.rgb32(74, 127, 146), unlit=True)

    def start(self):
        game = self.game
        self.finished = False
        self.phase = "flight"
        self.story_timer = 0
        self.lives = 3
        self.invulnerable = 1.5
        self.dived = False
        game.elapsed = 0
        game.lives = self.lives
        game.game_over = False
        game.won = False
        game.water_scene.enabled = False
        game.room.root.enabled = False
        game.room_message.enabled = False
        self.sleep_room.enabled = False
        self.world.enabled = True
        self.hatchling.entity.parent = self.world
        self.queen.entity.parent = self.world
        self.hatchling.entity.enabled = True
        self.hatchling.entity.position = Vec3(0, 7.5, 0)
        self.hatchling.entity.rotation = Vec3(0, 0, 0)
        game.player = self.hatchling
        self.palace_dragon.entity.enabled = False
        self.queen.entity.enabled = True
        self.queen.entity.position = Vec3(3, 8.2, -6)
        for fish, base, _ in self.fish:
            fish.position = Vec3(base)
        for item in game.hud_items:
            item.enabled = False
        game.progress_text.enabled = True
        game.status_text.enabled = True
        game.lives_text.enabled = True
        game.status_text.scale = .9
        game.progress_text.text = "UNDERWATER PALACE"
        game.status_text.text = (
            "Follow the Queen: dive beneath the surface,\n"
            "dodge the fish, and reach the palace!"
        )
        game.lives_text.text = "HEARTS: 3"
        window.color = color.rgb32(57, 132, 158)
        camera.position = self.hatchling.entity.position + Vec3(0, 5.5, -13)
        camera.look_at(self.hatchling.entity.position + Vec3(0, .3, 12))

    def restart(self):
        self.start()

    def update(self, dt):
        game = self.game
        if self.phase == "sleep":
            self._update_sleep(dt)
            return
        if self.phase == "wake":
            game.elapsed += dt
            self.hatchling.animate(game.elapsed)
            self.palace_dragon.animate(game.elapsed + 1)
            return
        if self.finished:
            return

        game.elapsed += dt
        self.invulnerable = max(0, self.invulnerable - dt)
        player = self.hatchling.entity
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        boost = 1.3 if held_keys["space"] else 1.0
        player.x += horizontal * 11 * dt
        player.y += vertical * 8 * dt
        player.z += 12.5 * boost * dt
        player.x = max(-23, min(23, player.x))
        player.y = max(-2.5, min(9.5, player.y))
        if not self.dived and player.z >= self.DIVE_Z:
            if player.y < self.SURFACE_Y - .3:
                self.dived = True
                game.status_text.text = (
                    "You dive beneath the surface!\n"
                    "Follow the Queen to the palace."
                )
            else:
                player.z = self.DIVE_Z
                game.status_text.text = "DIVE BELOW THE SURFACE!\nUse S or Down."

        player.rotation_z = lerp(player.rotation_z, -horizontal * 20, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 10, dt * 4)
        self.hatchling.animate(game.elapsed)
        queen_entity = self.queen.entity
        target = player.position + Vec3(2.8, .8, -4.5)
        queen_entity.position = lerp(queen_entity.position, target, min(1, dt * 2.5))
        queen_entity.y = max(-1, min(9, queen_entity.y))
        queen_entity.look_at(player.position)
        self.queen.animate(game.elapsed + .8)

        for fish, base, phase in self.fish:
            fish.position = Vec3(base.x + math.sin(game.elapsed * 1.4 + phase) * 2.0,
                                 base.y + math.sin(game.elapsed * 1.1 + phase) * .8,
                                 base.z)
            if (self.dived and self.invulnerable <= 0
                    and distance(player.position, fish.position) < 1.55):
                self._hit_fish()
                break

        if player.z >= self.GOAL_Z - 2:
            if self.dived and player.y <= self.SURFACE_Y - .5 and abs(player.x) <= 8:
                self._arrive_at_palace()
                return
            player.z = min(player.z, self.GOAL_Z - 2)
            game.status_text.text = (
                "The palace entrance is below the surface.\n"
                "Dive down to enter!"
            )

        camera.position = lerp(camera.position, player.position + Vec3(0, 5, -13), dt * 3)
        camera.look_at(player.position + Vec3(0, .2, 12))
        game.progress_text.text = f"PALACE DISTANCE  {max(0, int(self.GOAL_Z - player.z))} m"
        game.lives_text.text = f"HEARTS: {self.lives}"
        player.alpha = ((.45 if int(game.elapsed * 12) % 2 else 1)
                        if self.invulnerable > 0 else 1)

    def _hit_fish(self):
        self.lives -= 1
        self.invulnerable = 2.0
        self.game.lives = self.lives
        if self.lives <= 0:
            self.finished = True
            self.game.game_over = True
            self.game.status_text.text = (
                "THE FISH CAUGHT YOU!\nPress R to retry the sea journey."
            )
            return
        self.game.status_text.text = "FISH BUMP!\nSteady your wings and keep going."
        self.hatchling.entity.position = Vec3(
            self.hatchling.entity.x, self.hatchling.entity.y,
            max(0, self.hatchling.entity.z - 8))
        self.hatchling.entity.rotation = Vec3(0, 0, 0)

    def _arrive_at_palace(self):
        game = self.game
        self.phase = "sleep"
        self.story_timer = 3.5
        self.world.enabled = False
        self.sleep_room.enabled = True
        self.hatchling.entity.parent = self.sleep_room
        self.queen.entity.parent = self.sleep_room
        self.hatchling.entity.enabled = True
        self.hatchling.entity.position = Vec3(0, .9, 0)
        self.hatchling.entity.rotation = Vec3(0, 0, 90)
        self.queen.entity.position = Vec3(4, 1.4, 2.8)
        self.queen.entity.rotation_y = 180
        self.palace_dragon.entity.enabled = False
        for item in game.hud_items:
            item.enabled = False
        game.room_message.scale = 1.0
        game.room_message.position = (0, .34)
        game.room_message.text = (
            "You and the Queen reach the underwater palace.\n"
            "After a warm welcome, you curl up and fall asleep."
        )
        game.room_message.enabled = True
        window.color = color.rgb32(35, 64, 83)
        camera.position = Vec3(0, 5.2, -9)
        camera.look_at(Vec3(0, 1.2, 1))

    def _update_sleep(self, dt):
        self.story_timer -= dt
        self.game.elapsed += dt
        self.hatchling.animate(self.game.elapsed)
        self.queen.animate(self.game.elapsed + .8)
        if self.story_timer <= 0:
            self.phase = "wake"
            self.finished = True
            self.hatchling.entity.rotation = Vec3(0, 0, 0)
            self.palace_dragon.entity.enabled = True
            self.game.room_message.text = (
                "Wake up, young Water Dragon!\n"
                "Your new quest: find the lost Moon Pearl in the palace caves."
            )
            self.game.room_message.position = (0, .34)
            camera.position = Vec3(0, 5.5, -9)
            camera.look_at(Vec3(0, 1.5, 2.5))
