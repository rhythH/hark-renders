"""ORCA rig (killer whale). Side view is the hero; plus head-on, from-below
silhouette, top-down and x-ray/blueprint variants and a breaching pose.

Local coords: body length 1000 units, nose at x≈-490 (faces LEFT by default),
flukes at x≈+510, y down. scale=0.6 -> ~600 px long on the 1920x1080 canvas.

Rig:  swim cycle (head pinned sine wave, period ~3 s, tail ±13 px at scale .6),
      jaw (degrees, keyframable) with interlocking conical teeth, eye blink,
      pectoral flap, fluke pitch, static bend (breach arc), dorsal 'male'/'female'.
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, hexc, mix, set_col, catmull, poly, circle, stroke_glow, TAU, remap, PAL

# ---------------------------------------------------------------- geometry (units)
NOSE = (-492, 19)
HINGE = np.array([-342.0, 12.0])
TOP = [(-492, 19), (-487, 2), (-472, -22), (-442, -49), (-398, -73), (-332, -93), (-250, -107),
       (-150, -115), (-60, -115), (40, -107), (140, -90), (240, -63), (322, -39), (382, -23), (420, -15)]
FLUKE = [(420, -15), (446, -24), (482, -50), (514, -66), (508, -40), (488, -10), (482, 2), (490, 14),
         (510, 44), (514, 66), (480, 50), (446, 22), (420, 12)]
BOTTOM = [(420, 12), (380, 21), (320, 39), (240, 63), (140, 89), (40, 105), (-60, 111), (-150, 105),
          (-240, 90), (-312, 72), (-372, 55), (-422, 42), (-462, 33), (-486, 26), (-492, 21)]
LIP = [(-492, 20), (-462, 21), (-430, 21), (-395, 18), (-366, 15), (-342, 12)]   # nose -> hinge
DORSAL_M = [(-150, -112), (-126, -170), (-108, -245), (-96, -318), (-88, -350), (-72, -352),
            (-58, -300), (-38, -220), (-12, -150), (14, -109)]
DORSAL_F = [(-150, -112), (-118, -168), (-82, -214), (-40, -246), (2, -262), (-6, -236),
            (-14, -196), (-6, -150), (22, -108)]
PEC = [(0, -12), (28, 14), (52, 66), (62, 120), (54, 160), (30, 178), (6, 170), (-12, 138),
       (-22, 80), (-22, 26)]
PEC_ROOT = np.array([-262.0, 66.0])
EYE = np.array([-322.0, -6.0])
EYEPATCH = [(-300, -26), (-276, -44), (-224, -54), (-188, -48), (-214, -30), (-262, -20)]
WHITE = [(-520, 22), (-462, 26), (-420, 30), (-380, 37), (-320, 50), (-262, 66), (-200, 82), (-120, 90),
         (-50, 84), (8, 60), (48, 24), (84, -8), (120, -22), (156, -14), (198, 4), (246, 24), (300, 38),
         (250, 52), (180, 70), (110, 98), (110, 200), (-560, 200), (-560, 22)]
SADDLE_C = (110, -98)

def _sm(pts, n=10):
    return catmull(pts, n)

YS = 1.16
def _ys(pts, k=YS):
    return [(x, y * k) for x, y in pts]
TOP = _ys(TOP); BOTTOM = _ys(BOTTOM); WHITE = _ys(WHITE)
DORSAL_M = [(x, y * YS if i in (0, len(DORSAL_M) - 1) else y - 18) for i, (x, y) in enumerate(DORSAL_M)]
DORSAL_F = [(x, y * YS if i in (0, len(DORSAL_F) - 1) else y - 18) for i, (x, y) in enumerate(DORSAL_F)]
EYEPATCH = [(-322 + (x + 300) * 1.25, -30 + (y + 26) * 1.3) for x, y in EYEPATCH]
SADDLE_C = (110, -112)
PEC_ROOT = np.array([-262.0, 74.0])
PEC_BASE = -0.42

class OrcaGeo:
    """Precomputed smooth polylines."""
    def __init__(self, dorsal='male'):
        self.top = _sm(TOP, 10)
        self.fluke = _sm(FLUKE, 8)
        self.bottom = _sm(BOTTOM, 10)
        self.lip = _sm(LIP, 8)
        self.dorsal = _sm(DORSAL_M if dorsal == 'male' else DORSAL_F, 8)
        self.pec = catmull(PEC, 8, closed=True)
        self.eyepatch = catmull(EYEPATCH, 6, closed=True)
        self.white = np.array(WHITE, float)
        self.white = np.vstack([_sm(WHITE[:19], 8), np.array(WHITE[19:], float)])

_GEO = {}
def geo(dorsal):
    if dorsal not in _GEO: _GEO[dorsal] = OrcaGeo(dorsal)
    return _GEO[dorsal]

# ---------------------------------------------------------------- deformers
def swim_dy(x, t, amp, period, phase0=0.0):
    """Head-pinned travelling sine. amp = tail amplitude (units)."""
    w = np.clip((np.asarray(x) + 150.0) / 660.0, 0, 1) ** 2
    ph = TAU * t / period + phase0
    return amp * w * np.sin(ph - (np.asarray(x) + 150.0) / 700.0 * math.pi * 0.9)

def rot_pts(P, c, a):
    ca, sa = math.cos(a), math.sin(a)
    d = P - c
    return np.column_stack([c[0] + d[:, 0] * ca - d[:, 1] * sa, c[1] + d[:, 0] * sa + d[:, 1] * ca])

class Deform:
    def __init__(self, t, amp, period, bend=0.0, phase0=0.0):
        self.t, self.amp, self.period, self.bend, self.ph = t, amp, period, bend, phase0
        # fluke pitch from tail slope
        x0 = 400.0
        d = (swim_dy(x0 + 5, t, amp, period, phase0) - swim_dy(x0 - 5, t, amp, period, phase0)) / 10.0
        self.fluke_a = math.atan(float(d)) * 1.6 + math.atan(2 * bend * x0 / 500 ** 2) * 0.6
        self.p0 = np.array([x0, float(self.dy(np.array([x0]))[0])])

    def dy(self, x):
        return swim_dy(x, self.t, self.amp, self.period, self.ph) + self.bend * (np.asarray(x) / 500.0) ** 2

    def __call__(self, P, fluke=False):
        P = np.asarray(P, float).copy()
        if fluke:
            P[:, 1] += float(self.dy(np.array([400.0]))[0])
            mask = P[:, 0] > 400
            if mask.any():
                P[mask] = rot_pts(P[mask], self.p0, self.fluke_a)
            return P
        P[:, 1] += self.dy(P[:, 0])
        return P

def jaw_open(P, ang_deg, region=True):
    """Rotate lower-jaw points (x < hinge) about the hinge by ang, blended near hinge."""
    if not ang_deg: return P
    a = -math.radians(ang_deg)
    P = np.asarray(P, float).copy()
    x = P[:, 0]
    w = np.clip((HINGE[0] + 70 - x) / 110.0, 0, 1)
    w = w * w * (3 - 2 * w)
    R = rot_pts(P, HINGE, a)
    return P + (R - P) * w[:, None]

def _path(ctx, P, close=True):
    ctx.move_to(float(P[0, 0]), float(P[0, 1]))
    for x, y in P[1:]:
        ctx.line_to(float(x), float(y))
    if close: ctx.close_path()

def _teeth(ctx, lip_pts, n, size, up, offset, fill='#F4F1E8', edge='#2a1a1a', lw=1.5):
    """Conical teeth along a lip polyline; up=True points toward -y (lower jaw teeth)."""
    L = np.cumsum(np.r_[0, np.hypot(*np.diff(lip_pts, axis=0).T)])
    for i in range(n):
        s = (i + 0.5 + offset) / (n + 0.6) * L[-1] * 0.92 + L[-1] * 0.04
        j = min(np.searchsorted(L, s), len(L) - 1); j = max(j, 1)
        p0, p1 = lip_pts[j - 1], lip_pts[j]
        k = (s - L[j - 1]) / max(1e-6, L[j] - L[j - 1])
        px, py = p0 + (p1 - p0) * k
        tx, ty = (p1 - p0) / max(1e-6, np.hypot(*(p1 - p0)))
        nx, ny = -ty, tx
        if up: nx, ny = -nx, -ny
        sz = size * (0.75 + 0.5 * math.sin(math.pi * (i + 0.5) / n))
        hw = sz * 0.42
        ctx.move_to(px - tx * hw, py - ty * hw)
        ctx.curve_to(px - tx * hw * 0.5 + nx * sz * 0.5, py - ty * hw * 0.5 + ny * sz * 0.5,
                     px + nx * sz * 0.95 - tx * hw * 0.1, py + ny * sz * 0.95 - ty * hw * 0.1,
                     px + nx * sz, py + ny * sz)
        ctx.curve_to(px + nx * sz * 0.9 + tx * hw * 0.2, py + ny * sz * 0.9 + ty * hw * 0.2,
                     px + tx * hw * 0.5 + nx * sz * 0.4, py + ty * hw * 0.5 + ny * sz * 0.4,
                     px + tx * hw, py + ty * hw)
        ctx.close_path()
        set_col(ctx, fill); ctx.fill_preserve()
        set_col(ctx, edge, 0.8); ctx.set_line_width(lw); ctx.stroke()

# ---------------------------------------------------------------- side view
class Orca(Element):
    """Side-view orca.

    Orca(pos=(960,540), scale=0.6, facing='left'|'right', dorsal='male'|'female',
         variant='side'|'xray'|'silhouette', swim=1.0, period=3.0, jaw=0 (deg or K()),
         blink=[times] or 'auto', bend=0 (static arc, + = belly-down curve),
         pec_flap=1.0, outline=8, body='#12171C', glow=True (xray), tint=None)
    Pose presets: Orca.breach(...) returns an orca rotated nose-up, no swim.
    """
    def __init__(self, facing='left', dorsal='male', variant='side', swim=1.0, period=3.0, jaw=0.0,
                 blink='auto', bend=0.0, pec_flap=1.0, outline=8.0, body='#12171C', white='#EEF2F3',
                 tint=None, phase=0.0, sil_color='#061722', xray_color=PAL.CYAN, teeth_closed=True, **kw):
        super().__init__(**kw)
        self.facing, self.dorsal_kind, self.variant = facing, dorsal, variant
        self.swim, self.period, self.jaw, self.blink, self.bend = swim, period, jaw, blink, bend
        self.pec_flap, self.outline, self.body_col, self.white_col = pec_flap, outline, body, white
        self.tint, self.phase, self.sil_color, self.xray_color = tint, phase, sil_color, xray_color
        self.teeth_closed = teeth_closed
        self.g = geo(dorsal)

    @classmethod
    def breach(cls, **kw):
        kw.setdefault('swim', 0.12); kw.setdefault('bend', -18); kw.setdefault('rot', 58 if kw.get('facing', 'left') == 'left' else -58)
        return cls(**kw)

    # -- rig evaluation
    def pose(self, t):
        amp = 22.0 * ev(self.swim, t)
        D = Deform(t, amp, self.period, ev(self.bend, t), self.phase)
        jaw = ev(self.jaw, t)
        g = self.g
        top = D(g.top)
        fl = D(g.fluke, fluke=True)
        bottom = D(jaw_open(g.bottom, jaw))
        lip_u = D(g.lip)
        lip_l = D(jaw_open(g.lip, jaw))
        dorsal = D(g.dorsal)
        flap = PEC_BASE + math.radians(7 * ev(self.pec_flap, t) * math.sin(TAU * t / self.period + self.phase + 1.2))
        pec = rot_pts(g.pec + PEC_ROOT, PEC_ROOT, flap)
        pec = D(pec)
        outline = np.vstack([top, fl[1:], bottom[1:], lip_l[1:], lip_u[::-1][1:-1]])
        return dict(D=D, top=top, fluke=fl, bottom=bottom, lip_u=lip_u, lip_l=lip_l, dorsal=dorsal, pec=pec,
                    outline=outline, jaw=jaw)

    def blink_k(self, t):
        if self.blink == 'auto':
            ph = (t + self.phase * 1.7) % 4.1
            return max(0.0, 1 - abs(ph - 2.0) / 0.07) if abs(ph - 2.0) < 0.07 else 0.0
        if self.blink:
            for b in self.blink:
                if abs(t - b) < 0.08: return 1 - abs(t - b) / 0.08
        return 0.0

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        P = self.pose(t)
        if self.variant == 'xray': self._draw_xray(ctx, t, P)
        elif self.variant == 'silhouette': self._draw_sil(ctx, P)
        else: self._draw_side(ctx, t, P)
        ctx.restore()

    def _body_col(self, c):
        return mix(c, self.tint, 0.55) if self.tint else hexc(c)

    def _draw_side(self, ctx, t, P):
        ow = self.outline
        OUT = PAL.OUTLINE
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        body = self._body_col(self.body_col)
        # dorsal fin (behind body outline so the base merges)
        _path(ctx, P['dorsal'], close=False)
        ctx.line_to(float(P['dorsal'][0, 0]) + 30, float(P['dorsal'][0, 1]) + 40); ctx.close_path()
        ctx.set_source_rgba(*body); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # mouth interior (visible when open)
        jaw = P['jaw']
        if jaw > 0.5:
            mi = np.vstack([P['lip_u'], P['lip_l'][::-1]])
            _path(ctx, mi); set_col(ctx, '#3A1217'); ctx.fill_preserve()
            ctx.save(); ctx.clip()
            # tongue
            ll = P['lip_l']
            cx, cy = ll[len(ll) // 2]
            ctx.save(); ctx.translate(cx + 30, cy - 6); ctx.rotate(-math.radians(jaw) * 0.7); ctx.scale(1.0, 0.42)
            circle(ctx, 0, 0, 70); set_col(ctx, '#B85A62'); ctx.fill(); ctx.restore()
            ctx.restore()
            n = 9
            _teeth(ctx, P['lip_u'][:-3], n, 26, up=False, offset=0.0)
            _teeth(ctx, P['lip_l'][:-3], n, 26, up=True, offset=0.5)
            ctx.new_path()
        # body
        _path(ctx, P['outline'])
        ctx.set_source_rgba(*body); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        # sheen along the back (soft grey highlight, painted)
        g = cairo.LinearGradient(0, -120, 0, 20)
        g.add_color_stop_rgba(0, 0.36, 0.42, 0.48, 0.55); g.add_color_stop_rgba(0.45, 0.25, 0.30, 0.35, 0.18)
        g.add_color_stop_rgba(1, 0.2, 0.25, 0.3, 0)
        ctx.save(); ctx.translate(-150, -60); ctx.scale(1.0, 0.55)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, 360)
        rg.add_color_stop_rgba(0, 0.42, 0.48, 0.55, 0.42); rg.add_color_stop_rgba(0.6, 0.30, 0.36, 0.42, 0.14)
        rg.add_color_stop_rgba(1, 0.3, 0.35, 0.4, 0)
        ctx.set_source(rg); circle(ctx, 0, 0, 360); ctx.fill(); ctx.restore()
        # saddle patch
        D = P['D']
        sx, sy = SADDLE_C[0], SADDLE_C[1] + float(D.dy(np.array([SADDLE_C[0]]))[0])
        ctx.save(); ctx.translate(sx, sy); ctx.scale(1.0, 0.30)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, 130)
        sc = hexc('#7A8590'); rg.add_color_stop_rgba(0, sc[0], sc[1], sc[2], 0.85); rg.add_color_stop_rgba(0.55, sc[0], sc[1], sc[2], 0.55)
        rg.add_color_stop_rgba(1, sc[0], sc[1], sc[2], 0)
        ctx.set_source(rg); circle(ctx, 0, 0, 130); ctx.fill(); ctx.restore()
        # white belly + flank patch
        wp = jaw_open(self.g.white, jaw)
        wp = D(wp)
        _path(ctx, wp)
        wc = hexc(self.white_col)
        g = cairo.LinearGradient(0, -30, 0, 115)
        g.add_color_stop_rgba(0, *wc); g.add_color_stop_rgba(0.75, *mix(wc, '#AFC0C8', 0.35)); g.add_color_stop_rgba(1, *mix(wc, '#8FA3AD', 0.6))
        ctx.set_source(g); ctx.fill()
        # rim light (navy) just inside the top edge
        top = P['top'].copy(); top[:, 1] += 7
        _path(ctx, top[3:-2], close=False)
        ctx.set_source_rgba(0.24, 0.40, 0.56, 0.55); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
        # eye patch
        ep = D(self.g.eyepatch)
        _path(ctx, ep)
        g = cairo.LinearGradient(0, -55, 0, -18)
        g.add_color_stop_rgba(0, *wc); g.add_color_stop_rgba(1, *mix(wc, '#B5C3CA', 0.5))
        ctx.set_source(g); ctx.fill()
        # mouth line + closed teeth hint
        if jaw <= 0.5:
            lu = P['lip_u']
            _path(ctx, lu[1:], close=False)
            set_col(ctx, OUT); ctx.set_line_width(ow * 0.6); ctx.stroke()
            if self.teeth_closed:
                for i, k in enumerate(np.linspace(0.18, 0.72, 6)):
                    j = int(k * (len(lu) - 1)); x, y = lu[j]
                    ctx.move_to(x - 5, y + 1); ctx.line_to(x, y + 9); ctx.line_to(x + 5, y + 1); ctx.close_path()
                    set_col(ctx, '#F4F1E8', 0.95); ctx.fill()
        # body outline
        _path(ctx, P['outline'])
        set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # eye
        ex, ey = EYE[0], EYE[1] + float(D.dy(np.array([EYE[0]]))[0])
        bk = self.blink_k(t)
        ctx.save(); ctx.translate(ex, ey); ctx.scale(1.0, max(0.08, 1 - bk))
        circle(ctx, 0, 0, 9.5); set_col(ctx, '#3D4A55'); ctx.fill()
        circle(ctx, 0, 0, 6.5); set_col(ctx, '#050607'); ctx.fill()
        circle(ctx, -2.5, -2.5, 2.2); set_col(ctx, '#E8EEF0', 0.9); ctx.fill()
        ctx.restore()
        # pectoral (near side, in front)
        pc = P['pec']
        _path(ctx, pc); ctx.set_source_rgba(*body); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.LinearGradient(pc[:, 0].min(), 0, pc[:, 0].max(), 0)
        g.add_color_stop_rgba(0, 0.32, 0.38, 0.44, 0.45); g.add_color_stop_rgba(1, 0.2, 0.25, 0.3, 0)
        ctx.set_source(g); ctx.paint(); ctx.restore()
        _path(ctx, pc); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # tiny v2 line detail: crease behind the jaw + flank seam
        D_ = P['D']
        cr = D_(np.array([[-345.0, 30], [-318, 40], [-296, 46]]))
        _path(ctx, cr, close=False); ctx.set_source_rgba(0.55, 0.62, 0.68, 0.55); ctx.set_line_width(2.4); ctx.stroke()

    def _draw_sil(self, ctx, P):
        _path(ctx, P['dorsal'], close=False)
        ctx.line_to(float(P['dorsal'][0, 0]) + 30, float(P['dorsal'][0, 1]) + 40); ctx.close_path()
        _path(ctx, P['outline']); _path(ctx, P['pec'])
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        set_col(ctx, self.sil_color); ctx.fill()

    def _draw_xray(self, ctx, t, P):
        c = self.xray_color
        cc = hexc(c)
        D = P['D']
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        # translucent fill
        _path(ctx, P['outline']); ctx.set_source_rgba(0.16, 0.38, 0.45, 0.40); ctx.fill()
        _path(ctx, P['dorsal'], close=False); ctx.set_source_rgba(0.14, 0.33, 0.39, 0.22); ctx.fill()
        _path(ctx, P['pec']); ctx.set_source_rgba(0.14, 0.33, 0.39, 0.30); ctx.fill()
        # skeleton (thin, slightly dimmer)
        sk = hexc(PAL.CYAN_HI)
        def S(pts):
            return D(jaw_open(np.array(pts, float), 0))
        # spine
        xs = np.linspace(-290, 430, 60)
        spine = np.column_stack([xs, -38 + 30 * ((xs + 290) / 720) ** 1.4])
        spine = D(spine)
        stroke_glow(ctx, lambda: _path(ctx, spine, False), sk, 4.0, glow=2, glow_alpha=0.16)
        # vertebra ticks
        ctx.set_line_width(3.0); ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.8)
        for i in range(2, 58, 2):
            x, y = spine[i]; ctx.move_to(x, y - 12); ctx.line_to(x, y + 6)
        ctx.stroke()
        # ribs
        for i, x0 in enumerate(np.linspace(-215, 30, 11)):
            y0 = -38 + 30 * ((x0 + 290) / 720) ** 1.4
            L = 120 - abs(i - 4) * 9
            rib = D(np.array([[x0, y0], [x0 + 18, y0 + L * 0.45], [x0 + 12, y0 + L * 0.85], [x0 + 2, y0 + L]]))
            rib = catmull(rib, 6)
            stroke_glow(ctx, lambda r=rib: _path(ctx, r, False), sk, 2.6, glow=1, glow_alpha=0.12)
        # skull + jaw bone
        jaw = P['jaw']
        skull = D(catmull([(-472, 10), (-440, -14), (-390, -36), (-350, -44), (-322, -34), (-330, -12), (-380, 0), (-430, 8)], 6, closed=True))
        stroke_glow(ctx, lambda: _path(ctx, skull), sk, 3.0, glow=2, glow_alpha=0.14)
        jb = D(jaw_open(np.array([(-480, 28), (-420, 34), (-350, 30), (-300, 20)], float), jaw))
        stroke_glow(ctx, lambda: _path(ctx, catmull(jb, 6), False), sk, 3.0, glow=2, glow_alpha=0.14)
        # pectoral bones
        pc = P['pec']; root = pc[0]
        tip = pc[len(pc) // 2]
        for k in (-0.18, -0.06, 0.06, 0.18):
            mid = root + (tip - root) * 0.45
            end = root + (tip - root) * 0.92 + np.array([-(tip - root)[1], (tip - root)[0]]) * k
            stroke_glow(ctx, lambda m=mid, e=end: (ctx.move_to(*root), ctx.line_to(*m), ctx.line_to(*e)), sk, 2.4, glow=1, glow_alpha=0.12)
        # teeth when open
        if jaw > 0.5:
            _teeth(ctx, P['lip_u'][:-3], 9, 24, up=False, offset=0, fill=(cc[0], cc[1], cc[2], 0.35), edge=c, lw=2)
            _teeth(ctx, P['lip_l'][:-3], 9, 24, up=True, offset=0.5, fill=(cc[0], cc[1], cc[2], 0.35), edge=c, lw=2)
        # eye ring + eye patch outline
        ex, ey = EYE[0], EYE[1] + float(D.dy(np.array([EYE[0]]))[0])
        stroke_glow(ctx, lambda: circle(ctx, ex, ey, 10), sk, 2.4, glow=1)
        ep = D(self.g.eyepatch)
        _path(ctx, ep); ctx.set_source_rgba(cc[0], cc[1], cc[2], 0.5); ctx.set_line_width(1.8); ctx.stroke()
        # outlines (bright, glowing)
        stroke_glow(ctx, lambda: _path(ctx, P['outline']), c, 4.5, glow=3, glow_alpha=0.20)
        stroke_glow(ctx, lambda: (_path(ctx, P['dorsal'], False)), c, 4.0, glow=3, glow_alpha=0.18)
        stroke_glow(ctx, lambda: _path(ctx, P['pec']), c, 3.6, glow=2, glow_alpha=0.18)
        if jaw <= 0.5:
            stroke_glow(ctx, lambda: _path(ctx, P['lip_u'][1:], False), c, 3.0, glow=1)

def orca_silhouette_path(ctx, dorsal='male'):
    """Adds a static side silhouette path (body+dorsal+pectoral) at origin, facing left."""
    o = Orca(dorsal=dorsal, swim=0)
    P = o.pose(0)
    _path(ctx, P['dorsal'], close=False)
    ctx.line_to(float(P['dorsal'][0, 0]) + 30, float(P['dorsal'][0, 1]) + 40); ctx.close_path()
    _path(ctx, P['outline']); _path(ctx, P['pec'])

# ---------------------------------------------------------------- ventral / dorsal outline (below + top-down)
_VB = None
def _ventral_shape():
    """Half-outline of the body seen from above/below (nose at -500, y>0 half)."""
    half = [(-500, 0), (-492, 26), (-460, 62), (-400, 98), (-300, 122), (-180, 130), (-60, 124), (60, 108),
            (180, 82), (300, 50), (390, 26), (430, 16)]
    return catmull(half, 8)

class OrcaBelow(Element):
    """Seen from below (dark silhouette against the bright surface), or with
    real colours (white belly) when colored=True. Faces left. Flukes beat by
    foreshortening; pectorals flap. Defocus via `soft` (0..1)."""
    def __init__(self, colored=False, period=3.0, color='#05151F', outline=0, **kw):
        super().__init__(**kw)
        self.colored, self.period, self.color, self.ow = colored, period, color, outline

    def outline_pts(self, t):
        half = _ventral_shape()
        top = half.copy(); top[:, 1] *= -1
        k = math.sin(TAU * t / self.period)
        fl_half = np.array([(430, 16), (450, 60), (490, 150), (530, 190), (545, 170), (520, 90), (505, 0)])
        fl_half = catmull(fl_half, 6)
        fsc = 0.75 + 0.25 * k   # foreshortening of the flukes as they beat
        fl = fl_half.copy(); fl[:, 1] *= fsc; fl[:, 0] = 430 + (fl[:, 0] - 430) * (0.9 + 0.1 * k)
        fl_t = fl[::-1].copy(); fl_t[:, 1] *= -1
        pts = np.vstack([half, fl, fl_t, top[::-1]])
        return pts

    def pec_pts(self, t, side):
        """Paddle sticking out sideways and swept back (side=+1 lower half, -1 upper half)."""
        sweep = 40 + 7 * math.sin(TAU * t / self.period + 1)
        pad = catmull([(0, -26), (60, -34), (130, -30), (178, -12), (190, 12), (170, 32), (110, 34), (50, 28), (0, 24)], 6, closed=True)
        pad = rot_pts(pad, np.array([0.0, 0.0]), math.radians(90 - sweep))
        pad[:, 1] *= side
        return pad + np.array([-250.0, 96.0 * side])

    def draw(self, ctx, t):
        body = self.outline_pts(t)
        for side in (1, -1):
            _path(ctx, self.pec_pts(t, side))
            set_col(ctx, self.color if not self.colored else '#12171C'); ctx.fill()
        _path(ctx, body)
        if not self.colored:
            set_col(ctx, self.color); ctx.fill(); return
        set_col(ctx, '#12171C'); ctx.fill_preserve(); ctx.save(); ctx.clip()
        belly = catmull([(-490, 0), (-440, 40), (-320, 62), (-200, 46), (-80, 30), (20, 40), (120, 60), (220, 40),
                         (300, 10), (220, -40), (120, -60), (20, -40), (-80, -30), (-200, -46), (-320, -62), (-440, -40)], 6, closed=True)
        _path(ctx, belly); set_col(ctx, '#EEF2F3'); ctx.fill(); ctx.restore()
        _path(ctx, body); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(7); ctx.stroke()

class OrcaTop(OrcaBelow):
    """Top-down orca: black back, grey saddle, white eye-patch slivers, dorsal ridge."""
    def draw(self, ctx, t):
        body = self.outline_pts(t)
        for side in (1, -1):
            _path(ctx, self.pec_pts(t, side)); set_col(ctx, '#12171C'); ctx.fill_preserve()
            set_col(ctx, PAL.OUTLINE); ctx.set_line_width(6); ctx.stroke()
        _path(ctx, body); set_col(ctx, '#12171C'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        # eye patch slivers at the sides
        for side in (1, -1):
            ep = catmull([(-330, 100 * side), (-260, 118 * side), (-200, 126 * side), (-230, 140 * side), (-320, 130 * side)], 5, closed=True)
            _path(ctx, ep); set_col(ctx, '#EEF2F3'); ctx.fill()
            fp = catmull([(60, 108 * side), (160, 90 * side), (240, 70 * side), (180, 110 * side), (80, 130 * side)], 5, closed=True)
            _path(ctx, fp); set_col(ctx, '#DDE4E7'); ctx.fill()
        # saddle
        ctx.save(); ctx.translate(90, 0); ctx.scale(1, 0.7)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, 140)
        rg.add_color_stop_rgba(0, 0.48, 0.52, 0.57, 0.9); rg.add_color_stop_rgba(1, 0.48, 0.52, 0.57, 0)
        ctx.set_source(rg); circle(ctx, 0, 0, 140); ctx.fill(); ctx.restore()
        # back sheen
        g = cairo.LinearGradient(0, -130, 0, 130)
        g.add_color_stop_rgba(0, 0.3, 0.36, 0.42, 0); g.add_color_stop_rgba(0.5, 0.35, 0.4, 0.46, 0.16); g.add_color_stop_rgba(1, 0.3, 0.36, 0.42, 0)
        ctx.set_source(g); ctx.paint()
        ctx.restore()
        # dorsal fin ridge (seen edge-on from above)
        ctx.move_to(-140, 0); ctx.curve_to(-80, -6, -20, -6, 20, 0); ctx.curve_to(-20, 6, -80, 6, -140, 0)
        set_col(ctx, '#05080A'); ctx.fill()
        ctx.move_to(-140, -1); ctx.curve_to(-80, -5, -30, -4, 15, -1)
        ctx.set_source_rgba(0.5, 0.6, 0.7, 0.6); ctx.set_line_width(2); ctx.stroke()
        _path(ctx, body); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(7); ctx.stroke()

# ---------------------------------------------------------------- head-on
class OrcaHeadOn(Element):
    """Front view, coming at the camera. jaw 0..1 opens the mouth (teeth rows).
    Animate `scale` with an ease-in for the toward-lens move. Faces the lens,
    slightly from below so the white chin reads."""
    def __init__(self, jaw=0.0, dorsal='male', bob=1.0, **kw):
        super().__init__(**kw); self.jaw, self.dorsal, self.bob = jaw, dorsal, bob

    @staticmethod
    def _head(ctx):
        # bullet-shaped: narrow rounded melon on top, broad jowls, flat-ish chin
        ctx.move_to(0, -190)
        ctx.curve_to(70, -190, 128, -150, 160, -80)
        ctx.curve_to(190, -10, 205, 60, 196, 112)
        ctx.curve_to(184, 168, 110, 196, 0, 198)
        ctx.curve_to(-110, 196, -184, 168, -196, 112)
        ctx.curve_to(-205, 60, -190, -10, -160, -80)
        ctx.curve_to(-128, -150, -70, -190, 0, -190); ctx.close_path()

    def draw(self, ctx, t):
        OUT = PAL.OUTLINE; ow = 7
        BODY = '#12171C'; WH = '#EEF2F3'
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        b = self.bob * 6 * math.sin(TAU * t / 3.0)
        ctx.translate(0, b)
        jaw = ev(self.jaw, t)
        h = 360 if self.dorsal == 'male' else 250
        ctx.move_to(-30, -170); ctx.curve_to(-26, -170 - h * 0.55, -14, -170 - h * 0.92, 2, -170 - h)
        ctx.curve_to(14, -170 - h * 0.8, 24, -170 - h * 0.45, 32, -170); ctx.close_path()
        set_col(ctx, BODY); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        ctx.move_to(-8, -180); ctx.curve_to(-6, -170 - h * 0.5, -3, -170 - h * 0.85, 1, -165 - h)
        ctx.set_source_rgba(0.4, 0.47, 0.54, 0.5); ctx.set_line_width(3); ctx.stroke()
        # pectoral paddles, angled down/out
        for s in (1, -1):
            ctx.save(); ctx.translate(170 * s, 120)
            ctx.rotate(math.radians((28 + 5 * math.sin(TAU * t / 3 + 1)) * s))
            ctx.move_to(0, -26)
            ctx.curve_to(80 * s, -34, 205 * s, -8, 232 * s, 26); ctx.curve_to(240 * s, 58, 150 * s, 66, 70 * s, 50)
            ctx.curve_to(30 * s, 42, 0, 34, 0, 26); ctx.close_path()
            set_col(ctx, BODY); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
            ctx.restore()
        self._head(ctx); set_col(ctx, BODY); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        rg = cairo.RadialGradient(-30, -120, 0, -30, -120, 230)
        rg.add_color_stop_rgba(0, 0.45, 0.51, 0.58, 0.5); rg.add_color_stop_rgba(1, 0.3, 0.35, 0.4, 0)
        ctx.set_source(rg); ctx.paint()
        # white lower jaw / chin (narrow band, tapering up the sides)
        my = 70
        ctx.move_to(-205, my - 30); ctx.curve_to(-150, my + 10 + jaw * 60, 150, my + 10 + jaw * 60, 205, my - 30)
        ctx.line_to(205, 260); ctx.line_to(-205, 260); ctx.close_path(); set_col(ctx, WH); ctx.fill()
        ctx.move_to(-205, 150); ctx.curve_to(-100, 200, 100, 200, 205, 150); ctx.line_to(205, 260); ctx.line_to(-205, 260)
        ctx.close_path(); ctx.set_source_rgba(0.55, 0.65, 0.72, 0.35); ctx.fill()
        # eye patches: slanted lozenges on the sides of the melon
        for s in (1, -1):
            ctx.save(); ctx.translate(118 * s, -52); ctx.rotate(math.radians(-24 * s))
            ctx.move_to(-46 * s, 4); ctx.curve_to(-30 * s, -16, 20 * s, -20, 52 * s, -6)
            ctx.curve_to(40 * s, 12, -10 * s, 18, -46 * s, 4); ctx.close_path()
            set_col(ctx, WH); ctx.fill(); ctx.restore()
        ctx.restore()
        # mouth
        if jaw > 0.02:
            mh = 120 * jaw
            def mouth():
                ctx.move_to(-165, my - 18); ctx.curve_to(-100, my + mh * 1.25, 100, my + mh * 1.25, 165, my - 18)
                ctx.curve_to(100, my - 4, -100, my - 4, -165, my - 18); ctx.close_path()
            mouth(); set_col(ctx, '#3A1217'); ctx.fill_preserve(); ctx.save(); ctx.clip()
            ctx.save(); ctx.translate(0, my + mh * 0.85); ctx.scale(1, 0.33); circle(ctx, 0, 0, 100); set_col(ctx, '#B85A62'); ctx.fill(); ctx.restore()
            for i in range(12):
                x = -138 + i * 25
                yb = my - 10 - 10 * (x / 165) ** 2
                ctx.move_to(x - 8, yb); ctx.curve_to(x - 4, yb + 12, x - 1, yb + 20, x, yb + 24)
                ctx.curve_to(x + 1, yb + 20, x + 4, yb + 12, x + 8, yb); ctx.close_path()
                set_col(ctx, '#F4F1E8'); ctx.fill()
                x2 = x + 12.5
                yl = my - 14 + mh * 1.0 * (1 - (x2 / 170) ** 2) + 6
                ctx.move_to(x2 - 7, yl); ctx.curve_to(x2 - 3, yl - 10, x2 - 1, yl - 18, x2, yl - 21)
                ctx.curve_to(x2 + 1, yl - 18, x2 + 3, yl - 10, x2 + 7, yl); ctx.close_path()
                set_col(ctx, '#F4F1E8'); ctx.fill()
            ctx.restore()
            mouth(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        else:
            ctx.move_to(-165, my - 18); ctx.curve_to(-100, my - 2, 100, my - 2, 165, my - 18)
            set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        # eyes: small, just below/in front of the patch, at the mouth corners
        for s in (1, -1):
            circle(ctx, 168 * s, 8, 7); set_col(ctx, '#3D4A55'); ctx.fill()
            circle(ctx, 168 * s, 8, 4.5); set_col(ctx, '#050607'); ctx.fill()
        self._head(ctx); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
