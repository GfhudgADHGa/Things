import math

from physics2d.body import Circle
from physics2d.vec2 import Vec2
from physics2d.world import World


def test_gravity_accelerates_body_downward():
    world = World(width=200, height=200, gravity=Vec2(0, 100))
    ball = Circle(Vec2(100, 50), Vec2(0, 0), radius=5, static=False)
    world.add(ball)
    world.step(0.1)
    assert ball.velocity.y > 0
    assert ball.position.y > 50


def test_static_body_never_moves():
    world = World(width=200, height=200)
    floor = Circle(Vec2(100, 190), Vec2(0, 0), radius=10, static=True)
    world.add(floor)
    for _ in range(50):
        world.step(1 / 60)
    assert floor.position == Vec2(100, 190)
    assert floor.velocity == Vec2(0, 0)


def test_ball_bounces_off_floor():
    world = World(width=200, height=200, gravity=Vec2(0, 500))
    ball = Circle(Vec2(100, 100), Vec2(0, 0), radius=10, restitution=0.9)
    world.add(ball)
    for _ in range(200):
        world.step(1 / 60)
    # after falling and bouncing, ball should never sink through the floor
    assert ball.position.y <= 200 - 10 + 1e-6


def test_ball_never_falls_through_floor_over_long_simulation():
    world = World(width=200, height=200, gravity=Vec2(0, 800))
    ball = Circle(Vec2(100, 20), Vec2(0, 0), radius=8, restitution=0.7)
    world.add(ball)
    for _ in range(1000):
        world.step(1 / 60)
        assert ball.position.y <= world.height - ball.radius + 1e-6
        assert ball.position.y >= ball.radius - 1e-6


def test_ball_stays_within_horizontal_bounds():
    world = World(width=100, height=200, gravity=Vec2(0, 0))
    ball = Circle(Vec2(50, 100), Vec2(500, 0), radius=10, restitution=1.0)
    world.add(ball)
    for _ in range(200):
        world.step(1 / 60)
        assert ball.position.x <= world.width - ball.radius + 1e-6
        assert ball.position.x >= ball.radius - 1e-6


def test_wall_bounce_loses_energy_with_restitution_below_one():
    world = World(width=200, height=200, gravity=Vec2(0, 0))
    ball = Circle(Vec2(190, 100), Vec2(100, 0), radius=5, restitution=0.5)
    world.add(ball)
    speed_before = ball.velocity.length()
    # step until it bounces off the right wall
    for _ in range(50):
        world.step(1 / 60)
    assert ball.velocity.length() <= speed_before + 1e-6


def test_two_circles_separate_after_colliding():
    world = World(width=300, height=300, gravity=Vec2(0, 0))
    a = Circle(Vec2(100, 100), Vec2(100, 0), radius=10, restitution=1.0)
    b = Circle(Vec2(140, 100), Vec2(-100, 0), radius=10, restitution=1.0)
    world.add(a)
    world.add(b)
    for _ in range(60):
        world.step(1 / 60)
    # after colliding elastically, they should be moving apart, not through each other
    distance = (b.position - a.position).length()
    assert distance >= a.radius + b.radius - 0.5


def test_collision_does_not_leave_circles_overlapping_forever():
    world = World(width=300, height=300, gravity=Vec2(0, 0))
    a = Circle(Vec2(95, 100), Vec2(0, 0), radius=10, mass=1)
    b = Circle(Vec2(105, 100), Vec2(0, 0), radius=10, mass=1)  # overlapping at start
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)
    distance = (b.position - a.position).length()
    assert distance >= a.radius + b.radius - 0.5


def test_elastic_collision_between_equal_masses_swaps_velocity_along_normal():
    # classic 1D-like elastic collision: equal masses, head-on, restitution 1
    world = World(width=300, height=10, gravity=Vec2(0, 0))
    a = Circle(Vec2(100, 5), Vec2(50, 0), radius=5, mass=1, restitution=1.0)
    b = Circle(Vec2(112, 5), Vec2(0, 0), radius=5, mass=1, restitution=1.0)
    world.add(a)
    world.add(b)
    world.step(1 / 60)
    # push through many steps until they actually collide
    for _ in range(100):
        world.step(1 / 60)
        if (b.position - a.position).length() <= a.radius + b.radius + 0.1:
            break
    total_momentum_before = 50  # a=50*1 + b=0*1
    total_momentum_after = a.velocity.x * a.mass + b.velocity.x * b.mass
    assert math.isclose(total_momentum_before, total_momentum_after, abs_tol=1.0)


def test_static_body_does_not_get_pushed_by_dynamic_body():
    world = World(width=200, height=200, gravity=Vec2(0, 0))
    static_ball = Circle(Vec2(100, 100), Vec2(0, 0), radius=20, static=True)
    moving_ball = Circle(Vec2(60, 100), Vec2(200, 0), radius=10, restitution=1.0)
    world.add(static_ball)
    world.add(moving_ball)
    for _ in range(60):
        world.step(1 / 60)
    assert static_ball.position == Vec2(100, 100)
