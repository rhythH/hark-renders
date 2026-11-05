"""Core: colours, easing, keyframe tracks, elements, camera, shots.

All drawing happens in DESIGN units: a 1920x1080 canvas. Preview renders just
scale the cairo context, so scene code never thinks about resolution.
"""
import math, random
import cairocffi as cairo
import numpy as np

W, H = 1920, 1080
FPS = 30
TAU = math.tau

# --------------------------------------------------------------------------- colours
def hexc(h, a=1.0):
    """'#RRGGBB' -> (r,g,b,a) floats. Tuples pass through."""
    if isinstance(h, (tuple, list)):
        return tuple(h) if len(h) == 4 else (h[0], h[1], h[2], a)
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

def mix(c1, c2, k):
    c1, c2 = hexc(c1), hexc(c2)
    return tuple(a + (b - a) * k for a, b in zip(c1, c2))

def with_alpha(c, a):
    c = hexc(c)
    return (c[0], c[1], c[2], c[3] * a)

class PAL:
    """House palette (Style Bible section 4 + measured humpback values)."""
    RED = '#D73F3C'; RED_DARK = '#AB2C24'
    ORANGE = '#F0A54A'; ORANGE_HI = '#FEB959'
    WHITE = '#F2F0EB'; WHITE_V1 = '#E6E1D7'
    GREY = '#9CA2A1'
    GREEN = '#4DB271'; GREEN_LT = '#76D0AC'
    CYAN = '#7FC1CB'; CYAN_HI = '#B6E8F3'; CYAN_DK = '#458B9A'
    SONAR = '#17A734'; SONAR_BG = '#000503'
    PAPER = '#EDE6CF'; PAPER2 = '#F3F0E7'; INK = '#2A2F30'
    BOARD = '#0B2530'; BOARD_GRID = '#123441'
    PILL = (0.04, 0.06, 0.075, 0.86)
    OUTLINE = '#0A0D10'
    YELLOW = '#E8B32A'

# --------------------------------------------------------------------------- easing
def _clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def _bezier_ease(x1, y1, x2, y2):
    """CSS-style cubic-bezier easing f(x)->y."""
    def f(x):
        if x <= 0: return 0.0
        if x >= 1: return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(22):
            m = (lo + hi) / 2
            bx = 3 * (1 - m) ** 2 * m * x1 + 3 * (1 - m) * m * m * x2 + m ** 3
            if bx < x: lo = m
            else: hi = m
        m = (lo + hi) / 2
        return 3 * (1 - m) ** 2 * m * y1 + 3 * (1 - m) * m * m * y2 + m ** 3
    return f

# After Effects "70% influence" easy-ease == cubic-bezier(0.7,0,0.3,1)
EASES = {
    'linear': lambda x: x,
    'eio': _bezier_ease(0.70, 0.0, 0.30, 1.0),     # ease-in-out, 70% influence (AE easy ease)
    'eio66': _bezier_ease(0.66, 0.0, 0.34, 1.0),
    'eo': _bezier_ease(0.0, 0.0, 0.30, 1.0),       # ease-out (graphics, bars, strike-through)
    'ei': _bezier_ease(0.70, 0.0, 1.0, 1.0),       # ease-in (accelerate, e.g. toward lens)
    'eo3': lambda x: 1 - (1 - x) ** 3,
    'ei2': lambda x: x * x,
    'sine': lambda x: 0.5 - 0.5 * math.cos(math.pi * x),
    'hold': lambda x: 0.0,                          # stays at the start value until next key
    'back': lambda x: 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2,  # small overshoot (badges only)
}

def ease(name_or_fn, x):
    f = EASES[name_or_fn] if isinstance(name_or_fn, str) else name_or_fn
    return f(_clamp(x))

def lerp(a, b, k):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * k for x, y in zip(a, b))
    return a + (b - a) * k

def remap(t, t0, t1, v0=0.0, v1=1.0, e='linear'):
    """Map time t in [t0,t1] -> [v0,v1] with easing, clamped."""
    if t1 == t0: k = 1.0 if t >= t1 else 0.0
    else: k = ease(e, (t - t0) / (t1 - t0))
    return lerp(v0, v1, k)

# --------------------------------------------------------------------------- keyframes
class Track:
    """Keyframed property. keys: (t, value[, ease]) — ease applies to the
    segment that *starts* at that key. Values: number, tuple, or '#hex' colour."""
    def __init__(self, *keys):
        ks = []
        for k in keys:
            t, v = k[0], k[1]
            e = k[2] if len(k) > 2 else 'eio'
            if isinstance(v, str): v = hexc(v)
            ks.append((float(t), v, e))
        ks.sort(key=lambda k: k[0])
        self.keys = ks

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]: return ks[0][1]
        if t >= ks[-1][0]: return ks[-1][1]
        for i in range(len(ks) - 1):
            t0, v0, e = ks[i]
            t1, v1, _ = ks[i + 1]
            if t0 <= t <= t1:
                return lerp(v0, v1, ease(e, (t - t0) / (t1 - t0)))
        return ks[-1][1]

def K(*keys):
    """Shorthand: K((0, 0), (1.2, 100, 'eo'))."""
    return Track(*keys)

def ev(p, t):
    """Evaluate a property: constant, Track, or callable(t)."""
    if isinstance(p, Track): return p(t)
    if callable(p): return p(t)
    return p

# --------------------------------------------------------------------------- elements
class Element:
    """Base drawable. Override draw(ctx, t) and draw in LOCAL coords.

    pos, scale, rot (degrees), opacity, color may each be a constant, a Track
    (K(...)) or a callable f(t). `scale` may be a number or (sx, sy).
    t0/t1: visibility window in shot time; the element's local time is t - t0.
    """
    def __init__(self, pos=(0, 0), scale=1.0, rot=0.0, opacity=1.0, t0=0.0, t1=None,
                 color=None, anchor=(0, 0), children=None, layer='mid', z=0, **kw):
        self.pos, self.scale, self.rot, self.opacity = pos, scale, rot, opacity
        self.t0, self.t1, self.color, self.anchor = t0, t1, color, anchor
        self.children = list(children or [])
        self.layer, self.z = layer, z
        self.procs = []          # per-frame callables f(el, t) -> dict of prop overrides
        for k, v in kw.items(): setattr(self, k, v)

    def add(self, *els):
        self.children.extend(els); return self

    def proc(self, fn):
        """Attach a procedural motion fn(el, lt) -> dict(pos=..., rot=..., ...) offsets
        ('dpos','drot','dscale') or absolute overrides."""
        self.procs.append(fn); return self

    def visible(self, t):
        if t < self.t0: return False
        if self.t1 is not None and t >= self.t1: return False
        return True

    def props(self, lt):
        pos = ev(self.pos, lt); sc = ev(self.scale, lt); rot = ev(self.rot, lt)
        op = ev(self.opacity, lt)
        for fn in self.procs:
            d = fn(self, lt) or {}
            if 'pos' in d: pos = d['pos']
            if 'dpos' in d: pos = (pos[0] + d['dpos'][0], pos[1] + d['dpos'][1])
            if 'rot' in d: rot = d['rot']
            if 'drot' in d: rot = rot + d['drot']
            if 'scale' in d: sc = d['scale']
            if 'dscale' in d:
                sc = (sc * d['dscale']) if not isinstance(sc, tuple) else (sc[0] * d['dscale'], sc[1] * d['dscale'])
            if 'opacity' in d: op = d['opacity']
        return pos, sc, rot, op

    def render(self, ctx, t):
        if not self.visible(t): return
        lt = t - self.t0
        pos, sc, rot, op = self.props(lt)
        if op <= 0.002: return
        ctx.save()
        ctx.translate(pos[0], pos[1])
        if rot: ctx.rotate(math.radians(rot))
        if isinstance(sc, tuple): ctx.scale(sc[0], sc[1])
        elif sc != 1: ctx.scale(sc, sc)
        if self.anchor != (0, 0): ctx.translate(-self.anchor[0], -self.anchor[1])
        group = op < 0.999
        if group: ctx.push_group()
        self.draw(ctx, lt)
        for c in sorted(self.children, key=lambda c: c.z):
            c.render(ctx, lt)
        if group:
            ctx.pop_group_to_source(); ctx.paint_with_alpha(op)
        ctx.restore()

    def draw(self, ctx, t):
        pass

class Group(Element):
    pass

class Fn(Element):
    """Element from a plain function: Fn(lambda ctx, t: ..., pos=...)."""
    def __init__(self, fn, **kw):
        super().__init__(**kw); self.fn = fn
    def draw(self, ctx, t):
        self.fn(ctx, t)

# --------------------------------------------------------------------------- drawing helpers
def set_col(ctx, c, alpha=1.0):
    c = hexc(c); ctx.set_source_rgba(c[0], c[1], c[2], c[3] * alpha)

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

def poly(ctx, pts, close=True):
    pts = np.asarray(pts)
    ctx.move_to(float(pts[0, 0]), float(pts[0, 1]))
    for x, y in pts[1:]:
        ctx.line_to(float(x), float(y))
    if close: ctx.close_path()

def catmull(pts, n=12, closed=False):
    """Smooth polyline through control points (centripetal-ish uniform Catmull-Rom)."""
    P = np.asarray(pts, dtype=float)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    ts = np.linspace(0, 1, n, endpoint=False)
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t = ts[:, None]
        seg = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 +
                     (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
        out.append(seg)
    if not closed: out.append(P[-2][None])
    return np.vstack(out)

def circle(ctx, x, y, r):
    ctx.new_sub_path(); ctx.arc(x, y, r, 0, TAU)

def stroke_glow(ctx, path_fn, color, width, glow=3, glow_alpha=0.18):
    """Draw path with a soft glow made of stacked wide low-alpha strokes."""
    c = hexc(color)
    for i in range(glow, 0, -1):
        path_fn(); ctx.set_line_width(width * (1 + i * 2.2))
        ctx.set_source_rgba(c[0], c[1], c[2], glow_alpha / i); ctx.stroke()
    path_fn(); ctx.set_line_width(width); ctx.set_source_rgba(*c); ctx.stroke()

def rng(seed):
    return random.Random(seed)

# --------------------------------------------------------------------------- camera
class Camera:
    """Virtual camera for world layers.

    push: slow linear push in %/s (0.6–1.0 house default)
    drift: (px/s, px/s) slow pan;  wander: amplitude px of slow noise
    Moves: emphasis(), crash(), shake(), handheld() (REC wobble), focus target.
    """
    def __init__(self, push=0.8, drift=(10, -3), wander=6.0, focus=(W / 2, H / 2), seed=1, zoom=1.0):
        self.push, self.drift, self.wander, self.focus0, self.zoom0 = push, drift, wander, focus, zoom
        self.moves = []   # (kind, params)
        self.seed = seed
        r = rng(seed); self.ph = [r.random() * TAU for _ in range(6)]

    def emphasis(self, t0, t1, amount=0.2, target=None, e='eio'):
        """Push +amount (0.15–0.30) over [t0,t1], easing (70% influence), optional re-centre."""
        self.moves.append(('emph', (t0, t1, amount, target, e))); return self

    def crash(self, t0, dur=0.25, amount=1.2, target=None):
        """Fast crash zoom (ease-in) by +amount towards target."""
        self.moves.append(('emph', (t0, t0 + dur, amount, target, 'ei'))); return self

    def pull(self, t0, t1, amount=0.2, e='eio'):
        self.moves.append(('emph', (t0, t1, -amount, None, e))); return self

    def shake(self, t0, amp=14, decay=0.4, freq=26):
        """Decaying shake ±amp px over `decay` s (impacts: 8–20 px)."""
        self.moves.append(('shake', (t0, amp, decay, freq))); return self

    def handheld(self, amp=2.5, freq=1.0, t0=0, t1=1e9):
        """Constant subtle handheld wobble (REC shots)."""
        self.moves.append(('hand', (t0, t1, amp, freq))); return self

    def state(self, t):
        z = self.zoom0 * (1 + self.push / 100.0 * t)
        fx, fy = self.focus0
        ox = self.drift[0] * t + self.wander * math.sin(t * 0.37 + self.ph[0]) + self.wander * 0.5 * math.sin(t * 0.91 + self.ph[1])
        oy = self.drift[1] * t + self.wander * 0.7 * math.sin(t * 0.29 + self.ph[2]) + self.wander * 0.4 * math.sin(t * 0.77 + self.ph[3])
        rot = 0.0
        tx, ty = fx, fy
        for kind, p in self.moves:
            if kind == 'emph':
                t0, t1, amt, target, e = p
                k = remap(t, t0, t1, 0, 1, e)
                z *= (1 + amt * k)
                if target is not None:
                    tx, ty = lerp((tx, ty), target, k)
            elif kind == 'shake':
                t0, amp, decay, freq = p
                if t0 <= t < t0 + decay * 1.6:
                    d = t - t0
                    a = amp * math.exp(-d / (decay / 3.0))
                    ox += a * math.sin(d * freq * TAU / 2 + 1.3)
                    oy += a * math.cos(d * freq * TAU / 2.3 + 0.4)
                    rot += a * 0.02 * math.sin(d * freq * 2)
            elif kind == 'hand':
                t0, t1, amp, freq = p
                if t0 <= t < t1:
                    ox += amp * (math.sin(t * freq * TAU + self.ph[4]) + 0.5 * math.sin(t * freq * 2.7 * TAU))
                    oy += amp * (math.cos(t * freq * 0.83 * TAU + self.ph[5]) + 0.5 * math.sin(t * freq * 2.1 * TAU + 1))
                    rot += amp * 0.06 * math.sin(t * freq * 0.6 * TAU)
        return z, (tx, ty), (ox, oy), rot

    def apply(self, ctx, t, parallax=1.0):
        z, (tx, ty), (ox, oy), rot = self.state(t)
        zp = 1 + (z - 1) * parallax
        ctx.translate(W / 2 - ox * parallax, H / 2 - oy * parallax)
        if rot: ctx.rotate(math.radians(rot * parallax))
        ctx.scale(zp, zp)
        # focus point moves to screen centre, scaled by parallax
        fx = W / 2 + (tx - W / 2) * min(1.0, parallax)
        fy = H / 2 + (ty - H / 2) * min(1.0, parallax)
        ctx.translate(-fx, -fy)

    def matrix(self, t, parallax=1.0):
        c = cairo.Context(_DUMMY)
        self.apply(c, t, parallax)
        return c.get_matrix()

    def to_screen(self, p, t, parallax=1.0):
        """World point -> screen (design px) at shot time t."""
        return self.matrix(t, parallax).transform_point(float(p[0]), float(p[1]))

_DUMMY = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
CUR = {'cam': None, 't': 0.0}

def to_screen(p, parallax=1.0):
    """World -> screen using the camera of the shot currently rendering."""
    cam = CUR['cam']
    return p if cam is None else cam.to_screen(p, CUR['t'], parallax)

class StaticCamera(Camera):
    def __init__(self):
        super().__init__(push=0, drift=(0, 0), wander=0)

# --------------------------------------------------------------------------- shot
LAYERS = ['back', 'mid', 'fg']          # world layers (camera applied)
PARALLAX = {'plate': 0.35, 'back': 0.7, 'mid': 1.0, 'fg': 1.35}

class Shot:
    """One shot = duration + plate + elements on layers + camera + transition in.

    layers: 'back' (parallax .7), 'mid' (1.0), 'fg' (1.35), 'overlay' (screen
    space, no camera). The plate draws first (parallax .35); its vignette is
    drawn after world layers, before the overlay.
    trans_in: None/'cut' | ('dip', 0.7) | ('dissolve', 1.0) | ('ink', 0.6) |
              ('flash', 0.2) | ('lens', 0.8)   — see transitions.py
    """
    def __init__(self, dur, plate=None, camera=None, name='', trans_in=None, overlay_follows_camera=False):
        self.dur, self.plate, self.name = dur, plate, name
        self.camera = camera if camera is not None else Camera()
        self.els = []
        self.trans_in = trans_in
        self.post = []        # screen-space post fns f(ctx, t) (flash frames etc.)
        self.overlay_hand = None
        self.start = None     # filled by Timeline
        self.abs_start = None # optional: pin this shot's global start (word-locked cut)

    def add(self, *els, layer=None):
        for e in els:
            if layer: e.layer = layer
            self.els.append(e)
        return els[0] if len(els) == 1 else els

    def __iadd__(self, el):
        self.add(el); return self

    def render(self, ctx, t):
        cam = self.camera
        CUR['cam'], CUR['t'] = cam, t
        if self.plate is not None:
            self.plate.draw_bg(ctx, t, cam)
        for L in LAYERS:
            els = [e for e in self.els if e.layer == L]
            if not els: continue
            ctx.save(); cam.apply(ctx, t, PARALLAX[L])
            for e in sorted(els, key=lambda e: e.z):
                e.render(ctx, t)
            ctx.restore()
        if self.plate is not None:
            self.plate.draw_fg(ctx, t, cam)
        ov = [e for e in self.els if e.layer == 'overlay']
        for e in sorted(ov, key=lambda e: e.z):
            e.render(ctx, t)
        for fn in self.post:
            fn(ctx, t)
