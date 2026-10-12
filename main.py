import math
import random
import numpy as np

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
FPS = 60


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        length = self.length()
        if length > 0.0001:
            return Vector3(self.x / length, self.y / length, self.z / length)
        return Vector3()

    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def copy(self):
        return Vector3(self.x, self.y, self.z)


class Mesh:
    def __init__(self, vertices, faces, color=(1.0, 1.0, 1.0)):
        self.vertices = vertices
        self.faces = faces
        self.color = color
        self.position = Vector3()
        self.rotation = Vector3()
        self.scale = Vector3(1.0, 1.0, 1.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glRotatef(math.degrees(self.rotation.x), 1, 0, 0)
        glRotatef(math.degrees(self.rotation.y), 0, 1, 0)
        glRotatef(math.degrees(self.rotation.z), 0, 0, 1)
        glScalef(self.scale.x, self.scale.y, self.scale.z)

        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for vertex_idx in face:
                v = self.vertices[vertex_idx]
                glVertex3f(v[0], v[1], v[2])
        glEnd()
        glPopMatrix()

    def get_world_position(self):
        return self.position.copy()


class BoxMesh(Mesh):
    def __init__(self, width, height, depth, color=(1.0, 1.0, 1.0)):
        w, h, d = width / 2, height / 2, depth / 2
        vertices = [
            [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d],  # front
            [-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d],  # back
        ]
        faces = [
            [0, 1, 2], [0, 2, 3],  # front
            [5, 4, 7], [5, 7, 6],  # back
            [4, 0, 3], [4, 3, 7],  # left
            [1, 5, 6], [1, 6, 2],  # right
            [3, 2, 6], [3, 6, 7],  # top
            [4, 5, 1], [4, 1, 0],  # bottom
        ]
        super().__init__(vertices, faces, color)


class SphereMesh(Mesh):
    def __init__(self, radius=1.0, segments=16, rings=16, color=(1.0, 1.0, 1.0)):
        vertices = []
        faces = []

        for ring in range(rings + 1):
            theta = ring * math.pi / rings
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            for seg in range(segments + 1):
                phi = seg * 2 * math.pi / segments
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                x = radius * sin_theta * cos_phi
                y = radius * cos_theta
                z = radius * sin_theta * sin_phi
                vertices.append([x, y, z])

        for ring in range(rings):
            for seg in range(segments):
                a = ring * (segments + 1) + seg
                b = a + 1
                c = a + (segments + 1)
                d = c + 1

                faces.append([a, c, b])
                faces.append([b, c, d])

        super().__init__(vertices, faces, color)


class OctahedronMesh(Mesh):
    def __init__(self, size=1.0, color=(1.0, 1.0, 1.0)):
        vertices = [
            [size, 0, 0], [-size, 0, 0],
            [0, size, 0], [0, -size, 0],
            [0, 0, size], [0, 0, -size],
        ]
        faces = [
            [0, 4, 2], [0, 2, 5], [0, 5, 3], [0, 3, 4],
            [1, 2, 4], [1, 5, 2], [1, 3, 5], [1, 4, 3],
        ]
        super().__init__(vertices, faces, color)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Neon Siege - Advanced FPS")
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_NORMALIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        light_position = (15.0, 25.0, 10.0, 1.0)
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.95, 0.9, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.3, 0.35, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 100.0)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24, bold=True)
        self.large_font = pygame.font.SysFont("consolas", 32, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 18)

        self.player = {
            "pos": Vector3(0.0, 1.75, 12.0),
            "yaw": 180.0,
            "pitch": 0.0,
            "health": 100.0,
            "max_health": 100.0,
            "armor": 50.0,
            "max_armor": 100.0,
            "ammo": 30,
            "reserve": 120,
            "score": 0,
            "wave": 1,
            "kills": 0,
            "reloading": False,
            "reload_timer": 0.0,
            "fire_cooldown": 0.0,
            "sprint": False,
            "velocity": Vector3(),
            "grounded": True,
            "last_damage_time": 0.0,
        }

        self.keys = {name: False for name in [
            "forward", "backward", "left", "right", "jump", "crouch", "sprint"
        ]}

        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.pickups = []
        self.debris = []

        self.game_started = False
        self.game_over = False
        self.message = "Mission briefing: neutralize drone hive"
        self.message_timer = 0.0

        self.difficulty = 1.0
        self.enemies_spawned = False

    def set_message(self, text, duration=2.5):
        self.message = text
        self.message_timer = duration

    def spawn_wave(self, wave_num):
        self.enemies.clear()
        count = min(5 + int(wave_num * 2.5), 24)
        self.difficulty = 1.0 + wave_num * 0.25

        for i in range(count):
            angle = (i / max(count, 1)) * math.tau + random.uniform(-0.6, 0.6)
            radius = random.uniform(18, 42)
            x = math.cos(angle) * radius + random.uniform(-6, 6)
            z = math.sin(angle) * radius + random.uniform(-6, 6)

            self.enemies.append({
                "pos": Vector3(x, 0.85, z),
                "mesh": BoxMesh(1.3, 1.7, 0.8, (1.0, 0.15, 0.2)),
                "health": 100.0 * self.difficulty,
                "max_health": 100.0 * self.difficulty,
                "speed": (1.6 + wave_num * 0.15 + random.random() * 0.8) * self.difficulty,
                "alive": True,
                "attack_cooldown": random.random() * 1.5,
                "target_range": 35.0,
                "fire_rate": 1.2 - wave_num * 0.08,
            })

        self.set_message(f"Wave {wave_num}: Drone swarm incoming\", 3.0)\n        self.player[\"wave\"] = wave_num\n        self.enemies_spawned = True\n\n    def spawn_projectile(self, origin, direction, team=\"player\"):\n        self.projectiles.append({\n            \"pos\": origin.copy(),\n            \"velocity\": direction * (28.0 if team == \"player\" else 18.0),\n            \"team\": team,\n            \"life\": 4.0,\n            \"damage\": 35.0 if team == \"player\" else 18.0,\n        })\n\n    def spawn_pickup(self, kind, x, z):\n        color_map = {\n            \"health\": (0.2, 1.0, 0.5),\n            \"ammo\": (1.0, 0.8, 0.2),\n            \"armor\": (0.4, 0.6, 1.0),\n        }\n        self.pickups.append({\n            \"kind\": kind,\n            \"pos\": Vector3(x, 1.3, z),\n            \"mesh\": OctahedronMesh(0.6, color_map.get(kind, (1.0, 1.0, 1.0))),\n            \"phase\": random.random() * math.tau,\n            \"collected\": False,\n        })\n\n    def spawn_particle_burst(self, pos, color, count=12, velocity_scale=1.0):\n        for _ in range(count):\n            angle = random.random() * math.tau\n            elevation = random.uniform(0.3, math.pi / 2)\n            speed = random.uniform(0.08, 0.25) * velocity_scale\n\n            vx = speed * math.sin(elevation) * math.cos(angle)\n            vy = speed * math.sin(elevation) * math.sin(angle)\n            vz = speed * math.cos(elevation)\n\n            self.particles.append({\n                \"pos\": pos.copy(),\n                \"velocity\": Vector3(vx, vy, vz),\n                \"life\": random.uniform(0.3, 0.8),\n                \"color\": color,\n                \"size\": random.uniform(2.0, 6.0),\n            })\n\n    def shoot(self):\n        if not self.game_started or self.game_over:\n            return\n        if self.player[\"reloading\"]:\n            return\n        if self.player[\"fire_cooldown\"] > 0:\n            return\n        if self.player[\"ammo\"] <= 0:\n            self.reload()\n            return\n\n        self.player[\"ammo\"] -= 1\n        self.player[\"fire_cooldown\"] = 0.1\n\n        pitch_rad = math.radians(self.player[\"pitch\"])\n        yaw_rad = math.radians(self.player[\"yaw\"])\n\n        dx = math.sin(yaw_rad) * math.cos(pitch_rad)\n        dy = -math.sin(pitch_rad)\n        dz = math.cos(yaw_rad) * math.cos(pitch_rad)\n\n        direction = Vector3(dx, dy, dz).normalize()\n        self.spawn_projectile(self.player[\"pos\"].copy(), direction, \"player\")\n        self.spawn_particle_burst(self.player[\"pos\"], (1.0, 0.85, 0.3), 6, 0.5)\n\n        hit = False\n        for enemy in self.enemies:\n            if not enemy[\"alive\"]:\n                continue\n            to_enemy = enemy[\"pos\"] - self.player[\"pos\"]\n            dist = to_enemy.length()\n            if dist < 0.1:\n                dist = 0.1\n            to_enemy_norm = to_enemy.normalize()\n            dot = direction.dot(to_enemy_norm)\n\n            if dot > 0.92 and dist < 50.0:\n                enemy[\"health\"] -= 35.0\n                hit = True\n                self.spawn_particle_burst(enemy[\"pos\"], (1.0, 0.4, 0.2), 8)\n\n                if enemy[\"health\"] <= 0:\n                    enemy[\"alive\"] = False\n                    self.player[\"score\"] += 100\n                    self.player[\"kills\"] += 1\n                    self.set_message(f\"Target neutralized | Score +100\")\n                    if random.random() < 0.35:\n                        self.spawn_pickup(\n                            random.choice([\"health\", \"ammo\", \"armor\"]),\n                            enemy[\"pos\"].x + random.uniform(-1, 1),\n                            enemy[\"pos\"].z + random.uniform(-1, 1),\n                        )\n\n    def reload(self):\n        if self.player[\"reloading\"] or self.player[\"ammo\"] == 30 or self.player[\"reserve\"] <= 0:\n            return\n        self.player[\"reloading\"] = True\n        self.player[\"reload_timer\"] = 1.1\n        self.set_message(\"Reloading magazine...\")\n\n    def update_reload(self, dt):\n        if not self.player[\"reloading\"]:\n            return\n        self.player[\"reload_timer\"] -= dt\n        if self.player[\"reload_timer\"] <= 0:\n            needed = 30 - self.player[\"ammo\"]\n            loaded = min(needed, self.player[\"reserve\"])\n            self.player[\"ammo\"] += loaded\n            self.player[\"reserve\"] -= loaded\n            self.player[\"reloading\"] = False\n            self.set_message(\"Magazine ready\")\n\n    def update_enemy_ai(self, dt):\n        for enemy in self.enemies:\n            if not enemy[\"alive\"]:\n                continue\n\n            to_player = self.player[\"pos\"] - enemy[\"pos\"]\n            dist = to_player.length()\n\n            if dist > 0.1:\n                enemy[\"pos\"] = enemy[\"pos\"] + to_player.normalize() * enemy[\"speed\"] * dt\n\n            enemy[\"mesh\"].position = enemy[\"pos\"]\n\n            enemy[\"attack_cooldown\"] -= dt\n            if dist < 30.0 and dist > 0.1 and enemy[\"attack_cooldown\"] <= 0:\n                direction = to_player.normalize()\n                self.spawn_projectile(enemy[\"pos\"] + Vector3(0, 0.8, 0), direction, \"enemy\")\n                enemy[\"attack_cooldown\"] = enemy[\"fire_rate\"]\n\n            if dist < 1.9:\n                damage = 20.0 * dt\n                if self.player[\"armor\"] > 0:\n                    absorbed = min(self.player[\"armor\"], damage * 0.8)\n                    self.player[\"armor\"] -= absorbed\n                    self.player[\"health\"] -= damage * 0.2\n                else:\n                    self.player[\"health\"] -= damage\n                self.player[\"last_damage_time\"] = pygame.time.get_ticks() / 1000.0\n                self.set_message(f\"Taking fire! Health: {int(self.player['health'])}\")\n\n        alive_count = sum(1 for e in self.enemies if e[\"alive\"])\n        if alive_count == 0 and self.enemies_spawned:\n            self.enemies_spawned = False\n            self.player[\"wave\"] += 1\n            self.spawn_wave(self.player[\"wave\"])\n            self.spawn_pickup(\"armor\", 0, -5)\n            self.spawn_pickup(\"ammo\", 5, 0)\n\n    def update_projectiles(self, dt):\n        for proj in self.projectiles[:]:\n            proj[\"pos\"] = proj[\"pos\"] + proj[\"velocity\"] * dt\n            proj[\"life\"] -= dt\n\n            if proj[\"team\"] == \"player\":\n                for enemy in self.enemies:\n                    if not enemy[\"alive\"]:\n                        continue\n                    if proj[\"pos\"].distance_to(enemy[\"pos\"]) < 1.2:\n                        enemy[\"health\"] -= proj[\"damage\"]\n                        self.spawn_particle_burst(proj[\"pos\"], (1.0, 0.5, 0.2), 10, 1.5)\n                        if proj in self.projectiles:\n                            self.projectiles.remove(proj)\n                        break\n            else:\n                if proj[\"pos\"].distance_to(self.player[\"pos\"]) < 0.8:\n                    damage = proj[\"damage\"]\n                    if self.player[\"armor\"] > 0:\n                        absorbed = min(self.player[\"armor\"], damage * 0.8)\n                        self.player[\"armor\"] -= absorbed\n                        self.player[\"health\"] -= damage * 0.2\n                    else:\n                        self.player[\"health\"] -= damage\n                    self.player[\"last_damage_time\"] = pygame.time.get_ticks() / 1000.0\n                    self.set_message(\"Direct hit!\")\n                    self.spawn_particle_burst(self.player[\"pos\"], (1.0, 0.3, 0.3), 12, 1.2)\n                    if proj in self.projectiles:\n                        self.projectiles.remove(proj)\n                    break\n\n            if proj[\"life\"] <= 0:\n                if proj in self.projectiles:\n                    self.projectiles.remove(proj)\n\n    def update_pickups(self, dt):\n        for pickup in self.pickups:\n            if pickup[\"collected\"]:\n                continue\n            pickup[\"pos\"].y = 1.3 + math.sin((pygame.time.get_ticks() / 1000.0) + pickup[\"phase\"]) * 0.35\n            pickup[\"mesh\"].position = pickup[\"pos\"]\n            pickup[\"mesh\"].rotation.y += dt * 2.5\n\n            if pickup[\"pos\"].distance_to(self.player[\"pos\"]) < 1.5:\n                kind = pickup[\"kind\"]\n                if kind == \"health\":\n                    self.player[\"health\"] = min(self.player[\"max_health\"], self.player[\"health\"] + 30)\n                    self.set_message(\"Nano-kit recovered +30 HP\")\n                elif kind == \"ammo\":\n                    self.player[\"reserve\"] = min(240, self.player[\"reserve\"] + 40)\n                    self.set_message(\"Ammo cache collected +40\")\n                elif kind == \"armor\":\n                    self.player[\"armor\"] = min(self.player[\"max_armor\"], self.player[\"armor\"] + 35)\n                    self.set_message(\"Armor plating restored +35\")\n                self.spawn_particle_burst(pickup[\"pos\"], (0.2, 1.0, 0.6), 15, 2.0)\n                pickup[\"collected\"] = True\n\n    def update_particles(self, dt):\n        for particle in self.particles[:]:\n            particle[\"pos\"] = particle[\"pos\"] + particle[\"velocity\"] * (60.0 * dt)\n            particle[\"velocity\"] = particle[\"velocity\"] * 0.94\n            particle[\"life\"] -= dt\n            if particle[\"life\"] <= 0:\n                self.particles.remove(particle)\n\n    def update_player_movement(self, dt):\n        speed = 8.5 if self.keys[\"sprint\"] else 6.0\n        move_x = 0.0\n        move_z = 0.0\n\n        forward_x = math.sin(math.radians(self.player[\"yaw\"]))\n        forward_z = math.cos(math.radians(self.player[\"yaw\"]))\n        right_x = math.cos(math.radians(self.player[\"yaw\"]))\n        right_z = -math.sin(math.radians(self.player[\"yaw\"]))\n\n        if self.keys[\"forward\"]:\n            move_x += forward_x\n            move_z += forward_z\n        if self.keys[\"backward\"]:\n            move_x -= forward_x\n            move_z -= forward_z\n        if self.keys[\"left\"]:\n            move_x -= right_x\n            move_z -= right_z\n        if self.keys[\"right\"]:\n            move_x += right_x\n            move_z += right_z\n\n        length = math.hypot(move_x, move_z)\n        if length > 0:\n            move_x /= length\n            move_z /= length\n            self.player[\"pos\"].x += move_x * speed * dt\n            self.player[\"pos\"].z += move_z * speed * dt\n\n        self.player[\"pos\"].x = max(-50, min(50, self.player[\"pos\"].x))\n        self.player[\"pos\"].z = max(-50, min(50, self.player[\"pos\"].z))\n\n        if self.keys[\"jump\"] and self.player[\"grounded\"]:\n            self.player[\"velocity\"].y = 7.0\n            self.player[\"grounded\"] = False\n\n        self.player[\"velocity\"].y -= 18.0 * dt\n        self.player[\"pos\"].y += self.player[\"velocity\"].y * dt\n\n        if self.player[\"pos\"].y <= 1.75:\n            self.player[\"pos\"].y = 1.75\n            self.player[\"velocity\"].y = 0\n            self.player[\"grounded\"] = True\n\n        if self.keys[\"crouch\"]:\n            self.player[\"pos\"].y = 1.4\n\n        if self.player[\"health\"] <= 0:\n            self.game_over = True\n            self.set_message(f\"Mission Failed | Final Score: {self.player['score']}\", 5.0)\n\n    def handle_input(self, dt):\n        for event in pygame.event.get():\n            if event.type == QUIT:\n                return False\n            if event.type == MOUSEMOTION:\n                self.player[\"yaw\"] -= event.rel[0] * 0.25\n                self.player[\"pitch\"] -= event.rel[1] * 0.25\n                self.player[\"pitch\"] = max(-89, min(89, self.player[\"pitch\"]))\n            if event.type == MOUSEBUTTONDOWN and event.button == 1:\n                self.shoot()\n            if event.type == KEYDOWN:\n                if event.key == K_w:\n                    self.keys[\"forward\"] = True\n                elif event.key == K_s:\n                    self.keys[\"backward\"] = True\n                elif event.key == K_a:\n                    self.keys[\"left\"] = True\n                elif event.key == K_d:\n                    self.keys[\"right\"] = True\n                elif event.key == K_LSHIFT:\n                    self.keys[\"sprint\"] = True\n                elif event.key == K_SPACE:\n                    self.keys[\"jump\"] = True\n                elif event.key == K_LCTRL or event.key == K_RCTRL:\n                    self.keys[\"crouch\"] = True\n                elif event.key == K_r:\n                    self.reload()\n                elif event.key == K_ESCAPE:\n                    return False\n            if event.type == KEYUP:\n                if event.key == K_w:\n                    self.keys[\"forward\"] = False\n                elif event.key == K_s:\n                    self.keys[\"backward\"] = False\n                elif event.key == K_a:\n                    self.keys[\"left\"] = False\n                elif event.key == K_d:\n                    self.keys[\"right\"] = False\n                elif event.key == K_LSHIFT:\n                    self.keys[\"sprint\"] = False\n                elif event.key == K_SPACE:\n                    self.keys[\"jump\"] = False\n                elif event.key == K_LCTRL or event.key == K_RCTRL:\n                    self.keys[\"crouch\"] = False\n        return True\n\n    def draw_scene(self):\n        glClearColor(0.02, 0.04, 0.07, 1.0)\n        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)\n\n        glMatrixMode(GL_PROJECTION)\n        glLoadIdentity()\n        gluPerspective(75, DISPLAY_WIDTH / DISPLAY_HEIGHT, 0.1, 250.0)\n\n        glMatrixMode(GL_MODELVIEW)\n        glLoadIdentity()\n        glRotatef(-self.player[\"pitch\"], 1, 0, 0)\n        glRotatef(-self.player[\"yaw\"], 0, 1, 0)\n        glTranslatef(-self.player[\"pos\"].x, -self.player[\"pos\"].y, -self.player[\"pos\"].z)\n\n        self.draw_environment()\n        self.draw_enemies()\n        self.draw_pickups()\n        self.draw_projectiles()\n        self.draw_particles()\n\n    def draw_environment(self):\n        # Floor\n        glColor3f(0.08, 0.12, 0.16)\n        glBegin(GL_QUADS)\n        glVertex3f(-80, 0, -80)\n        glVertex3f(80, 0, -80)\n        glVertex3f(80, 0, 80)\n        glVertex3f(-80, 0, 80)\n        glEnd()\n\n        # Grid\n        glColor4f(0.35, 0.7, 0.95, 0.4)\n        glBegin(GL_LINES)\n        for i in range(-80, 81, 5):\n            glVertex3f(i, 0.01, -80)\n            glVertex3f(i, 0.01, 80)\n            glVertex3f(-80, 0.01, i)\n            glVertex3f(80, 0.01, i)\n        glEnd()\n\n        # Environment blocks\n        for i in range(-40, 41, 12):\n            for j in range(-40, 41, 12):\n                if abs(i) < 2 and abs(j) < 2:\n                    continue\n                box = BoxMesh(3.5, 4.0, 3.5, (0.2, 0.35, 0.45))\n                box.position = Vector3(i, 2.0, j)\n                box.draw()\n\n        # Central tower\n        tower = BoxMesh(8, 15, 8, (0.15, 0.25, 0.35))\n        tower.position = Vector3(0, 7.5, 0)\n        tower.draw()\n\n    def draw_enemies(self):\n        for enemy in self.enemies:\n            if not enemy[\"alive\"]:\n                continue\n            enemy[\"mesh\"].draw()\n\n            # Health bar above head\n            glDisable(GL_LIGHTING)\n            health_ratio = max(0, enemy[\"health\"] / enemy[\"max_health\"])\n            glColor3f(1.0 - health_ratio, health_ratio, 0.0)\n            glBegin(GL_QUADS)\n            x, y, z = enemy[\"pos\"].x, enemy[\"pos\"].y + 1.3, enemy[\"pos\"].z\n            glVertex3f(x - 0.6, y, z)\n            glVertex3f(x - 0.6 + 1.2 * health_ratio, y, z)\n            glVertex3f(x - 0.6 + 1.2 * health_ratio, y + 0.15, z)\n            glVertex3f(x - 0.6, y + 0.15, z)\n            glEnd()\n            glEnable(GL_LIGHTING)\n\n    def draw_pickups(self):\n        for pickup in self.pickups:\n            if not pickup[\"collected\"]:\n                pickup[\"mesh\"].draw()\n\n    def draw_projectiles(self):\n        glDisable(GL_LIGHTING)\n        for proj in self.projectiles:\n            glPointSize(4.0)\n            glColor3f(0.9, 0.8, 0.3) if proj[\"team\"] == \"player\" else glColor3f(1.0, 0.3, 0.3)\n            glBegin(GL_POINTS)\n            glVertex3f(proj[\"pos\"].x, proj[\"pos\"].y, proj[\"pos\"].z)\n            glEnd()\n        glEnable(GL_LIGHTING)\n\n    def draw_particles(self):\n        glDisable(GL_LIGHTING)\n        glPointSize(2.0)\n        glBegin(GL_POINTS)\n        for particle in self.particles:\n            r, g, b = particle[\"color\"]\n            alpha = max(0, particle[\"life\"] / 0.5)\n            glColor4f(r, g, b, alpha)\n            glVertex3f(particle[\"pos\"].x, particle[\"pos\"].y, particle[\"pos\"].z)\n        glEnd()\n        glEnable(GL_LIGHTING)\n\n    def draw_hud(self):\n        glMatrixMode(GL_PROJECTION)\n        glPushMatrix()\n        glLoadIdentity()\n        glOrtho(0, DISPLAY_WIDTH, DISPLAY_HEIGHT, 0, -1, 1)\n        glMatrixMode(GL_MODELVIEW)\n        glPushMatrix()\n        glLoadIdentity()\n\n        glDisable(GL_DEPTH_TEST)\n        glDisable(GL_LIGHTING)\n\n        # Crosshair\n        size = 12\n        center_x, center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2\n        glColor3f(1.0, 1.0, 1.0)\n        glBegin(GL_LINES)\n        glVertex2f(center_x - size, center_y)\n        glVertex2f(center_x + size, center_y)\n        glVertex2f(center_x, center_y - size)\n        glVertex2f(center_x, center_y + size)\n        glEnd()\n\n        glColor4f(0.5, 0.8, 1.0, 0.6)\n        self.draw_2d_circle(center_x, center_y, 6)\n\n        # HUD Stats\n        hud_stats = [\n            f\"Health: {max(0, int(self.player['health']))}/{int(self.player['max_health'])}\",\n            f\"Armor: {max(0, int(self.player['armor']))}/{int(self.player['max_armor'])}\",\n            f\"Ammo: {self.player['ammo']} / {self.player['reserve']}\",\n            f\"Wave: {self.player['wave']} | Kills: {self.player['kills']}\",\n            f\"Score: {self.player['score']}\",\n        ]\n\n        y_pos = 20\n        for stat in hud_stats:\n            text_surf = self.font.render(stat, True, (200, 235, 255))\n            text_data = pygame.image.tostring(text_surf, \"RGBA\", True)\n            glWindowPos2d(20, y_pos)\n            glDrawPixels(text_surf.get_width(), text_surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)\n            y_pos += 32\n\n        # Message\n        if self.message_timer > 0:\n            self.message_timer -= self.clock.get_time() / 1000.0\n            msg_surf = self.large_font.render(self.message, True, (150, 220, 255))\n            msg_data = pygame.image.tostring(msg_surf, \"RGBA\", True)\n            x_pos = (DISPLAY_WIDTH - msg_surf.get_width()) // 2\n            glWindowPos2d(x_pos, DISPLAY_HEIGHT - 100)\n            glDrawPixels(msg_surf.get_width(), msg_surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, msg_data)\n\n        glEnable(GL_DEPTH_TEST)\n        glEnable(GL_LIGHTING)\n\n        glPopMatrix()\n        glMatrixMode(GL_PROJECTION)\n        glPopMatrix()\n        glMatrixMode(GL_MODELVIEW)\n\n    def draw_2d_circle(self, x, y, radius, segments=16):\n        glBegin(GL_LINE_LOOP)\n        for i in range(segments):\n            angle = 2 * math.pi * i / segments\n            px = x + radius * math.cos(angle)\n            py = y + radius * math.sin(angle)\n            glVertex2f(px, py)\n        glEnd()\n\n    def run(self):\n        self.game_started = True\n        self.spawn_wave(1)\n\n        running = True\n        while running:\n            dt = self.clock.tick(FPS) / 1000.0\n            dt = min(dt, 0.033)\n\n            running = self.handle_input(dt)\n\n            if not self.game_over:\n                self.update_player_movement(dt)\n                self.update_reload(dt)\n                self.update_enemy_ai(dt)\n                self.update_projectiles(dt)\n                self.update_pickups(dt)\n                self.update_particles(dt)\n                self.player[\"fire_cooldown\"] = max(0.0, self.player[\"fire_cooldown\"] - dt)\n\n            self.draw_scene()\n            self.draw_hud()\n            pygame.display.flip()\n\n        pygame.quit()\n\n\ndef main():\n    game = Game()\n    game.run()\n\n\nif __name__ == \"__main__\":\n    main()\n