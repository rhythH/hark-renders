"""Act D custom assets (pure code)."""
import math
import cairocffi as cairo
from engine import *
from engine.core import Element, ev, set_col, hexc, circle, rrect, poly, W, H, PAL, ease
from engine.text import draw_text

OUT = '#0A0D10'


def fade_in(dur=0.6):
    return Fn(lambda ctx, t: (ctx.set_source_rgba(0, 0, 0, max(0.0, 1 - t / dur)), ctx.paint()), layer='overlay', t1=dur)


def sepia_grade(strength=1.0, seed=5):
    def fn(ctx, t):
        import random
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_HSL_COLOR)
        ctx.set_source_rgba(0.62, 0.47, 0.30, 0.85 * strength); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_MULTIPLY)
        ctx.set_source_rgba(1.0, 0.93, 0.80, 0.5 * strength); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        fl = 0.04 + 0.03 * math.sin(t * 23.0) * math.sin(t * 7.3)
        ctx.set_source_rgba(0.95, 0.88, 0.7, max(0, fl)); ctx.paint()
        r = random.Random(seed * 1000 + int(t * 30) % 997)
        for _ in range(200):
            c = r.random() < 0.5
            ctx.set_source_rgba(*((0.15, 0.1, 0.05) if c else (1, 0.97, 0.9)), r.uniform(0.08, 0.22))
            circle(ctx, r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.0)); ctx.fill()
        ctx.restore()
    return fn


def tint_grade(col='#C9A27A', alpha=0.25, op='multiply'):
    def fn(ctx, t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_MULTIPLY if op == 'multiply' else cairo.OPERATOR_OVER)
        set_col(ctx, col, alpha); ctx.paint(); ctx.restore()
    return fn


class TouristBoat(Element):
    """Flat river-cruise boat with canopy and a row of tourists; phones go up at t_phones.
    Origin = hull centre at waterline, ~700 units long. plate= floats it."""
    def __init__(self, plate=None, n=10, t_phones=None, facing='right', **kw):
        super().__init__(**kw)
        self.plate, self.n, self.tp, self.facing = plate, n, t_phones, facing
        if plate is not None:
            self.proc(self._float)

    def _float(self, el, t):
        x = ev(self.pos, t)[0]
        y = self.plate.water_y(x, t + self.t0) - self.plate.water_y(x, 0)
        return {'dpos': (0, y * 0.6), 'drot': 1.2 * math.sin(t * 1.3)}

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        cols = ['#C8453A', '#2F6FA0', '#F0A54A', '#4DB271', '#E8E2D0', '#7A5AA0', '#D96C8A', '#3A8F8A', '#B8863B', '#5C6E7E']
        skins = ['#E2B58F', '#C69273', '#8D5A3C', '#F0C9A6']
        k = 0.0 if self.tp is None else min(1, max(0, (t - self.tp) / 0.5))
        # people (behind rail)
        for i in range(self.n):
            x = -290 + i * (580 / max(1, self.n - 1))
            bob = 2 * math.sin(t * 2.1 + i)
            rrect(ctx, x - 17, -118 + bob, 34, 70, 10); set_col(ctx, cols[i % len(cols)]); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, x, -134 + bob, 15); set_col(ctx, skins[i % 4]); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
            # arm + phone
            kk = ease('eo', min(1, max(0, k * 1.6 - (i % 4) * 0.15)))
            ang = math.radians(-20 - 130 * kk)
            sx, sy = x + 10, -106 + bob
            ex, ey = sx + 44 * math.sin(math.radians(20 + 130 * kk)) * 0.7, sy + 44 * math.cos(math.radians(20 + 130 * kk))
            ctx.move_to(sx, sy); ctx.line_to(ex, ey); set_col(ctx, cols[i % len(cols)]); ctx.set_line_width(9); ctx.stroke()
            if kk > 0.3:
                rrect(ctx, ex - 8, ey - 20, 16, 26, 3); set_col(ctx, '#15181B'); ctx.fill()
                rrect(ctx, ex - 5, ey - 17, 10, 18, 2); set_col(ctx, '#BFE3EE', 0.9 if int(t * 3 + i) % 5 else 0.5); ctx.fill()
        # canopy posts + roof
        for x in (-330, -110, 110, 330):
            ctx.move_to(x, -40); ctx.line_to(x, -200); set_col(ctx, '#3A3F44'); ctx.set_line_width(6); ctx.stroke()
        poly(ctx, [(-360, -200), (360, -200), (345, -224), (-345, -224)]); set_col(ctx, '#2E6E6A'); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        # rail
        ctx.rectangle(-345, -62, 690, 6); set_col(ctx, '#D9D6CC'); ctx.fill()
        for x in range(-340, 345, 40):
            ctx.rectangle(x, -62, 3, 26); ctx.fill()
        # hull
        P = [(-360, -36), (360, -36), (390, -50), (372, 0), (330, 32), (-340, 32), (-372, 0)]
        poly(ctx, P); set_col(ctx, '#F2F1EC'); ctx.fill_preserve()
        ctx.save(); ctx.clip(); ctx.rectangle(-420, 4, 840, 60); set_col(ctx, '#C8453A'); ctx.fill(); ctx.restore()
        poly(ctx, P); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.restore()


class Thongs(Element):
    """Pair of flip-flops on the mud, 3/4 top view. ~220 units wide."""
    def draw(self, ctx, t):
        ctx.save(); ctx.scale(1, 0.3); circle(ctx, 0, 40, 190); ctx.set_source_rgba(0, 0, 0, 0.22); ctx.fill(); ctx.restore()
        for dx, rot, col in ((-60, -12, '#4A8EC2'), (60, 9, '#4A8EC2')):
            ctx.save(); ctx.translate(dx, 0); ctx.rotate(math.radians(rot)); ctx.scale(1, 0.42)
            ctx.move_to(0, -120); ctx.curve_to(48, -120, 52, -40, 40, 10); ctx.curve_to(36, 70, 46, 120, 0, 122)
            ctx.curve_to(-46, 120, -38, 70, -40, 10); ctx.curve_to(-52, -40, -48, -120, 0, -120); ctx.close_path()
            ctx.restore()
            set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
            # strap
            ctx.save(); ctx.translate(dx, 0); ctx.rotate(math.radians(rot)); ctx.scale(1, 0.42)
            ctx.move_to(-34, 0); ctx.curve_to(-20, -60, 20, -60, 34, 0)
            ctx.move_to(0, -52); ctx.line_to(0, -92)
            ctx.restore()
            set_col(ctx, '#1B2328'); ctx.set_line_width(11); ctx.stroke_preserve()
            set_col(ctx, '#F2F0EB'); ctx.set_line_width(6); ctx.stroke()


class Poster(Element):
    """Sepia 'MISSING' poster, centred; content drawn by caller elements on top."""
    def __init__(self, title='MISSING:', sub='1 FRONT LEG', w=1100, h=820, t_sub=0.3, **kw):
        super().__init__(**kw); self.title, self.sub, self.w, self.h, self.ts = title, sub, w, h, t_sub

    def draw(self, ctx, t):
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 12, -h / 2 + 16, w, h, 4); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 4); set_col(ctx, '#EDE6CF'); ctx.fill()
        ctx.rectangle(-w / 2 + 26, -h / 2 + 26, w - 52, h - 52); set_col(ctx, '#2A2F30', 0.8); ctx.set_line_width(3); ctx.stroke()
        draw_text(ctx, self.title, 0, -h / 2 + 140, 'black', 110, '#2A2F30', 0.06, 'center', shadow=False)
        if t > self.ts:
            a = min(1, (t - self.ts) / 0.2)
            draw_text(ctx, self.sub, 0, -h / 2 + 228, 'black', 74, PAL.RED, 0.06, 'center', shadow=False, alpha=a)
        draw_text(ctx, 'ANSWERS TO: BRUTUS', 0, h / 2 - 60, 'bold', 30, '#2A2F30', 0.22, 'center', shadow=False)


class DashedCircle(Element):
    def __init__(self, r=60, color=PAL.RED, **kw):
        super().__init__(**kw); self.r, self.c = r, color

    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.35))
        ctx.set_dash([14, 10], t * 30)
        ctx.arc(0, 0, self.r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * k)
        set_col(ctx, self.c); ctx.set_line_width(6); ctx.stroke(); ctx.set_dash([])


class Scoreboard(Element):
    """Two-row scoreboard; rows = [(name, v0, v1, t_flip)]."""
    def __init__(self, rows, w=760, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.rows, self.w = rows, w

    def draw(self, ctx, t):
        w = self.w; rh = 120
        k = ease('eo', min(1, t / 0.3))
        ctx.save(); ctx.translate(0, 40 * (1 - k))
        rrect(ctx, -w / 2, -20, w, rh * len(self.rows) + 40, 14); set_col(ctx, '#071A22', 0.92 * k); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, k); ctx.set_line_width(3); ctx.stroke()
        for i, (name, v0, v1, tf) in enumerate(self.rows):
            y = i * rh + 70
            draw_text(ctx, name, -w / 2 + 50, y + 10, 'xb', 56, PAL.WHITE, 0.08, alpha=k)
            flip = tf is not None and t >= tf
            v = v1 if flip else v0
            pk = 1.0
            if flip:
                pk = 1 + 0.35 * max(0, 1 - (t - tf) / 0.25)
            ctx.save(); ctx.translate(w / 2 - 90, y - 10); ctx.scale(pk, pk)
            rrect(ctx, -52, -52, 104, 104, 10); set_col(ctx, PAL.ORANGE if flip else '#1C3A46', k); ctx.fill()
            draw_text(ctx, str(v), 0, 26, 'black', 76, '#1A1410' if flip else PAL.WHITE, 0, 'center', shadow=False, alpha=k)
            ctx.restore()
        ctx.restore()


class StrikeLabel(Element):
    def __init__(self, text, size=110, t_strike=1.0, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.text, self.size, self.ts = text, size, t_strike

    def draw(self, ctx, t):
        from engine.text import measure
        a = min(1, t / 0.2)
        draw_text(ctx, self.text, 0, 0, 'black', self.size, PAL.WHITE, 0.06, 'center', alpha=a)
        wdt = measure(ctx, self.text, 'black', self.size, 0.06)[0]
        if t > self.ts:
            k = ease('eo', min(1, (t - self.ts) / 0.3))
            x0 = -wdt / 2 - 30; x1 = x0 + (wdt + 60) * k
            ctx.move_to(x0, -self.size * 0.32); ctx.line_to(x1, -self.size * 0.38)
            set_col(ctx, PAL.RED); ctx.set_line_width(16); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def crown(ctx, s=1.0, col=PAL.ORANGE):
    ctx.save(); ctx.scale(s, s)
    poly(ctx, [(-50, 30), (-56, -30), (-26, 0), (0, -44), (26, 0), (56, -30), (50, 30)])
    set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
    for x, y in ((-56, -30), (0, -44), (56, -30)):
        circle(ctx, x, y, 7); set_col(ctx, PAL.WHITE); ctx.fill()
    ctx.restore()


class Crown(Element):
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.3))
        ctx.save(); ctx.translate(0, 4 * math.sin(t * 2.4)); ctx.scale(k, k); crown(ctx); ctx.restore()


class SoundWave(Element):
    """Pulsing arcs (a yell), opening toward -x (left)."""
    def __init__(self, n=4, **kw):
        super().__init__(**kw); self.n = n

    def draw(self, ctx, t):
        for i in range(self.n):
            ph = (t * 1.6 - i * 0.22)
            if ph < 0: continue
            ph = ph % 1.0 if t > 1.2 else ph
            if ph > 1: continue
            r = 40 + ph * 260
            ctx.arc(0, 0, r, math.radians(140), math.radians(220))
            set_col(ctx, PAL.WHITE, 0.9 * (1 - ph)); ctx.set_line_width(8); ctx.stroke()


class SplashRing(Element):
    """Flat ellipse rings on the water surface."""
    def draw(self, ctx, t):
        for i in range(3):
            ph = (t - i * 0.25) / 1.6
            if ph < 0 or ph > 1: continue
            ctx.save(); ctx.scale(1, 0.22); circle(ctx, 0, 0, 30 + 260 * ease('eo', ph))
            ctx.restore(); set_col(ctx, PAL.WHITE, 0.85 * (1 - ph)); ctx.set_line_width(5); ctx.stroke()
        if t < 0.5:   # droplets
            for j in range(9):
                a = math.radians(-160 + j * 17.5)
                d = 220 * t
                x = math.cos(a) * d; y = math.sin(a) * d + 600 * t * t
                circle(ctx, x, y, 7); set_col(ctx, PAL.WHITE, 1 - t * 2); ctx.fill()


class Redacted(Element):
    """'FEARS:' heading + numbered line with a redaction bar and padlock."""
    def __init__(self, t_line=0.4, t_lock=1.2, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.tl, self.tk = t_line, t_lock

    def draw(self, ctx, t):
        draw_text(ctx, 'FEARS:', -420, -120, 'xb', 96, PAL.WHITE, 0.04, alpha=min(1, t / 0.2))
        ctx.move_to(-420, -90); ctx.line_to(420, -90); set_col(ctx, PAL.WHITE, 0.5); ctx.set_line_width(2); ctx.stroke()
        if t > self.tl:
            k = ease('eo', min(1, (t - self.tl) / 0.4))
            draw_text(ctx, '1.', -420, 40, 'xb', 72, PAL.ORANGE, 0)
            rrect(ctx, -330, -20, 620 * k, 80, 4); set_col(ctx, '#020405'); ctx.fill_preserve()
            set_col(ctx, PAL.WHITE, 0.25); ctx.set_line_width(2); ctx.stroke()
        for i in range(3):
            y = 130 + i * 70
            ctx.move_to(-420, y); ctx.line_to(420, y); set_col(ctx, PAL.WHITE, 0.08); ctx.set_line_width(2); ctx.stroke()
        if t > self.tk:
            k = ease('back', min(1, (t - self.tk) / 0.25))
            ctx.save(); ctx.translate(360, 20); ctx.scale(k, k)
            ctx.arc(0, -22, 22, math.pi, 0); set_col(ctx, PAL.WHITE); ctx.set_line_width(8); ctx.stroke()
            rrect(ctx, -34, -22, 68, 54, 6); set_col(ctx, PAL.ORANGE); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, 0, 0, 7); set_col(ctx, OUT); ctx.fill()
            ctx.restore()


class ToothDots(Element):
    """n dots appear in sequence over dur, at fixed pseudo-random spots inside ellipses."""
    def __init__(self, pts, dur=0.9, **kw):
        super().__init__(**kw); self.pts, self.d = pts, dur

    def draw(self, ctx, t):
        n = len(self.pts)
        for i, (x, y) in enumerate(self.pts):
            ti = i * self.d / n
            if t < ti: continue
            k = ease('back', min(1, (t - ti) / 0.15))
            circle(ctx, x, y, 9 * k); set_col(ctx, PAL.RED); ctx.fill_preserve(); set_col(ctx, PAL.WHITE); ctx.set_line_width(2.5); ctx.stroke()


class TugArrow(Element):
    """Arrow pointing +x (rotate via rot), pulsing at times."""
    def __init__(self, times=(), length=220, color=PAL.ORANGE, **kw):
        super().__init__(**kw); self.times, self.L, self.c = times, length, color

    def draw(self, ctx, t):
        p = 0.0
        for tt in self.times:
            if tt <= t < tt + 0.45: p = math.sin(math.pi * (t - tt) / 0.45)
        a = min(1, t / 0.2)
        L = self.L * (1 + 0.35 * p)
        ctx.move_to(0, 0); ctx.line_to(L - 40, 0); set_col(ctx, self.c, a); ctx.set_line_width(16 + 6 * p); ctx.stroke()
        poly(ctx, [(L, 0), (L - 60, -36), (L - 60, 36)]); ctx.fill()


class MudIsland(Element):
    def __init__(self, w=900, **kw):
        super().__init__(**kw); self.w = w

    def draw(self, ctx, t):
        w = self.w
        ctx.move_to(-w / 2, 20); ctx.curve_to(-w * 0.35, -40, w * 0.3, -50, w / 2, 16)
        ctx.curve_to(w * 0.3, 40, -w * 0.3, 44, -w / 2, 20); ctx.close_path()
        set_col(ctx, '#5E6A55'); ctx.fill()
        ctx.move_to(-w / 2, 20); ctx.curve_to(-w * 0.3, 30, w * 0.3, 26, w / 2, 16)
        set_col(ctx, '#3F4A3C'); ctx.set_line_width(5); ctx.stroke()
        for i in range(4):
            x = -w * 0.3 + i * w * 0.2 + 10 * math.sin(t + i)
            ctx.move_to(x, 46 + i % 2 * 8); ctx.line_to(x + 80, 46 + i % 2 * 8)
            set_col(ctx, PAL.WHITE, 0.15); ctx.set_line_width(3); ctx.stroke()


class BankSil(Element):
    """Maroon chapter card: riverbank cross-section silhouette (screen-wide), waterline at y=0 local."""
    def draw(self, ctx, t):
        # water band
        ctx.rectangle(-200, 0, W + 400, H); set_col(ctx, '#1C0507', 0.75); ctx.fill()
        ctx.move_to(-200, 0)
        for x in range(-200, W + 220, 20):
            ctx.line_to(x, 3 * math.sin(x * 0.02 + t * 2))
        set_col(ctx, '#E07A6A', 0.6); ctx.set_line_width(3); ctx.stroke()
        # bank (right)
        poly(ctx, [(1100, 0), (1260, -110), (W + 300, -130), (W + 300, H), (1500, H), (1180, 120)])
        set_col(ctx, '#0B0203'); ctx.fill()


class RiverMap(Element):
    """Blueprint river strip: winding river drawn on; 'upstream' arrow; pins."""
    def __init__(self, t_arrow=1.0, **kw):
        super().__init__(**kw); self.ta = t_arrow
        self.pts = [(-760, 220), (-560, 160), (-380, 220), (-180, 120), (20, 150), (200, 40), (420, 60), (600, -60), (780, -40)]

    def draw(self, ctx, t):
        from engine.core import catmull
        P = catmull(self.pts, 10, closed=False) if True else None
        k = ease('eo', min(1, t / 0.8))
        n = max(2, int(len(P) * k))
        ctx.move_to(*P[0])
        for p in P[1:n]: ctx.line_to(*p)
        set_col(ctx, '#2C6F7A'); ctx.set_line_width(46); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.move_to(*P[0])
        for p in P[1:n]: ctx.line_to(*p)
        set_col(ctx, PAL.CYAN, 0.8); ctx.set_line_width(3); ctx.set_dash([12, 10]); ctx.stroke(); ctx.set_dash([])
        if t > self.ta:
            kk = ease('eo', min(1, (t - self.ta) / 0.8))
            # dashed arrow above the river from bank spot to upstream
            x0, y0, x1, y1 = -480, 60, -480 + (920 * kk), 60 - 230 * kk
            ctx.move_to(x0, y0); ctx.line_to(x1, y1); set_col(ctx, PAL.ORANGE); ctx.set_line_width(7)
            ctx.set_dash([18, 12]); ctx.stroke(); ctx.set_dash([])
            ang = math.atan2(y1 - y0, x1 - x0)
            ctx.save(); ctx.translate(x1, y1); ctx.rotate(ang)
            poly(ctx, [(16, 0), (-26, -20), (-26, 20)]); set_col(ctx, PAL.ORANGE); ctx.fill(); ctx.restore()
        # bank marker
        circle(ctx, -480, 190, 12); set_col(ctx, PAL.WHITE); ctx.fill()

# ---- navigator chapter card (copied from act B for a consistent look)
from engine.core import TAU, rrect as _rr
from engine.ui import ChapterTitle, icon as ui_icon
# ================================================================ croc-episode additions
NAV_ICONS = ['ruler', 'jaw', 'fin', 'foot', 'run', 'tag']
NAV_LABELS = ['SIZE', 'BITE', 'RIVALS', 'PEOPLE', 'YOUR MOVE', 'THE REAL DANGER']


def icon(ctx, name, r=20, color=PAL.WHITE, lw=None):
    lw = lw or max(1.5, r * 0.12)
    set_col(ctx, color); ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    s = r
    if name == 'ruler':
        ctx.save(); ctx.rotate(-0.6)
        rrect(ctx, -s * 0.9, -s * 0.28, s * 1.8, s * 0.56, s * 0.08); ctx.stroke()
        for i in range(1, 6):
            x = -s * 0.9 + i * s * 0.3
            ctx.move_to(x, -s * 0.28); ctx.line_to(x, -s * (0.02 if i % 2 else 0.1)); ctx.stroke()
        ctx.restore()
    elif name == 'jaw':   # open jaw + small gauge
        ctx.move_to(-s * 0.85, -s * 0.15); ctx.line_to(s * 0.6, -s * 0.55); ctx.stroke()
        ctx.move_to(-s * 0.85, s * 0.05); ctx.line_to(s * 0.6, s * 0.45); ctx.stroke()
        for i in range(4):
            x = -s * 0.55 + i * s * 0.3
            ctx.move_to(x, -s * 0.15 - (x + s * 0.85) * 0.27); ctx.line_to(x + s * 0.08, -s * 0.0 - (x + s * 0.85) * 0.2); ctx.stroke()
        ctx.move_to(s * 0.6, -s * 0.55); ctx.line_to(s * 0.85, 0); ctx.line_to(s * 0.6, s * 0.45); ctx.stroke()
    elif name == 'fin':
        ui_icon(ctx, 'fin', r, color, lw)
    elif name == 'foot':
        rrect(ctx, -s * 0.28, -s * 0.15, s * 0.56, s * 0.85, s * 0.28); ctx.fill()
        for i, dx in enumerate((-0.32, -0.12, 0.08, 0.26)):
            circle(ctx, s * dx, -s * (0.42 + (0.12 if i == 0 else 0.0)), s * (0.13 if i == 0 else 0.1)); ctx.fill()
    elif name == 'run':
        circle(ctx, s * 0.2, -s * 0.7, s * 0.17); ctx.fill()
        ctx.move_to(s * 0.1, -s * 0.45); ctx.line_to(-s * 0.1, s * 0.15); ctx.stroke()
        ctx.move_to(-s * 0.1, s * 0.15); ctx.line_to(s * 0.35, s * 0.45); ctx.line_to(s * 0.3, s * 0.85); ctx.stroke()
        ctx.move_to(-s * 0.1, s * 0.15); ctx.line_to(-s * 0.45, s * 0.55); ctx.line_to(-s * 0.8, s * 0.5); ctx.stroke()
        ctx.move_to(-s * 0.55, -s * 0.2); ctx.line_to(s * 0.05, -s * 0.35); ctx.line_to(s * 0.55, -s * 0.05); ctx.stroke()
    elif name == 'tag':
        ctx.move_to(-s * 0.8, -s * 0.15); ctx.line_to(-s * 0.35, -s * 0.6); ctx.line_to(s * 0.8, -s * 0.6)
        ctx.line_to(s * 0.8, s * 0.3); ctx.line_to(-s * 0.35, s * 0.3); ctx.close_path(); ctx.stroke()
        circle(ctx, -s * 0.35, -s * 0.15, s * 0.1); ctx.fill()
    else:
        ui_icon(ctx, name, r, color, lw)


class NavChapterTitle(ChapterTitle):
    """Chapter card overlay with the croc episode's six navigator icons."""
    def __init__(self, title, subtitle, n, **kw):
        kw.setdefault('pos', (110, 830))
        super().__init__(title, subtitle, n, 6, icons=NAV_ICONS, labels=NAV_LABELS, **kw)
    def draw(self, ctx, t):
        from engine.text import draw_text_reveal
        draw_text_reveal(ctx, self.title, 0, 0, min(1, t / 0.2), 'xb', self.size, PAL.WHITE, 0.04, 'left', 'letters')
        ts = t - 0.5
        if ts > 0:
            draw_text(ctx, self.sub, 6, 72, 'bold', 28, PAL.WHITE, 0.24, alpha=min(1, ts / 0.3))
        tn = t - 0.75
        if tn > 0:
            a = min(1, tn / 0.3); r = 21; gap = 64; y = 150
            for i in range(self.total):
                cx = 6 + r + i * gap
                if i > 0:
                    ctx.move_to(cx - gap + r + 4, y); ctx.line_to(cx - r - 4, y); set_col(ctx, PAL.WHITE, 0.5 * a); ctx.set_line_width(2); ctx.stroke()
                cur = (i + 1) == self.n
                circle(ctx, cx, y, r)
                if cur:
                    set_col(ctx, PAL.ORANGE, a); ctx.fill_preserve()
                set_col(ctx, PAL.ORANGE if cur else PAL.WHITE, a); ctx.set_line_width(2.4); ctx.stroke()
                ctx.save(); ctx.translate(cx, y); ctx.push_group()
                icon(ctx, self.icons[i], r * 0.62, '#1A1410' if cur else PAL.WHITE)
                ctx.pop_group_to_source(); ctx.paint_with_alpha(a); ctx.restore()
            draw_text(ctx, f'{self.n} / {self.total}', 6 + self.total * gap + 6, y + 15, 'xb', 44, PAL.WHITE, 0.02, alpha=a)
            draw_text(ctx, self.labels[self.n - 1], 6 + r + (self.n - 1) * gap, y + r + 36, 'bold', 20, PAL.WHITE, 0.2, 'center', alpha=a)




class Tinted(Element):
    """Render child element, then wash its own pixels toward `col` (ATOP) — e.g. darker, stockier bull shark."""
    def __init__(self, child, col='#55636B', alpha=0.45, **kw):
        super().__init__(**kw); self.child, self.col, self.a = child, col, alpha

    def draw(self, ctx, t):
        ctx.push_group()
        self.child.render(ctx, t)
        ctx.set_operator(cairo.OPERATOR_ATOP); set_col(ctx, self.col, self.a); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source(); ctx.paint()


def bull_shark(**kw):
    """Bull-shark read: shorter/deeper body (stocky), darker grey wash."""
    layer, z = kw.pop('layer', 'mid'), kw.pop('z', 0)
    sc = kw.pop('scale', 0.5)
    return Tinted(BullShark(scale=(sc * 0.9, sc * 1.12), **kw), layer=layer, z=z)
