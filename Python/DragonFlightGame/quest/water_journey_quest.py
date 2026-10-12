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
        self.palace_halls = Entity(name="underwater_palace_halls", enabled=False)
        self.time_skip_room = Entity(name="seventeen_years_later", enabled=False)
        self.sky_scene = Entity(name="sky_kingdom", enabled=False)
        self._build_ocean()
        self._build_palace()
        self._build_bedroom()
        self._build_palace_halls()
        self._build_time_skip_room()
        self._build_sky_kingdom()
        self.fish = []
        self._build_fish()
        self.palace_dragon = self.dragon_factory(
            Vec3(0, 1.5, 7),
            (color.rgb32(177, 105, 71), color.rgb32(107, 70, 65),
             color.rgb32(245, 201, 120)),
            scale=1.05, parent=self.palace_halls)
        self.palace_dragon.entity.rotation_y = 180
        self.sky_queen = self.dragon_factory(
            Vec3(0, 1.7, 13),
            (color.rgb32(123, 170, 220), color.rgb32(77, 112, 179),
             color.rgb32(255, 221, 128)),
            scale=1.2, parent=self.sky_scene)
        self.sky_queen.entity.rotation_y = 180
        self._add_sky_crown(self.sky_queen.entity)
        self.sky_prince = self.dragon_factory(
            Vec3(0, 1.5, 19),
            (color.rgb32(94, 149, 192), color.rgb32(54, 91, 146),
             color.rgb32(209, 235, 246)),
            scale=1.05, parent=self.sky_scene)
        self.sky_prince.entity.rotation_y = 180
        self.sky_prince.entity.enabled = False
        self.sky_princesses = []
        for position, palette in (
                (Vec3(-3, 1.5, 19),
                 (color.rgb32(190, 126, 200), color.rgb32(129, 82, 159),
                  color.rgb32(255, 218, 139))),
                (Vec3(3, 1.5, 19),
                 (color.rgb32(233, 155, 185), color.rgb32(173, 102, 147),
                  color.rgb32(255, 231, 157)))):
            princess = self.dragon_factory(position, palette,
                                           scale=1.0, parent=self.sky_scene)
            princess.entity.rotation_y = 180
            princess.entity.enabled = False
            self.sky_princesses.append(princess)
        self.phase = "flight"
        self.story_timer = 0
        self.lives = 3
        self.invulnerable = 0
        self.dived = False
        self.has_flica = False
        self.magic_pulse_age = 0
        self.magic_cooldown = 0

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
        palace_color = color.rgb32(53, 127, 151)
        light_stone = color.rgb32(105, 190, 190)
        trim_color = color.rgb32(245, 211, 129)
        deep_blue = color.rgb32(24, 78, 111)

        # A broad central hall and two stepped wings make the palace read as
        # a large destination from far down the swimming route.
        Entity(parent=self.world, model="cube", position=(0, 3, z),
               scale=(25, 16, 7), color=palace_color, unlit=True)
        Entity(parent=self.world, model="cube", position=(0, 11.2, z),
               scale=(28, 1.2, 8), color=trim_color, unlit=True)
        for x in (-15, 15):
            Entity(parent=self.world, model="cube", position=(x, 1.8, z),
                   scale=(9, 13, 7), color=light_stone, unlit=True)
            Entity(parent=self.world, model="cube", position=(x, 8.5, z),
                   scale=(10, 1, 8), color=trim_color, unlit=True)
            # Tall cylindrical towers rise above the wings.
            Entity(parent=self.world, model=Cylinder(), position=(x, -5, z),
                   scale=(3.8, 23, 3.8), color=palace_color, unlit=True)
            Entity(parent=self.world, model=Cone(), position=(x, 13.5, z),
                   scale=(5.2, 6, 5.2), color=deep_blue, unlit=True)
            Entity(parent=self.world, model="sphere", position=(x, 16.2, z),
                   scale=1.1, color=trim_color, unlit=True)

        # Central keep, layered roof, and columns frame a clearly visible gate.
        Entity(parent=self.world, model="cube", position=(0, 12.2, z),
               scale=(15, 2, 8), color=light_stone, unlit=True)
        Entity(parent=self.world, model=Cone(), position=(0, 15.4, z),
               scale=(18, 7, 10), color=deep_blue, unlit=True)
        Entity(parent=self.world, model="cube", position=(0, 2.3, z + 3.2),
               scale=(11, 8, 1.1), color=deep_blue, unlit=True)
        Entity(parent=self.world, model="cube", position=(0, 2.3, z + 3.85),
               scale=(7.6, 6.3, .22), color=color.rgb32(14, 43, 74), unlit=True)
        for x in (-5.5, 5.5):
            Entity(parent=self.world, model=Cylinder(), position=(x, -5, z + 3),
                   scale=(1.35, 14, 1.35), color=trim_color, unlit=True)
            Entity(parent=self.world, model="sphere", position=(x, 2.1, z + 3),
                   scale=(1.8, .65, 1.8), color=light_stone, unlit=True)

        # Repeated glowing windows, pearls, and a crest add detail at distance.
        for x in (-17, -12, -7, 7, 12, 17):
            Entity(parent=self.world, model="sphere", position=(x, 4.8, z + 3.65),
                   scale=(1.25, 2.1, .35), color=color.rgb32(102, 224, 230),
                   unlit=True)
        Entity(parent=self.world, model="sphere", position=(0, 7.3, z + 3.9),
               scale=(2.5, 3, .65), color=color.rgba32(93, 225, 231, 190),
               unlit=True)
        for x in (-21, 21):
            Entity(parent=self.world, model="sphere", position=(x, 10.8, z),
                   scale=1.25, color=color.rgb32(113, 231, 225), unlit=True)
        Text("UNDERWATER PALACE", parent=self.world,
             position=(0, 20, z), origin=(0, 0), scale=2.7,
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
            belly = color.rgb32(255, 223, 166)
            fin = color.rgb32(255, 210, 123)
            Entity(parent=fish, model="sphere", scale=(1.05, .72, 1.55),
                   color=tint)
            Entity(parent=fish, model="sphere", position=(0, -.27, .18),
                   scale=(.79, .3, 1.05), color=belly)
            # A forked tail, dorsal fin, and paired pectoral fins give each
            # fish a recognizable silhouette from the chase camera.
            for side in (-1, 1):
                Entity(parent=fish, model=Cone(), position=(0, 0, -1.42),
                       rotation_x=side * 24, scale=(.48, .17, .78), color=fin)
                Entity(parent=fish, model=Cone(), position=(side * .72, -.02, -.05),
                       rotation_z=side * -38, rotation_x=90,
                       scale=(.27, .15, .68), color=fin)
                Entity(parent=fish, model="sphere", position=(side * .83, .18, .52),
                       scale=(.16, .2, .12), color=color.white, unlit=True)
                Entity(parent=fish, model="sphere", position=(side * .94, .18, .56),
                       scale=(.075, .11, .07), color=color.rgb32(29, 43, 54),
                       unlit=True)
                # Three little gill marks on each side.
                for gill in range(3):
                    Entity(parent=fish, model="sphere",
                           position=(side * .91, .02, .02 + gill * .19),
                           scale=(.045, .17, .055),
                           color=color.rgb32(255, 236, 188), unlit=True)
            Entity(parent=fish, model=Cone(), position=(0, .55, .05),
                   rotation_z=180, scale=(.4, .45, .55), color=tint)
            Entity(parent=fish, model="sphere", position=(0, .05, 1.32),
                   scale=(.17, .13, .1), color=color.rgb32(49, 73, 82),
                   unlit=True)
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
        wood = color.rgb32(108, 72, 116)
        gold = color.rgb32(234, 195, 112)
        mattress = color.rgb32(114, 177, 190)
        blanket = color.rgb32(68, 125, 164)
        # Raised carved frame with four feet and a mattress whose top remains
        # at the original sleeping height for the hatchling.
        for x in (-2, 2):
            for z in (-2.65, 2.65):
                Entity(parent=self.sleep_room, model="cube", position=(x, .18, z),
                       scale=(.38, .75, .38), color=wood, unlit=True)
                Entity(parent=self.sleep_room, model="sphere", position=(x, .58, z),
                       scale=(.48, .4, .48), color=gold, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, .47, 0),
               scale=(4.8, .45, 6.2), color=wood, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, .72, 0),
               scale=(4.35, .48, 5.8), color=mattress, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, .98, .55),
               scale=(4.15, .12, 3.1), color=blanket, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 1.02, -1.65),
               scale=(3.5, .26, 1.15), color=color.rgb32(223, 235, 220),
               unlit=True)
        # Tall jeweled headboard and canopy make it feel like a royal bed.
        Entity(parent=self.sleep_room, model="cube", position=(0, 2.1, -3.05),
               scale=(5.4, 2.5, .45), color=wood, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 2.65, -3.31),
               scale=(4.6, .16, .08), color=gold, unlit=True)
        for x in (-2.15, 2.15):
            Entity(parent=self.sleep_room, model="cube", position=(x, 2.25, 0),
                   scale=(.2, 3.2, .2), color=gold, unlit=True)
            Entity(parent=self.sleep_room, model="sphere", position=(x, 3.95, 0),
                   scale=.42, color=color.rgb32(120, 227, 227), unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 3.7, 0),
               scale=(4.6, .16, .2), color=gold, unlit=True)
        Entity(parent=self.sleep_room, model="cube", position=(0, 3.48, 0),
               scale=(4.25, .24, .16), color=color.rgb32(99, 156, 181),
               unlit=True)
        for x in (-1.55, 1.55):
            Entity(parent=self.sleep_room, model="sphere", position=(x, 3.5, .13),
                   scale=.26, color=color.rgb32(132, 236, 225), unlit=True)

    def _build_palace_halls(self):
        hall = self.palace_halls
        stone = color.rgb32(40, 104, 127)
        pale_stone = color.rgb32(96, 169, 177)
        gold = color.rgb32(235, 195, 112)
        Entity(parent=hall, model="cube", position=(0, -.35, 45),
               scale=(20, .7, 100), color=color.rgb32(34, 87, 111), unlit=True)
        Entity(parent=hall, model="cube", position=(0, 10, 45),
               scale=(20, .6, 100), color=stone, unlit=True)
        for x in (-10, 10):
            Entity(parent=hall, model="cube", position=(x, 5, 45),
                   scale=(.7, 11, 100), color=stone, unlit=True)
        # Repeated columns, arch bands, and glowing windows make the long
        # corridor legible and lead the player toward the gem at its far end.
        for index, z in enumerate(range(8, 88, 12)):
            for x in (-8.5, 8.5):
                Entity(parent=hall, model=Cylinder(), position=(x, 0, z),
                       scale=(1.1, 10, 1.1), color=pale_stone, unlit=True)
                Entity(parent=hall, model="sphere", position=(x, 5, z),
                       scale=(1.45, .5, 1.45), color=gold, unlit=True)
            Entity(parent=hall, model="cube", position=(0, 9.2, z),
                   scale=(18, .7, .8), color=gold, unlit=True)
            for x in (-9.2, 9.2):
                Entity(parent=hall, model="sphere", position=(x, 5.7, z + 5),
                       scale=(.22, 1.8, 1.15),
                       color=color.rgb32(91, 224, 231), unlit=True)

        self.gem_position = Vec3(0, 2.3, 76)
        self.gem = Entity(parent=hall, position=self.gem_position)
        Entity(parent=self.gem, model=Cone(), position=(0, .45, 0),
               scale=(1.25, 1.8, 1.25),
               color=color.rgb32(106, 247, 236), unlit=True)
        Entity(parent=self.gem, model=Cone(), position=(0, -.45, 0),
               rotation_z=180, scale=(1.25, 1.8, 1.25),
               color=color.rgb32(47, 183, 220), unlit=True)
        Entity(parent=self.gem, model="sphere", scale=1.05,
               color=color.rgba32(121, 255, 247, 75), unlit=True)
        Entity(parent=hall, model="cube", position=(0, .25, 76),
               scale=(3.2, .5, 3.2), color=gold, unlit=True)
        for radius in (2.1, 2.8):
            for segment in range(24):
                angle = math.tau * segment / 24
                Entity(parent=hall, model="sphere",
                       position=(math.cos(angle) * radius, .65,
                                 76 + math.sin(angle) * radius),
                       scale=.18, color=color.rgb32(119, 232, 224),
                       unlit=True)
        Text("THE FLICA GEM", parent=hall, position=(0, 5, 76),
             origin=(0, 0), scale=1.4,
             color=color.rgb32(225, 255, 235), billboard=True)

        # A soft magical aura and orbiting motes become visible after contact.
        aura = Entity(parent=self.hatchling.entity, model="sphere",
                      position=(0, .15, .1), scale=(2.8, 2.5, 3.4),
                      color=color.rgba32(87, 235, 238, 45), unlit=True,
                      enabled=False)
        self.flica_sparkles = [aura]
        for index in range(6):
            mote = Entity(parent=self.hatchling.entity, model="sphere",
                          position=(0, 0, 0), scale=.16,
                          color=color.rgb32(148, 255, 231), unlit=True,
                          enabled=False)
            self.flica_sparkles.append(mote)
        self.magic_pulse = Entity(
            parent=self.hatchling.entity, model="sphere", scale=.5,
            position=(0, 0, 0),
            color=color.rgba32(105, 245, 255, 150), unlit=True,
            enabled=False)

    def _build_time_skip_room(self):
        room = self.time_skip_room
        white = color.white
        Entity(parent=room, model="plane", position=(0, 0, 0),
               scale=(40, 1, 40), color=white, unlit=True)
        Entity(parent=room, model="plane", position=(0, 14, 0),
               scale=(40, 1, 40), color=white, unlit=True)
        for x in (-20, 20):
            wall = Entity(parent=room, model="plane", position=(x, 7, 0),
                          scale=(40, 1, 14), color=white, unlit=True)
            wall.rotation_z = 90
        for z in (-20, 20):
            wall = Entity(parent=room, model="plane", position=(0, 7, z),
                          scale=(40, 1, 14), color=white, unlit=True)
            wall.rotation_x = 90

    def _build_sky_kingdom(self):
        scene = self.sky_scene
        cloud = color.rgb32(226, 246, 252)
        stone = color.rgb32(137, 190, 220)
        gold = color.rgb32(255, 220, 137)
        Entity(parent=scene, model="plane", position=(0, -.4, 12),
               scale=(65, 1, 72), color=color.rgb32(151, 207, 225), unlit=True)
        Entity(parent=scene, model="sphere", position=(0, -4, 12),
               scale=(58, 8, 65), color=color.rgb32(128, 190, 216), unlit=True)
        for index, (x, y, z, size) in enumerate((
                (-22, 1, 2, 9), (20, 0, 7, 11), (-17, -1, 28, 12),
                (19, -2, 32, 13), (-23, 1, 48, 10), (24, 0, 53, 12))):
            Entity(parent=scene, model="sphere", position=(x, y, z),
                   scale=(size, size * .38, size * .7), color=cloud, unlit=True)
        # A bright, airy castle behind the audience makes the destination clear.
        Entity(parent=scene, model="cube", position=(0, 5, 39),
               scale=(24, 11, 9), color=stone, unlit=True)
        Entity(parent=scene, model="cube", position=(0, 11, 39),
               scale=(27, 1, 11), color=gold, unlit=True)
        for x in (-10, 10):
            Entity(parent=scene, model=Cylinder(), position=(x, 0, 39),
                   scale=(3.4, 18, 3.4), color=stone, unlit=True)
            Entity(parent=scene, model=Cone(), position=(x, 11, 39),
                   scale=(5.2, 6, 5.2), color=color.rgb32(91, 136, 194),
                   unlit=True)
        Entity(parent=scene, model=Cone(), position=(0, 13, 39),
               scale=(15, 8, 12), color=color.rgb32(92, 142, 198), unlit=True)
        Text("SKY KINGDOM", parent=scene, position=(0, 19, 39),
             origin=(0, 0), scale=2.3, color=color.rgb32(255, 246, 208),
             billboard=True)

    def _add_sky_crown(self, dragon_entity):
        crown = color.rgb32(255, 214, 87)
        Entity(parent=dragon_entity, model="cube", position=(0, .92, 1.02),
               scale=(.7, .14, .5), color=crown, unlit=True)
        for x, height in ((-.25, .28), (-.13, .38), (0, .45),
                          (.13, .38), (.25, .28)):
            Entity(parent=dragon_entity, model=Cone(), position=(x, 1.13, 1.02),
                   scale=(.13, height, .13), color=crown, unlit=True)

    def start(self):
        game = self.game
        self.finished = False
        self.phase = "flight"
        self.story_timer = 0
        self.lives = 3
        self.invulnerable = 1.5
        self.dived = False
        self.has_flica = False
        self.magic_cooldown = 0
        self.magic_pulse.enabled = False
        game.elapsed = 0
        game.lives = self.lives
        game.game_over = False
        game.won = False
        game.water_scene.enabled = False
        game.room.root.enabled = False
        game.room_message.enabled = False
        self.sleep_room.enabled = False
        self.palace_halls.enabled = False
        self.time_skip_room.enabled = False
        self.sky_scene.enabled = False
        self.world.enabled = True
        self.hatchling.entity.parent = self.world
        self.queen.entity.parent = self.world
        self.hatchling.entity.enabled = True
        self.hatchling.entity.scale = .62
        self.hatchling.entity.position = Vec3(0, 7.5, 0)
        self.hatchling.entity.rotation = Vec3(0, 0, 0)
        self.hatchling.entity.alpha = 1
        game.player = self.hatchling
        self.palace_dragon.entity.enabled = False
        self.gem.enabled = True
        self.gem.position = Vec3(self.gem_position)
        for sparkle in self.flica_sparkles:
            sparkle.enabled = False
        self.sky_prince.entity.enabled = False
        for princess in self.sky_princesses:
            princess.entity.enabled = False
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
        if self.phase == "gem_hunt":
            self._update_gem_hunt(dt)
            return
        if self.phase == "flica_awakened":
            self._update_flica_awakened(dt)
            return
        if self.phase in ("time_skip", "sky_travel", "sky_arrival", "sky_meeting"):
            self._update_future_story(dt)
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
        self.hatchling.entity.position = Vec3(0, 1.4, 0)
        self.hatchling.entity.rotation = Vec3(0, 180, 90)
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
            self.phase = "gem_hunt"
            self.finished = False
            self.sleep_room.enabled = False
            self.palace_halls.enabled = True
            self.hatchling.entity.parent = self.palace_halls
            self.queen.entity.parent = self.palace_halls
            self.hatchling.entity.position = Vec3(0, 1.5, 0)
            self.hatchling.entity.rotation = Vec3(0, 0, 0)
            self.queen.entity.position = Vec3(3, 1.5, -4)
            self.queen.entity.rotation = Vec3(0, 0, 0)
            self.palace_dragon.entity.enabled = True
            self.palace_dragon.entity.position = Vec3(0, 1.5, 7)
            self.game.room_message.text = (
                "Wake up, young Water Dragon!\n"
                "A Flica gem waits deep down the palace halls. Touch it to"
                " awaken your magic!"
            )
            self.game.room_message.position = (0, .34)
            self.game.room_message.scale = .9
            self.game.room_message.enabled = True
            self.story_timer = self.game.elapsed + 8
            self.game.progress_text.enabled = True
            self.game.status_text.enabled = True
            self.game.lives_text.enabled = False
            self.game.progress_text.text = "PALACE HALLS"
            self.game.status_text.text = "Fly down the hall to find the glowing gem."
            camera.position = Vec3(0, 6.5, -12)
            camera.look_at(Vec3(0, 2, 16))

    def _update_gem_hunt(self, dt):
        game = self.game
        game.elapsed += dt
        player = self.hatchling.entity
        horizontal = (held_keys["d"] + held_keys["right"]
                      - held_keys["a"] - held_keys["left"])
        vertical = (held_keys["w"] + held_keys["up"]
                    - held_keys["s"] - held_keys["down"])
        player.x = max(-7, min(7, player.x + horizontal * 9 * dt))
        player.y = max(.5, min(7.5, player.y + vertical * 7 * dt))
        player.z += 10 * dt
        player.rotation_z = lerp(player.rotation_z, -horizontal * 18, dt * 5)
        player.rotation_x = lerp(player.rotation_x, vertical * 10, dt * 4)
        self.hatchling.animate(game.elapsed)
        self.palace_dragon.animate(game.elapsed + 1)
        self.queen.animate(game.elapsed + .8)
        self.gem.rotation_y += 45 * dt
        self.gem.y = self.gem_position.y + math.sin(game.elapsed * 2) * .18
        self.queen.entity.position = lerp(
            self.queen.entity.position,
            player.position + Vec3(-3, .5, -5), min(1, dt * 2))
        self.queen.entity.look_at(player.position)
        camera.position = lerp(camera.position, player.position + Vec3(0, 5, -12), dt * 3)
        camera.look_at(player.position + Vec3(0, .3, 14))
        game.progress_text.text = f"PALACE HALLS  {max(0, int(self.gem_position.z - player.z))} m"
        if game.room_message.enabled and game.elapsed > self.story_timer:
            game.room_message.enabled = False
        if distance(player.position, self.gem.position) < 2.4:
            self._awaken_flica()

    def _awaken_flica(self):
        self.phase = "flica_awakened"
        self.has_flica = True
        self.gem.enabled = False
        self.story_timer = 2.7
        self.story_stage = 0
        for sparkle in self.flica_sparkles:
            sparkle.enabled = True
        player = self.hatchling.entity
        player.rotation = Vec3(0, 0, 0)
        player.look_at(self.queen.entity.position)
        self.queen.entity.look_at(player.position)
        self.game.progress_text.enabled = False
        self.game.status_text.enabled = False
        self.game.lives_text.enabled = False
        self.game.room_message.text = "You: What is this?"
        self.game.room_message.scale = 1.0
        self.game.room_message.enabled = True
        self.game.status_text.text = "The gem's light swirls around you..."

    def _update_flica_awakened(self, dt):
        game = self.game
        game.elapsed += dt
        self.hatchling.animate(game.elapsed)
        for index, mote in enumerate(self.flica_sparkles[1:]):
            angle = game.elapsed * 2.2 + index * math.tau / 6
            mote.position = Vec3(math.cos(angle) * 1.5,
                                 .3 + math.sin(angle * 1.3) * .7,
                                 math.sin(angle) * 1.5)
        self.queen.animate(game.elapsed + .8)
        if self.story_timer > 0:
            self.story_timer -= dt
            return
        if self.story_stage == 0:
            game.room_message.text = "Mother: Now you have the power of Flica."
            self.story_stage = 1
            self.story_timer = 3.3
            return
        self._begin_time_skip()

    def _begin_time_skip(self):
        self.phase = "time_skip"
        self.story_timer = 3.5
        self.palace_halls.enabled = False
        self.time_skip_room.enabled = True
        self.hatchling.entity.parent = self.time_skip_room
        self.hatchling.entity.position = Vec3(0, 1.5, 0)
        self.hatchling.entity.rotation = Vec3(0, 0, 0)
        self.hatchling.entity.scale = 1.25
        self.queen.entity.enabled = False
        self.palace_dragon.entity.enabled = False
        self.game.room_message.text = "17 YEARS LATER"
        self.game.room_message.scale = 1.7
        self.game.room_message.enabled = True
        self.game.status_text.text = ""
        window.color = color.white
        camera.position = Vec3(0, 5.5, -10)
        camera.look_at(Vec3(0, 1.7, 1))

    def _begin_sky_arrival(self):
        self.phase = "sky_travel"
        self.story_timer = 3.0
        self.time_skip_room.enabled = False
        self.sky_scene.enabled = True
        self.hatchling.entity.parent = self.sky_scene
        self.hatchling.entity.position = Vec3(0, 3.2, -18)
        self.hatchling.entity.rotation = Vec3(0, 0, 0)
        self.hatchling.entity.scale = 1.25
        self.sky_queen.entity.enabled = True
        self.sky_prince.entity.enabled = False
        for princess in self.sky_princesses:
            princess.entity.enabled = False
        self.game.room_message.scale = 1.0
        self.game.room_message.text = "You fly through the clouds toward the Sky Kingdom."
        self.game.room_message.enabled = True
        window.color = color.rgb32(156, 211, 235)
        camera.position = Vec3(0, 9, -29)
        camera.look_at(Vec3(0, 3, 13))

    def _begin_sky_greeting(self):
        self.phase = "sky_arrival"
        self.story_timer = 3.8
        self.hatchling.entity.position = Vec3(0, 1.6, 0)
        self.game.room_message.text = (
            "You arrive at the Sky Kingdom.\n"
            "You: Hello, Sky Queen. I have come from the Water Kingdom."
        )
        camera.position = Vec3(0, 7, -15)
        camera.look_at(Vec3(0, 2, 13))

    def _begin_sky_meeting(self):
        self.phase = "sky_meeting"
        gender = getattr(self.game, "hatching_gender", "male") or "male"
        if gender == "female":
            self.sky_prince.entity.enabled = True
            self.game.room_message.text = (
                "Sky Queen: Welcome to our kingdom!\n"
                "She introduces you to the Sky Prince.\n"
                "Press SPACE to show your Flica magic."
            )
        else:
            for princess in self.sky_princesses:
                princess.entity.enabled = True
            self.game.room_message.text = (
                "Sky Queen: Welcome to our kingdom!\n"
                "She introduces you to the Sky Princesses.\n"
                "Press SPACE to show your Flica magic."
            )
        self.story_timer = 0

    def _update_future_story(self, dt):
        self.game.elapsed += dt
        dragons = [(self.hatchling, 0), (self.sky_queen, 1.2),
                   (self.sky_prince, 2.1)]
        dragons.extend((princess, 1.8 + index * .6)
                       for index, princess in enumerate(self.sky_princesses))
        for dragon, offset in dragons:
            if dragon.entity.enabled:
                dragon.animate(self.game.elapsed + offset)
        if self.phase == "sky_meeting":
            self.magic_cooldown = max(0, self.magic_cooldown - dt)
            if self.has_flica and held_keys["space"] and self.magic_cooldown <= 0:
                self._cast_flica()
            if self.magic_pulse.enabled:
                self.magic_pulse_age += dt
                self.magic_pulse.scale = 1 + self.magic_pulse_age * 7
                if self.magic_pulse_age >= .8:
                    self.magic_pulse.enabled = False
            return
        if self.phase == "sky_travel":
            self.hatchling.entity.z += 6 * dt
            self.hatchling.entity.y = lerp(self.hatchling.entity.y, 1.8, dt * 2)
            camera.position = lerp(
                camera.position,
                self.hatchling.entity.position + Vec3(0, 6, -11), dt * 2)
            camera.look_at(Vec3(0, 2, 13))
        self.story_timer -= dt
        if self.story_timer > 0:
            return
        if self.phase == "time_skip":
            self._begin_sky_arrival()
        elif self.phase == "sky_travel":
            self._begin_sky_greeting()
        else:
            self._begin_sky_meeting()

    def _cast_flica(self):
        self.magic_pulse_age = 0
        self.magic_cooldown = 1.5
        self.magic_pulse.position = Vec3(0, 0, 0)
        self.magic_pulse.scale = .5
        self.magic_pulse.enabled = True
