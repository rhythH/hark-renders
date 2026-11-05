"""Act C (chapter 3/6 SHARKS) assets: shark silhouette, x-ray shark with liver,
top-down shark, beach plate, cage, suitcase, sale sign, rear-view floppy fins,
drone, floppy-dorsal orca, liver prop, phone-holding tourist, clock, paper props."""
import math, copy
import numpy as np
import cairocffi as cairo
from engine.core import (Element, ev, set_col, hexc, mix, circle, rrect, TAU, PAL, catmull, poly, rng, W, H,
                         ease, remap, stroke_glow)
from engine.chars.animals import S_TOP, S_BOT, S_TAIL, S_DORSAL, S_PEC, S_LIP
from engine.chars.orca import Deform, _path, Orca, geo, _sm, DORSAL_M, YS
from engine.chars.human import Human
from engine.plates import Plate, vignette_builder, Particles
from engine.text import draw_text, measure
from engine.ui import RecOverlay, icon
OUT = PAL.OUTLINE

# ------------------------------------------------------------------ shark geometry helper
_ST = catmull(S_TOP, 8); _SB = catmull(S_BOT, 8); _STL = catmull(S_TAIL, 6)
_SD = catmull(S_DORSAL, 6); _SP = catmull(S_PEC, 6, closed=True)

def shark_pose(t, swim=1.0, period=2.2, phase=0.0):
    D = Deform(t, 30 * swim, period, 0.0, phase)
    top, bot, tail, dor = D(_ST), D(_SB), D(_STL, fluke=True), D(_SD)
    pec = D(_SP + np.array([-250.0, 50]))
    body = np.vstack([top, tail[1:], bot[1:]])
    return D, body, dor, pec


class SharkSil(Element):
    """Flat silhouette great white, facing left (chapter card / background)."""
    def __init__(self, facing='left', color='#050203', swim=1.0, period=2.4, phase=0.0, **kw):
        super().__init__(**kw); self.facing, self.col, self.swim, self.period, self.ph = facing, color, swim, period, phase
    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        D, body, dor, pec = shark_pose(t, ev(self.swim, t), self.period, self.ph)
        _path(ctx, dor, close=False); ctx.line_to(float(dor[0, 0]) + 60, float(dor[0, 1]) + 30); ctx.close_path()
        _path(ctx, body); _path(ctx, pec)
        set_col(ctx, self.col); ctx.fill()
        ctx.restore()


class XRayShark(Element):
    """Blueprint x-ray great white facing left. liver_glow (0..1) fills the liver
    red; liver_gone (0..1) removes it, leaving a dotted outline."""
    LIVER = [(-300, 6), (-230, -16), (-120, -26), (0, -18), (90, 0), (130, 22), (80, 42), (-20, 54),
             (-130, 64), (-230, 56), (-290, 34)]
    def __init__(self, liver_glow=0.0, liver_gone=0.0, swim=0.5, period=2.6, color=PAL.CYAN, **kw):
        super().__init__(**kw)
        self.lg, self.lo, self.swim, self.period, self.c = liver_glow, liver_gone, swim, period, color
        self.liver = catmull(self.LIVER, 8, closed=True)
    def draw(self, ctx, t):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        D, body, dor, pec = shark_pose(t, ev(self.swim, t), self.period)
        c = hexc(self.c); sk = hexc(PAL.CYAN_HI)
        # translucent fill
        _path(ctx, body); ctx.set_source_rgba(c[0], c[1], c[2], 0.07); ctx.fill()
        # spine (cartilage) + vertebra ticks
        sp = D(catmull([(-430, -6), (-300, -20), (-150, -30), (0, -32), (150, -26), (300, -16), (420, -2), (500, -60)], 10))
        stroke_glow(ctx, lambda: _path(ctx, sp, False), sk, 3.0, glow=2, glow_alpha=0.14)
        ctx.set_source_rgba(sk[0], sk[1], sk[2], 0.7); ctx.set_line_width(2.4)
        for i in range(3, len(sp) - 8, 2):
            x, y = sp[i]; ctx.move_to(x, y - 10); ctx.line_to(x, y + 6)
        ctx.stroke()
        # skull / jaw cartilage
        sk_p = D(catmull([(-490, 30), (-470, 0), (-420, -30), (-360, -44), (-330, -24), (-350, 10), (-420, 30)], 6, closed=True))
        stroke_glow(ctx, lambda: _path(ctx, sk_p), sk, 2.6, glow=1, glow_alpha=0.12)
        jb = D(np.array(catmull([(-470, 40), (-420, 46), (-360, 42), (-320, 30)], 6)))
        stroke_glow(ctx, lambda: _path(ctx, jb, False), sk, 2.6, glow=1, glow_alpha=0.12)
        # gill arches
        for i in range(5):
            x = -300 + i * 22
            g0 = D(np.array([[x, -30.0], [x + 6, 10], [x, 44]]))
            ctx.move_to(*g0[0]); ctx.curve_to(*g0[1], *g0[1], *g0[2])
        ctx.set_source_rgba(c[0], c[1], c[2], 0.75); ctx.set_line_width(2.4); ctx.stroke()
        # liver
        glow = ev(self.lg, t); gone = ev(self.lo, t)
        lv = D(self.liver)
        if gone < 1:
            a = 1 - gone
            _path(ctx, lv)
            ctx.set_source_rgba(0.84, 0.25, 0.24, (0.12 + 0.7 * glow) * a); ctx.fill()
            if glow > 0:
                pulse = 0.75 + 0.25 * math.sin(t * 9)
                stroke_glow(ctx, lambda: _path(ctx, lv), (0.95, 0.35, 0.32, a * pulse), 4.0, glow=4, glow_alpha=0.25 * glow * a)
            else:
                _path(ctx, lv); ctx.set_source_rgba(c[0], c[1], c[2], 0.55 * a); ctx.set_line_width(2.2); ctx.stroke()
        if gone > 0:
            ctx.set_dash([10, 9]); _path(ctx, lv)
            ctx.set_source_rgba(0.95, 0.4, 0.38, min(1, gone * 1.5)); ctx.set_line_width(3.2); ctx.stroke(); ctx.set_dash([])
        # eye
        e = D(np.array([[-400.0, -22]]))[0]
        stroke_glow(ctx, lambda: circle(ctx, e[0], e[1], 9), sk, 2.4, glow=1)
        # outlines
        stroke_glow(ctx, lambda: _path(ctx, body), c, 4.5, glow=3, glow_alpha=0.2)
        stroke_glow(ctx, lambda: _path(ctx, dor, False), c, 4.0, glow=3, glow_alpha=0.18)
        stroke_glow(ctx, lambda: _path(ctx, pec), c, 3.6, glow=2, glow_alpha=0.18)
        lu = D(catmull(S_LIP, 5)); stroke_glow(ctx, lambda: _path(ctx, lu, False), c, 3.0, glow=1)


class SharkTop(Element):
    """Top-down great white facing left (nose at -500). Tail beats side to side."""
    def __init__(self, period=0.9, beat=1.0, **kw):
        super().__init__(**kw); self.period, self.beat = period, beat
        half = [(-500, 0), (-490, 22), (-450, 48), (-380, 70), (-260, 84), (-120, 84), (20, 70), (160, 48),
                (280, 26), (360, 12), (400, 8)]
        self.half = catmull(half, 8)
    def draw(self, ctx, t):
        b = ev(self.beat, t)
        def bend(P):
            P = P.copy(); u = np.clip((P[:, 0] + 100) / 600, 0, 1)
            P[:, 1] += b * 40 * u ** 2 * math.sin(TAU * t / self.period)
            return P
        top = self.half.copy(); top[:, 1] *= -1
        # pectorals
        for s in (1, -1):
            pc = np.array(catmull([(-230, 70 * s), (-200, 150 * s), (-150, 230 * s), (-120, 240 * s), (-130, 160 * s), (-120, 80 * s)], 5))
            _path(ctx, pc); set_col(ctx, '#5E6D78'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # tail crescent
        tail = bend(np.array(catmull([(380, 0), (440, -40), (520, -150), (540, -140), (500, -40), (480, 0), (500, 40), (540, 140),
                                      (520, 150), (440, 40), (380, 0)], 5)))
        _path(ctx, tail); set_col(ctx, '#5E6D78'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        body = bend(np.vstack([self.half, top[::-1]]))
        _path(ctx, body); set_col(ctx, '#6E7E8A'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.LinearGradient(0, -90, 0, 90)
        g.add_color_stop_rgba(0, 0.25, 0.3, 0.35, 0.5); g.add_color_stop_rgba(0.5, 0.6, 0.66, 0.7, 0.25); g.add_color_stop_rgba(1, 0.25, 0.3, 0.35, 0.5)
        ctx.set_source(g); ctx.paint(); ctx.restore()
        _path(ctx, body); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # dorsal ridge
        ctx.move_to(-130, 0); ctx.curve_to(-60, -8, 0, -8, 40, 0); ctx.curve_to(0, 8, -60, 8, -130, 0); set_col(ctx, '#3A464E'); ctx.fill()
        for s in (1, -1):
            circle(ctx, -430, 34 * s, 6); set_col(ctx, '#050607'); ctx.fill()


# ------------------------------------------------------------------ beach plate
class Beach(Plate):
    """Overcast grey beach: sky, grey sea with moving surf, wet sand, dry sand."""
    parallax = 1.0
    margin = 0.12
    def __init__(self, horizon=360, shore=600):
        super().__init__(); self.hz, self.sh = horizon, shore
    def _base(self, c, s):
        hz, sh = self.hz, self.sh
        g = cairo.LinearGradient(0, -H * 0.2, 0, hz)
        g.add_color_stop_rgba(0, *hexc('#7E8A8E')); g.add_color_stop_rgba(1, *hexc('#C3C8C2'))
        c.set_source(g); c.rectangle(-W, -H, W * 3, hz + H); c.fill()
        # distant headland
        c.move_to(-400, hz + 2); c.curve_to(200, hz - 70, 520, hz - 60, 820, hz + 2); c.close_path()
        set_col(c, '#8C9590'); c.fill()
        g = cairo.LinearGradient(0, hz, 0, sh)
        g.add_color_stop_rgba(0, *hexc('#5D7476')); g.add_color_stop_rgba(1, *hexc('#7F9895'))
        c.set_source(g); c.rectangle(-W, hz, W * 3, sh - hz + 60); c.fill()
        g = cairo.LinearGradient(0, sh, 0, H * 1.2)
        g.add_color_stop_rgba(0, *hexc('#A99A7C')); g.add_color_stop_rgba(0.25, *hexc('#C8B894')); g.add_color_stop_rgba(1, *hexc('#B39F79'))
        c.set_source(g); c.rectangle(-W, sh + 20, W * 3, H * 2); c.fill()
        r = rng(5)
        for _ in range(1800):
            x, y = r.uniform(-300, W + 300), r.uniform(sh + 30, H + 150)
            c.set_source_rgba(0.35, 0.28, 0.18, r.uniform(0.05, 0.16)); circle(c, x, y, r.uniform(0.8, 2.4)); c.fill()
        for _ in range(14):   # pebbles/shells
            x, y = r.uniform(-200, W + 200), r.uniform(sh + 80, H + 80)
            c.save(); c.translate(x, y); c.scale(1, 0.5); circle(c, 0, 0, r.uniform(5, 11)); c.restore()
            set_col(c, '#E5DCC8'); c.fill()
    def surf_y(self, x, t):
        return self.sh + 16 * math.sin(t * 0.9) + 6 * math.sin(x * 0.008 + t * 1.4)
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
        ctx.save(); cam.apply(ctx, t, 1.0)
        # swell lines on the sea
        ctx.set_line_width(2.0)
        for i in range(9):
            y = self.hz + 20 + i * (self.sh - self.hz - 30) / 9
            off = (t * 30 + i * 140) % 400
            ctx.set_source_rgba(1, 1, 1, 0.10 + 0.03 * i)
            for x0 in range(-600, W + 600, 400):
                xx = x0 + off
                ctx.move_to(xx, y); ctx.curve_to(xx + 60, y - 4, xx + 120, y - 4, xx + 180, y)
            ctx.stroke()
        xs = np.arange(-500, W + 520, 30)
        ys = [self.surf_y(x, t) for x in xs]
        # wet sand sheen
        ctx.move_to(xs[0], ys[0])
        for x, y in zip(xs, ys): ctx.line_to(float(x), y + 46 + 10 * math.sin(x * 0.01))
        ctx.line_to(xs[-1], ys[-1]); ctx.close_path()
        ctx.set_source_rgba(0.45, 0.42, 0.36, 0.35); ctx.fill()
        # foam band
        ctx.move_to(xs[0], ys[0] - 24)
        for x, y in zip(xs, ys): ctx.line_to(float(x), y - 24 + 4 * math.sin(x * 0.03 + t * 2))
        for x, y in zip(xs[::-1], ys[::-1]): ctx.line_to(float(x), y + 6 * math.sin(x * 0.02 - t))
        ctx.close_path(); ctx.set_source_rgba(0.95, 0.96, 0.95, 0.85); ctx.fill()
        ctx.restore()
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(0.35, '#1A1A18'), None, t, parallax=0, margin=0)


class MaroonPlate(Plate):
    """Chapter-card maroon variant #120708: dark radial gradient + drifting motes + soft red rays."""
    parallax = 0.35
    def __init__(self):
        super().__init__()
        self.parts = Particles(n_specks=70, n_discs=10, alpha=0.25, color='#E8A0A0')
    def _base(self, c, s):
        rg = cairo.RadialGradient(W * 0.5, H * 0.3, 0, W * 0.5, H * 0.45, W * 0.75)
        rg.add_color_stop_rgba(0, *hexc('#3A1216')); rg.add_color_stop_rgba(0.5, *hexc('#200A0C')); rg.add_color_stop_rgba(1, *hexc('#120708'))
        c.set_source(rg); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        # faint rays from top
        for i in range(7):
            x = 300 + i * 220
            c.move_to(x - 30, -60); c.line_to(x + 30, -60); c.line_to(x + 160 + i * 20, H); c.line_to(x + 40 + i * 20, H); c.close_path()
            c.set_source_rgba(1, 0.6, 0.55, 0.025); c.fill()
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t); self.parts.draw(ctx, t, cam)
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(0.55), None, t, parallax=0, margin=0)


# ------------------------------------------------------------------ props
class Cage(Element):
    """Shark-diving cage (front bars). Origin = cage centre. w x h units."""
    def __init__(self, w=300, h=340, **kw):
        super().__init__(**kw); self.w, self.h = w, h
    def draw(self, ctx, t):
        w, h = self.w, self.h
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        rrect(ctx, -w / 2, -h / 2, w, h, 8); ctx.set_source_rgba(0.6, 0.75, 0.8, 0.06); ctx.fill()
        for k in range(7):
            x = -w / 2 + k * w / 6
            ctx.move_to(x, -h / 2); ctx.line_to(x, h / 2)
        for y in (-h / 2, -h / 6, h / 6, h / 2):
            ctx.move_to(-w / 2, y); ctx.line_to(w / 2, y)
        set_col(ctx, OUT); ctx.set_line_width(14); ctx.stroke_preserve()
        set_col(ctx, '#B8C4C8'); ctx.set_line_width(8); ctx.stroke()
        # float pontoons on top
        for x in (-w / 2, w / 2 - 70):
            rrect(ctx, x, -h / 2 - 34, 70, 30, 12); set_col(ctx, '#E8B32A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()


def suitcase(ctx, w=120, h=84, col='#9A5B34'):
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-w * 0.18, -h / 2); ctx.line_to(-w * 0.18, -h / 2 - 22); ctx.line_to(w * 0.18, -h / 2 - 22); ctx.line_to(w * 0.18, -h / 2)
    set_col(ctx, OUT); ctx.set_line_width(8); ctx.stroke()
    rrect(ctx, -w / 2, -h / 2, w, h, 10); set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
    for x in (-w * 0.3, w * 0.3):
        ctx.move_to(x, -h / 2); ctx.line_to(x, h / 2); set_col(ctx, '#5E3520'); ctx.set_line_width(7); ctx.stroke()
    rrect(ctx, -w / 2 + 6, -6, w - 12, 8, 3); ctx.set_source_rgba(1, 1, 1, 0.15); ctx.fill()


class Suitcase(Element):
    """Suitcase that pops in at t0 and swings slightly."""
    def __init__(self, w=120, h=84, col='#9A5B34', **kw):
        super().__init__(**kw); self.w, self.h, self.col = w, h, col
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.18))
        ctx.save(); ctx.translate(0, -self.h / 2 - 22); ctx.rotate(math.radians(8 * math.sin(t * 5)))
        ctx.translate(0, self.h / 2 + 22); ctx.scale(k, k)
        suitcase(ctx, self.w, self.h, self.col)
        ctx.restore()


class SaleSign(Element):
    """Wooden sign on a post: 'FOR SALE' -> red 'SOLD' slapped on at t_sold. Origin = post foot."""
    def __init__(self, t_sold=1e9, **kw):
        super().__init__(**kw); self.ts = t_sold
    def draw(self, ctx, t):
        sway = math.radians(1.5 * math.sin(t * 1.3))
        ctx.save(); ctx.rotate(sway)
        rrect(ctx, -10, -260, 20, 260, 4); set_col(ctx, '#6B4A2E'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -170, -380, 340, 150, 10); set_col(ctx, '#EFE6CF'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        rrect(ctx, -158, -368, 316, 126, 6); set_col(ctx, PAL.RED); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, 'FOR SALE', 0, -282, 'black', 60, PAL.RED, 0.03, 'center', shadow=False)
        if t >= self.ts:
            k = min(1, (t - self.ts) / (5 / 30)); s = 1.35 - 0.35 * ease('ei2', k)
            ctx.save(); ctx.translate(0, -305); ctx.rotate(math.radians(-12)); ctx.scale(s, s)
            rrect(ctx, -150, -52, 300, 104, 10); set_col(ctx, PAL.RED); ctx.fill_preserve(); set_col(ctx, '#7A1A18'); ctx.set_line_width(5); ctx.stroke()
            draw_text(ctx, 'SOLD', 0, 30, 'black', 84, PAL.WHITE, 0.04, 'center', shadow=False)
            ctx.restore()
        ctx.restore()


class Reef(Element):
    """Simple rock + kelp reef strip along the bottom (kelp sways)."""
    def __init__(self, width=2400, seed=3, **kw):
        super().__init__(**kw); self.wd = width
        r = rng(seed)
        self.rocks = [(r.uniform(-width / 2, width / 2), r.uniform(60, 170), r.uniform(0.6, 1.0)) for _ in range(16)]
        self.kelp = [(r.uniform(-width / 2, width / 2), r.uniform(160, 360), r.random() * TAU) for _ in range(18)]
    def draw(self, ctx, t):
        for (x, L, ph) in self.kelp:
            ctx.move_to(x, 0)
            for k in range(1, 9):
                u = k / 8
                ctx.line_to(x + 30 * u * math.sin(t * 0.9 + ph + u * 2), -L * u)
            ctx.set_source_rgba(0.12, 0.32, 0.28, 0.9); ctx.set_line_width(12); ctx.stroke()
        for (x, rr, sh) in sorted(self.rocks, key=lambda a: a[1]):
            ctx.save(); ctx.translate(x, 30); ctx.scale(1.3, 0.6 * sh)
            circle(ctx, 0, 0, rr); ctx.restore()
            set_col(ctx, mix('#0E2C36', '#1E4652', sh - 0.6)); ctx.fill()
        ctx.rectangle(-self.wd / 2 - 400, 20, self.wd + 800, 400); set_col(ctx, '#0B2229'); ctx.fill()


class RearFin(Element):
    """Orca seen from behind at the surface: dark back mound + dorsal fin whose
    tip bends sideways by `bend` degrees (+ = screen right). Origin = waterline centre."""
    def __init__(self, bend=0.0, height=300, base=90, **kw):
        super().__init__(**kw); self.bend, self.hgt, self.base = bend, height, base
    def draw(self, ctx, t):
        b = math.radians(ev(self.bend, t)); bob = 4 * math.sin(t * 1.4)
        ctx.save(); ctx.translate(0, bob)
        # back mound
        ctx.move_to(-230, 10); ctx.curve_to(-200, -70, 200, -70, 230, 10); ctx.close_path()
        set_col(ctx, '#12171C'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(7); ctx.stroke()
        ctx.move_to(-150, -30); ctx.curve_to(-80, -52, 80, -52, 150, -30); ctx.set_source_rgba(0.45, 0.5, 0.56, 0.35); ctx.set_line_width(8); ctx.stroke()
        # fin centreline integrated with progressive bend
        n = 14; pts_c = []; ang = 0.0; x, y = 0.0, -40.0
        seg = self.hgt / n
        for i in range(n + 1):
            u = i / n
            pts_c.append((x, y, ang, u))
            ang = b * (u ** 1.6) * 1.6
            x += seg * math.sin(ang); y -= seg * math.cos(ang)
        left, right = [], []
        for (x, y, a, u) in pts_c:
            wdt = self.base * (1 - u) ** 0.9 + 4
            nx, ny = math.cos(a), math.sin(a)
            left.append((x - nx * wdt / 2, y - ny * wdt / 2)); right.append((x + nx * wdt / 2, y + ny * wdt / 2))
        P = np.array(left + right[::-1])
        _path(ctx, P); set_col(ctx, '#12171C'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        ctx.restore()
        # foam at the waterline
        ctx.set_source_rgba(1, 1, 1, 0.9)
        for i in range(9):
            xx = -220 + i * 55
            circle(ctx, xx, 10 + 3 * math.sin(t * 3 + i), 12 + 4 * math.sin(t * 2 + i * 1.7)); ctx.fill()


class NavLight(Element):
    """Blinking nautical side light (red port / green starboard) with glow."""
    def __init__(self, color='#E5332E', period=1.0, r=22, **kw):
        super().__init__(**kw); self.c, self.p, self.r = color, period, r
    def draw(self, ctx, t):
        on = 1.0 if (t % self.p) < self.p * 0.65 else 0.35
        k = ease('back', min(1, t / 0.2)); ctx.scale(k, k)
        c = hexc(self.c)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, self.r * 4)
        rg.add_color_stop_rgba(0, c[0], c[1], c[2], 0.55 * on); rg.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.set_source(rg); circle(ctx, 0, 0, self.r * 4); ctx.fill()
        rrect(ctx, -self.r - 8, -self.r - 8, 2 * self.r + 16, 2 * self.r + 16, 8); set_col(ctx, '#1E2328'); ctx.fill()
        circle(ctx, 0, 0, self.r); ctx.set_source_rgba(c[0] * (0.5 + 0.5 * on), c[1] * (0.5 + 0.5 * on), c[2] * (0.5 + 0.5 * on), 1); ctx.fill()
        circle(ctx, -self.r * 0.3, -self.r * 0.35, self.r * 0.3); ctx.set_source_rgba(1, 1, 1, 0.5 * on); ctx.fill()


class Drone(Element):
    """Small quadcopter with spinning rotors and a blinking REC light; bobs."""
    def draw(self, ctx, t):
        ctx.translate(0, 6 * math.sin(t * 2.1)); ctx.rotate(math.radians(2 * math.sin(t * 1.3)))
        for x in (-90, 90):
            ctx.move_to(0, 0); ctx.line_to(x, -22); set_col(ctx, OUT); ctx.set_line_width(8); ctx.stroke()
            w = 70 * abs(math.sin(t * 40 + x))
            ctx.save(); ctx.translate(x, -30); ctx.scale(1, 0.18); circle(ctx, 0, 0, 30 + w * 0.4); ctx.restore()
            ctx.set_source_rgba(0.85, 0.9, 0.92, 0.45); ctx.fill()
            rrect(ctx, x - 6, -36, 12, 14, 3); set_col(ctx, '#2A2F33'); ctx.fill()
        rrect(ctx, -40, -14, 80, 32, 10); set_col(ctx, '#E9ECEB'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        circle(ctx, 0, 26, 12); set_col(ctx, '#1E2328'); ctx.fill()
        circle(ctx, 0, 26, 5); set_col(ctx, '#4A7FA0'); ctx.fill()
        if (t % 1.0) < 0.6:
            circle(ctx, 28, -4, 5); set_col(ctx, '#E5332E'); ctx.fill()


class Liver(Element):
    """Peach-coloured liver blob held in a mouth."""
    def draw(self, ctx, t):
        ctx.rotate(math.radians(6 * math.sin(t * 2.2)))
        P = catmull([(-80, -10), (-40, -34), (20, -30), (70, -14), (96, 10), (70, 30), (10, 38), (-50, 30), (-90, 12)], 6, closed=True)
        _path(ctx, P); set_col(ctx, '#E39A7E'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        ctx.move_to(-90, 6); ctx.curve_to(-30, -6, 30, 16, 100, 4); ctx.set_source_rgba(0.6, 0.3, 0.25, 0.35); ctx.set_line_width(5); ctx.stroke()
        circle(ctx, -20, -16, 12); ctx.set_source_rgba(1, 0.9, 0.85, 0.35); ctx.fill()
        ctx.restore()
        _path(ctx, P); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()


def floppy_orca(lean='back', **kw):
    """Side-view male orca with a collapsed dorsal: lean='back' (tip droops toward
    the flukes) or 'front' (tip droops toward the head)."""
    o = Orca(**kw)
    g = copy.copy(geo('male'))
    if lean == 'back':
        pts = [(-150, -130), (-132, -200), (-104, -262), (-62, -304), (-6, -320), (48, -308), (86, -282), (96, -258),
               (70, -262), (30, -258), (2, -232), (-2, -180), (14, -126)]
    else:
        pts = [(-150, -130), (-160, -196), (-190, -250), (-236, -286), (-268, -290), (-262, -272), (-232, -258),
               (-196, -232), (-150, -196), (-100, -170), (-40, -140), (14, -126)]
    g.dorsal = _sm(pts, 8)
    o.g = g
    return o


class PhoneHuman(Human):
    """Tourist who raises a phone (raise: 0..1 track). Phone screen glows."""
    def __init__(self, raise_=0.0, **kw):
        self.raise_ = raise_
        kw['pose'] = lambda t: self._pose(t)
        super().__init__(**kw)
    def _pose(self, t):
        k = ease('eo', min(1, max(0, ev(self.raise_, t))))
        return (8, 0, 8 + 140 * k, 0 + 40 * k)
    def draw(self, ctx, t):
        super().draw(ctx, t)
        k = ease('eo', min(1, max(0, ev(self.raise_, t))))
        if k <= 0.05: return
        a1, a2 = 8 + 140 * k, 40 * k
        breathe = 1.5 * math.sin(TAU * t / 3.2)
        sh = np.array([30, -205 + breathe]); r1 = math.radians(a1); r2 = math.radians(a1 + a2)
        el = sh + 52 * np.array([math.sin(r1), math.cos(r1)]); hd = el + 50 * np.array([math.sin(r2), math.cos(r2)])
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.translate(hd[0] + 4, hd[1] - 22)
        rrect(ctx, -13, -22, 26, 44, 5); set_col(ctx, '#15181B'); ctx.fill()
        rrect(ctx, -9, -17, 18, 34, 3); ctx.set_source_rgba(0.75, 0.9, 1.0, 0.95 * k); ctx.fill()
        ctx.restore()


class RecFreeze(RecOverlay):
    """REC overlay whose timecode freezes at t_freeze (and shows a pause mark)."""
    def __init__(self, t_freeze=1e9, **kw):
        super().__init__(**kw); self.tf = t_freeze
    def tc(self, t):
        return super().tc(min(t, self.tf))
    def draw(self, ctx, t):
        super().draw(ctx, t)
        if t >= self.tf:
            for x in (W / 2 - 22, W / 2 + 8):
                rrect(ctx, x, 86, 14, 40, 3); set_col(ctx, PAL.WHITE); ctx.fill()


class Clock(Element):
    """Clock card: minute hand sweeps 0 -> `minutes` over [t_a, t_b]."""
    def __init__(self, r=230, t_a=0.2, t_b=1.6, minutes=60, **kw):
        super().__init__(**kw); self.r, self.ta, self.tb, self.m = r, t_a, t_b, minutes
    def draw(self, ctx, t):
        r = self.r
        k0 = ease('back', min(1, t / 0.25)); ctx.scale(k0, k0)
        circle(ctx, 8, 12, r + 14); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.fill()
        circle(ctx, 0, 0, r + 14); set_col(ctx, '#1E2328'); ctx.fill()
        circle(ctx, 0, 0, r); set_col(ctx, '#F4F2EC'); ctx.fill()
        m = self.m * ease('eio', (t - self.ta) / (self.tb - self.ta))
        a = m / 60 * TAU
        ctx.move_to(0, 0); ctx.arc(0, 0, r * 0.88, -math.pi / 2, -math.pi / 2 + a); ctx.close_path()
        set_col(ctx, PAL.RED, 0.25); ctx.fill()
        for i in range(60):
            aa = i / 60 * TAU; L = 26 if i % 5 == 0 else 10
            ctx.move_to(math.sin(aa) * (r - 14), -math.cos(aa) * (r - 14)); ctx.line_to(math.sin(aa) * (r - 14 - L), -math.cos(aa) * (r - 14 - L))
            set_col(ctx, '#1A1E22'); ctx.set_line_width(6 if i % 5 == 0 else 2.5); ctx.stroke()
        ha = (m / 60) / 12 * TAU
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(0, 0); ctx.line_to(math.sin(ha) * r * 0.5, -math.cos(ha) * r * 0.5); set_col(ctx, '#1A1E22'); ctx.set_line_width(14); ctx.stroke()
        ctx.move_to(0, 0); ctx.line_to(math.sin(a) * r * 0.82, -math.cos(a) * r * 0.82); set_col(ctx, PAL.RED); ctx.set_line_width(9); ctx.stroke()
        circle(ctx, 0, 0, 14); set_col(ctx, '#1A1E22'); ctx.fill()


def paper_card(ctx, w, h, col='#F6F1E2', shadow=True):
    if shadow:
        rrect(ctx, -w / 2 + 10, -h / 2 + 16, w, h, 6); ctx.set_source_rgba(0.2, 0.12, 0.04, 0.3); ctx.fill()
    rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, '#3A2E22', 0.6); ctx.set_line_width(2); ctx.stroke()


class MenuCard(Element):
    """Diner menu: header + lines; last line '???' big; shark line circled at t_circle."""
    def __init__(self, t_items=(0.1, 0.35, 0.6), t_circle=0.9, t_big=1.3, **kw):
        super().__init__(**kw); self.ti, self.tc, self.tb = t_items, t_circle, t_big
    def draw(self, ctx, t):
        ctx.rotate(math.radians(1.2 * math.sin(t * 0.8)))
        w, h = 760, 860
        paper_card(ctx, w, h)
        rrect(ctx, -w / 2 + 24, -h / 2 + 24, w - 48, h - 48, 4); set_col(ctx, '#7A2A22'); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, 'ORCA CAFÉ', 0, -h / 2 + 120, 'black', 74, '#2A2F30', 0.04, 'center', shadow=False)
        draw_text(ctx, 'TODAY\u2019S MENU', 0, -h / 2 + 172, 'bold', 26, '#7A2A22', 0.24, 'center', shadow=False)
        ctx.move_to(-w / 2 + 80, -h / 2 + 200); ctx.line_to(w / 2 - 80, -h / 2 + 200); set_col(ctx, '#2A2F30', 0.5); ctx.set_line_width(2); ctx.stroke()
        items = [('SEAL', 46), ('GREAT WHITE (LIVER ONLY)', 40)]
        y = -h / 2 + 300
        for i, (txt, sz) in enumerate(items):
            if t >= self.ti[i]:
                a = min(1, (t - self.ti[i]) / 0.15)
                draw_text(ctx, txt, 0, y, 'black', sz, '#2A2F30', 0.03, 'center', shadow=False, alpha=a)
            y += 110
        # circle the shark line
        if t >= self.tc:
            k = ease('eo', min(1, (t - self.tc) / 0.4))
            ctx.save(); ctx.translate(0, -h / 2 + 398); ctx.scale(1, 0.2)
            ctx.arc(0, 0, 330, -2.6, -2.6 + TAU * 1.03 * k); ctx.restore()
            set_col(ctx, PAL.RED); ctx.set_line_width(6); ctx.stroke()
        if t >= self.tb:
            k = ease('back', min(1, (t - self.tb) / 0.25))
            ctx.save(); ctx.translate(0, -h / 2 + 640); ctx.scale(k, k)
            draw_text(ctx, '? ? ?', 0, 40, 'black', 150, '#7A2A22', 0.06, 'center', shadow=False)
            ctx.restore()
            draw_text(ctx, 'ASK YOUR SERVER', 0, h / 2 - 70, 'bold', 22, '#2A2F30', 0.24, 'center', shadow=False, alpha=min(1, (t - self.tb) / 0.3))


class FieldReport(Element):
    """Research report sheet on paper, with header lines and a small figure box."""
    def __init__(self, figure=None, **kw):
        super().__init__(**kw); self.fig = figure
    def draw(self, ctx, t):
        ctx.rotate(math.radians(-2 + 0.6 * math.sin(t * 0.7)))
        w, h = 980, 700
        paper_card(ctx, w, h, '#F4EEDC')
        draw_text(ctx, 'FIELD REPORT', -w / 2 + 60, -h / 2 + 90, 'black', 54, '#2A2F30', 0.04, shadow=False)
        draw_text(ctx, 'OFF WESTERN AUSTRALIA \u2014 MARCH 2019', -w / 2 + 62, -h / 2 + 136, 'bold', 22, '#7A2A22', 0.18, shadow=False)
        ctx.move_to(-w / 2 + 60, -h / 2 + 160); ctx.line_to(w / 2 - 60, -h / 2 + 160); set_col(ctx, '#2A2F30', 0.6); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, 'ORCAS ATTACK ADULT BLUE WHALE', -w / 2 + 60, -h / 2 + 222, 'black', 40, '#2A2F30', 0.02, shadow=False)
        r = rng(2)
        for i in range(7):
            L = r.uniform(0.6, 1.0) * 470
            rrect(ctx, -w / 2 + 60, -h / 2 + 270 + i * 40, L, 14, 4); set_col(ctx, '#2A2F30', 0.18); ctx.fill()
        bx, by, bw, bh = 90, -h / 2 + 260, 330, 260
        rrect(ctx, bx, by, bw, bh, 4); set_col(ctx, '#1E5566'); ctx.fill()
        if self.fig is not None:
            ctx.save(); ctx.rectangle(bx, by, bw, bh); ctx.clip(); ctx.translate(bx, by); self.fig(ctx, t, bw, bh); ctx.restore()
        rrect(ctx, bx, by, bw, bh, 4); set_col(ctx, '#2A2F30'); ctx.set_line_width(3); ctx.stroke()
        draw_text(ctx, 'FIG. 1', bx, by + bh + 32, 'bold', 18, '#2A2F30', 0.2, shadow=False)


class Clipboard(Element):
    """Clipboard 'SURVIVAL PLAN' with '1. BE ENORMOUS' struck through at t_strike."""
    def __init__(self, t_strike=1e9, figure=None, **kw):
        super().__init__(**kw); self.ts, self.fig = t_strike, figure
    def draw(self, ctx, t):
        ctx.rotate(math.radians(3 + 0.8 * math.sin(t * 0.9)))
        w, h = 700, 900
        rrect(ctx, -w / 2 + 12, -h / 2 + 18, w, h, 24); ctx.set_source_rgba(0.2, 0.12, 0.04, 0.35); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 24); set_col(ctx, '#B9875A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        paper_card(ctx, w - 70, h - 90, '#F7F4EC', shadow=False)
        rrect(ctx, -120, -h / 2 - 30, 240, 70, 14); set_col(ctx, '#9AA3A8'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        draw_text(ctx, 'SURVIVAL PLAN', 0, -h / 2 + 130, 'black', 62, '#2A2F30', 0.04, 'center', shadow=False)
        draw_text(ctx, 'SPECIES: BLUE WHALE', 0, -h / 2 + 176, 'bold', 22, '#7A2A22', 0.22, 'center', shadow=False)
        if self.fig is not None:
            bx, by, bw, bh = -230, -h / 2 + 210, 460, 230
            ctx.save(); rrect(ctx, bx, by, bw, bh, 4); ctx.clip(); set_col(ctx, '#1E5566'); ctx.paint()
            ctx.translate(bx, by); self.fig(ctx, t, bw, bh); ctx.restore()
            rrect(ctx, bx, by, bw, bh, 4); set_col(ctx, '#2A2F30'); ctx.set_line_width(3); ctx.stroke()
        y = -h / 2 + 560
        draw_text(ctx, '1. BE ENORMOUS', -250, y, 'black', 54, '#2A2F30', 0.03, shadow=False)
        tw = measure(ctx, '1. BE ENORMOUS', 'black', 54, 0.03)[0]
        if t >= self.ts:
            k = ease('eo', min(1, (t - self.ts) / (10 / 30)))
            ctx.move_to(-262, y - 18); ctx.line_to(-262 + (tw + 24) * k, y - 22)
            set_col(ctx, PAL.RED); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        for i in range(2):
            draw_text(ctx, f'{i + 2}.', -250, y + 100 + i * 90, 'black', 54, '#2A2F30', 0.03, shadow=False, alpha=0.35)
            ctx.move_to(-180, y + 100 + i * 90); ctx.line_to(250, y + 100 + i * 90); set_col(ctx, '#2A2F30', 0.25); ctx.set_line_width(2); ctx.stroke()


class SurgTray(Element):
    """Surgical tray with scalpel + forceps; slides in from the right over 0.35 s."""
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.35)); ctx.translate(500 * (1 - k), 0)
        rrect(ctx, -250 + 8, -110 + 14, 500, 220, 24); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.fill()
        rrect(ctx, -250, -110, 500, 220, 24); set_col(ctx, '#AEB9BE'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -226, -88, 452, 176, 16); set_col(ctx, '#C9D3D7'); ctx.fill()
        # scalpel
        ctx.save(); ctx.translate(-40, -30); ctx.rotate(-0.12)
        rrect(ctx, -180, -9, 220, 18, 6); set_col(ctx, '#5F6E78'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        ctx.move_to(40, -8); ctx.line_to(150, -14); ctx.curve_to(180, -6, 170, 10, 150, 10); ctx.line_to(40, 8); ctx.close_path()
        set_col(ctx, '#E8EDEF'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        g = (t * 0.7) % 1.0   # glint sweeping the blade
        ctx.move_to(40 + 120 * g, -10); ctx.line_to(52 + 120 * g, -10); ctx.line_to(46 + 120 * g, 8); ctx.line_to(34 + 120 * g, 8); ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, 0.9); ctx.fill()
        ctx.restore()
        # forceps
        ctx.save(); ctx.translate(-20, 45); ctx.rotate(0.05)
        for s in (1, -1):
            ctx.move_to(-170, 0); ctx.line_to(150, s * 14); set_col(ctx, OUT); ctx.set_line_width(10); ctx.stroke()
            ctx.move_to(-170, 0); ctx.line_to(150, s * 14); set_col(ctx, '#DDE3E5'); ctx.set_line_width(6); ctx.stroke()
        ctx.restore()


class TopSplash(Element):
    """Top-down white water burst: irregular blobs expanding and fading over `dur`."""
    def __init__(self, r=220, dur=1.0, seed=2, **kw):
        super().__init__(**kw); self.r, self.d = r, dur
        rr = rng(seed); self.b = [(rr.uniform(0, TAU), rr.uniform(0.3, 1.0), rr.uniform(14, 40)) for _ in range(26)]
    def draw(self, ctx, t):
        k = t / self.d
        if k >= 1: return
        a = (1 - k) ** 1.5
        for (ang, d, s) in self.b:
            rr = self.r * d * ease('eo', k)
            circle(ctx, math.cos(ang) * rr, math.sin(ang) * rr, s * (1 - 0.5 * k)); ctx.set_source_rgba(1, 1, 1, 0.85 * a); ctx.fill()
        circle(ctx, 0, 0, self.r * 0.9 * ease('eo', k)); ctx.set_source_rgba(1, 1, 1, 0.5 * a); ctx.set_line_width(10); ctx.stroke()


class SightingsGraph(Element):
    """Small data card: 'SHARK SIGHTINGS' line that runs flat then drops to ~0."""
    def __init__(self, t_draw=0.0, t_drop=0.6, w=460, h=250, **kw):
        super().__init__(**kw); self.td, self.tdrop, self.w, self.h = t_draw, t_drop, w, h
    def draw(self, ctx, t):
        w, h = self.w, self.h
        a = min(1, t / 0.15)
        rrect(ctx, 0, 0, w, h, 10); ctx.set_source_rgba(0.04, 0.09, 0.11, 0.88 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.8 * a); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, 'SHARK SIGHTINGS', 24, 44, 'bold', 22, PAL.WHITE, 0.22, shadow=False, alpha=a)
        x0, x1, y0, y1 = 30, w - 30, 80, h - 36
        ctx.move_to(x0, y0); ctx.line_to(x0, y1); ctx.line_to(x1, y1); set_col(ctx, PAL.WHITE, 0.35 * a); ctx.set_line_width(2); ctx.stroke()
        r = rng(4)
        pts = []
        for i in range(31):
            u = i / 30
            v = 0.75 + 0.12 * math.sin(i * 1.3) + r.uniform(-0.05, 0.05)
            if u > 0.6: v *= max(0.04, 1 - (u - 0.6) / 0.12)
            pts.append((x0 + u * (x1 - x0), y1 - v * (y1 - y0)))
        k = min(1, max(0, (t - self.td) / max(0.01, self.tdrop + 0.6 - self.td)))
        n = max(2, int(len(pts) * k))
        ctx.move_to(*pts[0])
        for p in pts[1:n]: ctx.line_to(*p)
        set_col(ctx, PAL.RED if k > 0.62 else PAL.CYAN, a); ctx.set_line_width(4); ctx.stroke()
        if n > 2:
            circle(ctx, *pts[n - 1], 6); set_col(ctx, PAL.WHITE, a); ctx.fill()


class IconRow(Element):
    """Row of icons ticking in at given local times (centred on origin)."""
    def __init__(self, name='orca', times=(), r=30, gap=78, color=PAL.WHITE, **kw):
        super().__init__(**kw); self.name, self.times, self.r, self.gap, self.c = name, list(times), r, gap, color
    def draw(self, ctx, t):
        n = len(self.times); x0 = -(n - 1) * self.gap / 2
        for i, ti in enumerate(self.times):
            if t < ti: continue
            k = ease('back', min(1, (t - ti) / 0.15))
            ctx.save(); ctx.translate(x0 + i * self.gap, 0); ctx.scale(k, k)
            circle(ctx, 0, 0, self.r + 8); ctx.set_source_rgba(0.04, 0.06, 0.08, 0.75); ctx.fill_preserve()
            set_col(ctx, self.c); ctx.set_line_width(2.4); ctx.stroke()
            icon(ctx, self.name, self.r * 0.8, self.c)
            ctx.restore()


class FadeIn(Element):
    """Full-frame black that fades out over `dur` (dip-from-black at an act head)."""
    def __init__(self, dur=0.4, **kw):
        kw.setdefault('layer', 'overlay'); kw.setdefault('z', 99)
        super().__init__(**kw); self.d = dur
    def draw(self, ctx, t):
        a = 1 - ease('eo', min(1, t / self.d))
        if a > 0: ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(0, 0, W, H); ctx.fill()
