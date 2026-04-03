import pytest
from src import entities


def test_city_has_ten_buildings():
    city = entities.City.create()
    assert len(city.buildings) == 10


def test_dome_radius_px():
    dome = entities.Dome(center_x=0, center_y=0, radius_m=50000)
    assert dome.radius_px == 50.0


def test_projectile_update_stops_at_ground():
    tank = entities.Tank()
    proj = entities.Projectile.create_from_tank(tank, angle_deg=45)
    for _ in range(100):
        proj.update(0.02)
    assert proj.y >= entities.constants.GROUND_HEIGHT
    assert not proj.alive or proj.y == entities.constants.GROUND_HEIGHT + proj.radius
