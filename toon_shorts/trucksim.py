"""Tractor-trailer kinematics for a 90-degree 'alley dock' back-in.

State: tractor rear axle (= fifth wheel / kingpin) (x, z), tractor heading h1, trailer heading h2.
heading h: forward = (sin h, cos h).  h1' = v/L1 tan(delta) ; h2' = v/L2 sin(h1 - h2).
Trailer axle = kingpin - L2*(sin h2, cos h2). The dock wall is z = DOCK_Z, door centre x = 0,
backed-in trailer heading = pi (front pointing south, rear at the wall).
"""
import math

import numpy as np

L1, L2 = 4.0, 12.3
REAR_OH = 3.0                      # trailer rear overhang behind its axles
DOCK_Z = 40.0
AXLE_DOCKED = DOCK_Z - REAR_OH - 0.15
DMAX = 0.6
DT = 1 / 120


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def simulate(p, log_extra=False):
    x, z, h1, h2 = p.get('x0', -30.0), p.get('z0', 14.0), math.pi / 2, math.pi / 2
    t = 0.0
    out = []

    def rec(v, d, phase):
        out.append((t, x, z, h1, h2, v, d, phase))

    def step(v, d):
        nonlocal x, z, h1, h2, t
        x += v * math.sin(h1) * DT
        z += v * math.cos(h1) * DT
        h1 += v / L1 * math.tan(d) * DT
        h2 += v / L2 * math.sin(h1 - h2) * DT
        t += DT

    def ramp(v_target, a=2.0):
        return v_target

    # 1) drive east past the dock
    v = 0.0
    while x < p['x_turn']:
        v = min(p.get('v_fwd', 5.0), v + 3.0 * DT)
        rec(v, 0, 'fwd'); step(v, 0)
    # 2) swing the tractor away from the dock (right turn), then straighten
    tt = 0.0
    while tt < p['t_swing']:
        d = min(DMAX, tt / 0.6 * DMAX)
        rec(v, d, 'swing'); step(v, d); tt += DT
    tt = 0.0
    while tt < p['t_straight']:
        d = max(0.0, DMAX * (1 - tt / 0.6))
        v2 = max(0.0, v * (1 - tt / p['t_straight']))
        rec(v2, d, 'swing2'); step(v2, d); tt += DT
    # 3) stopped: flashers, mirrors (pause)
    tt = 0.0
    while tt < p['t_pause']:
        rec(0, 0, 'pause'); step(0, 0); tt += DT
    # 4) reverse with a trailer-path controller (pure pursuit on the trailer axle)
    d = 0.0
    goal_done = False
    k = 0
    while k < 120 * 80:
        k += 1
        ax, az = x - L2 * math.sin(h2), z - L2 * math.cos(h2)
        if az >= AXLE_DOCKED - 0.02:
            break
        if not goal_done and az >= p['goal_z']:
            tt = 0.0
            while tt < p['t_goal']:
                rec(0, d, 'goal'); step(0, d); tt += DT
            goal_done = True
        remain = AXLE_DOCKED - az
        vr = -min(p['v_rev'], 0.5 + 0.6 * remain)
        Ld = p['look']
        px, pz = 0.0, min(az + Ld, AXLE_DOCKED + 2)
        move_dir = math.atan2(px - ax, pz - az)          # direction the trailer axle should move
        h2_des = wrap(move_dir + math.pi)               # trailer faces the opposite way
        e = wrap(h2_des - h2)
        phi_des = max(-0.9, min(0.9, -p['k1'] * e * L2 / max(abs(vr), 0.3) * 0.5))
        if remain < p.get('settle', 6.0):
            phi_des *= remain / p.get('settle', 6.0)
        phi = wrap(h1 - h2)
        rhs = p['k2'] * (phi_des - phi) + vr / L2 * math.sin(phi)
        tan_d = rhs * L1 / vr
        d_cmd = max(-DMAX, min(DMAX, math.atan(tan_d)))
        d += max(-1.2 * DT, min(1.2 * DT, d_cmd - d))    # limited steering rate
        rec(vr, d, 'rev'); step(vr, d)
    tt = 0.0
    while tt < 6:
        rec(0, 0, 'done'); step(0, 0); tt += DT
    return out


def evaluate(log):
    t, x, z, h1, h2, v, d, ph = log[-1]
    ax, az = x - L2 * math.sin(h2), z - L2 * math.cos(h2)
    return dict(ax=ax, az=az, h2=math.degrees(wrap(h2 - math.pi)), phi=math.degrees(wrap(h1 - h2)), t=t)


if __name__ == '__main__':
    import itertools
    best = None
    for x_turn, t_swing, t_straight, look, k1, k2 in itertools.product(
            (6, 10, 14), (2.0, 3.0, 4.0), (1.5, 2.5), (6, 9, 12), (0.8, 1.5), (2.0, 4.0)):
        p = dict(x_turn=x_turn, t_swing=t_swing, t_straight=t_straight, t_pause=3.0, goal_z=26, t_goal=3.5,
                 v_rev=2.2, look=look, k1=k1, k2=k2)
        log = simulate(p)
        r = evaluate(log)
        # trailer must never hit neighbouring docked trailers (x = +-4.3) -> keep axle |x| small near the wall
        ok = all(abs((x - L2 * math.sin(h2))) < 2.2 + 0.08 * max(0, 30 - (z - L2 * math.cos(h2)))
                 for t, x, z, h1, h2, v, d, ph in log if ph == 'rev' and (z - L2 * math.cos(h2)) > 25)
        score = abs(r['ax']) * 3 + abs(r['h2']) * 0.3 + abs(r['phi']) * 0.1 + (0 if ok else 100) + abs(r['az'] - 36.85)
        if best is None or score < best[0]:
            best = (score, p, r)
    print(best)
