"""Forward-driving tractor-trailer with pure-pursuit steering, for the narrow-bridge episode.

Road layout (metres): main mountain road runs east-west, centreline z = -45 (truck heads WEST in the
north lane, z = -43.2). A short stub road runs north from it (x = -3.6..3.6) to a one-lane bridge
(inner width 3.6 m, x = -1.8..1.8) from z = 0 to z = 40 over a river. The north-east corner of the
junction is a rock wall (x > 4.0, z > -40.6): the inside of the truck's right turn.
"""
import math

import numpy as np

L1, L2 = 4.0, 12.3
DMAX = 0.62
BRIDGE_Z0, BRIDGE_Z1, BRIDGE_HALF = 0.0, 40.0, 1.8
ROCK_X, ROCK_Z = 3.6, -41.4
FILLET_C, FILLET_R = (13.6, -31.4), 10.0       # rounded (flared) inside corner
LANE_Z = -43.2


def dense(pts, step=0.5):
    out = []
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) / step))
        for k in range(n):
            u = k / n
            out.append((x0 + (x1 - x0) * u, z0 + (z1 - z0) * u))
    out.append(pts[-1])
    return np.array(out)


def arc(cx, cz, r, a0, a1, n=40):
    return [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


# pro: drive past the corner, swing wide, turn sharply, line up dead straight long before the bridge
PRO = dense([(160, LANE_Z), (9, LANE_Z)] + arc(9, LANE_Z + 13.0, 13.0, -90, -180, 30)[1:] + [(-4.0, -24), (-0.2, -8), (0, 0), (0, 160)])
# beginner: turns in right at the corner
NOOB = dense([(160, LANE_Z), (13, LANE_Z)] + arc(13, LANE_Z + 13.0, 13.0, -90, -180, 30)[1:] + [(0, -26), (0, 0), (0, 160)])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def simulate(path, speed, x0=150.0, dur=48.0, dt=1 / 120):
    """Tractor rear axle starts on the path at x=x0 heading west."""
    x, z, h1, h2 = x0, LANE_Z, -math.pi / 2, -math.pi / 2
    d = 0.0
    idx = 0
    log = []
    t = 0.0
    while t < dur:
        v = speed(t)
        Ld = max(5.0, 0.9 * v + 4.5)
        # closest path index (search forward only)
        j1 = min(len(path) - 1, idx + 200)
        dd = np.hypot(path[idx:j1, 0] - x, path[idx:j1, 1] - z)
        idx = idx + int(np.argmin(dd))
        k = idx
        while k < len(path) - 1 and math.hypot(path[k, 0] - x, path[k, 1] - z) < Ld:
            k += 1
        tx, tz = path[k]
        alpha = wrap(math.atan2(tx - x, tz - z) - h1)
        d_cmd = math.atan(2 * L1 * math.sin(alpha) / Ld)
        d_cmd = max(-DMAX, min(DMAX, d_cmd))
        d += max(-0.9 * dt, min(0.9 * dt, d_cmd - d))
        log.append((t, x, z, h1, h2, v, d))
        x += v * math.sin(h1) * dt
        z += v * math.cos(h1) * dt
        h1 += v / L1 * math.tan(d) * dt
        h2 += v / L2 * math.sin(h1 - h2) * dt
        t += dt
    return np.array(log)


def corners_trailer(x, z, h2):
    out = []
    for lx, lz in ((-1.3, 0.9), (1.3, 0.9), (1.3, -15.3), (-1.3, -15.3), (1.3, -7.0), (-1.3, -7.0)):
        out.append((x + lx * math.cos(h2) + lz * math.sin(h2), z - lx * math.sin(h2) + lz * math.cos(h2)))
    return out


def corners_tractor(x, z, h1):
    out = []
    for lx, lz in ((-1.3, -1.6), (1.3, -1.6), (1.3, 6.3), (-1.3, 6.3)):
        out.append((x + lx * math.cos(h1) + lz * math.sin(h1), z - lx * math.sin(h1) + lz * math.cos(h1)))
    return out


def in_rock(x, z):
    return x > ROCK_X and ROCK_Z < z < BRIDGE_Z0 and math.hypot(x - FILLET_C[0], z - FILLET_C[1]) > FILLET_R and \
        not (x < FILLET_C[0] and z < FILLET_C[1])


def make_path(x_turn, R, swing, x_end=0.0, lu=20.0):
    """Drive west, drift 'swing' m toward the far side, turn right with radius R, then line up on x_end."""
    pts = [(160, LANE_Z), (x_turn + 14, LANE_Z), (x_turn + 2, LANE_Z - swing)]
    cz = LANE_Z - swing + R
    pts += arc(x_turn, cz, R, -90, -180, 40)[1:]
    xa = x_turn - R
    pts += [(xa, cz + 2), ((xa + x_end) / 2, cz + lu / 2), (x_end, cz + lu), (x_end, 0), (x_end, 160)]
    return dense(pts)


def check(log):
    """Returns (rock_hit, min_bridge_clearance_left, right, south_edge_min_z)."""
    rock = False
    cl, cr = 9.0, 9.0
    zmin = 0.0
    for t, x, z, h1, h2, v, d in log[::4]:
        pts = corners_trailer(x, z, h2) + corners_tractor(x, z, h1)
        for cx, cz in pts:
            if in_rock(cx, cz):
                rock = True
            if BRIDGE_Z0 - 0.5 < cz < BRIDGE_Z1 + 0.5:
                cl = min(cl, cx + BRIDGE_HALF)
                cr = min(cr, BRIDGE_HALF - cx)
            zmin = min(zmin, cz)
    return rock, cl, cr, zmin
