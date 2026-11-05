"""Act F custom assets (chapter 6 + outro). Only used by scenes/act_f.py."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import Element, ev, hexc, mix, set_col, rrect, circle, poly, catmull, W, H, PAL, ease, remap, rng, lerp
from engine.text import draw_text, measure, text_path, cap_height
from engine.ui import UI, icon, Globe, _ortho, _pop
from engine.plates import Surface, Underwater

TAU = math.pi * 2
INK = '#2A2F30'
PAPER = '#EDE6CF'


# ------------------------------------------------------------------ plates
class NightSurface(Surface):
    """Cold-open night look: navy sky, black-teal sea, moon glow."""
    def __init__(self, **kw):
        kw.setdefault('sun', (0.78, 0.16)); kw.setdefault('vignette', 0.5)
        super().__init__('storm', **kw)
        self.p = dict(sky=('#040D14', '#081A26', '#0E2433'), sun='#CFE3EA', sea=('#0B2A35', '#061C25', '#020A0E'),
                      far='#0F2E3A')


class TintedSurface(Surface):
    """Surface plate with a custom palette (e.g. muted peach tragedy dawn)."""
    def __init__(self, palette, **kw):
        super().__init__('dawn', **kw); self.p = palette


DAWN_SOFT = dict(sky=('#C98E7E', '#E7B79E', '#F3D9C0'), sun='#FFF0D8', sea=('#4D6A73', '#243F4A', '#0B1C24'), far='#8A7A78')
DAWN_GREY = dict(sky=('#8E7A7C', '#B79C94', '#D2BCAA'), sun='#F5E6D2', sea=('#3E5960', '#1E353D', '#081519'), far='#776A6A')


# ------------------------------------------------------------------ chapter card props
class Net(Element):
    """Hanging fishing/capture net: catenary mesh that sways, with floats on top."""
    def __init__(self, width=1500, depth=420, cells=22, color='#D9C9B0', alpha=0.55, **kw):
        super().__init__(**kw); self.w, self.d, self.n, self.c, self.a = width, depth, cells, color, alpha

    def pt(self, u, v, t):
        x = -self.w / 2 + u * self.w
        sag = math.sin(u * math.pi)
        y = v * self.d * (0.55 + 0.45 * sag) + 10 * math.sin(t * 0.9 + u * 5 + v * 2) * v
        x += 14 * math.sin(t * 0.7 + v * 3) * v
        return x, y

    def draw(self, ctx, t):
        n = self.n; rows = 9
        set_col(ctx, self.c, self.a); ctx.set_line_width(2.2)
        for i in range(n + 1):
            u = i / n
            for j in range(rows + 1):
                x, y = self.pt(u, j / rows, t)
                (ctx.move_to if j == 0 else ctx.line_to)(x, y)
        ctx.stroke()
        for j in range(rows + 1):
            v = j / rows
            for i in range(n + 1):
                x, y = self.pt(i / n, v, t)
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.stroke()
        # floats
        for i in range(0, n + 1, 2):
            x, y = self.pt(i / n, 0, t)
            circle(ctx, x, y - 4, 11); set_col(ctx, PAL.ORANGE, 0.9); ctx.fill()


class BigArrow(Element):
    """Thick arrow from (x0) to (x1) along y=0 that draws on, label at each end."""
    def __init__(self, length=700, color=PAL.WHITE, width=26, dur=0.4, flip_at=None, **kw):
        super().__init__(**kw); self.L, self.c, self.wd, self.dur, self.flip_at = length, color, width, dur, flip_at

    def draw(self, ctx, t):
        L = self.L
        if self.flip_at is not None and t >= self.flip_at:
            k = ease('eio', min(1, (t - self.flip_at) / 0.35))
            ctx.scale(1 - 2 * k, 1)
        k = ease('eo', min(1, t / self.dur))
        x0 = -L / 2; x1 = -L / 2 + L * k
        hw = self.wd / 2; head = self.wd * 1.6
        ctx.move_to(x0, -hw); ctx.line_to(max(x0, x1 - head), -hw); ctx.line_to(max(x0, x1 - head), -hw - head * 0.55)
        ctx.line_to(x1, 0); ctx.line_to(max(x0, x1 - head), hw + head * 0.55); ctx.line_to(max(x0, x1 - head), hw)
        ctx.line_to(x0, hw); ctx.close_path()
        ctx.save(); ctx.translate(3, 5); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.fill_preserve(); ctx.restore()
        set_col(ctx, self.c); ctx.fill()


class PersonIcon(Element):
    """Simple human pictogram (no face)."""
    def __init__(self, h=120, color='#B9C0C2', **kw):
        super().__init__(**kw); self.h, self.c = h, color

    def draw(self, ctx, t):
        h = self.h
        set_col(ctx, self.c)
        circle(ctx, 0, -h * 0.82, h * 0.13); ctx.fill()
        rrect(ctx, -h * 0.19, -h * 0.64, h * 0.38, h * 0.42, h * 0.08); ctx.fill()
        rrect(ctx, -h * 0.17, -h * 0.30, h * 0.15, h * 0.30, h * 0.05); ctx.fill()
        rrect(ctx, h * 0.02, -h * 0.30, h * 0.15, h * 0.30, h * 0.05); ctx.fill()


# ------------------------------------------------------------------ old map
class OldShip(Element):
    """Inked three-masted sailing ship (old map style) that bobs on drawn waves."""
    def __init__(self, ink=INK, fill='#E6DAB9', **kw):
        super().__init__(**kw); self.ink, self.fill = ink, fill

    def draw(self, ctx, t):
        ctx.save()
        ctx.rotate(math.radians(3 * math.sin(t * 1.4)))
        ctx.translate(0, 6 * math.sin(t * 1.4 + 0.6))
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        # hull
        ctx.move_to(-230, -40); ctx.line_to(240, -52); ctx.curve_to(220, 10, 170, 40, 110, 46)
        ctx.line_to(-150, 46); ctx.curve_to(-200, 30, -225, 0, -230, -40); ctx.close_path()
        set_col(ctx, '#7A5A3A'); ctx.fill_preserve(); set_col(ctx, self.ink); ctx.set_line_width(5); ctx.stroke()
        for y in (-18, 8, 30):
            ctx.move_to(-200 + (y + 18) * 0.6, y); ctx.line_to(200 - (y + 18) * 0.9, y - 6); set_col(ctx, self.ink, 0.6); ctx.set_line_width(2.5); ctx.stroke()
        for i in range(5):
            circle(ctx, -120 + i * 55, -26, 6); set_col(ctx, self.ink); ctx.fill()
        # masts + sails (billow)
        bill = 8 * math.sin(t * 2.0)
        for mx, mh, sw in ((-120, 300, 110), (20, 360, 130), (150, 280, 100)):
            ctx.move_to(mx, -44); ctx.line_to(mx, -44 - mh); set_col(ctx, self.ink); ctx.set_line_width(5); ctx.stroke()
            for k, (y0, y1) in enumerate(((-44 - mh + 20, -44 - mh * 0.55), (-44 - mh * 0.5, -60))):
                w = sw * (0.8 + 0.25 * k)
                ctx.move_to(mx - w, y0); ctx.line_to(mx + w, y0)
                ctx.curve_to(mx + w + 14 + bill, (y0 + y1) / 2, mx + w + 10 + bill, y1, mx + w, y1)
                ctx.line_to(mx - w, y1)
                ctx.curve_to(mx - w + 10 + bill, (y0 + y1) / 2, mx - w + 14 + bill, y0, mx - w, y0)
                ctx.close_path()
                set_col(ctx, self.fill); ctx.fill_preserve(); set_col(ctx, self.ink); ctx.set_line_width(3.5); ctx.stroke()
        # flag
        fy = -44 - 360
        ctx.move_to(20, fy); ctx.curve_to(50, fy - 10 + 6 * math.sin(t * 5), 70, fy + 10, 100, fy + 4 * math.sin(t * 5 + 1))
        ctx.line_to(100, fy + 26); ctx.curve_to(70, fy + 30, 50, fy + 20, 20, fy + 28); ctx.close_path()
        set_col(ctx, PAL.RED); ctx.fill()
        ctx.restore()


class InkWaves(Element):
    """Rows of little inked map-wave strokes drifting."""
    def __init__(self, n=40, area=(0, 0, W, H), seed=5, ink=INK, **kw):
        super().__init__(**kw)
        r = rng(seed); x0, y0, w, h = area
        self.p = [(r.uniform(x0, x0 + w), r.uniform(y0, y0 + h), r.uniform(0.7, 1.3), r.random() * TAU) for _ in range(n)]
        self.ink = ink

    def draw(self, ctx, t):
        set_col(ctx, self.ink, 0.45); ctx.set_line_width(2.4); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for x, y, s, ph in self.p:
            x = x + 6 * math.sin(t * 0.8 + ph); y = y + 3 * math.sin(t * 1.1 + ph)
            for k in range(3):
                xx = x + k * 26 * s
                ctx.move_to(xx, y); ctx.curve_to(xx + 6 * s, y - 10 * s, xx + 14 * s, y - 10 * s, xx + 20 * s, y)
            ctx.stroke()


class Compass(Element):
    def __init__(self, r=110, ink=INK, **kw):
        super().__init__(**kw); self.r, self.ink = r, ink

    def draw(self, ctx, t):
        r = self.r
        ctx.rotate(math.radians(4 * math.sin(t * 0.6)))
        circle(ctx, 0, 0, r); set_col(ctx, self.ink, 0.7); ctx.set_line_width(3); ctx.stroke()
        circle(ctx, 0, 0, r * 0.82); ctx.set_line_width(1.5); ctx.stroke()
        for i in range(8):
            a = i * TAU / 8 - math.pi / 2; L = r * (1.0 if i % 2 == 0 else 0.6)
            b1 = a + 0.18; b2 = a - 0.18
            ctx.move_to(0, 0); ctx.line_to(math.cos(b1) * L * 0.25, math.sin(b1) * L * 0.25); ctx.line_to(math.cos(a) * L, math.sin(a) * L)
            ctx.line_to(math.cos(b2) * L * 0.25, math.sin(b2) * L * 0.25); ctx.close_path()
            set_col(ctx, PAL.RED if i == 0 else self.ink, 0.85); ctx.fill()
        draw_text(ctx, 'N', 0, -r - 14, 'black', 34, self.ink, 0, 'center', shadow=False)


class SwapLabel(UI):
    """'WHALE KILLER' on a paper banner; at t_swap the two words physically swap
    places along arcs (0.5 s) to read 'KILLER WHALE', then a red underline draws."""
    def __init__(self, a='WHALE', b='KILLER', size=96, t_swap=1.0, ink=INK, **kw):
        super().__init__(**kw); self.a, self.b, self.size, self.ts, self.ink = a, b, size, t_swap, ink

    def draw(self, ctx, t):
        al, _ = _pop(t, 4, 0.85)
        sz = self.size; gap = sz * 0.35
        wa = measure(ctx, self.a, 'black', sz, 0.06)[0]; wb = measure(ctx, self.b, 'black', sz, 0.06)[0]
        tot = wa + gap + wb
        # banner (scroll)
        bw, bh = tot + sz * 1.2, sz * 1.55
        ctx.save(); ctx.scale(_pop(t, 4, 0.85)[1], _pop(t, 4, 0.85)[1])
        ctx.move_to(-bw / 2, -bh / 2); ctx.curve_to(-bw / 6, -bh / 2 - 14, bw / 6, -bh / 2 + 14, bw / 2, -bh / 2)
        ctx.line_to(bw / 2, bh / 2); ctx.curve_to(bw / 6, bh / 2 + 14, -bw / 6, bh / 2 - 14, -bw / 2, bh / 2); ctx.close_path()
        ctx.save(); ctx.translate(6, 8); ctx.set_source_rgba(0.2, 0.12, 0.05, 0.25 * al); ctx.fill_preserve(); ctx.restore()
        set_col(ctx, '#F3EBD3', al); ctx.fill_preserve(); set_col(ctx, self.ink, al); ctx.set_line_width(4); ctx.stroke()
        k = 0.0 if t < self.ts else ease('eio', min(1, (t - self.ts) / 0.5))
        y0 = sz * 0.36
        # start positions (A left, B right) -> end (B left, A right)
        ax0 = -tot / 2; bx0 = -tot / 2 + wa + gap
        bx1 = -tot / 2; ax1 = -tot / 2 + wb + gap
        ax = lerp(ax0, ax1, k); bx = lerp(bx0, bx1, k)
        lift = math.sin(k * math.pi) * sz * 0.9
        draw_text(ctx, self.a, ax, y0 + lift, 'black', sz, self.ink, 0.06, shadow=False, alpha=al)
        draw_text(ctx, self.b, bx, y0 - lift, 'black', sz, PAL.RED_DARK if k >= 1 else self.ink, 0.06, shadow=False, alpha=al)
        if k >= 1:
            u = ease('eo', min(1, (t - self.ts - 0.5) / 0.3))
            ctx.move_to(-tot / 2, y0 + 18); ctx.line_to(-tot / 2 + tot * u, y0 + 18 + 3 * math.sin(u * 3))
            set_col(ctx, PAL.RED); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()


class NameTag(Element):
    """'HELLO my name is' sticker with a marker name; swings slightly."""
    def __init__(self, name='KILLER WHALE', w=300, **kw):
        super().__init__(**kw); self.name, self.w = name, w

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.6)
        w = self.w; h = w * 0.62
        ctx.rotate(math.radians(-6 + 4 * math.sin(t * 2.2)))
        ctx.scale(s, s)
        ctx.move_to(0, -h / 2 - 40); ctx.line_to(0, -h / 2); set_col(ctx, '#EEEEEE', a); ctx.set_line_width(3); ctx.stroke()
        rrect(ctx, -w / 2 + 5, -h / 2 + 7, w, h, 14); ctx.set_source_rgba(0, 0, 0, 0.3 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 14); set_col(ctx, '#C9302C', a); ctx.fill()
        rrect(ctx, -w / 2 + 12, -h / 2 + h * 0.36, w - 24, h * 0.52, 6); set_col(ctx, '#FFFFFF', a); ctx.fill()
        draw_text(ctx, 'HELLO', 0, -h / 2 + h * 0.2, 'black', w * 0.12, '#FFFFFF', 0.1, 'center', shadow=False, alpha=a)
        draw_text(ctx, 'MY NAME IS', 0, -h / 2 + h * 0.31, 'bold', w * 0.06, '#FFFFFF', 0.2, 'center', shadow=False, alpha=a)
        draw_text(ctx, self.name, 0, h * 0.24, 'marker', w * 0.105, '#1A1A1A', 0, 'center', shadow=False, alpha=a)


# ------------------------------------------------------------------ captivity tank
class Tank(Element):
    """Concrete-grey tank outline with water, rippling surface, an orca circling
    slowly inside (clipped) - grey and sombre."""
    def __init__(self, w=760, h=420, orca=None, **kw):
        super().__init__(**kw); self.w, self.h, self.orca = w, h, orca

    def draw(self, ctx, t):
        w, h = self.w, self.h
        x0, y0 = -w / 2, -h / 2
        wl = y0 + 60
        # water
        ctx.save(); ctx.rectangle(x0, y0, w, h); ctx.clip()
        g = cairo.LinearGradient(0, wl, 0, y0 + h)
        g.add_color_stop_rgba(0, *hexc('#2E4950')); g.add_color_stop_rgba(1, *hexc('#0E1C20'))
        ctx.move_to(x0, wl)
        for i in range(41):
            x = x0 + w * i / 40
            ctx.line_to(x, wl + 4 * math.sin(x * 0.03 + t * 2.0))
        ctx.line_to(x0 + w, y0 + h); ctx.line_to(x0, y0 + h); ctx.close_path(); ctx.set_source(g); ctx.fill()
        # caustic lines
        for i in range(7):
            yy = wl + 40 + i * 45
            ctx.move_to(x0, yy)
            for j in range(21):
                x = x0 + w * j / 20
                ctx.line_to(x, yy + 6 * math.sin(x * 0.02 + t * 0.9 + i))
            ctx.set_source_rgba(1, 1, 1, 0.035); ctx.set_line_width(2); ctx.stroke()
        if self.orca is not None:
            self.orca.render(ctx, t)
        ctx.move_to(x0, wl)
        for i in range(41):
            x = x0 + w * i / 40
            ctx.line_to(x, wl + 4 * math.sin(x * 0.03 + t * 2.0))
        ctx.set_source_rgba(0.85, 0.9, 0.9, 0.6); ctx.set_line_width(2.5); ctx.stroke()
        ctx.restore()
        # concrete walls
        ctx.set_line_join(cairo.LINE_JOIN_MITER)
        ctx.move_to(x0 - 30, y0 - 10); ctx.line_to(x0 - 30, y0 + h + 30); ctx.line_to(x0 + w + 30, y0 + h + 30); ctx.line_to(x0 + w + 30, y0 - 10)
        ctx.line_to(x0 + w, y0 - 10); ctx.line_to(x0 + w, y0 + h); ctx.line_to(x0, y0 + h); ctx.line_to(x0, y0 - 10); ctx.close_path()
        set_col(ctx, '#6D7375'); ctx.fill_preserve(); set_col(ctx, '#2A2E30'); ctx.set_line_width(4); ctx.stroke()


class OutlineNumber(UI):
    """Huge outlined (key-claim) number/text that pops."""
    def __init__(self, text, size=300, color=PAL.WHITE, width=7, fill=None, **kw):
        super().__init__(**kw); self.text, self.size, self.c, self.lw, self.fill = text, size, color, width, fill

    def draw(self, ctx, t):
        a, s = _pop(t, 4, 1.25)
        ctx.scale(s, s)
        text_path(ctx, self.text, 0, self.size * 0.36, 'xb', self.size, 0.0, 'center')
        if self.fill:
            set_col(ctx, self.fill, a); ctx.fill_preserve()
        set_col(ctx, self.c, a); ctx.set_line_width(self.lw); ctx.stroke()


# ------------------------------------------------------------------ capture polaroid content
def capture_scene(ctx, t, w, h):
    """1960s capture: boat on the surface, net arc, orca fins trapped (sepia toned)."""
    wl = h * 0.42
    g = cairo.LinearGradient(0, 0, 0, wl)
    g.add_color_stop_rgba(0, *hexc('#B9A98A')); g.add_color_stop_rgba(1, *hexc('#D6C7A6'))
    ctx.rectangle(0, 0, w, wl); ctx.set_source(g); ctx.fill()
    g = cairo.LinearGradient(0, wl, 0, h)
    g.add_color_stop_rgba(0, *hexc('#6F7466')); g.add_color_stop_rgba(1, *hexc('#3A3D35'))
    ctx.rectangle(0, wl, w, h - wl); ctx.set_source(g); ctx.fill()
    # mountains
    ctx.move_to(0, wl); ctx.line_to(60, wl - 50); ctx.line_to(120, wl - 20); ctx.line_to(200, wl - 70); ctx.line_to(290, wl - 25)
    ctx.line_to(360, wl - 55); ctx.line_to(w, wl - 15); ctx.line_to(w, wl); ctx.close_path(); set_col(ctx, '#8E8670'); ctx.fill()
    # net float line (arc) with floats
    cx, cy, rx, ry = w * 0.55, wl + 8, w * 0.36, 34
    pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a) * 0.6) for a in np.linspace(0.05, math.pi * 2 - 0.05, 40)]
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    set_col(ctx, '#2A2620', 0.8); ctx.set_line_width(2); ctx.stroke()
    for i, p in enumerate(pts[::3]):
        circle(ctx, p[0], p[1] + 1.5 * math.sin(t * 3 + i), 4); set_col(ctx, '#E8DCC0'); ctx.fill()
    # trapped fins circling inside
    for k in range(3):
        a = t * 0.9 + k * TAU / 3
        fx = cx + rx * 0.55 * math.cos(a); fy = cy + 6 + 8 * math.sin(a)
        sc = 0.8 + 0.2 * math.sin(a)
        ctx.move_to(fx - 14 * sc, fy); ctx.curve_to(fx - 6 * sc, fy - 20 * sc, fx - 2 * sc, fy - 40 * sc, fx + 4 * sc, fy - 46 * sc)
        ctx.curve_to(fx + 2 * sc, fy - 28 * sc, fx + 8 * sc, fy - 10 * sc, fx + 16 * sc, fy); ctx.close_path()
        set_col(ctx, '#1F1D19'); ctx.fill()
    # boat
    bx = w * 0.2 + 6 * math.sin(t * 0.8); by = wl - 2 + 2 * math.sin(t * 2)
    ctx.move_to(bx - 60, by - 14); ctx.line_to(bx + 66, by - 14); ctx.line_to(bx + 50, by + 10); ctx.line_to(bx - 52, by + 10); ctx.close_path()
    set_col(ctx, '#2F2B25'); ctx.fill()
    ctx.rectangle(bx - 30, by - 40, 34, 26); ctx.fill()
    ctx.move_to(bx + 20, by - 14); ctx.line_to(bx + 20, by - 70); ctx.set_line_width(3); ctx.stroke()
    # grain
    r = rng(int(t * 12))
    for _ in range(140):
        circle(ctx, r.uniform(0, w), r.uniform(0, h), r.uniform(0.4, 1.3)); ctx.set_source_rgba(0.1, 0.08, 0.05, 0.18); ctx.fill()
    ctx.rectangle(0, 0, w, h); ctx.set_source_rgba(0.55, 0.42, 0.22, 0.22); ctx.fill()


# ------------------------------------------------------------------ pollution / noise
class Magnifier(UI):
    """Round magnifier showing a skin/blubber cross-section; red PCB specks pulse in the blubber."""
    def __init__(self, r=230, t_specks=0.6, target=None, **kw):
        super().__init__(**kw); self.r, self.ts, self.target = r, t_specks, target

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.7)
        r = self.r
        if self.target is not None:
            tx, ty = self.target
            k = ease('eo', min(1, t / 0.25))
            ang = math.atan2(ty, tx)
            sx, sy = math.cos(ang) * r, math.sin(ang) * r
            ctx.move_to(sx, sy); ctx.line_to(sx + (tx - sx) * k, sy + (ty - sy) * k)
            set_col(ctx, PAL.WHITE, a); ctx.set_line_width(2.4); ctx.stroke()
            if k >= 1: circle(ctx, tx, ty, 8); ctx.fill()
        ctx.save(); ctx.scale(s, s)
        circle(ctx, 0, 0, r); ctx.save(); ctx.clip()
        # layers: skin / blubber / muscle
        sk = -r * 0.62; bl = r * 0.35
        ctx.rectangle(-r, -r, 2 * r, sk + r); set_col(ctx, '#0B1A22'); ctx.fill()
        ctx.move_to(-r, sk)
        for i in range(21):
            x = -r + 2 * r * i / 20; ctx.line_to(x, sk + 4 * math.sin(x * 0.05))
        ctx.line_to(r, sk + 26); ctx.line_to(-r, sk + 26); ctx.close_path(); set_col(ctx, '#15191C'); ctx.fill()
        ctx.rectangle(-r, sk + 24, 2 * r, bl - sk - 24); set_col(ctx, '#E9D9B8'); ctx.fill()
        ctx.rectangle(-r, bl, 2 * r, r); set_col(ctx, '#9C3C3E'); ctx.fill()
        for i in range(6):
            ctx.move_to(-r, bl + 20 + i * 22); ctx.line_to(r, bl + 14 + i * 22); ctx.set_source_rgba(0, 0, 0, 0.15); ctx.set_line_width(3); ctx.stroke()
        rr = rng(9)
        for i in range(34):
            px, py = rr.uniform(-r, r), rr.uniform(sk + 40, bl - 14)
            ti = self.ts + i * 0.025
            if t < ti: continue
            pu = 1 + 0.25 * math.sin(t * 5 + i)
            circle(ctx, px, py, rr.uniform(5, 10) * pu * min(1, (t - ti) / 0.12)); set_col(ctx, PAL.RED); ctx.fill()
        ctx.restore()
        circle(ctx, 0, 0, r); set_col(ctx, PAL.WHITE, a); ctx.set_line_width(6); ctx.stroke()
        draw_text(ctx, 'BLUBBER', -r + 24, (sk + bl) / 2 + 10, 'bold', 24, '#5B4A33', 0.2, shadow=False, alpha=a)
        ctx.restore()


class HullFromBelow(Element):
    """Dark boat hull silhouette at the top of the frame with a spinning propeller."""
    def __init__(self, w=520, **kw):
        super().__init__(**kw); self.w = w

    def draw(self, ctx, t):
        w = self.w
        ctx.move_to(-w / 2, 0); ctx.line_to(w / 2, 0); ctx.curve_to(w / 2 - 30, 50, w / 2 - 90, 70, w / 2 - 160, 74)
        ctx.line_to(-w / 2 + 40, 74); ctx.curve_to(-w / 2 + 10, 60, -w / 2, 30, -w / 2, 0); ctx.close_path()
        set_col(ctx, '#061017'); ctx.fill()
        # shaft + prop
        px, py = -w / 2 + 20, 92
        ctx.move_to(-w / 2 + 70, 70); ctx.line_to(px, py); set_col(ctx, '#061017'); ctx.set_line_width(8); ctx.stroke()
        bl = 26 * abs(math.sin(t * 40))
        ctx.save(); ctx.translate(px, py); ctx.scale(0.35, 1)
        circle(ctx, 0, -bl, 12); circle(ctx, 0, bl, 12); set_col(ctx, '#0B1820'); ctx.fill(); ctx.restore()


class NoiseRings(Element):
    """Jagged expanding noise rings (red/orange) from a point."""
    def __init__(self, period=0.7, n=5, rmax=900, color=PAL.RED, **kw):
        super().__init__(**kw); self.per, self.n, self.rmax, self.c = period, n, rmax, color

    def draw(self, ctx, t):
        for i in range(self.n):
            ph = ((t / self.per) + i / self.n) % 1.0
            if t < i * self.per / self.n: continue
            r = 30 + ph * self.rmax
            ctx.new_path()
            for j in range(97):
                a = j / 96 * TAU
                rr = r + 9 * math.sin(a * 23 + t * 9) * (1 - ph)
                (ctx.move_to if j == 0 else ctx.line_to)(rr * math.cos(a), rr * math.sin(a) * 0.8)
            ctx.close_path()
            set_col(ctx, self.c, 0.65 * (1 - ph)); ctx.set_line_width(5); ctx.stroke()


class BrokenArcs(Element):
    """Orca echolocation arcs (cyan) going out; after t_jam they wobble + fade (drowned out)."""
    def __init__(self, t_jam=1.0, period=0.9, color='#B6E8F3', direction=0, **kw):
        super().__init__(**kw); self.tj, self.per, self.c, self.dir = t_jam, period, color, direction

    def draw(self, ctx, t):
        ctx.rotate(math.radians(self.dir))
        jam = 0 if t < self.tj else min(1, (t - self.tj) / 0.6)
        for i in range(3):
            ph = ((t / self.per) + i / 3) % 1.0
            r = 40 + ph * 380
            ctx.new_path()
            for j in range(31):
                a = math.radians(-35 + 70 * j / 30)
                rr = r + jam * 22 * math.sin(j * 1.7 + t * 30)
                (ctx.move_to if j == 0 else ctx.line_to)(rr * math.cos(a), rr * math.sin(a))
            set_col(ctx, self.c, (1 - ph) * 0.8 * (1 - 0.75 * jam)); ctx.set_line_width(4); ctx.stroke()


# ------------------------------------------------------------------ globe with population dots
class DotGlobe(Globe):
    """Globe + orca population dots; dots in `red_idx` turn red (staggered) at t_red."""
    def __init__(self, dots=(), red_idx=(), t_red=1.0, t_dots=0.2, **kw):
        super().__init__(**kw); self.dots, self.red, self.tr_, self.td = list(dots), set(red_idx), t_red, t_dots

    def draw(self, ctx, t):
        super().draw(ctx, t)
        R = self.R
        lon0 = math.radians(self.c0[0] - self.spin * t); lat0 = math.radians(self.c0[1])
        for i, (lo, la) in enumerate(self.dots):
            ti = self.td + i * 0.05
            if t < ti: continue
            x, y, c = _ortho(np.radians(np.array([[lo, la]], float)), lon0, lat0, R)
            if c[0] <= 0: continue
            k = min(1, (t - ti) / 0.15)
            col = PAL.WHITE
            rd = 0
            if i in self.red:
                order = sorted(self.red).index(i)
                tk = self.tr_ + order * 0.12
                if t >= tk:
                    rd = min(1, (t - tk) / 0.15); col = mix(PAL.WHITE, PAL.RED, rd)
            rr = 12 * k * (1 + 0.35 * rd * (0.5 + 0.5 * math.sin(t * 6 + i)))
            circle(ctx, x[0], y[0], rr + 3); ctx.set_source_rgba(0, 0, 0, 0.4); ctx.fill()
            circle(ctx, x[0], y[0], rr); set_col(ctx, col); ctx.fill()


# ------------------------------------------------------------------ Toñi fin close-up
class FinClose(Element):
    """Close side view of a tall-ish (female) dorsal fin + back rising from the water,
    bobbing; small dark marks on the fin. Coordinates: base centre at (0,0), fin up."""
    MARKS = [(-30, -210), (10, -150), (-60, -110), (25, -260)]

    def __init__(self, marks_t=0.0, **kw):
        super().__init__(**kw); self.mt = marks_t

    def draw(self, ctx, t):
        ctx.save()
        ctx.translate(0, 10 * math.sin(t * 0.9)); ctx.rotate(math.radians(1.2 * math.sin(t * 0.9 + 0.5)))
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        # back
        ctx.move_to(-900, 120); ctx.curve_to(-500, 20, -250, -10, 0, -10); ctx.curve_to(300, -10, 600, 30, 950, 140)
        ctx.line_to(950, 400); ctx.line_to(-900, 400); ctx.close_path()
        set_col(ctx, '#12171C'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(8); ctx.stroke()
        # saddle
        ctx.save(); ctx.translate(200, 20); ctx.scale(1, 0.25)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, 260)
        rg.add_color_stop_rgba(0, 0.5, 0.55, 0.6, 0.8); rg.add_color_stop_rgba(1, 0.5, 0.55, 0.6, 0)
        ctx.set_source(rg); circle(ctx, 0, 0, 260); ctx.fill(); ctx.restore()
        # fin (curved, female, slightly falcate) with a worn notch
        ctx.move_to(-230, 0); ctx.curve_to(-150, -120, -90, -260, -20, -360)
        ctx.curve_to(10, -395, 40, -400, 60, -385)
        ctx.curve_to(40, -330, 50, -250, 80, -160); ctx.line_to(70, -150); ctx.line_to(92, -128)
        ctx.curve_to(110, -70, 140, -30, 190, 0); ctx.close_path()
        set_col(ctx, '#151B21'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(8); ctx.stroke()
        # sheen on fin
        ctx.move_to(-180, -20); ctx.curve_to(-110, -140, -70, -250, -20, -340)
        ctx.set_source_rgba(0.5, 0.58, 0.65, 0.35); ctx.set_line_width(10); ctx.stroke()
        # scratches (age)
        for (x, y, L) in ((-60, -60, 60), (-10, -90, 50), (30, -40, 70)):
            ctx.move_to(x, y); ctx.line_to(x + L, y - 8); ctx.set_source_rgba(0.6, 0.65, 0.7, 0.25); ctx.set_line_width(2); ctx.stroke()
        if t >= self.mt:
            for (x, y) in self.MARKS:
                circle(ctx, x, y, 7); set_col(ctx, '#05080A'); ctx.fill()
                circle(ctx, x - 2, y - 2, 3); ctx.set_source_rgba(0.45, 0.4, 0.4, 0.6); ctx.fill()
        ctx.restore()

    def mark_pos(self, i, t):
        x, y = self.MARKS[i]
        return (x, y + 10 * math.sin(t * 0.9))


class Reticle(Element):
    """Red targeting reticle (circle + ticks) that shrinks in and rotates."""
    def __init__(self, r=46, color=PAL.RED, dash=False, **kw):
        super().__init__(**kw); self.r, self.c, self.dash = r, color, dash

    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.3))
        r = self.r * (1.8 - 0.8 * k)
        ctx.rotate(t * 0.8)
        if self.dash: ctx.set_dash([8, 7])
        circle(ctx, 0, 0, r); set_col(ctx, self.c, k); ctx.set_line_width(4); ctx.stroke()
        ctx.set_dash([])
        for i in range(4):
            a = i * math.pi / 2
            ctx.move_to(math.cos(a) * r * 0.7, math.sin(a) * r * 0.7); ctx.line_to(math.cos(a) * r * 1.3, math.sin(a) * r * 1.3)
        ctx.set_line_width(4); ctx.stroke()


# ------------------------------------------------------------------ grandmother risk
class RiskBars(UI):
    """Two horizontal bars: 'WHILE SHE'S ALIVE' 1x and 'AFTER SHE DIES' growing to 4.5x."""
    def __init__(self, t_grow=1.0, unit=110, **kw):
        super().__init__(**kw); self.tg, self.u = t_grow, unit

    def draw(self, ctx, t):
        a = min(1, t / 0.2); u = self.u
        draw_text(ctx, 'GRANDMOTHER ALIVE', 0, -70, 'bold', 24, PAL.WHITE, 0.22, alpha=a)
        rrect(ctx, 0, -50, u * ease('eo', min(1, t / 0.3)), 50, 6); set_col(ctx, PAL.CYAN, a); ctx.fill()
        draw_text(ctx, '×1', u + 22, -12, 'xb', 40, PAL.CYAN, 0.0, alpha=a)
        draw_text(ctx, 'AFTER SHE DIES', 0, 70, 'bold', 24, PAL.WHITE, 0.22, alpha=a)
        k = 0 if t < self.tg else ease('eo', min(1, (t - self.tg) / 1.0))
        val = 1 + 3.5 * k
        rrect(ctx, 0, 90, u * val, 50, 6); set_col(ctx, PAL.RED, a); ctx.fill()
        draw_text(ctx, f'×{val:.1f}', u * val + 22, 128, 'xb', 52, PAL.RED, 0.0, alpha=a)


class CalfRow(UI):
    """Grandmother icon + row of grandchild icons; grandmother fades to an outline at t_die,
    grandchildren then tremble."""
    def __init__(self, n=5, t_die=1.0, **kw):
        super().__init__(**kw); self.n, self.td = n, t_die

    def draw(self, ctx, t):
        die = 0 if t < self.td else min(1, (t - self.td) / 0.5)
        ctx.save(); ctx.translate(0, 0)
        ctx.push_group(); icon(ctx, 'orca', 70, mix(PAL.ORANGE, '#4A3A30', die)); ctx.pop_group_to_source(); ctx.paint_with_alpha(1 - 0.6 * die)
        if die > 0:
            circle(ctx, 0, 0, 88); set_col(ctx, PAL.WHITE, 0.4 * die); ctx.set_dash([6, 6]); ctx.set_line_width(2); ctx.stroke(); ctx.set_dash([])
        draw_text(ctx, 'GRANDMOTHER', 0, 128, 'bold', 22, PAL.WHITE, 0.2, 'center')
        ctx.restore()
        for i in range(self.n):
            x = 220 + i * 120
            jit = die * 3 * math.sin(t * 20 + i * 2)
            ctx.save(); ctx.translate(x + jit, 10)
            icon(ctx, 'orca', 40, PAL.WHITE)
            ctx.restore()
        draw_text(ctx, 'GRANDCHILDREN', 220 + (self.n - 1) * 60, 128, 'bold', 22, PAL.WHITE, 0.2, 'center')


# ------------------------------------------------------------------ ships (night strait)
class ContainerShip(Element):
    """Long low container ship silhouette with stacked boxes and deck lights; sits on plate water."""
    def __init__(self, plate=None, length=900, facing='right', **kw):
        super().__init__(**kw); self.plate, self.L, self.facing = plate, length, facing

    def render(self, ctx, t):
        if self.plate is not None and self.visible(t):
            lt = t - self.t0
            p = ev(self.pos, lt)
            orig = self.pos
            self.pos = (p[0], self.plate.water_y(p[0], t) - 2)
            try: super().render(ctx, t)
            finally: self.pos = orig
        else:
            super().render(ctx, t)

    def draw(self, ctx, t):
        L = self.L
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.move_to(-L / 2, -40); ctx.line_to(L / 2 - 40, -40); ctx.line_to(L / 2, -70); ctx.line_to(L / 2 - 50, 22)
        ctx.line_to(-L / 2 + 20, 22); ctx.close_path(); set_col(ctx, '#0A1820'); ctx.fill()
        cols = ['#2A3E4A', '#3A2E2E', '#2E3A32', '#3C3A2A']
        r = rng(4)
        x = -L / 2 + 110
        while x < L / 2 - 120:
            for k in range(r.randint(1, 3)):
                ctx.rectangle(x, -40 - 34 * (k + 1), 52, 32); set_col(ctx, cols[r.randint(0, 3)]); ctx.fill()
            x += 56
        ctx.rectangle(-L / 2 + 20, -150, 70, 110); set_col(ctx, '#0E1F28'); ctx.fill()
        for i in range(3):
            ctx.rectangle(-L / 2 + 30, -140 + i * 24, 50, 8); set_col(ctx, '#F7D88A', 0.85); ctx.fill()
        for i, x in enumerate(np.linspace(-L / 2 + 20, L / 2 - 30, 9)):
            a = 0.5 + 0.5 * math.sin(t * 2 + i)
            circle(ctx, x, -44, 3.5); set_col(ctx, '#FFE7A8', 0.6 + 0.4 * a); ctx.fill()
        circle(ctx, L / 2 - 10, -72, 5); set_col(ctx, '#7CFF9A'); ctx.fill()


class Ferry(Element):
    """Big white ferry (side view), windows lit, funnel; deck-level y=-120 (local).
    rudder huge below the waterline."""
    def __init__(self, plate=None, length=1300, facing='right', rudder=True, **kw):
        super().__init__(**kw); self.plate, self.L, self.facing, self.rud = plate, length, facing, rudder

    def render(self, ctx, t):
        if self.plate is not None and self.visible(t):
            lt = t - self.t0; p = ev(self.pos, lt); orig = self.pos
            self.pos = (p[0], self.plate.water_y(p[0], t) * 0.3 + p[1] * 0.7)
            try: super().render(ctx, t)
            finally: self.pos = orig
        else:
            super().render(ctx, t)

    def draw(self, ctx, t):
        L = self.L
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        # underwater hull
        ctx.move_to(-L / 2, 0); ctx.line_to(L / 2 - 60, 0); ctx.curve_to(L / 2 - 120, 90, L / 2 - 260, 120, L / 2 - 420, 125)
        ctx.line_to(-L / 2 + 60, 125); ctx.curve_to(-L / 2 + 20, 110, -L / 2, 60, -L / 2, 0); ctx.close_path()
        set_col(ctx, '#3A2A2E'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(6); ctx.stroke()
        if self.rud:
            ctx.move_to(-L / 2 + 70, 110); ctx.line_to(-L / 2 + 160, 110); ctx.line_to(-L / 2 + 150, 330); ctx.line_to(-L / 2 + 75, 320); ctx.close_path()
            set_col(ctx, '#4A3A3E'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.stroke()
            # propeller
            px, py = -L / 2 + 210, 150
            bl = 40 * abs(math.sin(t * 12))
            ctx.save(); ctx.translate(px, py); ctx.scale(0.4, 1); circle(ctx, 0, -bl, 18); circle(ctx, 0, bl, 18)
            set_col(ctx, '#C9A050'); ctx.fill(); ctx.restore()
        # hull above water
        ctx.move_to(-L / 2, 0); ctx.line_to(-L / 2 + 10, -130); ctx.line_to(L / 2 - 80, -130); ctx.line_to(L / 2, -150)
        ctx.line_to(L / 2 - 60, 0); ctx.close_path()
        set_col(ctx, '#F2F1EC'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(6); ctx.stroke()
        ctx.rectangle(-L / 2 + 6, -40, L - 70, 22); set_col(ctx, '#1E5A8C'); ctx.fill()
        # superstructure
        ctx.move_to(-L / 2 + 120, -130); ctx.line_to(-L / 2 + 140, -250); ctx.line_to(L / 2 - 280, -250); ctx.line_to(L / 2 - 220, -130); ctx.close_path()
        set_col(ctx, '#E8E7E2'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.stroke()
        ctx.move_to(-L / 2 + 220, -250); ctx.line_to(-L / 2 + 240, -330); ctx.line_to(L / 2 - 420, -330); ctx.line_to(L / 2 - 360, -250); ctx.close_path()
        set_col(ctx, '#E1E0DA'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.stroke()
        for row, (y, x0, x1) in enumerate(((-100, -L / 2 + 40, L / 2 - 140), (-215, -L / 2 + 160, L / 2 - 270), (-300, -L / 2 + 250, L / 2 - 410))):
            x = x0
            while x < x1:
                ctx.rectangle(x, y, 26, 18); set_col(ctx, '#20333D'); ctx.fill(); x += 40
        # funnel
        ctx.move_to(-L / 2 + 330, -330); ctx.line_to(-L / 2 + 345, -420); ctx.line_to(-L / 2 + 435, -420); ctx.line_to(-L / 2 + 450, -330); ctx.close_path()
        set_col(ctx, '#1E5A8C'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.stroke()
        ctx.rectangle(-L / 2 + 345, -410, 90, 18); set_col(ctx, PAL.RED); ctx.fill()
        # smoke puffs
        for i in range(4):
            ph = (t * 0.5 + i / 4) % 1
            circle(ctx, -L / 2 + 390 - ph * 160, -440 - ph * 120, 20 + ph * 40); ctx.set_source_rgba(0.85, 0.85, 0.85, 0.35 * (1 - ph)); ctx.fill()


class StickWaver(Element):
    """Tiny stick figure waving (for the ferry deck)."""
    def __init__(self, h=60, color='#1A1F24', **kw):
        super().__init__(**kw); self.h, self.c = h, color

    def draw(self, ctx, t):
        h = self.h
        set_col(ctx, self.c); ctx.set_line_width(h * 0.07); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        circle(ctx, 0, -h * 0.85, h * 0.12); ctx.fill()
        ctx.move_to(0, -h * 0.72); ctx.line_to(0, -h * 0.35)
        ctx.move_to(0, -h * 0.35); ctx.line_to(-h * 0.15, 0); ctx.move_to(0, -h * 0.35); ctx.line_to(h * 0.15, 0)
        ctx.move_to(0, -h * 0.65); ctx.line_to(-h * 0.22, -h * 0.42)
        a = math.radians(-120 + 30 * math.sin(t * 9))
        ctx.move_to(0, -h * 0.65); ctx.line_to(h * 0.32 * math.cos(a) * -1, -h * 0.65 + h * 0.32 * math.sin(a))
        ctx.stroke()


class HullPlank(Element):
    """Broken white hull panel with 'CHAMPAGNE' lettering, sinking and turning."""
    def __init__(self, w=420, **kw):
        super().__init__(**kw); self.w = w

    def draw(self, ctx, t):
        w = self.w; h = w * 0.26
        ctx.move_to(-w / 2, -h / 2); ctx.line_to(w / 2 - 30, -h / 2); ctx.line_to(w / 2, -h / 2 + 18); ctx.line_to(w / 2 - 22, -4)
        ctx.line_to(w / 2 - 4, h / 2 - 10); ctx.line_to(w / 2 - 20, h / 2); ctx.line_to(-w / 2 + 14, h / 2); ctx.line_to(-w / 2, h / 2 - 22)
        ctx.close_path()
        set_col(ctx, '#C8D0CF'); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE); ctx.set_line_width(4); ctx.stroke()
        ctx.rectangle(-w / 2 + 6, h / 2 - 22, w - 30, 8); set_col(ctx, '#1E3A4C'); ctx.fill()
        draw_text(ctx, 'CHAMPAGNE', 0, 12, 'black', w * 0.105, '#1E3A4C', 0.12, 'center', shadow=False, alpha=0.85)


# ------------------------------------------------------------------ outro
class CommentBox(UI):
    """Mock comment box: avatar, 'Add a comment…' that types the given text with cursor,
    COMMENT button lights up when done; heart pops at t_heart."""
    def __init__(self, text='Do the leopard seal next', cps=16, t_type=0.6, t_heart=None, w=980, **kw):
        super().__init__(**kw); self.text, self.cps, self.tt, self.th, self.w = text, cps, t_type, t_heart, w

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.9)
        ctx.scale(s, s)
        w = self.w; h = 210
        rrect(ctx, -w / 2 + 6, -h / 2 + 10, w, h, 18); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 18); set_col(ctx, '#0F1A20', 0.96 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.25 * a); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, 'COMMENTS', -w / 2 + 36, -h / 2 + 48, 'bold', 22, PAL.WHITE, 0.24, shadow=False, alpha=0.7 * a)
        # avatar
        ax, ay = -w / 2 + 70, 14
        circle(ctx, ax, ay, 34); set_col(ctx, PAL.ORANGE, a); ctx.fill()
        ctx.save(); ctx.translate(ax, ay); icon(ctx, 'person', 20, '#1A1410'); ctx.restore()
        n = int(max(0, t - self.tt) * self.cps)
        txt = self.text[:n]
        tx = ax + 60
        if n == 0:
            draw_text(ctx, 'Add a comment…', tx, ay + 12, 'semi', 34, '#7D8A90', 0, shadow=False, alpha=a)
        else:
            draw_text(ctx, txt, tx, ay + 12, 'semi', 36, PAL.WHITE, 0, shadow=False, alpha=a)
        tw = measure(ctx, txt, 'semi', 36, 0)[0] if n else 0
        if (t * 2) % 1 < 0.6:
            ctx.rectangle(tx + tw + 4, ay - 22, 3, 42); set_col(ctx, PAL.WHITE, a); ctx.fill()
        ctx.move_to(tx, ay + 34); ctx.line_to(w / 2 - 40, ay + 34); set_col(ctx, PAL.WHITE, 0.35 * a); ctx.set_line_width(2); ctx.stroke()
        done = n >= len(self.text)
        bx, by = w / 2 - 190, ay + 62
        rrect(ctx, bx, by, 150, 46, 23); set_col(ctx, '#3EA6FF' if done else '#2A3A42', a); ctx.fill()
        draw_text(ctx, 'COMMENT', bx + 75, by + 31, 'xb', 22, '#0B1418' if done else '#7D8A90', 0.06, 'center', shadow=False, alpha=a)
        if self.th is not None and t >= self.th:
            k, sc = _pop(t - self.th, 5, 1.6)
            ctx.save(); ctx.translate(-w / 2 + 120, by + 23); ctx.scale(sc, sc)
            icon(ctx, 'heart', 22, PAL.RED); ctx.restore()
            draw_text(ctx, 'READ ✓', -w / 2 + 160, by + 32, 'xb', 26, PAL.GREEN, 0.06, shadow=False, alpha=k)


class VideoCard(UI):
    """End-screen video placeholder: dashed rounded box with a pulsing play button and title bars."""
    def __init__(self, w=620, h=350, label='WATCH NEXT', seed=1, **kw):
        super().__init__(**kw); self.w, self.h, self.label, self.seed = w, h, label, seed

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.85)
        ctx.scale(s, s)
        w, h = self.w, self.h
        rrect(ctx, -w / 2, -h / 2, w, h, 16); set_col(ctx, '#0E2A36', 0.85 * a); ctx.fill()
        ctx.set_dash([16, 10], -t * 30)
        rrect(ctx, -w / 2, -h / 2, w, h, 16); set_col(ctx, PAL.WHITE, 0.9 * a); ctx.set_line_width(3); ctx.stroke()
        ctx.set_dash([])
        pr = 46 * (1 + 0.06 * math.sin(t * 3 + self.seed))
        circle(ctx, 0, -10, pr); set_col(ctx, PAL.RED, a); ctx.fill()
        ctx.move_to(-pr * 0.32, -10 - pr * 0.42); ctx.line_to(pr * 0.48, -10); ctx.line_to(-pr * 0.32, -10 + pr * 0.42); ctx.close_path()
        set_col(ctx, PAL.WHITE, a); ctx.fill()
        rrect(ctx, -w / 2 + 30, h / 2 - 70, w * 0.55, 16, 8); set_col(ctx, PAL.WHITE, 0.35 * a); ctx.fill()
        rrect(ctx, -w / 2 + 30, h / 2 - 42, w * 0.35, 12, 6); set_col(ctx, PAL.WHITE, 0.2 * a); ctx.fill()
        draw_text(ctx, self.label, 0, -h / 2 - 26, 'bold', 28, PAL.WHITE, 0.24, 'center', alpha=a)


class SubscribeButton(UI):
    """Red SUBSCRIBE pill with bell; a cursor arrow glides in and clicks at t_click
    (button turns grey 'SUBSCRIBED', bell rings)."""
    def __init__(self, t_click=1.5, **kw):
        super().__init__(**kw); self.tc = t_click

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.8)
        clicked = t >= self.tc
        press = 1 - 0.08 * max(0, 1 - abs(t - self.tc) / 0.12)
        ctx.save(); ctx.scale(s * press, s * press)
        w, h = 360, 84
        rrect(ctx, -w / 2 + 4, -h / 2 + 7, w, h, h / 2); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, h / 2); set_col(ctx, '#3A4448' if clicked else '#D7302C', a); ctx.fill()
        draw_text(ctx, 'SUBSCRIBED' if clicked else 'SUBSCRIBE', -20, 14, 'xb', 34, PAL.WHITE, 0.06, 'center', shadow=False, alpha=a)
        # bell
        ring = math.sin((t - self.tc) * 25) * 18 * math.exp(-max(0, t - self.tc) * 2.5) if clicked else 0
        ctx.save(); ctx.translate(w / 2 - 50, 0); ctx.rotate(math.radians(ring))
        ctx.move_to(-14, 10); ctx.curve_to(-14, -20, 14, -20, 14, 10); ctx.line_to(18, 14); ctx.line_to(-18, 14); ctx.close_path()
        set_col(ctx, PAL.WHITE, a); ctx.fill(); circle(ctx, 0, 18, 4); ctx.fill()
        ctx.restore(); ctx.restore()
        # cursor
        k = ease('eio', min(1, max(0, (t - (self.tc - 0.8)) / 0.7)))
        if t > self.tc - 0.8:
            cx, cy = lerp(260, 40, k), lerp(160, 20, k)
            ctx.save(); ctx.translate(cx, cy)
            ctx.move_to(0, 0); ctx.line_to(0, 40); ctx.line_to(10, 30); ctx.line_to(18, 48); ctx.line_to(25, 45); ctx.line_to(17, 27); ctx.line_to(30, 27); ctx.close_path()
            set_col(ctx, PAL.WHITE); ctx.fill_preserve(); set_col(ctx, '#111111'); ctx.set_line_width(2.5); ctx.stroke()
            ctx.restore()
