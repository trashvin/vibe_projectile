class Missile:
    def __init__(self, start_x, start_y, target_x, target_y, speed=600):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.alive = True
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.vx = 0
            self.vy = 0
        else:
            self.vx = dx / dist * speed
            self.vy = dy / dist * speed

    def update(self, dt):
        if not self.alive:
            return
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step:
            self.x = self.target_x
            self.y = self.target_y
            self.alive = False
        else:
            self.x += self.vx * dt
            self.y += self.vy * dt

    def draw(self, batch):
        color = (0, 255, 80) if self.alive else (120, 180, 120)
        # Make missile larger and green
        pyglet.shapes.Ellipse(self.x, self.y, 32, 14, color=color).draw()
        # Draw a green line showing the missile's path
        pyglet.shapes.Line(self.x, self.y, self.target_x, self.target_y, color=(0, 200, 80)).draw()
import math
import random
import pyglet
from dataclasses import dataclass

try:
    from src import constants
except ImportError:
    import constants


@dataclass
class Building:
    x: float
    y: float
    width: float
    height: float


class City:
    def __init__(self, buildings, center_x, center_y):
        self.buildings = buildings
        self.center_x = center_x
        self.center_y = center_y
        # Anti-missile launcher must be at ground level, at city center
        self.anti_missile_launcher_x = center_x
        self.anti_missile_launcher_y = constants.GROUND_HEIGHT

    # Remove old _compute_laser_cannon_y, fix indentation for _compute_anti_missile_launcher_y
    def _compute_anti_missile_launcher_y(self):
        mid_x = self.center_x
        supporting_heights = [
            building.y + building.height
            for building in self.buildings
            if building.x <= mid_x <= building.x + building.width
        ]
        top_y = max(supporting_heights, default=constants.GROUND_HEIGHT + 120)
        return top_y + 18

    @classmethod
    def create(cls):
        buildings = []
        spacing = constants.CITY_WIDTH / (constants.CITY_BUILDING_COUNT - 2)
        dome_top_y = constants.GROUND_HEIGHT + (constants.DOME_RADIUS_M / constants.METERS_PER_PIXEL)
        max_building_height = dome_top_y - constants.GROUND_HEIGHT - 1
        for i in range(constants.CITY_BUILDING_COUNT):
            w = random.randint(40, 66)
            h = random.randint(constants.CITY_HEIGHT_MIN, constants.CITY_HEIGHT_MAX)
            # Clamp building height to not exceed dome
            h = min(h, int(max_building_height))
            x = constants.CITY_X + i * spacing * 0.8 + random.uniform(-spacing * 0.2, spacing * 0.2)
            x = max(constants.CITY_X, min(x, constants.CITY_X + constants.CITY_WIDTH - w))
            buildings.append(Building(x=x, y=constants.GROUND_HEIGHT, width=w, height=h))
        center_x = constants.CITY_X + constants.CITY_WIDTH / 2
        center_y = constants.GROUND_HEIGHT
        return cls(buildings=buildings, center_x=center_x, center_y=center_y)

    def draw(self, batch, tank=None, fade=0):
        # fade: 0 = normal, 1 = fully transparent, 0.5 = half faded, etc.
        building_opacity = int(255 * (1.0 - fade))
        roof_opacity = int(255 * (1.0 - fade))
        window_opacity = int(180 * (1.0 - fade))
        for b in self.buildings:
            rect = pyglet.shapes.Rectangle(b.x, b.y, b.width, b.height, color=(108, 136, 224), batch=batch)
            rect.opacity = building_opacity
            rect.draw()
            roof = pyglet.shapes.Rectangle(b.x + 4, b.y + b.height - 10, b.width - 8, 10, color=(178, 82, 66), batch=batch)
            roof.opacity = roof_opacity
            roof.draw()
            for row_y in range(int(b.y + 18), int(b.y + b.height - 20), 24):
                for col_x in range(int(b.x + 10), int(b.x + b.width - 10), 14):
                    window = pyglet.shapes.Rectangle(col_x, row_y, 6, 10, color=(245, 223, 120), batch=batch)
                    window.opacity = window_opacity
                    window.draw()

            cannon_x = self.anti_missile_launcher_x
            cannon_y = self.anti_missile_launcher_y
        base = pyglet.shapes.Rectangle(cannon_x - 14, cannon_y - 18, 28, 14, color=(66, 66, 70), batch=batch)
        base.draw()
        body = pyglet.shapes.Rectangle(cannon_x - 10, cannon_y - 8, 20, 16, color=(200, 50, 50), batch=batch)
        body.draw()

        barrel_len = 40
        if tank is not None:
            dx = tank.x + tank.width * 0.5 - cannon_x
            dy = tank.y + tank.height * 0.5 - cannon_y
            angle = math.atan2(dy, dx)
            end_x = cannon_x + math.cos(angle) * barrel_len
            end_y = cannon_y + math.sin(angle) * barrel_len
            cannon_line = pyglet.shapes.Line(cannon_x, cannon_y, end_x, end_y, color=(255, 0, 0), batch=batch)
            cannon_line.draw()
        else:
            barrel = pyglet.shapes.Rectangle(cannon_x + 7, cannon_y + 3, 24, 6, color=(255, 80, 80), batch=batch)
            barrel.draw()


class Dome:
    def __init__(self, center_x, center_y, radius_m):
        self.center_x = center_x
        self.center_y = center_y
        self.radius_m = radius_m

    @property
    def radius_px(self):
        return self.radius_m / constants.METERS_PER_PIXEL

    def contains(self, x, y):
        return math.hypot(x - self.center_x, y - self.center_y) <= self.radius_px

    def draw(self, batch):
        segment_count = 32
        previous_point = None
        for index in range(segment_count + 1):
            angle = math.pi * index / segment_count
            x = self.center_x + math.cos(angle) * self.radius_px
            y = self.center_y + math.sin(angle) * self.radius_px
            if previous_point is not None:
                line = pyglet.shapes.Line(previous_point[0], previous_point[1], x, y, color=(255, 255, 255), batch=batch)
                line.opacity = 80
                line.draw()
            previous_point = (x, y)


class Tank:
    def __init__(self):
        self.x = constants.TANK_X
        self.y = constants.GROUND_HEIGHT
        self.width = 80
        self.height = 40
        self.barrel_length = 65
        self.angle_deg = 35

    def draw(self, batch):
        track = pyglet.shapes.Rectangle(self.x + 6, self.y - 2, self.width - 12, 14, color=(60, 60, 60), batch=batch)
        track.draw()
        body = pyglet.shapes.Rectangle(self.x, self.y + 10, self.width, self.height - 8, color=(130, 118, 82), batch=batch)
        body.draw()
        glacis = pyglet.shapes.Rectangle(self.x + 12, self.y + self.height - 2, self.width - 24, 10, color=(158, 144, 98), batch=batch)
        glacis.draw()

        turret_radius = 20
        turret = pyglet.shapes.Circle(self.x + self.width * 0.5, self.y + self.height + turret_radius * 0.2, turret_radius, color=(170, 160, 80), batch=batch)
        turret.draw()

        angle_rad = math.radians(self.angle_deg)
        barrel_start_x = self.x + self.width * 0.5
        barrel_start_y = self.y + self.height + turret_radius * 0.2
        barrel_end_x = barrel_start_x + math.cos(angle_rad) * self.barrel_length
        barrel_end_y = barrel_start_y + math.sin(angle_rad) * self.barrel_length

        for offset in (-2, 0, 2):
            barrel = pyglet.shapes.Line(
                barrel_start_x,
                barrel_start_y + offset,
                barrel_end_x,
                barrel_end_y + offset,
                color=(150, 140, 65),
                batch=batch,
            )
            barrel.draw()

        for i in range(3):
            wheel_x = self.x + 15 + i * 20
            wheel = pyglet.shapes.Circle(wheel_x, self.y + 8, 8, color=(80, 80, 80), batch=batch)
            wheel.draw()


def solve_launch_parameters(origin_x, origin_y, target_x, target_y):
    dx = target_x - origin_x
    dy = target_y - origin_y
    if dx <= 0:
        return 45.0, constants.PROJECTILE_SPEED

    best_angle = 45.0
    best_speed = None
    for angle_tenths in range(100, 601, 5):
        angle_deg = angle_tenths / 10.0
        angle_rad = math.radians(angle_deg)
        denom = dx * math.tan(angle_rad) - dy
        if denom <= 0:
            continue
        speed = math.sqrt((constants.GRAVITY * dx * dx) / (2 * (math.cos(angle_rad) ** 2) * denom))
        if best_speed is None or speed < best_speed:
            best_angle = angle_deg
            best_speed = speed

    if best_speed is None:
        return 60.0, constants.PROJECTILE_SPEED * 1.75

    return best_angle, max(best_speed, constants.PROJECTILE_SPEED)


class Projectile:
    def __init__(self, x, y, vx, vy, radius=constants.PROJECTILE_RADIUS):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.alive = True

    @classmethod
    def create_from_tank(cls, tank, angle_deg=45, speed=constants.PROJECTILE_SPEED):
        angle = math.radians(angle_deg)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        x = tank.x + tank.width + 2
        y = tank.y + tank.height
        return cls(x=x, y=y, vx=vx, vy=vy)

    def update(self, dt):
        if not self.alive:
            print(f"[DEBUG] Projectile.update: Not alive, skipping. y={self.y}")
            return
        self.vy -= constants.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        print(f"[DEBUG] Projectile.update: y={self.y:.2f}, ground={constants.GROUND_HEIGHT:.2f}, alive={self.alive}")
        # Do NOT clamp or kill projectile here; let main.py handle ground collision and explosion
        # This ensures the city explosion/game over logic is always hit

    def hits_dome(self, dome):
        return dome.contains(self.x, self.y)

    def draw(self, batch):
        color = (255, 25, 25) if self.alive else (255, 180, 180)
        circle = pyglet.shapes.Circle(self.x, self.y, self.radius, color=color, batch=batch)
        circle.draw()
