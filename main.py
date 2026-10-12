import math
import random

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

    def __truediv__(self, scalar):
        if scalar == 0:
            return Vector3()
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        length = self.length()
        if length < 1e-6:
            return Vector3()
        return Vector3(self.x / length, self.y / length, self.z / length)

    def distance_to(self, other):
        return (self - other).length()

    def copy(self):
        return Vector3(self.x, self.y, self.z)


class Weapon:
    def __init__(self, name, damage, mag_size, reserve, fire_rate, recoil, spread):
        self.name = name
        self.damage = damage
        self.mag_size = mag_size
        self.ammo_in_mag = mag_size
        self.reserve = reserve
        self.fire_rate = fire_rate
        self.recoil = recoil
        self.spread = spread
        self.cooldown = 0.0

    def reload(self, player):
        if self.ammo_in_mag >= self.mag_size or player['reserve'] <= 0:
            return
        needed = self.mag_size - self.ammo_in_mag
        loaded = min(needed, player['reserve'])
        self.ammo_in_mag += loaded
        player['reserve'] -= loaded


class BoxMesh:
    def __init__(self, width, height, depth, color=(1.0, 1.0, 1.0)):
        self.width = width
        self.height = height
        self.depth = depth
        self.color = color
        self.position = Vector3()
        self.rotation = Vector3()

    def draw(self):
        w = self.width / 2.0
        h = self.height / 2.0
        d = self.depth / 2.0
        vertices = [
            (-w, -h, d), (w, -h, d), (w, h, d), (-w, h, d),
            (-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d)
        ]
        faces = [
            (0, 1, 2, 3), (5, 4, 7, 6),
            (4, 0, 3, 7), (1, 5, 6, 2),
            (3, 2, 6, 7), (4, 5, 1, 0)
        ]

        glPushMatrix()
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glRotatef(self.rotation.x, 1, 0, 0)
        glRotatef(self.rotation.y, 0, 1, 0)
        glRotatef(self.rotation.z, 0, 0, 1)
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        for face in faces:
            for idx in face:
                x, y, z = vertices[idx]
                glVertex3f(x, y, z)
        glEnd()
        glPopMatrix()


class Enemy:
    def __init__(self, x, z, difficulty):
        self.position = Vector3(x, 1.0, z)
        self.mesh = BoxMesh(1.3, 1.8, 0.8, color=(0.85, 0.2, 0.25))
        self.mesh.position = self.position
        self.health = 100.0 * difficulty
        self.max_health = self.health
        self.speed = 1.7 + random.random() * 1.0 + difficulty * 0.25
        self.attack_cooldown = random.random() * 1.4
        self.alive = True

    def draw(self):
        if not self.alive:
            return
        self.mesh.draw()

        # To keep the code light, the head is drawn as a simple block.
        glPushMatrix()
        glTranslatef(self.position.x, self.position.y + 1.1, self.position.z)
        glColor3f(0.87, 0.78, 0.7)
        glBegin(GL_QUADS)
        s = 0.35
        vertices = [
            (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),
            (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s)
        ]
        faces = [
            (0, 1, 2, 3), (5, 4, 7, 6),
            (4, 0, 3, 7), (1, 5, 6, 2),
            (3, 2, 6, 7), (4, 5, 1, 0)
        ]
        for face in faces:
            for idx in face:
                x, y, z = vertices[idx]
                glVertex3f(x, y, z)
        glEnd()
        glPopMatrix()


class Projectile:
    def __init__(self, pos, velocity, team='enemy', damage=25.0):
        self.pos = pos.copy()
        self.velocity = velocity
        self.team = team
        self.damage = damage
        self.life = 4.0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glColor3f(1.0, 0.3, 0.3) if self.team == 'enemy' else glColor3f(1.0, 0.85, 0.3)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        glPopMatrix()


class Pickup:
    def __init__(self, kind, x, z):
        self.kind = kind
        self.pos = Vector3(x, 1.3, z)
        self.collected = False
        self.phase = random.random() * math.tau
        self.color = {
            'health': (0.25, 1.0, 0.52),
            'ammo': (1.0, 0.8, 0.2),
            'armor': (0.35, 0.7, 1.0),
        }[kind]

    def draw(self):
        if self.collected:
            return
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glRotatef((pygame.time.get_ticks() * 0.08) % 360, 0, 1, 0)
        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        s = 0.55
        vertices = [
            (0, s, 0), (s, 0, 0), (0, 0, s),
            (-s, 0, 0), (0, 0, -s), (0, -s, 0)
        ]
        faces = [
            (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
            (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)
        ]
        for face in faces:
            for idx in face:
                x, y, z = vertices[idx]
                glVertex3f(x, y, z)
        glEnd()
        glPopMatrix()


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption('Neon Siege - Advanced FPS')
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_NORMALIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glLightfv(GL_LIGHT0, GL_POSITION, (15.0, 25.0, 10.0, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.30, 0.35, 1.0))

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('consolas', 22, True)
        self.big_font = pygame.font.SysFont('consolas', 30, True)

        self.weapons = [
            Weapon('AR-9', 35, 30, 120, 0.12, 1.5, 0.03),
            Weapon('Pulse Rifle', 48, 18, 72, 0.18, 2.2, 0.05),
            Weapon('Shotgun', 24, 8, 32, 0.75, 3.0, 0.12),
        ]

        self.player = {
            'pos': Vector3(0.0, 1.75, 18.0),
            'yaw': 180.0,
            'pitch': 0.0,
            'health': 100.0,
            'armor': 50.0,
            'reserve': 120,
            'score': 0,
            'wave': 1,
            'kills': 0,
            'weapon_index': 0,
            'recoil': 0.0,
            'grounded': True,
            'velocity': Vector3(),
            'game_over': False,
        }

        self.keys = {
            'forward': False, 'backward': False, 'left': False, 'right': False,
            'jump': False, 'sprint': False, 'crouch': False
        }

        self.enemies = []
        self.projectiles = []
        self.pickups = []
        self.particles = []
        self.message = 'Mission briefing: clear the drone hive'
        self.message_timer = 3.0
        self.spawn_wave(1)

    def set_message(self, text, duration=2.0):
        self.message = text
        self.message_timer = duration

    def spawn_wave(self, wave_num):
        self.enemies.clear()
        count = min(5 + wave_num * 2, 22)
        for i in range(count):
            angle = (i / max(1, count)) * math.tau + random.uniform(-0.5, 0.5)
            radius = random.uniform(16, 42)
            x = math.cos(angle) * radius + random.uniform(-5, 5)
            z = math.sin(angle) * radius + random.uniform(-5, 5)
            self.enemies.append(Enemy(x, z, 1.0 + wave_num * 0.18))
        self.player['wave'] = wave_num
        self.set_message(f'Wave {wave_num}: hostile drones incoming', 2.5)

    def spawn_projectile(self, start_pos, direction, team='enemy', damage=25.0):
        dir_vec = Vector3(direction[0], direction[1], direction[2]).normalize()
        velocity = dir_vec * (32.0 if team == 'enemy' else 40.0)
        self.projectiles.append(Projectile(start_pos.copy(), velocity, team, damage))

    def spawn_pickup(self, kind, x, z):
        self.pickups.append(Pickup(kind, x, z))

    def spawn_particles(self, pos, color, count=12, speed=1.0):
        for _ in range(count):
            angle = random.random() * math.tau
            elevation = random.uniform(0.2, 1.3)
            v = Vector3(
                math.sin(elevation) * math.cos(angle) * speed,
                math.sin(elevation) * math.sin(angle) * speed,
                math.cos(elevation) * speed
            )
            self.particles.append({
                'pos': pos.copy(),
                'vel': v,
                'life': random.uniform(0.2, 0.8),
                'color': color,
            })

    def shoot(self):
        if self.player['game_over']:
            return

        weapon = self.weapons[self.player['weapon_index']]
        if weapon.cooldown > 0:
            return
        if weapon.ammo_in_mag <= 0:
            weapon.reload(self.player)
            return

        weapon.ammo_in_mag -= 1
        weapon.cooldown = weapon.fire_rate

        yaw = math.radians(self.player['yaw'])
        pitch = math.radians(self.player['pitch'])

        spread_x = random.uniform(-weapon.spread, weapon.spread)
        spread_y = random.uniform(-weapon.spread, weapon.spread)

        dx = math.sin(yaw) * math.cos(pitch) + spread_x
        dy = -math.sin(pitch) + spread_y
        dz = math.cos(yaw) * math.cos(pitch)

        direction = (dx, dy, dz)
        self.spawn_projectile(self.player['pos'].copy(), direction, team='player', damage=weapon.damage)
        self.player['recoil'] += weapon.recoil
        self.spawn_particles(self.player['pos'].copy(), (1.0, 0.9, 0.5), count=8, speed=0.8)

        best_target = None
        best_score = -999
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            to_enemy = enemy.position - self.player['pos']
            dist = to_enemy.length()
            if dist < 0.1:
                continue
            dir_to_enemy = to_enemy.normalize()
            aim_dir = Vector3(dx, dy, dz).normalize()
            score = dir_to_enemy.dot(aim_dir)
            if score > 0.94 and dist < 60 and score > best_score:
                best_score = score
                best_target = enemy

        if best_target is not None:
            best_target.health -= weapon.damage
            self.spawn_particles(best_target.position.copy(), (1.0, 0.45, 0.25), count=14, speed=1.4)
            if best_target.health <= 0:
                best_target.alive = False
                self.player['score'] += 100
                self.player['kills'] += 1
                self.set_message('Target eliminated', 1.4)
                if random.random() < 0.35:
                    kind = random.choice(['health', 'ammo', 'armor'])
                    self.spawn_pickup(kind, best_target.position.x, best_target.position.z)

    def reload(self):
        weapon = self.weapons[self.player['weapon_index']]
        if weapon.ammo_in_mag >= weapon.mag_size or self.player['reserve'] <= 0:
            return
        weapon.reload(self.player)
        self.set_message(f'{weapon.name} reloaded', 1.2)

    def update_reload(self, dt):
        pass

    def update_player(self, dt):
        speed = 8.5 if self.keys['sprint'] else 5.8
        if self.keys['crouch']:
            speed *= 0.6

        yaw_rad = math.radians(self.player['yaw'])
        forward_x = math.sin(yaw_rad)
        forward_z = math.cos(yaw_rad)
        right_x = math.cos(yaw_rad)
        right_z = -math.sin(yaw_rad)

        move_x = 0.0
        move_z = 0.0

        if self.keys['forward']:
            move_x += forward_x
            move_z += forward_z
        if self.keys['backward']:
            move_x -= forward_x
            move_z -= forward_z
        if self.keys['left']:
            move_x -= right_x
            move_z -= right_z
        if self.keys['right']:
            move_x += right_x
            move_z += right_z

        length = math.hypot(move_x, move_z)
        if length > 0:
            move_x /= length
            move_z /= length
            self.player['pos'].x += move_x * speed * dt
            self.player['pos'].z += move_z * speed * dt

        self.player['pos'].x = max(-50, min(50, self.player['pos'].x))
        self.player['pos'].z = max(-50, min(50, self.player['pos'].z))

        if self.keys['jump'] and self.player['grounded']:
            self.player['velocity'].y = 6.2
            self.player['grounded'] = False

        self.player['velocity'].y -= 18.0 * dt
        self.player['pos'].y += self.player['velocity'].y * dt
        if self.player['pos'].y <= 1.75:
            self.player['pos'].y = 1.75
            self.player['velocity'].y = 0.0
            self.player['grounded'] = True

        self.player['recoil'] *= 0.83
        self.player['pitch'] -= self.player['recoil'] * 0.08
        self.player['pitch'] = max(-88, min(88, self.player['pitch']))

        if self.player['health'] <= 0:
            self.player['game_over'] = True
            self.set_message(f'Mission failed. Final score: {self.player["score"]}', 999)

    def update_enemies(self, dt):
        remaining_alive = 0
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            remaining_alive += 1
            to_player = self.player['pos'] - enemy.position
            dist = to_player.length()
            if dist > 0.1:
                enemy.position = enemy.position + to_player.normalize() * enemy.speed * dt
                enemy.mesh.position = enemy.position

            enemy.attack_cooldown -= dt
            if dist < 1.8:
                damage = 16.0 * dt
                if self.player['armor'] > 0:
                    absorbed = min(self.player['armor'], damage * 0.85)
                    self.player['armor'] -= absorbed
                    self.player['health'] -= damage * 0.15
                else:
                    self.player['health'] -= damage
                self.set_message(f'Incoming fire! Health {int(self.player["health"])}', 0.4)

            if dist < 30 and enemy.attack_cooldown <= 0:
                shot_dir = (self.player['pos'] - enemy.position).normalize()
                self.spawn_projectile(enemy.position + Vector3(0, 0.7, 0), (shot_dir.x, shot_dir.y, shot_dir.z), team='enemy', damage=18.0)
                enemy.attack_cooldown = 1.5

        if remaining_alive == 0:
            self.spawn_wave(self.player['wave'] + 1)

    def update_projectiles(self, dt):
        for projectile in self.projectiles[:]:
            projectile.pos = projectile.pos + projectile.velocity * dt
            projectile.life -= dt

            # Player projectile collision
            if projectile.team == 'player':
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    if projectile.pos.distance_to(enemy.position) < 1.2:
                        enemy.health -= projectile.damage
                        self.spawn_particles(projectile.pos.copy(), (1.0, 0.5, 0.25), count=16, speed=1.5)
                        self.projectiles.remove(projectile)
                        if enemy.health <= 0:
                            enemy.alive = False
                            self.player['score'] += 100
                            self.player['kills'] += 1
                            self.set_message('Target eliminated', 1.4)
                            if random.random() < 0.35:
                                kind = random.choice(['health', 'ammo', 'armor'])
                                self.spawn_pickup(kind, enemy.position.x, enemy.position.z)
                        break
            else:
                if projectile.pos.distance_to(self.player['pos']) < 1.0:
                    damage = projectile.damage
                    if self.player['armor'] > 0:
                        absorbed = min(self.player['armor'], damage * 0.8)
                        self.player['armor'] -= absorbed
                        self.player['health'] -= damage * 0.2
                    else:
                        self.player['health'] -= damage
                    self.spawn_particles(self.player['pos'].copy(), (1.0, 0.2, 0.2), count=16, speed=1.5)
                    self.projectiles.remove(projectile)
                    self.set_message('Direct hit!', 0.8)
                    break

            if projectile.life <= 0:
                self.projectiles.remove(projectile)

    def update_pickups(self, dt):
        for pickup in self.pickups:
            if pickup.collected:
                continue
            pickup.pos.y = 1.3 + math.sin((pygame.time.get_ticks() / 250.0) + pickup.phase) * 0.25
            if pickup.pos.distance_to(self.player['pos']) < 1.5:
                pickup.collected = True
                if pickup.kind == 'health':
                    self.player['health'] = min(100.0, self.player['health'] + 30)
                    self.set_message('Nano-kit restored', 1.5)
                elif pickup.kind == 'ammo':
                    self.player['reserve'] += 28
                    self.set_message('Ammo cache found', 1.5)
                else:
                    self.player['armor'] = min(100.0, self.player['armor'] + 25)
                    self.set_message('Armor restored', 1.5)
                self.spawn_particles(pickup.pos.copy(), (0.2, 1.0, 0.6), count=18, speed=1.5)

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle['pos'] = particle['pos'] + particle['vel'] * (60.0 * dt)
            particle['vel'] = particle['vel'] * 0.94
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == MOUSEMOTION:
                self.player['yaw'] -= event.rel[0] * 0.22
                self.player['pitch'] -= event.rel[1] * 0.18
                self.player['pitch'] = max(-88, min(88, self.player['pitch']))
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.shoot()
            if event.type == KEYDOWN:
                if event.key == K_w:
                    self.keys['forward'] = True
                elif event.key == K_s:
                    self.keys['backward'] = True
                elif event.key == K_a:
                    self.keys['left'] = True
                elif event.key == K_d:
                    self.keys['right'] = True
                elif event.key == K_LSHIFT:
                    self.keys['sprint'] = True
                elif event.key == K_SPACE:
                    self.keys['jump'] = True
                elif event.key == K_LCTRL:
                    self.keys['crouch'] = True
                elif event.key == K_1:
                    self.player['weapon_index'] = 0
                elif event.key == K_2:
                    self.player['weapon_index'] = 1
                elif event.key == K_3:
                    self.player['weapon_index'] = 2
                elif event.key == K_r:
                    self.reload()
                elif event.key == K_ESCAPE:
                    return False
            if event.type == KEYUP:
                if event.key == K_w:
                    self.keys['forward'] = False
                elif event.key == K_s:
                    self.keys['backward'] = False
                elif event.key == K_a:
                    self.keys['left'] = False
                elif event.key == K_d:
                    self.keys['right'] = False
                elif event.key == K_LSHIFT:
                    self.keys['sprint'] = False
                elif event.key == K_SPACE:
                    self.keys['jump'] = False
                elif event.key == K_LCTRL:
                    self.keys['crouch'] = False
        return True

    def draw_world(self):
        glClearColor(0.03, 0.05, 0.08, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(75.0, DISPLAY_WIDTH / DISPLAY_HEIGHT, 0.1, 300.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(-self.player['pitch'], 1, 0, 0)
        glRotatef(-self.player['yaw'], 0, 1, 0)
        glTranslatef(-self.player['pos'].x, -self.player['pos'].y, -self.player['pos'].z)

        # Floor and grid
        glColor3f(0.13, 0.18, 0.22)
        glBegin(GL_QUADS)
        glVertex3f(-80, 0, -80)
        glVertex3f(80, 0, -80)
        glVertex3f(80, 0, 80)
        glVertex3f(-80, 0, 80)
        glEnd()

        glColor4f(0.3, 0.8, 1.0, 0.35)
        glBegin(GL_LINES)
        for i in range(-80, 81, 5):
            glVertex3f(i, 0.03, -80)
            glVertex3f(i, 0.03, 80)
            glVertex3f(-80, 0.03, i)
            glVertex3f(80, 0.03, i)
        glEnd()

        # Cover blocks
        glColor3f(0.3, 0.45, 0.55)
        for i in range(-35, 36, 12):
            for j in range(-35, 36, 12):
                if abs(i) < 3 and abs(j) < 3:
                    continue
                glPushMatrix()
                glTranslatef(i, 2.0, j)
                glScalef(2.5, 4.0, 2.5)
                glBegin(GL_QUADS)
                for face in [
                    (0, 1, 2, 3), (5, 4, 7, 6),
                    (4, 0, 3, 7), (1, 5, 6, 2),
                    (3, 2, 6, 7), (4, 5, 1, 0)
                ]:
                    for idx in face:
                        x, y, z = {
                            0: (-1, -1, 1), 1: (1, -1, 1), 2: (1, 1, 1), 3: (-1, 1, 1),
                            4: (-1, -1, -1), 5: (1, -1, -1), 6: (1, 1, -1), 7: (-1, 1, -1),
                        }[idx]
                        glVertex3f(x, y, z)
                glEnd()
                glPopMatrix()

        for enemy in self.enemies:
            enemy.draw()

        for pickup in self.pickups:
            pickup.draw()

        glDisable(GL_LIGHTING)
        glPointSize(4.0)
        glBegin(GL_POINTS)
        for projectile in self.projectiles:
            glColor3f(0.9, 0.8, 0.3) if projectile.team == 'player' else glColor3f(1.0, 0.3, 0.3)
            glVertex3f(projectile.pos.x, projectile.pos.y, projectile.pos.z)
        glEnd()
        glEnable(GL_LIGHTING)

        glDisable(GL_LIGHTING)
        glBegin(GL_POINTS)
        for particle in self.particles:
            r, g, b = particle['color']
            glColor4f(r, g, b, max(0.0, particle['life'] / 0.7))
            glVertex3f(particle['pos'].x, particle['pos'].y, particle['pos'].z)
        glEnd()
        glEnable(GL_LIGHTING)

    def draw_hud(self):
        surface = pygame.display.get_surface()
        cx = DISPLAY_WIDTH // 2
        cy = DISPLAY_HEIGHT // 2

        pygame.draw.line(surface, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 2)
        pygame.draw.line(surface, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 2)

        weapon = self.weapons[self.player['weapon_index']]
        stats = [
            f'Health: {int(max(0, self.player["health"]))}',
            f'Armor: {int(max(0, self.player["armor"]))}',
            f'Ammo: {weapon.ammo_in_mag} / {weapon.reserve}',
            f'Wave: {self.player["wave"]}',
            f'Score: {self.player["score"]}',
            f'Weapon: {weapon.name}',
        ]

        y = 20
        for stat in stats:
            text = self.font.render(stat, True, (220, 240, 255))
            surface.blit(text, (20, y))
            y += 28

        if self.message_timer > 0:
            msg = self.big_font.render(self.message, True, (170, 220, 255))
            surface.blit(msg, (DISPLAY_WIDTH // 2 - msg.get_width() // 2, DISPLAY_HEIGHT - 80))

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            running = self.handle_events()

            if not self.player['game_over']:
                self.update_player(dt)
                self.update_enemies(dt)
                self.update_projectiles(dt)
                self.update_pickups(dt)
                self.update_particles(dt)
                for weapon in self.weapons:
                    weapon.cooldown = max(0.0, weapon.cooldown - dt)

            self.message_timer = max(0.0, self.message_timer - dt)
            self.draw_world()
            self.draw_hud()
            pygame.display.flip()

        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
