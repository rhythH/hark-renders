"""SALTWATER CROCODILE rig (Crocodylus porosus).

One 2.5-D model drives every view: the body is a stack of elliptical cross-
sections along the spine (profiles below), each surface point (x, theta) is
deformed (jaw, swim, gait) and projected with a ROLL about the long axis.
roll=0 is the hero side view, roll=-90 the top view, and animating roll gives
the death roll with the pale belly coming round.  Painted flat bands (dark
olive back / olive-yellow flank / cream belly) are clipped exactly at the
visible half of each section, so there is no faceting.

Local units: 1000 snout tip (x=-500) -> tail tip (x=+500), y down, faces LEFT.
Body centre line ~y=0; belly ~+72, back ~-78, walking feet ~+118.

Classes: Croc, CrocTop, CrocHead, CrocHeadOn, Hatchling, CrocEyes.
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, hexc, mix, set_col, catmull, circle, stroke_glow, TAU, PAL, rng

PI = math.pi
OUT = PAL.OUTLINE

# ----------------------------------------------------------------------------- profiles (side view, body frame)
TOP_C = [(-500, -6), (-497, -20), (-489, -32), (-479, -33), (-466, -26), (-445, -25), (-420, -29), (-398, -35),
         (-384, -45), (-374, -60), (-361, -66), (-348, -60), (-338, -50), (-322, -49), (-305, -50), (-288, -54),
         (-262, -60), (-220, -72), (-160, -84), (-95, -90), (-25, -86), (30, -76), (100, -62), (200, -46),
         (300, -32), (400, -19), (470, -9), (500, -3)]
BOT_C = [(-500, -6), (-497, 8), (-486, 16), (-460, 20), (-425, 24), (-385, 29), (-350, 36), (-322, 45),
         (-292, 55), (-258, 63), (-205, 74), (-135, 86), (-55, 86), (5, 72), (60, 57), (150, 40), (250, 26),
         (350, 15), (450, 7), (500, 1)]
# upper lip line seen from the near side (the croc "grin", with the notch for the 4th lower tooth)
LIP_C = [(-499, 0), (-490, 5), (-478, 7), (-468, 3), (-458, 7), (-440, 11), (-415, 12), (-390, 14), (-365, 17),
         (-342, 21), (-322, 27), (-305, 34), (-288, 42), (-270, 50)]
WID_C = [(-500, 4), (-496, 18), (-484, 28), (-460, 33), (-440, 35), (-415, 40), (-388, 47), (-360, 55), (-330, 60),
         (-300, 60), (-272, 55), (-235, 66), (-175, 90), (-105, 104), (-35, 98), (15, 76), (70, 48), (150, 34),
         (250, 24), (350, 15), (430, 8), (500, 2)]
HINGE = (-316.0, 28.0)
SPLIT0, SPLIT1 = -334.0, -282.0          # head (split upper/lower jaw) -> body (full ring)
Y0 = -4.0                                # roll axis height

def _ss(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def _prof(ctrl, xs, n=10):
    C = catmull(ctrl, n)
    o = np.argsort(C[:, 0])
    return np.interp(xs, C[o, 0], C[o, 1])

def _path(ctx, P, close=True):
    ctx.move_to(float(P[0, 0]), float(P[0, 1]))
    for x, y in P[1:]:
        ctx.line_to(float(x), float(y))
    if close: ctx.close_path()

PALETTES = {
    'adult': dict(back='#3D4733', back_dk='#283020', flank='#5F6845', belly='#DDD4B1', belly_dk='#BFB48A',
                  blotch='#20271A', leg='#4C5639', iris='#CDBB4E', iris_dk='#7E6F22', plate='#3A4431',
                  keel='#5E6A4C', mouth='#E8D2A2', throat='#6E3C2C', gum='#C98C76'),
    'hatchling': dict(back='#7A7136', back_dk='#5D5628', flank='#A69A55', belly='#EFE6C4', belly_dk='#D6CA9E',
                      blotch='#1E1E16', leg='#8E8445', iris='#D8C35A', iris_dk='#8A7425', plate='#6B632E',
                      keel='#958A4D', mouth='#EAD6A8', throat='#6E3C2C', gum='#D09A82'),
}

# ----------------------------------------------------------------------------- model geometry (static)
class CrocGeo:
    def __init__(self, nh=46, nb=70):
        xs = np.r_[np.linspace(-500, -300, nh, endpoint=False), np.linspace(-300, 500, nb)]
        self.xs = xs
        top, bot = _prof(TOP_C, xs), _prof(BOT_C, xs)
        self.c = (top + bot) / 2
        self.a = np.maximum((bot - top) / 2, 1.2)
        self.b = np.maximum(_prof(WID_C, xs), 1.2)
        lip = _prof(LIP_C, xs)
        thm = np.arccos(np.clip((self.c - lip) / self.a, -0.96, 0.96))
        k = _ss(SPLIT0, SPLIT1, xs)
        self.TA = thm + (PI - thm) * k                  # half-angle of the upper (mesh A) arc
        self.mB = xs < SPLIT1 + 0.5                     # mesh B (lower jaw) rows

    def interp(self, x):
        x = np.asarray(x, float)
        return (np.interp(x, self.xs, self.c), np.interp(x, self.xs, self.a), np.interp(x, self.xs, self.b),
                np.interp(x, self.xs, self.TA))

_G = None
def geo():
    global _G
    if _G is None: _G = CrocGeo()
    return _G

def surf3(x, th, out=0.0):
    """Body-frame surface point(s) at x, angle theta (rad), pushed `out` along the outward normal."""
    g = geo()
    x = np.atleast_1d(np.asarray(x, float)); th = np.broadcast_to(np.asarray(th, float), x.shape)
    c, a, b, _ = g.interp(x)
    y = c - a * np.cos(th); z = b * np.sin(th)
    out = np.broadcast_to(np.asarray(out, float), x.shape)
    if np.any(out):
        ny, nz = -np.cos(th) / a, np.sin(th) / b
        n = np.hypot(ny, nz) + 1e-9
        y = y + out * ny / n; z = z + out * nz / n
    return x.copy(), y, z

class FSet:
    """Concatenated body-frame point items (static, built once) — projected in one batch per frame."""
    def __init__(self):
        self._p = []; self.rng = []; self._ref = []; self.meta = []; self._n = 0
    def add(self, xs, ths, out=0.0, low=0.0, ref=None, meta=None):
        X, Y, Z = surf3(xs, ths, out)
        return self.add_raw(X, Y, Z, np.atleast_1d(np.asarray(xs, float)),
                            np.broadcast_to(np.asarray(ths, float), X.shape), low, ref, meta)
    def add_raw(self, X, Y, Z, X0, TH, low=0.0, ref=None, meta=None):
        n = len(X)
        self._p.append((X, Y, Z, X0, TH, np.full(n, float(low))))
        self.rng.append((self._n, self._n + n)); self._n += n
        self._ref.append(ref if ref is not None else (float(np.mean(X0)), float(np.mean(TH))))
        self.meta.append(meta)
    def done(self):
        if not self._p: return self
        cols = list(zip(*self._p))
        self.X, self.Y, self.Z, self.X0, self.TH, self.low = [np.concatenate(c) for c in cols]
        self.rx = np.array([r[0] for r in self._ref]); self.rth = np.array([r[1] for r in self._ref])
        return self

# tooth tables (x position, size) — uneven, interlocking
_UP_X = np.array([-494, -486, -477, -468, -459, -447, -435, -423, -411, -399, -388, -377, -366, -356, -346, -337, -328])
_UP_S = np.array([8, 10, 8, 12, 6, 9, 12, 17, 13, 10, 8, 10, 12, 11, 9, 7, 6])
_LO_X = np.array([-491, -482, -473, -464, -452, -440, -428, -416, -404, -392, -380, -369, -358, -348, -339])
_LO_S = np.array([11, 9, 7, 17, 7, 7, 9, 10, 12, 11, 10, 9, 8, 7, 6])

_FEATS = None
def feats():
    """Static surface features of the crocodile in body coordinates."""
    global _FEATS
    if _FEATS is not None: return _FEATS
    g = geo(); R = math.radians
    F = {k: FSet() for k in ('grid', 'belly', 'ridge', 'snout', 'ear', 'jaw', 'blotch', 'saddle', 'hband',
                             'plates', 'bumps', 'teeth', 'domes')}
    # flank scale rows + transverse divisions, tail rings
    for s in (1, -1):
        for thd in (84, 98, 110):
            xs = np.linspace(-262, 470, 80); F['grid'].add(xs, R(thd) * s)
        for i, x in enumerate(np.arange(-255, 470, 14)):
            F['grid'].add(np.full(6, x + (i % 2) * 3.0), np.radians(np.linspace(76, 116, 6)) * s)
    for x in np.arange(40, 480, 16):
        F['grid'].add(np.full(9, x), np.radians(np.linspace(-72, 72, 9)))
    # belly scutes
    for thd in (128, 142, 156, 170, 180, -170, -156, -142, -128):
        xs = np.linspace(-280, 470, 60); F['belly'].add(xs, np.full_like(xs, R(thd)))
    for x in np.arange(-280, 470, 11):
        F['belly'].add(np.full(10, x), np.radians(np.linspace(120, 240, 10)))
    # head: preorbital ridges, snout scale ticks, ear slits
    rr = rng(17)
    for s in (1, -1):
        F['ridge'].add(np.linspace(-468, -380, 12), np.radians(np.linspace(20, 30, 12)) * s)
        for _ in range(30):
            x0 = rr.uniform(-480, -300); f = rr.uniform(0.3, 0.9)
            TA = float(g.interp(np.array([x0]))[3][0])
            th = TA * f * s
            F['snout'].add(np.array([x0, x0 + rr.uniform(6, 14)]), np.array([th, th + rr.uniform(-0.15, 0.15)]))
        F['ear'].add(np.linspace(-342, -326, 4), np.radians(np.linspace(40, 46, 4)) * s, out=0.6)
    # lower jaw scale divisions
    for x in np.arange(-480, -296, 12):
        TA = float(g.interp(np.array([x]))[3][0])
        F['jaw'].add(np.full(8, x), np.linspace(TA + 0.15, TAU - TA - 0.15, 8), low=1.0)
    # blotches
    r = rng(11)
    for _ in range(70):
        x, thd, sz = r.uniform(-240, 470), r.uniform(70, 114) * r.choice([1, -1]), r.uniform(6, 14)
        q = np.linspace(0, TAU, 9, endpoint=False)
        F['blotch'].add(x + sz * np.cos(q) * 1.2, R(thd) + R(sz * 0.55) * np.sin(q), out=0.4, ref=(x, R(thd)))
    for x in np.arange(95, 480, 50):
        for s in (1, -1):
            F['saddle'].add(np.r_[np.full(6, x - 9), np.full(6, x + 9)],
                            np.radians(np.r_[np.linspace(0, 92, 6), np.linspace(92, 0, 6)]) * s, out=0.5, ref=(x, R(40) * s))
    for x in np.arange(-230, 60, 42):
        for s in (1, -1):
            F['hband'].add(np.r_[np.full(6, x - 8), np.full(6, x + 8)],
                           np.radians(np.r_[np.linspace(0, 100, 6), np.linspace(100, 0, 6)]) * s, out=0.5, ref=(x, R(45) * s))
    # osteoderm plates (5 rows each side)
    for row, thd in enumerate((6, 19, 32, 45, 58)):
        for x in np.arange(-238 + (row % 2) * 8, 32, 17):
            for s in (1, -1):
                th = R(thd) * s; d = R(5.4)
                F['plates'].add(np.array([x - 7, x + 7, x + 7, x - 7]), np.array([th - d, th - d, th + d, th + d]),
                                out=0.5, ref=(x, th))
    # bumps: nuchal shields, 2 keel rows, tail double crest -> single crest. meta = height
    def bump(x, thd, h, w, lean=3.0):
        th = R(thd)
        F['bumps'].add(np.array([x - w, x + lean, x + w]), np.full(3, th), out=np.array([-1.0, h, -1.0]), ref=(x, th), meta=h)
    for i, x in enumerate((-280, -265, -250)):
        for s in (1, -1): bump(x, s * (12 + 5 * i), 8.5, 6.5, 2)
    for row, thd, h in ((0, 9, 9.0), (1, 24, 6.5)):
        for x in np.arange(-230 + row * 6, 34, 17):
            for s in (1, -1): bump(x, s * thd, h, 6.0, 2.5)
    for x in np.arange(36, 300, 17):
        h = 18 - (x - 36) / 264 * 6
        for s in (1, -1): bump(x + (0 if s > 0 else 8), s * 10, h, 7.5, 4)
    for x in np.arange(300, 488, 15):
        bump(x, 0.0, 12 - (x - 300) / 188 * 7, 6.5, 4)
    # teeth (body coords). meta=(upper, side)
    for side in (1, -1):
        for xs_, ss_, upper in ((_UP_X, _UP_S, True), (_LO_X, _LO_S, False)):
            for x, s in zip(xs_, ss_):
                s = float(s) * 1.15; w = max(2.6, s * 0.33)
                xx = np.array([x - w, x, x + w], float)
                TA = g.interp(xx)[3]
                th = TA * side
                X, Y, Z = surf3(xx, th, out=np.array([-1.5, 0.0, -1.5]))
                d = np.array([0.0, 1.0, 0.28 * side]) if upper else np.array([0.0, -1.0, 0.30 * side])
                d /= np.linalg.norm(d)
                PX = np.array([X[0], X[1] + s * 0.11 * (1 if upper else -1), X[2]])
                PY = np.array([Y[0], Y[1] + s * d[1], Y[2]]); PZ = np.array([Z[0], Z[1] + s * d[2], Z[2]])
                F['teeth'].add_raw(PX, PY, PZ, xx, th, low=0.0 if upper else 1.0, ref=(float(x), float(th[1])),
                                   meta=(upper, side))
    # sensory domes (ISOs). meta = lighting order
    rd = rng(5)
    for i in range(160):
        x = rd.uniform(-494, -326); f = rd.uniform(0.05, 0.9); lower = rd.random() < 0.45; s = rd.choice([1, -1])
        TA = float(g.interp(np.array([x]))[3][0])
        th = ((TA + 0.08 + f * 0.6) if lower else (TA - 0.08 - f * 0.6 * TA)) * s
        F['domes'].add(np.array([x]), np.array([th]), out=0.5, low=1.0 if lower else 0.0, ref=(x, th), meta=i)
    for k in F: F[k].done()
    _FEATS = F
    return F

# ----------------------------------------------------------------------------- side / any-roll crocodile
class Croc(Element):
    """Saltwater crocodile.

    Croc(pos, scale=0.6, facing='left'|'right', variant='side'|'xray'|'silhouette',
         swim=1 (tail-driven lateral undulation, K-able), period=2.6, gait=0 (0 swim .. 1 high-walk, K-able),
         walk_period=1.4, jaw=deg|K (0..55), blink='auto'|[t..]|None, submerged=0..1|K, waterline=0
         (local y of the surface), water='#2B4A3E', roll=deg|K (death roll; -90 = top view), turn=0
         (lateral body curve, top view), legs=True|False|'sprawl', domes=False, dome_glow=0..1|K,
         eye_scale=1, tooth_scale=1, outline=6, tint=None, palette='adult'|'hatchling', sil_color, xray_color)
    1000 units snout->tail tip; at scale .6 it is ~600 px long.
    """
    def __init__(self, facing='left', variant='side', swim=1.0, period=2.6, gait=0.0, walk_period=1.4, jaw=0.0,
                 blink='auto', submerged=0.0, waterline=0.0, water='#2B4A3E', roll=0.0, turn=0.0, legs=True,
                 domes=False, dome_glow=0.0, eye_scale=1.2, tooth_scale=0.9, outline=6.0, tint=None,
                 palette='adult', sil_color='#061722', xray_color=PAL.CYAN, phase=0.0, bands=None, **kw):
        super().__init__(**kw)
        self.facing, self.variant, self.swim, self.period, self.gait = facing, variant, swim, period, gait
        self.walk_period, self.jaw, self.blink, self.submerged, self.waterline = walk_period, jaw, blink, submerged, waterline
        self.water, self.roll, self.turn, self.legs, self.domes, self.dome_glow = water, roll, turn, legs, domes, dome_glow
        self.eye_scale, self.tooth_scale, self.ow, self.tint = eye_scale, tooth_scale, outline, tint
        self.pal = dict(PALETTES[palette]); self.sil_color, self.xray_color, self.phase = sil_color, xray_color, phase
        self.bands = (palette == 'hatchling') if bands is None else bands
        self.g = geo()
        r = rng(11)
        # flank blotches (x, theta deg, size)
        self._blot = [(r.uniform(-240, 470), r.uniform(58, 112) * r.choice([1, -1]), r.uniform(6, 14)) for _ in range(70)]
        rd = rng(5)
        self._domes = [(rd.uniform(-492, -330), rd.uniform(0.05, 0.9), rd.choice([0, 1]), rd.choice([1, -1])) for _ in range(150)]

    # ------------------------------------------------------------------ colour helpers
    def C(self, key):
        c = self.pal.get(key, key)
        return mix(c, self.tint, 0.55) if self.tint else hexc(c)

    # ------------------------------------------------------------------ pose state
    def state(self, t):
        sw = ev(self.swim, t); gt = float(np.clip(ev(self.gait, t), 0, 1))
        jaw = max(0.0, ev(self.jaw, t))
        return dict(t=t, sw=sw, gait=gt, jaw=math.radians(jaw), jawd=jaw,
                    ph=TAU * t / self.period + self.phase, wph=TAU * t / self.walk_period + self.phase,
                    roll=math.radians(ev(self.roll, t)), turn=ev(self.turn, t))

    # ------------------------------------------------------------------ surface + deformation pipeline
    def surf3(self, x, th, out=0.0):
        """Body-frame surface point(s) at x, angle theta (rad), pushed `out` along the normal."""
        return surf3(x, th, out)

    def _unused(self, x, th, out=0.0):
        c, a, b, _ = self.g.interp(x)
        th = np.asarray(th, float)
        y = c - a * np.cos(th); z = b * np.sin(th)
        if np.any(out):
            ny, nz = -np.cos(th) / a, np.sin(th) / b
            n = np.hypot(ny, nz) + 1e-9
            y = y + out * ny / n; z = z + out * nz / n
        return np.broadcast_to(np.asarray(x, float), y.shape).copy(), y, z

    def xf(self, st, X, Y, Z, low=0.0):
        """Deform + project body-frame points -> (sx, sy, depth). low = lower-jaw membership (0/1 array)."""
        X = np.asarray(X, float).copy(); Y = np.asarray(Y, float).copy(); Z = np.asarray(Z, float).copy()
        low = np.broadcast_to(np.asarray(low, float), X.shape)
        ja = st['jaw']
        if ja > 1e-4:
            hx, hy = HINGE
            for wgt, ang in ((low * _ss(-284, -326, X), -ja), ((1 - low) * _ss(-286, -340, X), ja * 0.16)):
                if not np.any(wgt): continue
                a = ang * wgt
                dx, dy = X - hx, Y - hy
                ca, sa = np.cos(a), np.sin(a)
                X, Y = hx + dx * ca - dy * sa, hy + dx * sa + dy * ca
        # swim: travelling lateral wave from the hips to the tail tip (+ a little heave)
        sw, g = st['sw'], st['gait']
        u = (X + 260.0) / 760.0
        w = np.clip(u, 0, 1) ** 1.5
        amp = 70.0 * sw * (1 - 0.75 * g)
        wave = np.sin(st['ph'] - u * PI * 1.15)
        Z = Z + amp * w * wave - amp * 0.06 * np.clip((-260 - X) / 240, 0, 1) * math.sin(st['ph'] + 0.7)
        Y = Y + amp * 0.2 * w * np.sin(st['ph'] + 0.9 - u * PI * 1.15)
        if g > 0:   # walking: S-curve sway + bob
            Z = Z + 22 * g * np.sin(st['wph'] - (X + 300) / 500 * PI) * np.clip((X + 300) / 800, 0, 1)
            Y = Y + 3 * g * math.sin(2 * st['wph'])
        if st['turn']:
            Z = Z + st['turn'] * ((X + 250) / 750) ** 2 * 120
        # roll about the long axis
        r = st['roll']
        if abs(r) > 1e-5:
            cr, sr = math.cos(r), math.sin(r)
            Yc = Y - Y0
            return X, Y0 + Yc * cr - Z * sr, Yc * sr + Z * cr
        return X, Y, Z

    def nz(self, st, x, th):
        """Facing toward the viewer (>0) of the surface normal at (x, theta)."""
        c, a, b, _ = self.g.interp(x)
        ny, nz = -np.cos(th) / a, np.sin(th) / b
        n = np.hypot(ny, nz) + 1e-9
        r = st['roll']
        return (ny * math.sin(r) + nz * math.cos(r)) / n

    # ------------------------------------------------------------------ meshes
    def meshes(self, st):
        """Returns list of mesh dicts (name, xs, th(lo..hi) grid, screen pts, low flag)."""
        g = self.g
        out = []
        sA = np.linspace(-1, 1, 33)
        thA = sA[None, :] * g.TA[:, None]
        XA = np.repeat(g.xs[:, None], len(sA), 1)
        X, Y, Z = self._grid3(XA, thA)
        sx, sy, sz = self.xf(st, X, Y, Z, 0.0)
        out.append(dict(name='A', x=g.xs, lo=-g.TA, hi=g.TA, sx=sx, sy=sy, low=0.0))
        xb = g.xs[g.mB]; TB = g.TA[g.mB]
        sB = np.linspace(0, 1, 13)
        thB = TB[:, None] + sB[None, :] * (2 * PI - 2 * TB[:, None])
        XB = np.repeat(xb[:, None], len(sB), 1)
        X, Y, Z = self._grid3(XB, thB)
        sx, sy, sz = self.xf(st, X, Y, Z, 1.0)
        out.append(dict(name='B', x=xb, lo=TB, hi=2 * PI - TB, sx=sx, sy=sy, low=1.0))
        return out

    def _grid3(self, XX, TH):
        c, a, b, _ = self.g.interp(XX)
        return XX, c - a * np.cos(TH), b * np.sin(TH)

    def silhouette(self, m):
        sx, sy = m['sx'], m['sy']
        i0 = np.argmin(sy, 1); i1 = np.argmax(sy, 1); r = np.arange(len(sy))
        top = np.column_stack([sx[r, i0], sy[r, i0]])
        bot = np.column_stack([sx[r, i1], sy[r, i1]])
        return top, bot

    def band_poly(self, st, m, th_lo, th_hi):
        """Polygon of the visible part of band [th_lo, th_hi] (rad, in the mesh's own angle frame)."""
        x = m['x']
        c, a, b, _ = self.g.interp(x)
        lo = np.clip(th_lo, m['lo'], m['hi']); hi = np.clip(th_hi, m['lo'], m['hi'])
        r = st['roll']
        th0 = np.arctan2(b * math.sin(r), a * math.cos(r))         # start of the visible half
        L = hi - lo
        vlo = np.mod(lo - th0 + PI / 2, TAU) - PI / 2
        vhi = vlo + L
        p1lo, p1hi = np.clip(vlo, 0, PI), np.clip(vhi, 0, PI)
        p2lo, p2hi = np.clip(vlo - TAU, 0, PI), np.clip(vhi - TAU, 0, PI)
        use2 = (p2hi - p2lo) > (p1hi - p1lo)
        plo = np.where(use2, p2lo, p1lo); phi = np.where(use2, p2hi, p1hi)
        if np.all(phi - plo < 1e-4): return None
        t1, t2 = th0 + plo, th0 + phi
        X1, Y1, Z1 = self.surf3(x, t1); X2, Y2, Z2 = self.surf3(x, t2)
        s1 = self.xf(st, X1, Y1, Z1, m['low']); s2 = self.xf(st, X2, Y2, Z2, m['low'])
        P = np.vstack([np.column_stack([s1[0], s1[1]]), np.column_stack([s2[0], s2[1]])[::-1]])
        return P

    BANDS_A = [('back', -76, 76), ('flank', 76, 118), ('flank', -118, -76), ('belly', 118, 181), ('belly', -181, -118)]
    BANDS_B = [('flank', 0, 118), ('belly', 118, 242), ('flank', 242, 360)]

    # ------------------------------------------------------------------ legs
    LEGS = {  # name: (root x, side, L1, L2, foot len, digits, width0, front?)
        'fn': (-228, 1, 52, 48, 30, 5, 34, True), 'ff': (-228, -1, 52, 48, 30, 5, 34, True),
        'hn': (-34, 1, 60, 54, 44, 4, 54, False), 'hf': (-34, -1, 60, 54, 44, 4, 54, False)}

    def leg_pts(self, st, name):
        """2-link IK leg in its own plane -> dict of screen polygons (+ depth)."""
        rx, side, L1, L2, LF, nd, w0, front = self.LEGS[name]
        g = st['gait']
        mode = self.legs
        # root on the lower flank, slightly inside
        th_root = math.radians(98) * side
        X0, Yr, Zr = self.surf3(np.array([rx]), np.array([th_root]), out=-6)
        Yr, Zr = float(Yr[0]), float(Zr[0])
        # leg plane: e_u = +x (tailward), e_v = (0, cos s, side*sin s)
        if mode == 'sprawl':
            splay = 72.0
        else:
            splay = 22 + (14 - 22) * g
        sp = math.radians(splay)
        ev_y, ev_z = math.cos(sp), side * math.sin(sp)
        # targets (u, v) for the foot (ankle)
        if mode == 'sprawl':
            tu, tv = ((-28, 92) if front else (26, 100))
            tu += 4 * math.sin(st['t'] * 0.9 + rx)
            fdir = -1.0
        else:
            # tucked swim pose
            su, sv = ((62, 46) if front else (86, 48))
            su += 3 * math.sin(st['t'] * 1.3 + rx * 0.01)
            # walk pose: diagonal gait, ground at body-y ~ +118
            phs = {'fn': 0.0, 'hf': 0.0, 'ff': PI, 'hn': PI}[name]
            p = st['wph'] + phs
            stride = 34 if front else 40
            ground = 118 - Yr
            wu = -stride * math.sin(p) + (0 if front else 8)
            lift = 22 * max(0.0, math.cos(p)) ** 2
            wv = (ground - lift) / max(0.2, ev_y)
            tu, tv = su + (wu - su) * g, sv + (wv - sv) * g
            fdir = 1.0 + (-1.0 - 1.0) * g          # swim: feet trail back (+u); walk: point forward (-u)
        # IK
        d = math.hypot(tu, tv); d = min(d, L1 + L2 - 0.5); d = max(d, abs(L1 - L2) + 0.5)
        base = math.atan2(tv, tu)
        k = math.acos(np.clip((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
        bend = 1 if front else -1               # elbow points back, knee forward
        a1 = base + bend * k
        J0 = np.array([0.0, 0.0]); J1 = J0 + L1 * np.array([math.cos(a1), math.sin(a1)])
        J2 = J0 + d * np.array([math.cos(base), math.sin(base)])
        # limb outline (u, v) with tapering widths
        w1, w2 = w0 * 0.62, w0 * 0.46
        def nrm(p, q):
            v = q - p; n = np.array([-v[1], v[0]]); return n / (np.linalg.norm(n) + 1e-9)
        n0 = nrm(J0, J1); n2 = nrm(J1, J2); n1 = (n0 + n2); n1 /= (np.linalg.norm(n1) + 1e-9)
        Jm = J0 + (J1 - J0) * 0.45
        Jr = J0 - (J1 - J0) / (np.linalg.norm(J1 - J0) + 1e-9) * 14      # root sunk into the body
        chain = [Jr, J0, Jm, J1, J2]; ws = [w0 * 1.15, w0 * 1.1, w0 * 0.86, w1, w2]; ns = [n0, n0, n0, n1, n2]
        left = [chain[i] + ns[i] * ws[i] / 2 for i in range(5)]
        right = [chain[i] - ns[i] * ws[i] / 2 for i in range(5)]
        limb = np.vstack([catmull(left, 4), catmull(right[::-1], 4)])
        # foot (palm + digits) fanning from the ankle along fdir
        fd = np.array([fdir, 0.12]); fd /= np.linalg.norm(fd)
        fn_ = np.array([-fd[1], fd[0]])
        palm_c = J2 + fd * LF * 0.3
        palm = np.array([palm_c + fd * LF * 0.38 * math.cos(q) + fn_ * w2 * 0.75 * math.sin(q) for q in np.linspace(0, TAU, 14, endpoint=False)])
        digits = []
        for i in range(nd):
            sp_ = (i - (nd - 1) / 2) / max(1, (nd - 1) / 2)
            dd = fd * math.cos(sp_ * 0.55) + fn_ * math.sin(sp_ * 0.55)
            p0 = palm_c + dd * LF * 0.25
            ln = LF * (0.75 if (nd == 5 and i in (0, 4)) else 0.95)
            p1 = p0 + dd * ln
            nn = np.array([-dd[1], dd[0]])
            digits.append(np.array([p0 + nn * 6.0, p1 + nn * 2.6, p1 + dd * 3, p1 - nn * 2.6, p0 - nn * 6.0]))
        def to3(P2):
            P2 = np.asarray(P2, float)
            return (rx + P2[:, 0], Yr + P2[:, 1] * ev_y, Zr + P2[:, 1] * ev_z)
        res = {}
        for key, P2 in [('limb', limb), ('palm', palm)] + [('d%d' % i, d_) for i, d_ in enumerate(digits)]:
            X, Y, Z = to3(P2)
            sx, sy, sz = self.xf(st, X, Y, Z, 0.0)
            res[key] = np.column_stack([sx, sy])
        bones = to3(np.array([J0, J1, J2, J2 + fd * LF]))
        bx, by, _ = self.xf(st, *bones, 0.0)
        res['bones'] = np.column_stack([bx, by])
        _, _, dz = self.xf(st, np.array([rx]), np.array([Yr]), np.array([Zr]), 0.0)
        res['z'] = float(dz[0]); res['front'] = front; res['side'] = side; res['cap'] = 6
        return res

    def eye_pt(self, st, side=1):
        x, thd = -361.0, 33.0 * side
        X, Y, Z = self.surf3(np.array([x]), np.array([math.radians(thd)]), out=2)
        sx, sy, sz = self.xf(st, X, Y, Z, 0.0)
        return float(sx[0]), float(sy[0]), float(self.nz(st, x, math.radians(thd)))

    def blink_k(self, t):
        if self.blink == 'auto':
            ph = (t + self.phase * 1.7) % 4.6
            return max(0.0, 1 - abs(ph - 2.2) / 0.1) if abs(ph - 2.2) < 0.1 else 0.0
        if self.blink:
            for b in self.blink:
                if abs(t - b) < 0.1: return 1 - abs(t - b) / 0.1
        return 0.0

    def teeth(self, st):
        """Teeth triangles: list of (pts[base_l, tip, base_r], depth, upper?, side)."""
        out = []
        ts = self.tooth_scale
        for side in (1, -1):
            for xs_, ss_, upper in ((_UP_X, _UP_S, True), (_LO_X, _LO_S, False)):
                for x, s in zip(xs_, ss_):
                    s = s * ts * 1.15
                    w = max(2.6, s * 0.33)
                    _, _, _, TA = self.g.interp(np.array([x - w, x, x + w]))
                    th = TA * side
                    X, Y, Z = self.surf3(np.array([x - w, x, x + w]), th, out=np.array([-1.5, 0.0, -1.5]))
                    tip_dir = np.array([0.0, 1.0, 0.28 * side]) if upper else np.array([0.0, -1.0, 0.30 * side])
                    tip_dir /= np.linalg.norm(tip_dir)
                    tx = X[1] + s * 0.18 * (1 if upper else -1) * 0.6
                    ty = Y[1] + s * tip_dir[1]; tz = Z[1] + s * tip_dir[2]
                    PX = np.array([X[0], tx, X[2]]); PY = np.array([Y[0], ty, Y[2]]); PZ = np.array([Z[0], tz, Z[2]])
                    sx, sy, sz = self.xf(st, PX, PY, PZ, 0.0 if upper else 1.0)
                    out.append((np.column_stack([sx, sy]), float(sz[0] + sz[2]) / 2 + 2, upper, side,
                                float(self.nz(st, x, float(th[1])))))
        return out

    # ------------------------------------------------------------------ drawing
    def draw(self, ctx, t):
        st = self.state(t)
        k = float(np.clip(ev(self.submerged, t), 0, 1))
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if k > 0.001:
            wl = ev(self.waterline, t)
            ctx.push_group()
            ctx.save()
            # sink + slight nose-up pitch about the eye so nostrils, eyes and scutes break the surface together
            dy = k * (wl + 50.0)
            ctx.translate(0, dy)
            ctx.translate(-361, -45); ctx.rotate(math.radians(8.0 * k)); ctx.translate(361, 45)
            self._draw_variant(ctx, t, st)
            ctx.restore()
            # tint everything below the surface with the water colour
            ctx.set_operator(cairo.OPERATOR_ATOP)
            wc = hexc(self.water)
            ctx.rectangle(-900, wl + 1.5, 1800, 1200)
            ctx.set_source_rgba(wc[0], wc[1], wc[2], 0.35 + 0.45 * k); ctx.fill()
            g = cairo.LinearGradient(0, wl, 0, wl + 160)
            g.add_color_stop_rgba(0, wc[0], wc[1], wc[2], 0.0); g.add_color_stop_rgba(1, wc[0], wc[1], wc[2], 0.35 * k)
            ctx.set_source(g); ctx.rectangle(-900, wl + 1.5, 1800, 1200); ctx.fill()
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.pop_group_to_source(); ctx.paint()
        else:
            self._draw_variant(ctx, t, st)
        ctx.restore()

    def _draw_variant(self, ctx, t, st):
        if self.variant == 'xray': self._draw_xray(ctx, t, st)
        elif self.variant == 'silhouette': self._draw_sil(ctx, t, st)
        else: self._draw_side(ctx, t, st)

    def _leg_list(self, st):
        if not self.legs: return []
        return [self.leg_pts(st, n) for n in ('ff', 'hf', 'fn', 'hn')]

    def _draw_leg(self, ctx, L, far):
        ow = self.ow * 0.8
        col = self.C('leg')
        if far: col = mix(col, '#0B1008', 0.4)
        hi = mix(col, '#C9D0A8', 0.18)
        claw = (0.86, 0.80, 0.62, 1) if not far else (0.5, 0.47, 0.38, 1)
        for i in range(5):
            key = 'd%d' % i
            if key not in L: continue
            D = L[key]
            p, q = D[2], (D[0] + D[4]) / 2; v = (p - q) / (np.linalg.norm(p - q) + 1e-9)
            ctx.move_to(*(p - v * 2)); ctx.line_to(*(p + v * 7)); ctx.set_source_rgba(*claw); ctx.set_line_width(2.6); ctx.stroke()
            _path(ctx, D); ctx.set_source_rgba(*col); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(ow * 0.6); ctx.stroke()
        _path(ctx, L['palm']); ctx.set_source_rgba(*col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow * 0.6); ctx.stroke()
        _path(ctx, L['limb']); ctx.set_source_rgba(*col); ctx.fill()
        ctx.save(); _path(ctx, L['limb']); ctx.clip()
        P = L['limb']; n = len(P) // 2
        # highlight along the upper edge + scale scallops
        _path(ctx, P[:n], False); ctx.set_source_rgba(*hi[:3], 0.5); ctx.set_line_width(9); ctx.stroke()
        for i in range(2, n - 1, 2):
            a, b = P[i], P[len(P) - 1 - i]
            ctx.move_to(*(a * 0.75 + b * 0.25)); ctx.line_to(*(a * 0.25 + b * 0.75))
        ctx.set_source_rgba(0.05, 0.07, 0.04, 0.35); ctx.set_line_width(1.5); ctx.stroke()
        ctx.restore()
        # outline everything except the root cap (so the limb grows out of the body)
        _path(ctx, P[L['cap']:len(P) - L['cap']], False); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()

    def _bands(self, ctx, st, m):
        bands = self.BANDS_A if m['name'] == 'A' else self.BANDS_B
        for name, a0, a1 in bands:
            P = self.band_poly(st, m, math.radians(a0), math.radians(a1))
            if P is None: continue
            _path(ctx, P); ctx.set_source_rgba(*self.C(name)); ctx.fill_preserve()
            ctx.set_line_width(0.8); ctx.stroke()

    def _line3(self, ctx, st, xs, ths, low=0.0, out=0.6, vis=0.02):
        """Stroke a surface polyline (x[], theta[]) skipping back-facing runs (current source/width)."""
        X, Y, Z = self.surf3(xs, ths, out=out)
        sx, sy, _ = self.xf(st, X, Y, Z, low)
        v = self.nz(st, xs, ths) > vis
        started = False
        for i in range(len(sx)):
            if v[i]:
                if not started: ctx.move_to(float(sx[i]), float(sy[i])); started = True
                else: ctx.line_to(float(sx[i]), float(sy[i]))
            else:
                started = False
        ctx.stroke()

    def _texture(self, ctx, st, m):
        """Scale grid, blotches, plates, belly scutes, tail bands — clipped to the mesh silhouette."""
        F = feats()
        dk = self.C('blotch'); bd = self.C('belly_dk')
        if m['name'] == 'A':
            self._lines(ctx, st, F['belly'], (bd[0], bd[1], bd[2], 0.9), 1.4)
            self._lines(ctx, st, F['grid'], (dk[0], dk[1], dk[2], 0.28), 1.4)
            self._polys(ctx, st, F['blotch'], (dk[0], dk[1], dk[2], 0.5))
            self._polys(ctx, st, F['saddle'], (dk[0], dk[1], dk[2], 0.62 if self.bands else 0.40), vis=-0.3)
            if self.bands: self._polys(ctx, st, F['hband'], (dk[0], dk[1], dk[2], 0.55), vis=-0.2)
            # osteoderm plates + keel highlights
            pc = self.C('plate'); kc = self.C('keel')
            sx, sy, vis, F_ = self._proj(st, F['plates'])
            ctx.new_path(); keel = []
            for (i0, i1), v in zip(F_.rng, vis):
                if v > 0.04:
                    ctx.move_to(sx[i0], sy[i0]); ctx.line_to(sx[i0 + 1], sy[i0 + 1]); ctx.line_to(sx[i0 + 2], sy[i0 + 2])
                    ctx.line_to(sx[i0 + 3], sy[i0 + 3]); ctx.close_path(); keel.append(i0)
            ctx.set_source_rgba(*pc); ctx.fill()
            ctx.new_path()
            for i0 in keel:
                mx, my = (sx[i0] + sx[i0 + 3]) / 2, (sy[i0] + sy[i0 + 3]) / 2
                nx, ny = (sx[i0 + 1] + sx[i0 + 2]) / 2, (sy[i0 + 1] + sy[i0 + 2]) / 2
                ctx.move_to(mx * 0.85 + nx * 0.15, my * 0.85 + ny * 0.15); ctx.line_to(nx * 0.8 + mx * 0.2, ny * 0.8 + my * 0.2)
            ctx.set_source_rgba(kc[0], kc[1], kc[2], 0.5); ctx.set_line_width(1.6); ctx.stroke()
            self._lines(ctx, st, F['ridge'], (dk[0], dk[1], dk[2], 0.45), 1.8)
            self._lines(ctx, st, F['snout'], (dk[0], dk[1], dk[2], 0.22), 1.2)
            self._lines(ctx, st, F['ear'], (0.07, 0.08, 0.06, 0.85), 2.6, vis_min=0.1)
        else:
            self._lines(ctx, st, F['jaw'], (bd[0], bd[1], bd[2], 0.85), 1.3)

    def _proj(self, st, fs):
        sx, sy, sz = self.xf(st, fs.X, fs.Y, fs.Z, fs.low)
        vis = self.nz(st, fs.rx, fs.rth)
        return sx.tolist(), sy.tolist(), vis.tolist(), fs

    def _lines(self, ctx, st, fs, col, width, vis_min=0.02):
        """Stroke a set of surface polylines, skipping back-facing runs."""
        sx, sy, sz = self.xf(st, fs.X, fs.Y, fs.Z, fs.low)
        v = (self.nz(st, fs.X0, fs.TH) > vis_min).tolist()
        sx, sy = sx.tolist(), sy.tolist()
        ctx.new_path()
        for i0, i1 in fs.rng:
            on = False
            for i in range(i0, i1):
                if v[i]:
                    if on: ctx.line_to(sx[i], sy[i])
                    else: ctx.move_to(sx[i], sy[i]); on = True
                else: on = False
        ctx.set_source_rgba(*col); ctx.set_line_width(width); ctx.stroke()

    def _polys(self, ctx, st, fs, col, vis=0.05):
        sx, sy, vv, _ = self._proj(st, fs)
        ctx.new_path()
        for (i0, i1), v in zip(fs.rng, vv):
            if v > vis:
                ctx.move_to(sx[i0], sy[i0])
                for i in range(i0 + 1, i1): ctx.line_to(sx[i], sy[i])
                ctx.close_path()
        ctx.set_source_rgba(*col); ctx.fill()

    def bumps(self, st):
        """Keels + tail double crest + nuchal shields: list of (P[3x2], depth, h, nz)."""
        fs = feats()['bumps']
        sx, sy, sz = self.xf(st, fs.X, fs.Y, fs.Z, fs.low)
        vis = self.nz(st, fs.rx, fs.rth)
        out = []
        for k, (i0, i1) in enumerate(fs.rng):
            P = np.column_stack([sx[i0:i1], sy[i0:i1]])
            out.append((P, float(sz[i0:i1].mean()), fs.meta[k], float(vis[k])))
        return out

    def plates(self, st):
        fs = feats()['plates']
        sx, sy, sz = self.xf(st, fs.X, fs.Y, fs.Z, fs.low)
        vis = self.nz(st, fs.rx, fs.rth)
        return [(np.column_stack([sx[i0:i1], sy[i0:i1]]), float(vis[k])) for k, (i0, i1) in enumerate(fs.rng)]

    def teeth(self, st):
        """Teeth triangles: list of (pts[base_l, tip, base_r], depth, upper?, side, nz)."""
        fs = feats()['teeth']
        ts = self.tooth_scale
        X, Y, Z = fs.X.copy(), fs.Y.copy(), fs.Z.copy()
        if ts != 1.0:   # scale each tooth about its base centre
            for i0, i1 in fs.rng:
                cx, cy, cz = (X[i0] + X[i0 + 2]) / 2, (Y[i0] + Y[i0 + 2]) / 2, (Z[i0] + Z[i0 + 2]) / 2
                X[i0 + 1] = cx + (X[i0 + 1] - cx) * ts; Y[i0 + 1] = cy + (Y[i0 + 1] - cy) * ts; Z[i0 + 1] = cz + (Z[i0 + 1] - cz) * ts
        sx, sy, sz = self.xf(st, X, Y, Z, fs.low)
        vis = self.nz(st, fs.rx, fs.rth)
        out = []
        for k, (i0, i1) in enumerate(fs.rng):
            up, side = fs.meta[k]
            out.append((np.column_stack([sx[i0:i1], sy[i0:i1]]), float(sz[i0:i1].mean()), up, side, float(vis[k])))
        return out

    def _domes(self, ctx, st, t):
        """Integumentary sensory organs (ISOs): tiny dark pits along both jaws; dome_glow lights them cyan."""
        glow = float(np.clip(ev(self.dome_glow, t), 0, 1))
        fs = feats()['domes']
        sx, sy, vis, _ = self._proj(st, fs)
        n = len(fs.rng); cc = hexc(PAL.CYAN_HI)
        ctx.new_path()
        lit = []
        for k, (i0, i1) in enumerate(fs.rng):
            if vis[k] < 0.08: continue
            if glow * n > fs.meta[k]: lit.append(i0)
            else: circle(ctx, sx[i0], sy[i0], 1.4)
        ctx.set_source_rgba(0.08, 0.07, 0.05, 0.85); ctx.fill()
        for i0 in lit:
            x, y = sx[i0], sy[i0]
            rg = cairo.RadialGradient(x, y, 0, x, y, 7)
            rg.add_color_stop_rgba(0, cc[0], cc[1], cc[2], 0.9); rg.add_color_stop_rgba(1, cc[0], cc[1], cc[2], 0)
            ctx.set_source(rg); circle(ctx, x, y, 7); ctx.fill()
            circle(ctx, x, y, 1.6); ctx.set_source_rgba(cc[0], cc[1], cc[2], 1); ctx.fill()

    def _mouth(self, ctx, st):
        """Mouth interior between the visible lips (when open)."""
        g = self.g; xs = g.xs[g.mB]; TB = g.TA[g.mB]
        side = 1 if math.cos(st['roll']) >= 0 else -1
        X, Y, Z = self.surf3(xs, TB * side); su = self.xf(st, X, Y, Z, 0.0)
        X, Y, Z = self.surf3(xs, TB * side); sl = self.xf(st, X, Y, Z, 1.0)
        P = np.vstack([np.column_stack(su[:2]), np.column_stack(sl[:2])[::-1]])
        _path(ctx, P)
        mc, tc = self.C('mouth'), self.C('throat')
        hx = float(su[0][-1]); fx = float(su[0][0])
        gr = cairo.LinearGradient(fx, 0, hx, 0)
        gr.add_color_stop_rgba(0, *mc); gr.add_color_stop_rgba(0.62, *mix(mc, tc, 0.35)); gr.add_color_stop_rgba(1, *tc)
        ctx.set_source(gr); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        # tongue floor + palate ridges
        lo = np.column_stack(sl[:2])
        tong = lo.copy(); tong[:, 1] -= 10
        _path(ctx, np.vstack([tong[6:-2], lo[6:-2][::-1]]))
        ctx.set_source_rgba(*mix(mc, '#C99A70', 0.6)); ctx.fill()
        up = np.column_stack(su[:2])
        gm = self.C('gum')
        _path(ctx, up, close=False); ctx.set_source_rgba(gm[0], gm[1], gm[2], 0.9); ctx.set_line_width(8); ctx.stroke()
        _path(ctx, lo, close=False); ctx.stroke()
        ctx.restore()

    def _draw_side(self, ctx, t, st):
        ow = self.ow
        legs = self._leg_list(st)
        bumps = self.bumps(st)
        teeth = self.teeth(st)
        ms = self.meshes(st)
        jaw_open = st['jawd'] > 1.0
        sr = math.sin(st['roll'])
        order = ['B', 'A'] if sr <= 0.02 else ['A', 'B']
        if jaw_open: self._mouth(ctx, st)
        for L in legs:
            if L['z'] < 0: self._draw_leg(ctx, L, True)
        bc = self.C('back')
        far_c = mix(bc, '#000000', 0.25)
        ctx.new_path()
        for P, z, h, v in bumps:
            if v < 0: _path(ctx, P)
        ctx.set_source_rgba(*far_c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow * 0.5); ctx.stroke()
        if jaw_open:
            for P, z, up, side, v in teeth:
                if v < 0: self._tooth(ctx, P, far=True)
        for name in order:
            m = next(mm for mm in ms if mm['name'] == name)
            top, bot = self.silhouette(m)
            sil = np.vstack([top, bot[::-1]])
            _path(ctx, sil); ctx.set_source_rgba(*self.C('back_dk')); ctx.fill()
            ctx.save(); _path(ctx, sil); ctx.clip()
            self._bands(ctx, st, m)
            self._texture(ctx, st, m)
            if self.domes and name == order[-1]: self._domes(ctx, st, t)
            # painted shading: inner edge shadow, back sheen, rim light
            _path(ctx, sil); ctx.set_source_rgba(0.02, 0.04, 0.02, 0.24); ctx.set_line_width(28); ctx.stroke()
            if name == 'A':
                tp = top.copy(); tp[:, 1] += 16
                _path(ctx, tp, False); ctx.set_source_rgba(0.80, 0.86, 0.66, 0.09); ctx.set_line_width(22); ctx.stroke()
                ctx.save(); ctx.translate(-130, float(np.interp(-130, top[:, 0], top[:, 1])) + 30); ctx.scale(1, 0.3)
                rg = cairo.RadialGradient(0, 0, 0, 0, 0, 340)
                rg.add_color_stop_rgba(0, 0.80, 0.86, 0.64, 0.20); rg.add_color_stop_rgba(1, 0.80, 0.86, 0.64, 0)
                ctx.set_source(rg); circle(ctx, 0, 0, 340); ctx.fill(); ctx.restore()
                tp = top.copy(); tp[:, 1] += 5
                _path(ctx, tp[4:-3], False); ctx.set_source_rgba(0.42, 0.64, 0.64, 0.42); ctx.set_line_width(3.5); ctx.stroke()
            ctx.restore()
            _path(ctx, sil); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # front bumps: edge-on ones (on the silhouette) get the black outline, inner ones a soft dark edge
        fc = self.C('back'); hl = mix(self.C('keel'), '#FFFFFF', 0.15)
        fr = [(P, v) for P, z, h, v in bumps if v >= 0]
        ctx.new_path()
        for P, v in fr: _path(ctx, P)
        ctx.set_source_rgba(*fc); ctx.fill()
        for edge in (True, False):
            ctx.new_path()
            for P, v in fr:
                if (v < 0.5) == edge: ctx.move_to(*P[0]); ctx.line_to(*P[1]); ctx.line_to(*P[2])
            if edge: set_col(ctx, OUT); ctx.set_line_width(ow * 0.55)
            else: ctx.set_source_rgba(0.08, 0.1, 0.06, 0.7); ctx.set_line_width(1.6)
            ctx.stroke()
        ctx.new_path()
        for P, v in fr: ctx.move_to(*(P[0] * 0.55 + P[1] * 0.45)); ctx.line_to(*P[1])
        ctx.set_source_rgba(hl[0], hl[1], hl[2], 0.55); ctx.set_line_width(1.4); ctx.stroke()
        ctx.new_path()
        for P, z, up, side, v in teeth:
            if v >= -0.05: self._tooth_path(ctx, P)
        set_col(ctx, '#F1EBD6'); ctx.fill_preserve(); set_col(ctx, OUT, 0.9); ctx.set_line_width(1.4); ctx.stroke()
        for side in (1, -1):
            self._nostril(ctx, st, side)
            self._eye(ctx, st, t, side)
        for L in legs:
            if L['z'] >= 0: self._draw_leg(ctx, L, False)

    def _tooth(self, ctx, P, far=False):
        self._tooth_path(ctx, P)
        set_col(ctx, '#B9B09A' if far else '#F1EBD6'); ctx.fill_preserve()
        set_col(ctx, OUT, 0.9); ctx.set_line_width(1.4); ctx.stroke()

    def _tooth_path(self, ctx, P):
        bl, tip, br = P
        mid = (bl + br) / 2
        v = tip - mid
        ctx.move_to(*bl)
        ctx.curve_to(*(bl + v * 0.55), *(tip - (br - bl) * 0.12), *tip)
        ctx.curve_to(*(tip + (br - bl) * 0.05), *(br + v * 0.45), *br)
        ctx.close_path()

    def _eye(self, ctx, st, t, side):
        x, y, v = self.eye_pt(st, side)
        if v < 0.05: return
        es = self.eye_scale
        r = 9.5 * es
        bk = self.blink_k(t)
        sq = 0.35 + 0.65 * min(1, v * 1.4)
        ctx.save(); ctx.translate(x, y); ctx.scale(1, sq)
        # bony socket
        circle(ctx, 0, 0, r + 3.2); ctx.set_source_rgba(*mix(self.C('back_dk'), '#000000', 0.3)); ctx.fill()
        ctx.save(); circle(ctx, 0, 0, r); ctx.clip()
        rg = cairo.RadialGradient(-2, -1, 0, 0, 0, r)
        ic, idk = self.C('iris'), self.C('iris_dk')
        rg.add_color_stop_rgba(0, *mix(ic, '#FFF6C0', 0.25)); rg.add_color_stop_rgba(0.7, *ic); rg.add_color_stop_rgba(1, *idk)
        ctx.set_source(rg); ctx.paint()
        ctx.save(); ctx.scale(0.22, 1); circle(ctx, 0, 0, r * 0.82); ctx.set_source_rgba(0.03, 0.03, 0.02, 1); ctx.fill(); ctx.restore()
        circle(ctx, -r * 0.35, -r * 0.38, r * 0.2); ctx.set_source_rgba(1, 1, 0.95, 0.85); ctx.fill()
        # heavy upper lid (+ blink)
        lid = -r * 0.28 + (r * 2.2) * bk
        ctx.move_to(-r * 1.3, -r * 1.4); ctx.line_to(r * 1.3, -r * 1.4); ctx.line_to(r * 1.3, lid - r * 0.15)
        ctx.curve_to(r * 0.4, lid + r * 0.2, -r * 0.4, lid + r * 0.2, -r * 1.3, lid + r * 0.05); ctx.close_path()
        ctx.set_source_rgba(*self.C('back')); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.set_line_width(2.2); ctx.stroke()
        ctx.restore()
        circle(ctx, 0, 0, r); set_col(ctx, OUT); ctx.set_line_width(2.4); ctx.stroke()
        ctx.restore()

    def _nostril(self, ctx, st, side):
        x, th = -488.0, math.radians(17) * side
        v = float(self.nz(st, x, th))
        if v < 0.05: return
        X, Y, Z = self.surf3(np.array([x]), np.array([th]), out=0.5)
        sx, sy, _ = self.xf(st, X, Y, Z)
        ctx.save(); ctx.translate(float(sx[0]), float(sy[0])); ctx.scale(1, 0.35 + 0.65 * v)
        ctx.scale(1.4, 0.75); circle(ctx, 0, 0, 3.4); ctx.set_source_rgba(0.05, 0.05, 0.03, 0.95); ctx.fill()
        ctx.restore()

    # ------------------------------------------------------------------ silhouette + xray
    def _draw_sil(self, ctx, t, st):
        ms = self.meshes(st)
        ctx.new_path()
        for m in ms:
            top, bot = self.silhouette(m); _path(ctx, np.vstack([top, bot[::-1]]))
        for P, z, h, v in self.bumps(st): _path(ctx, P)
        for L in self._leg_list(st):
            for k_, P in L.items():
                if isinstance(P, np.ndarray) and k_ != 'bones': _path(ctx, P)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        set_col(ctx, self.sil_color); ctx.fill()

    def _draw_xray(self, ctx, t, st):
        c = self.xray_color; cc = hexc(c); sk = hexc(PAL.CYAN_HI)
        ms = self.meshes(st)
        sils = []
        for m in ms:
            top, bot = self.silhouette(m); sils.append(np.vstack([top, bot[::-1]]))
        for P in sils:
            _path(ctx, P); ctx.set_source_rgba(0.16, 0.38, 0.45, 0.38); ctx.fill()
        legs = self._leg_list(st)
        for L in legs:
            _path(ctx, L['limb']); ctx.set_source_rgba(0.14, 0.33, 0.39, 0.25 if L['z'] < 0 else 0.32); ctx.fill()
        # osteoderms as faint bone plates
        ctx.new_path()
        for P, v in self.plates(st):
            if v > 0.04: _path(ctx, P)
        ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.22); ctx.set_line_width(1.2); ctx.stroke()
        # spine
        xs = np.linspace(-300, 492, 70)
        cc_, a_, b_, _ = self.g.interp(xs)
        X, Y, Z = xs, cc_ - 0.42 * a_, np.zeros_like(xs)
        sx, sy, _ = self.xf(st, X, Y, Z)
        spine = np.column_stack([sx, sy])
        stroke_glow(ctx, lambda: _path(ctx, spine, False), sk, 4.0, glow=2, glow_alpha=0.16)
        ctx.set_line_width(2.6); ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.8)
        for i in range(1, len(xs) - 1, 2):
            X2, Y2, Z2 = np.array([xs[i]] * 2), np.array([Y[i] - 9 * (1 - i / 80), Y[i] + 6 * (1 - i / 80)]), np.zeros(2)
            s2 = self.xf(st, X2, Y2, Z2)
            ctx.move_to(s2[0][0], s2[1][0]); ctx.line_to(s2[0][1], s2[1][1])
        ctx.stroke()
        # ribs + gastralia
        for i, x in enumerate(np.linspace(-262, -40, 13)):
            for s in (1, -1):
                ths = np.radians(np.linspace(12, 150 if i < 11 else 70, 9)) * s
                c0, a0, b0, _ = self.g.interp(np.full(9, x))
                X = np.full(9, x) + np.linspace(0, 10, 9)
                Y = c0 - 0.8 * a0 * np.cos(ths); Z = 0.8 * b0 * np.sin(ths)
                sx, sy, sz = self.xf(st, X, Y, Z)
                P = np.column_stack([sx, sy])
                if sz.mean() < 0:
                    _path(ctx, P, False); ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.25); ctx.set_line_width(1.8); ctx.stroke()
                else:
                    stroke_glow(ctx, lambda P=P: _path(ctx, P, False), sk, 2.4, glow=1, glow_alpha=0.12)
        # skull: outline of upper head + orbit + nostril; mandible outline
        g = self.g
        head = g.xs < -282
        A = next(m for m in ms if m['name'] == 'A')
        top, bot = self.silhouette(A)
        sk_poly = np.vstack([top[head], bot[head][::-1]])
        sk_poly = sk_poly + (np.array([[ -0.0, 4.0]]) * 0)
        stroke_glow(ctx, lambda: _path(ctx, sk_poly), sk, 2.8, glow=2, glow_alpha=0.14)
        B = next(m for m in ms if m['name'] == 'B')
        tb, bb = self.silhouette(B)
        stroke_glow(ctx, lambda: _path(ctx, np.vstack([tb, bb[::-1]])), sk, 2.8, glow=2, glow_alpha=0.14)
        ex, ey, v = self.eye_pt(st, 1)
        stroke_glow(ctx, lambda: circle(ctx, ex, ey + 2, 13), sk, 2.4, glow=1)
        # limb bones
        for L in legs:
            P = L['bones']
            a = 0.35 if L['z'] < 0 else 1.0
            ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.9 * a); ctx.set_line_width(3.4)
            _path(ctx, P, False); ctx.stroke()
            for p in P[:3]: circle(ctx, p[0], p[1], 4.5); ctx.fill()
        # teeth outlines
        jaw_open = st['jawd'] > 1.0
        for P, z, up, side, vv in self.teeth(st):
            if vv < 0: continue
            bl, tip, br = P
            ctx.move_to(*bl); ctx.line_to(*tip); ctx.line_to(*br); ctx.close_path()
            ctx.set_source_rgba(cc[0], cc[1], cc[2], 0.3); ctx.fill_preserve()
            ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.95); ctx.set_line_width(1.6); ctx.stroke()
        # crest outline
        ctx.new_path()
        for P, z, h, v in self.bumps(st):
            if v >= 0: ctx.move_to(*P[0]); ctx.line_to(*P[1]); ctx.line_to(*P[2])
        ctx.set_source_rgba(cc[0], cc[1], cc[2], 0.75); ctx.set_line_width(2.0); ctx.stroke()
        # glowing outlines
        for P in sils:
            stroke_glow(ctx, lambda P=P: _path(ctx, P), c, 4.2, glow=3, glow_alpha=0.2)
        for L in legs:
            if L['z'] >= 0: stroke_glow(ctx, lambda L=L: _path(ctx, L['limb']), c, 3.0, glow=2, glow_alpha=0.16)

    # ------------------------------------------------------------------ helpers for scenes
    def point(self, t, x, th_deg=0.0, depth=0.0):
        """Local (pre-facing) screen point of a body location: x along the body, theta round it."""
        st = self.state(t)
        X, Y, Z = self.surf3(np.array([float(x)]), np.array([math.radians(th_deg)]), out=depth)
        sx, sy, _ = self.xf(st, X, Y, Z)
        f = -1 if self.facing == 'right' else 1
        return (float(sx[0]) * f, float(sy[0]))

    def stomach_point(self, t=0.0):
        st = self.state(t)
        c, a, b, _ = self.g.interp(np.array([-120.0]))
        sx, sy, _ = self.xf(st, np.array([-120.0]), c + 0.25 * a, np.zeros(1))
        return (float(sx[0]) * (-1 if self.facing == 'right' else 1), float(sy[0]))

    def jaw_tip(self, t=0.0):
        """Screen point (local) between the jaw tips — for things held in the mouth."""
        st = self.state(t)
        X, Y, Z = self.surf3(np.array([-470.0]), np.array([1.6]))
        a = self.xf(st, X, Y, Z, 0.0); b = self.xf(st, X, Y, Z, 1.0)
        f = -1 if self.facing == 'right' else 1
        return (float(a[0][0] + b[0][0]) / 2 * f, float(a[1][0] + b[1][0]) / 2)


class CrocTop(Croc):
    """Top-down crocodile (lurking / swimming): back armour rows, eyes on top, legs splayed,
    tail sweeping side to side. CrocTop(swim=1, turn=0 (bend), legs='sprawl'|True, ...) — faces LEFT."""
    def __init__(self, **kw):
        kw.setdefault('roll', -90.0); kw.setdefault('legs', 'sprawl'); kw.setdefault('swim', 1.0)
        super().__init__(**kw)


class CrocHead(Croc):
    """Big close-up profile head: jaw/teeth/sensory-dome shots. Origin = mid-head (x=-400 on the body),
    so the neck and body run off to the right (facing left). CrocHead(jaw=deg|K, domes=True, dome_glow=0..1|K,
    breathe=1). Use scale 2–4."""
    def __init__(self, domes=True, breathe=1.0, **kw):
        kw.setdefault('swim', 0.0); kw.setdefault('tooth_scale', 1.1); kw.setdefault('legs', True)
        kw.setdefault('outline', 4.0)
        super().__init__(domes=domes, **kw)
        self.breathe = breathe
    def draw(self, ctx, t):
        ctx.save()
        f = -1 if self.facing == 'right' else 1
        ctx.translate(400 * f, 6 + 2.0 * self.breathe * math.sin(TAU * t / 3.4))
        ctx.rotate(math.radians(0.6 * self.breathe * math.sin(TAU * t / 5.0)) * f)
        super().draw(ctx, t)
        ctx.restore()


class Hatchling(Croc):
    """Baby crocodile: yellow-tan with black bands, big eyes, smaller crest. Same params as Croc."""
    def __init__(self, **kw):
        kw.setdefault('palette', 'hatchling'); kw.setdefault('eye_scale', 1.55); kw.setdefault('period', 1.6)
        kw.setdefault('tooth_scale', 0.6)
        super().__init__(**kw)
    def bumps(self, st):
        return [b for b in super().bumps(st) if b[2] > 6.6]


# ----------------------------------------------------------------------------- head-on
class CrocHeadOn(Element):
    """Front view toward the lens (camera just above the water line): wide flat head with the
    interlocking tooth line across the front, eye domes on the back corners, nostril dome on the
    snout, body hump with keels, sprawled front legs and a swaying tail behind.
    CrocHeadOn(jaw=0..1|K, bob=1, eyes_glow=0..1|K, legs=True, outline=6). ~640 units wide (legs),
    head ~340; origin = centre of the jaw line."""
    def __init__(self, jaw=0.0, bob=1.0, eyes_glow=0.0, legs=True, outline=6.0, **kw):
        super().__init__(**kw)
        self.jaw, self.bob, self.eyes_glow, self.legs, self.ow = jaw, bob, eyes_glow, legs, outline
        JL = [(-170, -4), (-142, 20), (-100, 47), (-52, 66), (0, 72), (52, 66), (100, 47), (142, 20), (170, -4)]
        self.JL = catmull(JL, 8)
        r = rng(4)
        self.up_t = [(f, r.uniform(9, 17) * (1.35 if abs(abs(f) - 0.62) < 0.07 else 1)) for f in np.linspace(-0.95, 0.95, 21)]
        self.lo_t = [(f, r.uniform(8, 14) * (1.5 if abs(abs(f) - 0.42) < 0.06 else 1)) for f in np.linspace(-0.9, 0.9, 18)]

    def _along(self, P, f):
        """Point + tangent at parameter f in [-1,1] along polyline P (by x)."""
        x = f * 168
        i = int(np.clip(np.searchsorted(P[:, 0], x), 1, len(P) - 1))
        p0, p1 = P[i - 1], P[i]
        k = (x - p0[0]) / max(1e-6, p1[0] - p0[0])
        return p0 + (p1 - p0) * k

    def draw(self, ctx, t):
        Pl = PALETTES['adult']
        back, back_dk, flank, belly = hexc(Pl['back']), hexc(Pl['back_dk']), hexc(Pl['flank']), hexc(Pl['belly'])
        k = float(np.clip(ev(self.jaw, t), 0, 1)); eg = float(ev(self.eyes_glow, t))
        ow = self.ow
        ctx.save()
        ctx.translate(3 * math.sin(TAU * t / 4.2) * self.bob, 3 * math.sin(TAU * t / 3.1) * self.bob)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        def fill_out(col, w=ow):
            ctx.set_source_rgba(*col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(w); ctx.stroke()
        lift = 34 * k                      # upper head tips up a little as the jaw opens
        # ---- tail swaying behind
        sw = math.sin(TAU * t / 2.6)
        tail = catmull([(40, -140), (70 + 20 * sw, -180), (90 + 50 * sw, -212), (100 + 90 * sw, -230)], 6)
        left = tail + np.array([[-26, 0]]) * np.linspace(1, 0.1, len(tail))[:, None]
        right = tail + np.array([[26, 0]]) * np.linspace(1, 0.1, len(tail))[:, None]
        _path(ctx, np.vstack([left, right[::-1]])); fill_out(mix(back, '#000000', 0.15))
        # ---- body hump
        body = catmull([(-262, 30), (-240, -50), (-176, -118), (-84, -150), (0, -156), (84, -150), (176, -118), (240, -50), (262, 30)], 8)
        _path(ctx, body); fill_out(back)
        ctx.save(); _path(ctx, body); ctx.clip()
        g = cairo.LinearGradient(0, -132, 0, 20); g.add_color_stop_rgba(0, 0.75, 0.82, 0.6, 0.18); g.add_color_stop_rgba(1, 0, 0, 0, 0.25)
        ctx.set_source(g); ctx.paint(); ctx.restore()
        for row, (yy, sc) in enumerate(((-152, 0.55), (-142, 0.7), (-128, 0.85), (-112, 1.0))):
            for xx in (-78, -40, 40, 78):
                x = xx * (0.6 + 0.4 * sc); y = yy + abs(xx) * 0.08
                ctx.move_to(x - 9 * sc, y + 2); ctx.line_to(x, y - 13 * sc); ctx.line_to(x + 9 * sc, y + 2); ctx.close_path()
                fill_out(mix(back, '#000000', 0.18), 2.4)
        # ---- front legs (sprawled)
        if self.legs:
            for s in (1, -1):
                st_ = 4 * math.sin(TAU * t / 3.3 + (0 if s > 0 else 1.5))
                sh, el, wr = np.array([200 * s, 0]), np.array([292 * s, -28 + st_]), np.array([316 * s, 62])
                ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*wr)
                set_col(ctx, OUT); ctx.set_line_width(46 + 2 * ow); ctx.stroke()
                ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*wr)
                ctx.set_source_rgba(*hexc(Pl['leg'])); ctx.set_line_width(46); ctx.stroke()
                for j in range(5):
                    a = math.radians(-60 + j * 30) if s > 0 else math.radians(240 - j * 30)
                    tip = wr + np.array([math.cos(a) * 30 * s * s, 18 + abs(math.sin(a)) * 6]) + np.array([(j - 2) * 11 * s, 0])
                    ctx.move_to(*wr); ctx.line_to(*tip); set_col(ctx, OUT); ctx.set_line_width(15); ctx.stroke()
                    ctx.move_to(*wr); ctx.line_to(*tip); ctx.set_source_rgba(*hexc(Pl['leg'])); ctx.set_line_width(10); ctx.stroke()
                    ctx.move_to(*tip); ctx.line_to(tip[0] + (j - 2) * 2, tip[1] + 7); ctx.set_source_rgba(0.86, 0.8, 0.62, 1); ctx.set_line_width(3); ctx.stroke()
        # ---- jaw geometry
        JL = self.JL.copy()
        JU = JL.copy(); JU[:, 1] -= lift * (1 - (JU[:, 0] / 175) ** 2) + 4 * k
        drop = k * (125 * (1 - (JL[:, 0] / 178) ** 2) + 10)
        LJ = JL.copy(); LJ[:, 1] += drop
        LE = LJ.copy(); LE[:, 1] += 30; LE[:, 0] *= 0.95
        UE = JU.copy(); UE[:, 1] -= 26; UE[:, 0] *= 0.985
        # lower jaw (behind upper)
        _path(ctx, np.vstack([LJ, LE[::-1]])); fill_out(belly)
        ctx.save(); _path(ctx, np.vstack([LJ, LE[::-1]])); ctx.clip()
        ctx.set_source_rgba(*hexc(Pl['flank'])); _path(ctx, np.vstack([LJ, (LJ + LE) / 2 + np.array([[0, -4]])][::-1] if False else np.vstack([LJ, ((LJ + LE) / 2 - np.array([[0, 6]]))[::-1]]))); ctx.fill()
        ctx.restore()
        if k > 0.01:
            M = np.vstack([JU, LJ[::-1]])
            _path(ctx, M)
            cy = float((JU[:, 1].mean() + LJ[:, 1].mean()) / 2) + 10
            rg = cairo.RadialGradient(0, cy - 10, 5, 0, cy, 150)
            tc, mc = hexc(Pl['throat']), hexc(Pl['mouth'])
            rg.add_color_stop_rgba(0, *mix(tc, '#000000', 0.4)); rg.add_color_stop_rgba(0.35, *tc); rg.add_color_stop_rgba(0.8, *mc); rg.add_color_stop_rgba(1, *mc)
            ctx.set_source(rg); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow * 0.7); ctx.stroke()
            # tongue
            ctx.save(); ctx.translate(0, float(LJ[:, 1].max()) - 18 - 10 * k); ctx.scale(1, 0.32)
            circle(ctx, 0, 0, 92); ctx.set_source_rgba(*mix(mc, '#C99A70', 0.55)); ctx.fill(); ctx.restore()
        # lower teeth (pointing up)
        for f, L in self.lo_t:
            p = self._along(LJ, f); w = L * 0.36
            tip = p + np.array([f * -2, -L * (1 + 0.4 * k)])
            ctx.move_to(p[0] - w, p[1] + 2); ctx.curve_to(p[0] - w * 0.6, p[1] - L * 0.5, tip[0] - 1, tip[1] + 3, *tip)
            ctx.curve_to(tip[0] + 1, tip[1] + 3, p[0] + w * 0.6, p[1] - L * 0.5, p[0] + w, p[1] + 2); ctx.close_path()
            set_col(ctx, '#E9E2CA'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(1.5); ctx.stroke()
        # upper jaw band + head top
        _path(ctx, np.vstack([UE, JU[::-1]])); fill_out(flank)
        top = np.vstack([UE, catmull([(UE[-1, 0], UE[-1, 1]), (162, -70 - lift * 0.3), (124, -100 - lift * 0.4),
                                      (60, -96 - lift * 0.5), (0, -93 - lift * 0.5), (-60, -96 - lift * 0.5),
                                      (-124, -100 - lift * 0.4), (-162, -70 - lift * 0.3), (UE[0, 0], UE[0, 1])], 6)])
        _path(ctx, top); ctx.set_source_rgba(*back); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.LinearGradient(0, -100, 0, 60); g.add_color_stop_rgba(0, 0, 0, 0, 0.18); g.add_color_stop_rgba(0.6, 0.78, 0.84, 0.62, 0.12); g.add_color_stop_rgba(1, 0.78, 0.84, 0.62, 0.22)
        ctx.set_source(g); ctx.paint()
        # preorbital ridges + scale ticks
        for s in (1, -1):
            ctx.move_to(82 * s, -84 - lift * 0.45); ctx.curve_to(52 * s, -10, 38 * s, 10, 24 * s, 36 - lift * 0.6)
        ctx.set_source_rgba(0.08, 0.1, 0.06, 0.4); ctx.set_line_width(2.4); ctx.stroke()
        rr = rng(9)
        for _ in range(40):
            x = rr.uniform(-140, 140); y = rr.uniform(-85, 40)
            ctx.move_to(x, y - lift * 0.4); ctx.line_to(x + rr.uniform(-4, 4), y + 6 - lift * 0.4)
        ctx.set_source_rgba(0.08, 0.1, 0.06, 0.22); ctx.set_line_width(1.4); ctx.stroke()
        ctx.restore()
        set_col(ctx, OUT); ctx.set_line_width(ow); _path(ctx, top); ctx.stroke()
        # upper teeth (hanging)
        for f, L in self.up_t:
            p = self._along(JU, f); w = L * 0.34
            tip = p + np.array([f * 2, L])
            ctx.move_to(p[0] - w, p[1] - 2); ctx.curve_to(p[0] - w * 0.6, p[1] + L * 0.5, tip[0] - 1, tip[1] - 3, *tip)
            ctx.curve_to(tip[0] + 1, tip[1] - 3, p[0] + w * 0.6, p[1] + L * 0.5, p[0] + w, p[1] - 2); ctx.close_path()
            set_col(ctx, '#F1EBD6'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(1.5); ctx.stroke()
        # nostril dome
        ny = 30 - lift * 0.75
        ctx.save(); ctx.translate(0, ny); ctx.scale(1, 0.5); circle(ctx, 0, 0, 26); ctx.restore()
        fill_out(mix(back, '#8C9670', 0.15), 3)
        for s in (1, -1):
            ctx.save(); ctx.translate(8 * s, ny); ctx.rotate(0.5 * s); ctx.scale(1.0, 0.55); circle(ctx, 0, 0, 5)
            ctx.restore()
        ctx.set_source_rgba(0.04, 0.04, 0.03, 0.95); ctx.fill()
        # eye domes
        bl = ((t + 0.7) % 4.6) > 4.48
        for s in (1, -1):
            ex, ey = 120 * s, -100 - lift * 0.45
            ctx.save(); ctx.translate(ex, ey)
            ctx.move_to(-34, 10); ctx.curve_to(-32, -22, -14, -34, 0, -34); ctx.curve_to(14, -34, 32, -22, 34, 10); ctx.close_path()
            fill_out(back)
            r = 13
            circle(ctx, 0, -6, r + 3.5); ctx.set_source_rgba(*back_dk); ctx.fill()
            circle(ctx, 0, -6, r); set_col(ctx, Pl['iris']); ctx.fill()
            ctx.save(); ctx.translate(0, -6); ctx.scale(0.22, 1); circle(ctx, 0, 0, r * 0.8); set_col(ctx, '#050505'); ctx.fill(); ctx.restore()
            lid = -6 - r * 0.25 if not bl else -6 + r
            ctx.move_to(-r - 3, lid); ctx.curve_to(-4, lid + 4, 4, lid + 4, r + 3, lid); ctx.line_to(r + 3, -6 - r - 4); ctx.line_to(-r - 3, -6 - r - 4); ctx.close_path()
            ctx.set_source_rgba(*back); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(2.2); ctx.stroke()
            if eg > 0:
                rg = cairo.RadialGradient(0, -6, 0, 0, -6, 46)
                rg.add_color_stop_rgba(0, 1, 0.72, 0.3, 0.9 * eg); rg.add_color_stop_rgba(0.35, 1, 0.55, 0.2, 0.45 * eg); rg.add_color_stop_rgba(1, 1, 0.5, 0.2, 0)
                ctx.set_source(rg); circle(ctx, 0, -6, 46); ctx.fill()
            circle(ctx, 0, -6, r); set_col(ctx, OUT); ctx.set_line_width(2.4); ctx.stroke()
            ctx.restore()
        ctx.restore()


# ----------------------------------------------------------------------------- eyes at the surface
class CrocEyes(Element):
    """Just the eyes + nostrils breaking a waterline (local y=0), with expanding ripples and a faint
    dark body shape under the surface. CrocEyes(view='side'|'front', ripples=True, body=True,
    eyeshine=0..1|K (orange night eye-shine), drift=1, water='#2B4A3E'). ~300 units long at scale 1."""
    def __init__(self, view='side', ripples=True, body=True, eyeshine=0.0, drift=1.0, water='#2B4A3E', **kw):
        super().__init__(**kw)
        self.view, self.ripples, self.body, self.eyeshine, self.drift, self.water = view, ripples, body, eyeshine, drift, water

    def draw(self, ctx, t):
        P = PALETTES['adult']
        bob = 1.6 * math.sin(TAU * t / 2.7)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        es = float(ev(self.eyeshine, t))
        # ripples (behind)
        if self.ripples:
            for k in range(3):
                ph = ((t / 2.4) + k / 3) % 1.0
                rx = 60 + ph * 260; ry = rx * 0.11
                for cx in ((-170, 0) if self.view == 'side' else (0,)):
                    ctx.save(); ctx.translate(cx * 0.5 + 0, 3); ctx.scale(1, ry / rx)
                    circle(ctx, cx * 0.5, 0, rx); ctx.restore()
                    ctx.set_source_rgba(0.88, 0.95, 0.92, 0.45 * (1 - ph)); ctx.set_line_width(2.2); ctx.stroke()
        if self.body:
            wc = hexc(self.water)
            ctx.save(); ctx.translate(120, 46); ctx.scale(1, 0.16)
            rg = cairo.RadialGradient(0, 0, 0, 0, 0, 420)
            rg.add_color_stop_rgba(0, 0.03, 0.06, 0.04, 0.45); rg.add_color_stop_rgba(1, 0.03, 0.06, 0.04, 0)
            ctx.set_source(rg); circle(ctx, 0, 0, 420); ctx.fill(); ctx.restore()
        ctx.save(); ctx.translate(0, bob)
        ctx.rectangle(-600, -200, 1200, 200); ctx.clip()          # only what is above the surface
        back = hexc(P['back'])
        def bump(cx, w, h):
            ctx.move_to(cx - w, 4); ctx.curve_to(cx - w * 0.7, -h * 0.9, cx - w * 0.25, -h, cx, -h)
            ctx.curve_to(cx + w * 0.3, -h, cx + w * 0.75, -h * 0.85, cx + w, 4); ctx.close_path()
        if self.view == 'side':
            shapes = [(-170, 26, 13), (-12, 40, 34), (20, 38, 30)]
        else:
            shapes = [(-46, 34, 32), (46, 34, 32), (0, 26, 10)]
        for cx, w, h in shapes:
            bump(cx, w, h); ctx.set_source_rgba(*back); ctx.fill_preserve()
            ctx.save(); ctx.clip()
            ctx.rectangle(cx - w, -h, w * 2, h * 0.35); ctx.set_source_rgba(0.75, 0.8, 0.6, 0.18); ctx.fill()
            ctx.restore()
            set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        # eyes
        eyes = [(-6, -18), (26, -15)] if self.view == 'side' else [(-46, -16), (46, -16)]
        bl = ((t % 5.0) > 4.85)
        for ex, ey in eyes:
            r = 9
            circle(ctx, ex, ey, r + 2.5); set_col(ctx, P['back_dk']); ctx.fill()
            circle(ctx, ex, ey, r); set_col(ctx, P['iris']); ctx.fill()
            ctx.save(); ctx.translate(ex, ey); ctx.scale(0.22, 1); circle(ctx, 0, 0, r * 0.8); set_col(ctx, '#050505'); ctx.fill(); ctx.restore()
            lid = -r * 0.3 if not bl else r
            ctx.rectangle(ex - r - 3, ey - r - 4, 2 * r + 6, lid + r + 4); set_col(ctx, P['back']); ctx.fill()
            ctx.move_to(ex - r - 1, ey + lid); ctx.curve_to(ex - 3, ey + lid + 2, ex + 3, ey + lid + 2, ex + r + 1, ey + lid)
            set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()
            circle(ctx, ex, ey, r); set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()
            if es > 0:
                rg = cairo.RadialGradient(ex, ey, 0, ex, ey, 34)
                rg.add_color_stop_rgba(0, 1, 0.72, 0.3, 0.95 * es); rg.add_color_stop_rgba(0.3, 1, 0.55, 0.2, 0.5 * es)
                rg.add_color_stop_rgba(1, 1, 0.5, 0.2, 0)
                ctx.set_source(rg); circle(ctx, ex, ey, 34); ctx.fill()
        # nostrils
        nx = -170 if self.view == 'side' else 0
        ctx.save(); ctx.translate(nx, -9); ctx.scale(1.5, 0.7)
        circle(ctx, -3, 0, 3); circle(ctx, 5, 0, 3); ctx.set_source_rgba(0.04, 0.04, 0.03, 0.95); ctx.fill(); ctx.restore()
        ctx.restore()
        # surface line through the bumps + glints
        ctx.move_to(-260, 3 + bob * 0.3); ctx.line_to(260, 3 + bob * 0.3)
        ctx.set_source_rgba(0.9, 0.96, 0.93, 0.0); ctx.stroke()
