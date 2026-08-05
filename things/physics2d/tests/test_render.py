from physics2d.body import Circle
from physics2d.render import render_frame
from physics2d.vec2 import Vec2
from physics2d.world import World


def test_frame_dimensions():
    world = World(width=50, height=30)
    frame = render_frame(world, 50, 30)
    assert len(frame) == 30
    assert all(len(row) == 50 for row in frame)


def test_empty_world_is_all_background():
    world = World(width=20, height=20)
    frame = render_frame(world, 20, 20, background=(1, 2, 3))
    assert all(pixel == (1, 2, 3) for row in frame for pixel in row)


def test_circle_center_pixel_is_colored():
    world = World(width=40, height=40)
    world.add(Circle(Vec2(20, 20), Vec2(0, 0), radius=10, color=(255, 0, 0)))
    frame = render_frame(world, 40, 40)
    assert frame[20][20] == (255, 0, 0)


def test_circle_corner_pixel_is_background():
    world = World(width=40, height=40)
    world.add(Circle(Vec2(20, 20), Vec2(0, 0), radius=5, color=(255, 0, 0)))
    frame = render_frame(world, 40, 40, background=(9, 9, 9))
    assert frame[0][0] == (9, 9, 9)


def test_two_circles_both_render():
    world = World(width=100, height=50)
    world.add(Circle(Vec2(20, 20), Vec2(0, 0), radius=8, color=(255, 0, 0)))
    world.add(Circle(Vec2(80, 20), Vec2(0, 0), radius=8, color=(0, 0, 255)))
    frame = render_frame(world, 100, 50)
    assert frame[20][20] == (255, 0, 0)
    assert frame[20][80] == (0, 0, 255)
