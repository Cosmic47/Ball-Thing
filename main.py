import pygame
import sys
import random

scr_w, scr_h = 1280, 720
center_pos = pygame.Vector2(scr_w / 2, scr_h / 2)
fps = 60

gravity = 400
time_speed = 1


# TODO:
# -check for sussy cases
# -rewrite intersection check (for fast moving ball case)

class Camera:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.speed = 0.1

    def follow(self, target):
        self.pos -= (self.pos - target) * self.speed

    def get_view_shift(self):
        return -self.pos + center_pos

    def get_screen_borders(self):
        return int(self.pos.x - center_pos.x), int(self.pos.x + center_pos.x)


class Ball:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.radius = 18
        self.jump_dir = pygame.Vector2(0, 0)
        self.rocket_timer = 0

    def draw(self, surf, camera):
        pygame.draw.circle(surf, (255, 0, 0), self.pos + camera.get_view_shift(), self.radius)

    def update(self, lines_arr, particles_arr, dt):
        self.vel += pygame.Vector2(0, gravity) * dt
        self.pos += self.vel * dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] and self.vel.x <= 500:
            self.vel.x += 300 * dt
        elif keys[pygame.K_LEFT] and self.vel.x >= -500:
            self.vel.x -= 300 * dt
        if keys[pygame.K_UP] and self.jump_dir.length_squared() > 0:
            # self.vel.y -= 300 * dt
            self.vel += self.jump_dir.normalize() * 20000 * dt
        if keys[pygame.K_DOWN] and self.vel.y <= 1500:
            self.vel.y += 500 * dt
        if keys[pygame.K_z]:
            self.vel.y = (-gravity) * dt - 100
            for i in range(10):
                vel = pygame.Vector2(0, 100).rotate(random.uniform(-20, 20))
                pos1 = self.pos - pygame.Vector2(self.radius, 0)
                pos2 = self.pos + pygame.Vector2(self.radius, 0)
                particles_arr.append(Particle(pos1, vel))
                particles_arr.append(Particle(pos2, vel))

        total_corr = pygame.Vector2(0, 0)
        for line in lines_arr:
            total_corr += self.get_correction(line, particles_arr)
        self.pos += total_corr
        self.jump_dir = total_corr
        # print(self.jump_dir)
        """
        for line in lines_arr:
            self.pos += self.get_correction(line, particles_arr)
        """

    def get_correction(self, line_obj, particles_arr):
        proj = line_obj.project(self.pos)
        dist = proj.distance_to(self.pos)
        collided = self.radius > dist

        if collided:
            # print("collided: ", line_obj.start, line_obj.end, self.radius, dist)
            # print(proj)
            corr = (self.pos - proj).normalize()
            v = line_obj.end - line_obj.start
            parall_vel = (line_obj.end - line_obj.start).normalize()
            parall_vel *= self.vel.dot(parall_vel) * line_obj.friction
            # perpen_vel = (self.pos - proj).normalize()
            perpen_vel = v.rotate(-90).normalize()
            perpen_vel *= abs(self.vel.dot(perpen_vel)) * line_obj.bounciness
            self.vel = parall_vel + perpen_vel
            # print(parall_vel, perpen_vel)

            if perpen_vel.length() > 100:
                intensity = int(perpen_vel.length() / 100)
                for i in range(intensity):
                    part_vel_parall = v.normalize() * random.randint(-200, 200)
                    part_vel_perpen = pygame.Vector2(-part_vel_parall.y, part_vel_parall.x) * random.uniform(-0.5, 0.5)
                    particles_arr.append(Particle(proj, part_vel_parall + part_vel_perpen))
                pygame.mixer.music.play()
            return (self.radius - dist) * corr
        else:
            return pygame.Vector2(0, 0)


class Line:
    def __init__(self, pos1, pos2, friction, bounciness):
        self.start = pygame.Vector2(*pos1)
        self.end = pygame.Vector2(*pos2)
        self.friction = friction
        self.bounciness = bounciness

        if self.end.x == self.start.x:
            self.end.x += 1e-3

        self.slope = (self.end.y - self.start.y) / (self.end.x - self.start.x)
        self.shift = self.start.y - self.slope * self.start.x

    def draw(self, surf, camera):
        view_shift = camera.get_view_shift()
        pygame.draw.line(surf, (128, 128, 128), self.start + view_shift, self.end + view_shift, 3)

    def update_params(self):
        self.slope = (self.end.y - self.start.y) / (self.end.x - self.start.x - 1e-9)
        self.shift = self.end.y - self.slope * self.end.x

    def project(self, point):
        a, b = self.slope, self.shift
        raw_px = (a * (point.y - b) + point.x) / (a * a + 1)
        px = min(max(raw_px, self.start.x), self.end.x)
        proj = pygame.Vector2(px, a * px + b)
        return proj


class Particle:
    friction = 0.9
    time_limit = 0.4

    def __init__(self, pos, vel):
        self.pos = pos.copy()
        self.vel = vel.copy()
        self.timer = 0

    def draw(self, surf, camera):
        color = (200 * (self.time_limit * 2 - self.timer) / (2 * self.time_limit), 0, 0)
        view_shift = camera.get_view_shift()
        pygame.draw.rect(surf, color, (self.pos.x - 1 + view_shift.x, self.pos.y - 1 + view_shift.y, 3, 3))

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= self.friction

        self.timer += dt
        return self.timer > self.time_limit


def main():
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load("boing.mp3")
    scr = pygame.display.set_mode((scr_w, scr_h))
    clk = pygame.time.Clock()
    dt = 1 / fps

    ball = Ball(200, 300)
    # f = lambda x: math.sin(x/100) * 100 + 360
    """
    f = lambda x: random.randint(260, 460)
    dx = 100
    points = [random.randint(260, 460) for i in range(1280//(dx+1)+2)]
    lines = [Line((i * (dx + 1), points[i]), (i*(dx+1)+dx, points[i+1]), 0.99, 0) for i in range(1280//(dx+1)+1)]
    """
    """
    lines = [
        Line((100, 500), (300, 500), 0.99, 0.3),
        Line((100, 720), (100, 501), 0.99, 0.3),
        Line((300, 501), (300, 720), 0.99, 0.3),

        Line((150, 400), (250, 400), 0.99, 0.3),
        Line((150, 500), (150, 401), 0.99, 0.3),
        Line((250, 401), (250, 500), 0.99, 0.3),

        Line((550, 300), (750, 300), 0.99, 0.3),
        Line((550, 720), (550, 301), 0.99, 0.3),
        Line((750, 301), (750, 720), 0.99, 0.3),

        Line((900, 400), (1100, 250), 0.99, 0.3),
        Line((900, 720), (900, 401), 0.99, 0.3),
        Line((1100, 251), (1100, 720), 0.99, 0.3),
    ]
    """
    dx = 100
    border_start, border_end = -800, 800
    points = {x: random.randint(600, 800) for x in range(border_start, border_end + 1, dx)}
    particles = []
    camera = Camera()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        left, right = camera.get_screen_borders()
        left, right = int(left // dx * dx), int(right // dx * dx)
        lines = [Line((x+1, points[x]), (x + dx - 1, points[x+dx]), 0.999, 0.5) for x in range(left, right+1, dx)]
        if right + 2 * dx > border_end:
            points[border_end + dx] = points[border_end] + random.randint(-200, 200) * (right / 10000) ** 0.7
            border_end += dx
        if left - dx < border_start:
            points[border_start - dx] = points[border_start] - 200/(left + 800.001)
            border_start -= dx

        ball.update(lines, particles, dt)
        if ball.pos.y > points[ball.pos.x // dx * dx] + 2000:
            ball.pos.y -= 10000
        new_particles = []
        for idx, particle in enumerate(particles):
            if not particle.update(dt):
                new_particles.append(particle)
        particles = new_particles

        scr.fill((0, 0, 0))
        ball.draw(scr, camera)
        for line in lines:
            line.draw(scr, camera)
        for particle in particles:
            particle.draw(scr, camera)
        pygame.display.update()
        camera.follow(ball.pos)
        dt = clk.tick(fps) * 0.001 * time_speed


main()
