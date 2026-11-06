"""Act A (croc cold open) custom assets. Pure code; never edits shared engine files."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import (W, H, TAU, PAL, Element, ev, set_col, hexc, mix, circle, rrect, poly, catmull, rng,
                         remap, ease, K)
from engine.text import draw_text, measure, cap_height, set_font

SKIN = '#D9A57E'
SKIN_DK = '#A8724F'
SCALE = '#4E5B45'
SCALE_DK = '#2E3829'
TOOTH = '#EDE6D2'


def corner_box(ctx, box, arm=40, col=PAL.WHITE, a=0.9, w=2.4):
    x0, y0, x1, y1 = box
    set_col(ctx, col, a); ctx.set_line_width(w)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ctx.move_to(cx, cy + sy * arm); ctx.line_to(cx, cy); ctx.line_to(cx + sx * arm, cy)
    ctx.stroke()


# ============================================================== Cape York map (blueprint)
WEST = [(142.45, -10.69), (142.30, -10.90), (142.15, -11.30), (142.02, -11.75), (141.92, -12.15), (141.80, -12.60)]
EAST = [(142.55, -10.70), (142.75, -10.86), (142.85, -11.06), (142.88, -11.36), (143.04, -11.60), (143.18, -11.86),
        (143.25, -11.98), (143.30, -12.22), (143.40, -12.60)]
ISLAND = (143.56, -11.90)
COAST_PT = (143.19, -11.88)


class CapeYorkMap(Element):
    """Stylised Cape York tip on a dark map card; dashed orange route from the coast to the islands,
    a distance ruler counting up to 40 KM. pin=t shows a pulsing island pin from local t."""
    def __init__(self, box=(160, 150, 1760, 990), t_route=0.2, route_dur=1.4, ruler=True, pin=None, **kw):
        super().__init__(**kw)
        self.box, self.t_route, self.route_dur, self.ruler, self.pin = box, t_route, route_dur, ruler, pin
        self.lon = (141.0, 145.0); x0, y0, x1, y1 = box
        span = (self.lon[1] - self.lon[0]) * (y1 - y0) / (x1 - x0)
        self.lat = (-10.35, -10.35 - span)

    def xy(self, lon, lat):
        x0, y0, x1, y1 = self.box
        u = (lon - self.lon[0]) / (self.lon[1] - self.lon[0]); v = (lat - self.lat[0]) / (self.lat[1] - self.lat[0])
        return x0 + u * (x1 - x0), y0 + v * (y1 - y0)

    def draw(self, ctx, t):
        x0, y0, x1, y1 = self.box
        ctx.save(); ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.clip()
        ctx.set_source_rgba(0.03, 0.12, 0.15, 0.85); ctx.paint()
        ctx.set_source_rgba(0.5, 0.75, 0.8, 0.10); ctx.set_line_width(1.5)
        cx, cy = self.xy(*ISLAND)
        for i in range(7):
            ctx.save(); ctx.translate(cx, cy); ctx.scale(1.0, 0.55)
            circle(ctx, 0, 0, 90 + i * 85 + 6 * math.sin(t * 0.8 + i)); ctx.restore(); ctx.stroke()
        w = catmull([self.xy(*p) for p in WEST], 8); e = catmull([self.xy(*p) for p in EAST], 8)
        ctx.move_to(*e[0])
        for p in e[1:]: ctx.line_to(*p)
        ctx.line_to(e[-1][0], y1 + 50); ctx.line_to(x0 - 50, y1 + 50); ctx.line_to(x0 - 50, w[-1][1])
        for p in w[::-1]: ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgba(0.11, 0.25, 0.30, 0.95); ctx.fill_preserve()
        set_col(ctx, PAL.CYAN, 0.9); ctx.set_line_width(3); ctx.stroke()
        # islands
        for dx, dy, r in ((0, 0, 9), (0.05, 0.03, 6), (-0.03, 0.05, 5)):
            ix, iy = self.xy(ISLAND[0] + dx, ISLAND[1] + dy)
            circle(ctx, ix, iy, r); set_col(ctx, PAL.CYAN); ctx.fill()
        lx, ly = self.xy(142.3, -11.5)
        draw_text(ctx, 'CAPE YORK', lx, ly, 'bold', 32, PAL.CYAN_HI, 0.3, 'center')
        draw_text(ctx, 'AUSTRALIA', lx, ly + 44, 'bold', 20, PAL.GREY, 0.3, 'center')
        sx, sy = self.xy(143.7, -11.15)
        draw_text(ctx, 'CORAL SEA', sx, sy, 'bold', 24, PAL.GREY, 0.4, 'center')
        ctx.restore()
        corner_box(ctx, self.box)
        lt = t - self.t_route
        a = self.xy(*COAST_PT); b = self.xy(*ISLAND)
        if lt > 0:
            k = ease('eio', min(1, lt / self.route_dur))
            ex, ey = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
            ctx.set_dash([16, 10], -t * 30); ctx.move_to(*a); ctx.line_to(ex, ey)
            set_col(ctx, PAL.ORANGE); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])
            circle(ctx, *a, 8); set_col(ctx, PAL.ORANGE); ctx.fill()
            circle(ctx, ex, ey, 22 + 4 * math.sin(t * 5)); ctx.set_source_rgba(0.94, 0.65, 0.29, 0.3); ctx.fill()
            circle(ctx, ex, ey, 9); set_col(ctx, PAL.WHITE); ctx.fill()
            if self.ruler:
                ry = a[1] + 90
                ctx.move_to(a[0], ry); ctx.line_to(a[0] + (b[0] - a[0]) * k, ry)
                set_col(ctx, PAL.WHITE); ctx.set_line_width(3); ctx.stroke()
                for i in range(5):
                    xx = a[0] + (b[0] - a[0]) * i / 4
                    if xx <= a[0] + (b[0] - a[0]) * k + 1:
                        ctx.move_to(xx, ry - (16 if i % 2 == 0 else 9)); ctx.line_to(xx, ry); ctx.stroke()
                draw_text(ctx, f'{int(round(40 * k))} KM', (a[0] + b[0]) / 2, ry + 62, 'xb', 52, PAL.WHITE, 0.02, 'center')
        if self.pin is not None and t >= self.pin:
            pk = ease('back', min(1, (t - self.pin) / 0.25))
            ctx.save(); ctx.translate(b[0], b[1] - 4); ctx.scale(pk, pk)
            ctx.move_to(0, 0); ctx.curve_to(-26, -40, -30, -60, -30, -76); ctx.arc(0, -76, 30, math.pi, 0)
            ctx.curve_to(30, -60, 26, -40, 0, 0); set_col(ctx, PAL.RED); ctx.fill()
            circle(ctx, 0, -76, 11); set_col(ctx, PAL.WHITE); ctx.fill()
            ctx.restore()
            rr = 30 + 60 * ((t - self.pin) % 1.2) / 1.2
            ctx.save(); ctx.translate(*b); ctx.scale(1, 0.5); circle(ctx, 0, 0, rr); ctx.restore()
            ctx.set_source_rgba(0.84, 0.25, 0.24, 0.6 * (1 - ((t - self.pin) % 1.2) / 1.2)); ctx.set_line_width(3); ctx.stroke()


# ============================================================== mask POV overlay
class MaskPOV(Element):
    """Snorkel-mask frame (screen space): black surround with two rounded lens windows, fogged rim."""
    def __init__(self, **kw):
        kw.setdefault('layer', 'overlay'); kw.setdefault('z', 50); super().__init__(**kw)

    def _windows(self, ctx):
        rrect(ctx, 150, 110, 780, 820, 260)
        rrect(ctx, 990, 110, 780, 820, 260)

    def draw(self, ctx, t):
        ctx.save()
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-60, -60, W + 120, H + 120); self._windows(ctx)
        set_col(ctx, '#05090B'); ctx.fill()
        ctx.restore()
        # nose bridge
        ctx.move_to(930, 1100); ctx.curve_to(930, 760, 990, 760, 990, 1100); set_col(ctx, '#05090B'); ctx.fill()
        # glass rim + fog
        ctx.save(); self._windows(ctx); ctx.clip()
        for (cx) in (540, 1380):
            g = cairo.RadialGradient(cx, 520, 250, cx, 520, 560)
            g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.85, 0.95, 1, 0.22)
            ctx.set_source(g); ctx.paint()
        # glint
        ctx.set_source_rgba(1, 1, 1, 0.10 + 0.04 * math.sin(t * 2)); ctx.move_to(260, 230); ctx.line_to(420, 180); ctx.line_to(330, 420); ctx.line_to(230, 470); ctx.close_path(); ctx.fill()
        ctx.restore()
        self._windows(ctx); ctx.set_source_rgba(0.15, 0.2, 0.22, 1); ctx.set_line_width(14); ctx.stroke()


# ============================================================== jaw closing silhouette
class JawClose(Element):
    """Dark irregular jaw outline closing in from the frame edges. close=K radius scale 1..0."""
    def __init__(self, close=1.0, inner='#1C6E72', **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw); self.close, self.inner = close, inner

    def draw(self, ctx, t):
        c = ev(self.close, t)
        R = 300 + 900 * c
        ctx.save(); ctx.translate(W / 2, H / 2)
        pts = []
        for i in range(120):
            a = i / 120 * TAU
            r = R * (1 + 0.05 * math.sin(a * 7 + 0.6) + 0.025 * math.sin(a * 23) + 0.012 * math.sin(t * 3 + a * 5))
            pts.append((r * math.cos(a) * 1.25, r * math.sin(a) * 0.95))
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-W, -H, W * 2, H * 2); poly(ctx, pts)
        set_col(ctx, '#020605'); ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        poly(ctx, pts); ctx.set_source_rgba(0.31, 0.36, 0.27, 0.9); ctx.set_line_width(10); ctx.stroke()
        # scute bumps on rim
        for i in range(0, 120, 4):
            x, y = pts[i]
            circle(ctx, x * 1.04, y * 1.04, 14); ctx.set_source_rgba(0.19, 0.23, 0.17, 1); ctx.fill()
        ctx.restore()


# ============================================================== thought bubble
class ThoughtBubble(Element):
    """White outline thought bubble with trailing dots, pops in."""
    def __init__(self, r=230, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw); self.r = r
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.25)); r = self.r * k
        a = min(1, t / 0.15)
        for i, (dx, dy, rr) in enumerate(((-r * 0.9, r * 1.15, 18), (-r * 1.15, r * 1.45, 11))):
            if t > 0.1 * (i + 1):
                circle(ctx, dx, dy, rr); ctx.set_source_rgba(0.95, 0.94, 0.92, 0.9 * a); ctx.fill()
        pts = []
        for i in range(10):
            ang = i / 10 * TAU
            pts.append((math.cos(ang) * r * 1.2, math.sin(ang) * r * 0.85))
        for (x, y) in pts:
            circle(ctx, x, y, r * 0.42)
        ctx.set_source_rgba(0.95, 0.94, 0.92, 0.92 * a); ctx.fill()
        ctx.save(); ctx.scale(1.2, 0.85); circle(ctx, 0, 0, r); ctx.restore()
        ctx.set_source_rgba(0.95, 0.94, 0.92, 0.95 * a); ctx.fill()


# ============================================================== hands reaching up + scaled edge
def _hand(ctx, flip):
    ctx.save()
    if flip: ctx.scale(-1, 1)
    # forearm
    ctx.move_to(-55, 520); ctx.line_to(-62, 60); ctx.line_to(60, 60); ctx.line_to(70, 520); ctx.close_path()
    set_col(ctx, '#1F6F86'); ctx.fill()
    rrect(ctx, -68, 40, 136, 40, 10); set_col(ctx, '#174F60'); ctx.fill()
    # palm
    rrect(ctx, -62, -80, 124, 140, 38); set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, SKIN_DK); ctx.set_line_width(5); ctx.stroke()
    for i, (dx, ln) in enumerate(((-44, 92), (-15, 112), (14, 108), (42, 88))):
        rrect(ctx, dx - 14, -80 - ln, 28, ln + 30, 14); set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, SKIN_DK); ctx.stroke()
    ctx.save(); ctx.translate(-62, -10); ctx.rotate(-0.7)
    rrect(ctx, -14, -80, 28, 90, 14); set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, SKIN_DK); ctx.stroke()
    ctx.restore()
    ctx.restore()


class Hands(Element):
    """Two flat hands reaching up from the bottom of frame. grope=1 small wiggle."""
    def __init__(self, gap=520, grope=1.0, **kw):
        super().__init__(**kw); self.gap, self.grope = gap, grope
    def draw(self, ctx, t):
        for s, ph in ((-1, 0), (1, 1.3)):
            ctx.save(); ctx.translate(s * self.gap / 2, 8 * math.sin(t * 3 + ph) * self.grope)
            ctx.rotate(s * (0.18 + 0.03 * math.sin(t * 2.4 + ph)))
            _hand(ctx, s > 0)
            ctx.restore()


class ScaleEdge(Element):
    """Rough armoured croc skin band across the top of the frame (stylised scutes), reveal=K 0..1 (slides down)."""
    def __init__(self, reveal=1.0, depth=330, **kw):
        super().__init__(**kw); self.reveal, self.depth = reveal, depth
    def draw(self, ctx, t):
        k = ev(self.reveal, t)
        d = self.depth * k
        if d <= 1: return
        ctx.save(); ctx.translate(0, -self.depth + d)
        edge = [(x, self.depth + 26 * math.sin(x * 0.011 + 0.5) + 10 * math.sin(x * 0.05)) for x in range(-100, W + 140, 40)]
        ctx.move_to(-100, -200)
        for p in edge: ctx.line_to(*p)
        ctx.line_to(W + 140, -200); ctx.close_path()
        set_col(ctx, SCALE); ctx.fill_preserve(); ctx.save(); ctx.clip()
        r = rng(4)
        for row in range(6):
            y = self.depth - 30 - row * 62
            off = 0 if row % 2 == 0 else 55
            for i in range(-1, 19):
                x = i * 110 + off
                rrect(ctx, x - 46, y - 26, 92 + r.uniform(-8, 8), 50, 14)
                set_col(ctx, mix(SCALE, SCALE_DK, 0.35 + 0.3 * r.random())); ctx.fill_preserve()
                set_col(ctx, SCALE_DK); ctx.set_line_width(4); ctx.stroke()
                circle(ctx, x, y - 4, 7); set_col(ctx, '#66745A'); ctx.fill()
        ctx.restore()
        ctx.move_to(*edge[0])
        for p in edge[1:]: ctx.line_to(*p)
        set_col(ctx, '#1C231A'); ctx.set_line_width(8); ctx.stroke()
        ctx.restore()


# ============================================================== teeth ring
class TeethRing(Element):
    """Conical teeth appearing one after another around an ellipse at the frame edge (screen space)."""
    def __init__(self, n=30, rx=900, ry=500, dur=1.0, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw); self.n, self.rx, self.ry, self.d = n, rx, ry, dur
    def draw(self, ctx, t):
        ctx.save(); ctx.translate(W / 2, H / 2)
        # gum band (dark) outside the ellipse
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-W, -H, W * 2, H * 2)
        ctx.save(); ctx.scale(self.rx + 40, self.ry + 40); circle(ctx, 0, 0, 1); ctx.restore()
        ctx.set_source_rgba(0.12, 0.05, 0.05, min(1, t / 0.3) * 0.95); ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        for i in range(self.n):
            ti = self.d * i / self.n
            if t < ti: continue
            k = ease('back', min(1, (t - ti) / 0.12))
            a = -math.pi / 2 + i / self.n * TAU
            x, y = (self.rx + 40) * math.cos(a), (self.ry + 40) * math.sin(a)
            L = (70 + 30 * ((i * 7) % 3)) * k
            ctx.save(); ctx.translate(x, y); ctx.rotate(a + math.pi / 2)
            ctx.move_to(-24, 0); ctx.curve_to(-18, L * 0.6, -4, L, 0, L); ctx.curve_to(4, L, 18, L * 0.6, 24, 0); ctx.close_path()
            set_col(ctx, TOOTH); ctx.fill_preserve(); set_col(ctx, '#2A2620'); ctx.set_line_width(4); ctx.stroke()
            ctx.restore()
        ctx.restore()


# ============================================================== generic clipped card (panel / postcard)
class Panel(Element):
    """Bracketed panel: clips children to its box (local coords centred on pos); pops in at t0; caption below."""
    def __init__(self, w=520, h=560, caption='', cap_color=PAL.WHITE, bg='#0E3140', cap_size=36, **kw):
        super().__init__(**kw); self.w, self.h, self.cap, self.cc, self.bg, self.cs = w, h, caption, cap_color, bg, cap_size

    def render(self, ctx, t):
        if not self.visible(t): return
        lt = t - self.t0
        pos, sc, rot, op = self.props(lt)
        k = min(1, lt / (4 / 30)); s = 0.9 + 0.1 * ease('eo', k)
        if isinstance(sc, tuple): sx, sy = sc
        else: sx = sy = sc
        ctx.save(); ctx.translate(*pos); ctx.rotate(math.radians(rot)); ctx.scale(s * sx, s * sy)
        w, h = self.w, self.h
        ctx.push_group()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, self.bg); ctx.fill()
        ctx.save(); rrect(ctx, -w / 2, -h / 2, w, h, 6); ctx.clip()
        for c in sorted(self.children, key=lambda c: c.z): c.render(ctx, lt)
        ctx.restore()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, PAL.WHITE, 0.35); ctx.set_line_width(2); ctx.stroke()
        corner_box(ctx, (-w / 2 - 12, -h / 2 - 12, w / 2 + 12, h / 2 + 12), arm=36)
        if self.cap:
            draw_text(ctx, self.cap, 0, h / 2 + 60, 'xb', self.cs, self.cc, 0.06, 'center')
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, op * (0.3 + k)))
        ctx.restore()


class Postcard(Element):
    """Vintage postcard: cream border, scene clipped inside (children), headline at the top. flip=K x-scale."""
    def __init__(self, w=1300, h=820, title='GREETINGS FROM THE RIVER!', flip=1.0, **kw):
        super().__init__(**kw); self.w, self.h, self.title, self.flip = w, h, title, flip
    def render(self, ctx, t):
        if not self.visible(t): return
        lt = t - self.t0
        pos, sc, rot, op = self.props(lt)
        fx = ev(self.flip, lt)
        ctx.save(); ctx.translate(*pos); ctx.rotate(math.radians(rot)); ctx.scale(sc * max(0.001, abs(fx)), sc)
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 14, -h / 2 + 18, w, h, 10); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 10); set_col(ctx, '#F3EBD3'); ctx.fill()
        iw, ih = w - 60, h - 60
        ctx.save(); rrect(ctx, -iw / 2, -ih / 2, iw, ih, 6); ctx.clip()
        g = cairo.LinearGradient(0, -ih / 2, 0, ih / 2)
        g.add_color_stop_rgba(0, *hexc('#F6C46B')); g.add_color_stop_rgba(0.5, *hexc('#F3DDA6')); g.add_color_stop_rgba(0.5, *hexc('#5E8A73'))
        g.add_color_stop_rgba(1, *hexc('#3D6656'))
        ctx.set_source(g); ctx.paint()
        circle(ctx, iw * 0.28, -ih * 0.18, 90); set_col(ctx, '#F9E3A8'); ctx.fill()
        for c in sorted(self.children, key=lambda c: c.z): c.render(ctx, lt)
        ctx.restore()
        rrect(ctx, -iw / 2, -ih / 2, iw, ih, 6); set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
        # headline banner
        set_font(ctx, 'black', 64)
        tw = measure(ctx, self.title, 'black', 64, 0.02)[0]
        ctx.save(); ctx.translate(0, -ih / 2 + 90); ctx.rotate(-0.03)
        rrect(ctx, -tw / 2 - 30, -70, tw + 60, 96, 8); set_col(ctx, PAL.RED); ctx.fill()
        draw_text(ctx, self.title, 0, 0, 'black', 64, '#FFF6E2', 0.02, 'center', shadow=False)
        ctx.restore()
        ctx.restore()


class MudBank(Element):
    """Flat cartoon mud bank + reeds for the postcard."""
    def draw(self, ctx, t):
        ctx.move_to(-700, 60); ctx.curve_to(-300, -40, 200, -50, 700, 30); ctx.line_to(700, 400); ctx.line_to(-700, 400); ctx.close_path()
        set_col(ctx, '#8A6A45'); ctx.fill()
        ctx.move_to(-700, 60); ctx.curve_to(-300, -40, 200, -50, 700, 30); set_col(ctx, '#6B5132'); ctx.set_line_width(6); ctx.stroke()
        for i in range(9):
            x = -560 + i * 140
            sw = 8 * math.sin(t * 1.5 + i)
            ctx.move_to(x, 0); ctx.curve_to(x + 4, -60, x + sw, -110, x + sw * 1.5, -150)
            set_col(ctx, '#4E6B3A'); ctx.set_line_width(7); ctx.stroke()


class Zzz(Element):
    def draw(self, ctx, t):
        for i in range(3):
            k = ((t * 0.6) + i / 3) % 1.0
            draw_text(ctx, 'Z', 40 * k + i * 6, -110 * k, 'black', 34 + 30 * k, PAL.INK, 0, 'center', shadow=False, alpha=1 - k)


# ============================================================== bite gauge
class BiteGauge(Element):
    """Semicircular force gauge; needle swings into the red at t_hit and jitters."""
    def __init__(self, r=300, t_hit=1.0, **kw):
        super().__init__(**kw); self.r, self.th = r, t_hit
    def draw(self, ctx, t):
        r = self.r
        segs = [(PAL.GREEN, 0, 0.45), (PAL.ORANGE, 0.45, 0.75), (PAL.RED, 0.75, 1.0)]
        for col, a0, a1 in segs:
            ctx.arc(0, 0, r, math.pi + a0 * math.pi, math.pi + a1 * math.pi)
            set_col(ctx, col); ctx.set_line_width(38); ctx.stroke()
        for i in range(11):
            a = math.pi + i / 10 * math.pi
            ctx.move_to(math.cos(a) * (r - 40), math.sin(a) * (r - 40)); ctx.line_to(math.cos(a) * (r - 64), math.sin(a) * (r - 64))
            set_col(ctx, PAL.WHITE, 0.8); ctx.set_line_width(4); ctx.stroke()
        v = 0.12 + 0.05 * math.sin(t * 2)
        if t > self.th:
            v = 0.12 + (0.97 - 0.12) * ease('eo', min(1, (t - self.th) / 0.5)) + 0.012 * math.sin(t * 40)
        a = math.pi + v * math.pi
        ctx.move_to(0, 0); ctx.line_to(math.cos(a) * (r - 30), math.sin(a) * (r - 30))
        set_col(ctx, PAL.WHITE); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        circle(ctx, 0, 0, 22); set_col(ctx, PAL.WHITE); ctx.fill()


# ============================================================== gap gauge
class GapGauge(Element):
    """Cyan vertical bracket gauge measuring the jaw gap: opens from 0 to `full` px with gap=K 0..1."""
    def __init__(self, gap=0.0, full=220, label='JUST ENOUGH', t_label=1.0, **kw):
        super().__init__(**kw); self.gap, self.full, self.label, self.tl = gap, full, label, t_label
    def draw(self, ctx, t):
        g = ev(self.gap, t) * self.full
        set_col(ctx, PAL.CYAN_HI); ctx.set_line_width(4)
        ctx.move_to(0, -g / 2); ctx.line_to(0, g / 2); ctx.stroke()
        for y in (-g / 2, g / 2):
            ctx.move_to(-18, y); ctx.line_to(18, y); ctx.stroke()
        if t > self.tl:
            draw_text(ctx, self.label, 0, -self.full / 2 - 40, 'xb', 40, PAL.CYAN_HI, 0.06, 'center', alpha=min(1, (t - self.tl) / 0.15))


# ============================================================== misc
class FadeIn(Element):
    def __init__(self, dur=0.6, **kw):
        kw.setdefault('layer', 'overlay'); kw.setdefault('z', 99); super().__init__(**kw); self.d = dur
    def draw(self, ctx, t):
        a = 1 - min(1, t / self.d)
        if a > 0: ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(-50, -50, W + 100, H + 100); ctx.fill()


class Ripples(Element):
    def __init__(self, period=1.4, n=3, rmax=180, alpha=0.5, **kw):
        super().__init__(**kw); self.period, self.n, self.rmax, self.al = period, n, rmax, alpha
    def draw(self, ctx, t):
        for i in range(self.n):
            k = ((t / self.period) + i / self.n) % 1.0
            ctx.save(); ctx.scale(1, 0.18); circle(ctx, 0, 0, 20 + self.rmax * k); ctx.restore()
            ctx.set_source_rgba(0.85, 0.93, 0.96, self.al * (1 - k)); ctx.set_line_width(2.5); ctx.stroke()


class Underline(Element):
    def __init__(self, w=900, dur=0.4, color=PAL.ORANGE, width=8, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw); self.w, self.d, self.c, self.lw = w, dur, color, width
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / self.d))
        ctx.move_to(-self.w / 2, 0); ctx.line_to(-self.w / 2 + self.w * k, 0)
        set_col(ctx, self.c); ctx.set_line_width(self.lw); ctx.set_line_cap(cairo.LINE_CAP_BUTT); ctx.stroke()


class Waterline(Element):
    """Thin animated white waterline across the screen (title card)."""
    def __init__(self, w=1400, **kw):
        super().__init__(**kw); self.w = w
    def draw(self, ctx, t):
        ctx.move_to(-self.w / 2, 0)
        for x in range(int(-self.w / 2), int(self.w / 2) + 1, 20):
            ctx.line_to(x, 3 * math.sin(x * 0.02 + t * 2.5))
        ctx.set_source_rgba(0.85, 0.93, 0.96, 0.6); ctx.set_line_width(2.5); ctx.stroke()


class WordReveal(Element):
    """Words appear grey->white at given local times (centred at pos, baseline y=0)."""
    def __init__(self, text, times, size=64, font='xb', color=PAL.WHITE, track=0.02, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw)
        self.words, self.times, self.size, self.font, self.c, self.track = text.split(), times, size, font, color, track
        self.text = text
    def draw(self, ctx, t):
        tw = measure(ctx, self.text, self.font, self.size, self.track)[0]
        x = -tw / 2
        set_font(ctx, self.font, self.size); sp = ctx.text_extents(' ')[4]
        for wd, tt in zip(self.words, self.times):
            ww = measure(ctx, wd, self.font, self.size, self.track)[0]
            if t >= tt:
                k = min(1, (t - tt) / 0.15)
                draw_text(ctx, wd, x, 0, self.font, self.size, mix('#5E6466', self.c, k), self.track, 'left', alpha=min(1, 0.3 + k))
            x += ww + sp


class TouristBoat(Element):
    """Flat white tour boat (side) with a row of tiny tourists, bobbing."""
    def draw(self, ctx, t):
        ctx.save(); ctx.translate(0, 4 * math.sin(t * 2)); ctx.rotate(0.02 * math.sin(t * 1.6))
        ctx.move_to(-200, -20); ctx.line_to(210, -20); ctx.line_to(170, 40); ctx.line_to(-170, 40); ctx.close_path()
        set_col(ctx, PAL.WHITE); ctx.fill_preserve(); set_col(ctx, '#1A2A30'); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -150, -80, 260, 60, 6); set_col(ctx, '#DDE3E3'); ctx.fill_preserve(); set_col(ctx, '#1A2A30'); ctx.stroke()
        for i in range(7):
            x = -130 + i * 38
            circle(ctx, x, -58 + 2 * math.sin(t * 6 + i), 10); set_col(ctx, ['#E08A6B', '#F0A54A', '#7FC1CB', '#D73F3C'][i % 4]); ctx.fill()
        ctx.restore()
