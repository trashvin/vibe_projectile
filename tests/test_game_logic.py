import math

from src import constants
from src.entities import City, Projectile, Tank, solve_launch_parameters


def test_projectile_trajectory():
    tank = Tank()
    proj = Projectile.create_from_tank(tank, angle_deg=45)
    assert proj.vx > 0
    assert proj.vy > 0

    initial_y = proj.y
    proj.update(0.1)
    assert proj.y > initial_y

    # simulate enough time to reach ground
    while proj.alive:
        proj.update(0.05)
    assert proj.y >= 0


def test_launch_parameters_reach_laser_cannon_height():
    tank = Tank()
    city = City.create()
    origin_x = tank.x + tank.width
    origin_y = tank.y + tank.height
    angle_deg, speed = solve_launch_parameters(origin_x, origin_y, city.laser_cannon_x, city.laser_cannon_y)

    assert 10 <= angle_deg <= 60
    assert speed >= constants.PROJECTILE_SPEED

    angle_rad = math.radians(angle_deg)
    dx = city.laser_cannon_x - origin_x
    travel_time = dx / (math.cos(angle_rad) * speed)
    impact_y = origin_y + math.sin(angle_rad) * speed * travel_time - 0.5 * constants.GRAVITY * travel_time * travel_time

    assert abs(impact_y - city.laser_cannon_y) < 12
