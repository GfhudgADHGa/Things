# raytracer

A ray tracer written from scratch in Python — no rendering libraries, just
vector math and physics. It supports:

- Spheres and infinite (optionally checkerboard) planes
- Three material types: diffuse (Lambertian), metal (with adjustable
  fuzziness), and dielectric (glass, with real Fresnel-based
  reflect/refract via Schlick's approximation)
- Soft shadows and reflections that fall out naturally from recursive
  path tracing (no special-cased shadow rays)
- Anti-aliasing via multi-sampling per pixel
- Depth of field via a thin-lens camera model
- Multi-process rendering (one worker per CPU core by default)
- A bounding volume hierarchy (BVH) for scenes with many objects — see
  below
- A PNG writer — uses Pillow if installed, otherwise falls back to a
  small hand-rolled PNG encoder built on stdlib `zlib` only

This follows the general approach of Peter Shirley's *Ray Tracing in One
Weekend*, implemented independently in idiomatic Python with a proper test
suite.

## Example renders

`three_spheres` — a diffuse sphere, a hollow glass sphere, and a metal
sphere on a checkered floor:

![three spheres](examples/three_spheres.png)

`random_field` — a field of small randomly-generated spheres around three
feature spheres:

![random field](examples/random_field.png)

## Usage

```bash
pip install -r requirements.txt

# quick preview
python3 main.py --scene three_spheres --width 300 --samples 10 --output preview.png

# higher quality
python3 main.py --scene random_field --width 800 --samples 200 --depth 20 --output render.png
```

Options (`python3 main.py --help`):

| Flag | Meaning |
|---|---|
| `--scene` | `three_spheres` or `random_field` |
| `--width` / `--height` | image size in pixels (`--height` defaults from aspect ratio) |
| `--samples` | samples per pixel (higher = less noise, slower) |
| `--depth` | max ray bounce depth |
| `--seed` | RNG seed, for reproducible renders |
| `--workers` | number of parallel processes (default: one per CPU) |
| `--output` | output PNG path |

## Architecture

```
raytracer/
  vec3.py        Vec3: vector/color math, reflection, refraction, sampling helpers
  ray.py         Ray: origin + direction
  camera.py      Camera: thin-lens camera producing rays for (u, v) viewport coords
  aabb.py         AABB: axis-aligned bounding box (slab-method ray intersection)
  bvh.py           BVHNode: binary tree over bounded objects for fast ray culling
  hittable.py    Sphere, Plane, HittableList: ray-object intersection
  materials.py   Lambertian, Metal, Dielectric: how surfaces scatter light
  render.py      ray_color() recursive path tracing + parallel render()
  png_writer.py  PNG output (Pillow or pure-stdlib fallback)
  scenes.py      example scene setups
```

`ray_color()` is the core recursive loop: cast a ray, find the closest hit,
ask its material how the ray scatters, and recurse — attenuating color at
each bounce — until it escapes to the sky or hits the depth limit.

### Bounding volume hierarchy

`random_field` has ~100+ spheres. Testing every ray against every sphere
(`HittableList`'s default behavior) means cost grows linearly with object
count, on top of the sampling and bounce-depth multipliers — this scene
originally took over an hour to render at moderate quality. `BVHNode`
recursively partitions objects into a binary tree of bounding boxes: pick
a random axis, sort objects along it, split into two halves, recurse. At
render time, a ray that misses a node's box skips its entire subtree
without testing any of the objects inside it. On a 150-sphere scene this
cuts total ray-intersection time by roughly **5x** (measured with
`HittableList` vs. `BVHNode` over 20,000 random rays); on `random_field`
the win is larger still since most camera rays miss most of the sphere
field entirely. The ground plane is infinite and can't have a bounding
box, so it stays outside the BVH and is still tested directly per ray.

Correctness is checked the same way as the acceleration structure's own
literature suggests: cross-check the BVH against the brute-force
`HittableList` over hundreds of random rays and require identical hit
results (same hit/miss, same `t`, same point) — see
`tests/test_bvh.py::test_bvh_matches_brute_force_hittable_list_on_random_rays`.

## Tests

```bash
python3 -m pytest
```

52 tests cover vector math, ray/object intersection (including edge cases
like rays starting inside a sphere, or missing entirely), camera ray
generation, material scattering behavior, end-to-end rendering
(dimensions, determinism given a seed, PNG round-tripping through both
writer paths), AABB ray intersection, and BVH construction/correctness
(including the brute-force cross-check above).

## Possible expansions

- Triangle meshes + OBJ loading
- Textures (image-mapped, procedural noise)
- Area lights / importance sampling for faster convergence
- Motion blur
- A surface-area-heuristic (SAH) BVH split instead of the current random-axis
  median split, for an even better tree on non-uniform scenes
