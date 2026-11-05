"""Custom assets for act D (chapter 4/6 BOATS). Never edits shared engine files."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import (Element, ev, set_col, hexc, mix, circle, rrect, poly, catmull, TAU, PAL, W, H, rng, ease,
                         remap)
from engine.plates import Surface, vignette_builder
from engine.text import draw_text, measure, cap_height
from engine.chars.orca import Orca, _path
from engine import ui as UI

OUT = PAL.OUTLINE
INK = '#3B2A1A'


# ------------------------------------------------------------------ plates / grades
class NightSurface(Surface):
    PRESETS = dict(Surface.PRESETS)
    PRESETS['night'] = dict(sky=('#06101C', '#0E2236', '#1B3A52'), sun='#CFE0EA',
                            sea=('#16404F', '#0A2430', '#020C12'), far='#173847')
    PRESETS['dusk'] = dict(sky=('#2B3245', '#5A5466', '#9C7A72'), sun='#F2C9A0',
                           sea=('#2A5560', '#143039', '#061418'), far='#3E5A62')

    def draw_bg(self, ctx, t, cam):
        super().draw_bg(ctx, t, cam)
        if self.p is self.PRESETS['night']:
            # stars twinkle
            r = rng(21)
            ctx.save(); cam.apply(ctx, t, 0.35)
            for i in range(70):
                x, y = r.uniform(-100, W + 100), r.uniform(-60, self.wl - 60)
                a = 0.35 + 0.35 * math.sin(t * r.uniform(1, 3) + i)
                circle(ctx, x, y, r.uniform(1.0, 2.4)); ctx.set_source_rgba(0.9, 0.95, 1, a); ctx.fill()
            ctx.restore()


def sepia_grade(strength=1.0, grain=True, seed=5):
    """shot.post fn: desaturate to sepia (HSL colour blend) + warm multiply + grain + flicker."""
    def fn(ctx, t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_HSL_COLOR)
        ctx.set_source_rgba(0.62, 0.47, 0.30, 0.85 * strength); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_MULTIPLY)
        ctx.set_source_rgba(1.0, 0.93, 0.80, 0.5 * strength); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        fl = 0.04 + 0.03 * math.sin(t * 23.0) * math.sin(t * 7.3)
        ctx.set_source_rgba(0.95, 0.88, 0.7, max(0, fl)); ctx.paint()
        if grain:
            fr = int(t * 30)
            r = rng(seed * 1000 + fr % 997)
            for _ in range(260):
                x, y = r.uniform(0, W), r.uniform(0, H)
                c = r.random() < 0.5
                ctx.set_source_rgba(*((0.15, 0.1, 0.05) if c else (1, 0.97, 0.9)), r.uniform(0.08, 0.25))
                circle(ctx, x, y, r.uniform(0.8, 2.2)); ctx.fill()
            if fr % 11 < 2:   # occasional scratch
                x = r.uniform(100, W - 100)
                ctx.move_to(x, 0); ctx.line_to(x + r.uniform(-20, 20), H)
                ctx.set_source_rgba(1, 0.97, 0.9, 0.18); ctx.set_line_width(1.5); ctx.stroke()
        ctx.restore()
    return fn


# ------------------------------------------------------------------ flat map
def _proj(lonlat_rad, lon0, lat0, k):
    lon = np.degrees(lonlat_rad[:, 0]); lat = np.degrees(lonlat_rad[:, 1])
    return (lon - lon0) * k * math.cos(math.radians(lat0)), -(lat - lat0) * k


class FlatMap(Element):
    """Flat map card centred on (lon0, lat0); k = px per degree latitude.
    highlight: country names in orange; pins: [(lon, lat, t_pop)] red pins popping with rings.
    labels: [(text, lon, lat, t, size)]; box=(w,h) card size; style 'blue' | 'sepia'."""
    def __init__(self, lon0, lat0, k=80, box=(1500, 860), highlight=None, pins=None, labels=None, style='blue',
                 pin_r=11, **kw):
        super().__init__(**kw)
        self.lon0, self.lat0, self.k, self.box = lon0, lat0, k, box
        self.hl, self.pins, self.labels, self.style, self.pin_r = highlight or [], pins or [], labels or [], style, pin_r
        if style == 'sepia':
            self.cols = dict(sea='#D9C9A3', sea2='#C9B48A', land='#EFE4C8', hl='#E3A65A', edge=INK, grid=(0.3, 0.2, 0.1, 0.14),
                             text=INK)
        else:
            self.cols = dict(sea='#174A5E', sea2='#0B2A38', land='#5E98A2', hl=PAL.ORANGE, edge='#0A1C24',
                             grid=(1, 1, 1, 0.07), text=PAL.WHITE)

    def _polys(self, polys, col, edge=True):
        ctx = self._ctx
        for p in polys:
            x, y = _proj(p, self.lon0, self.lat0, self.k)
            if x.max() < -self.box[0] or x.min() > self.box[0] or y.max() < -self.box[1] or y.min() > self.box[1]:
                continue
            ctx.move_to(x[0], y[0])
            for xx, yy in zip(x[1:], y[1:]): ctx.line_to(xx, yy)
            ctx.close_path()
        set_col(ctx, col); ctx.fill_preserve()
        if edge: set_col(ctx, self.cols['edge'], 0.8); ctx.set_line_width(2.5); ctx.stroke()
        ctx.new_path()

    def xy(self, lon, lat):
        return ((lon - self.lon0) * self.k * math.cos(math.radians(self.lat0)), -(lat - self.lat0) * self.k)

    def draw(self, ctx, t):
        self._ctx = ctx
        bw, bh = self.box
        c = self.cols
        ctx.save()
        rrect(ctx, -bw / 2, -bh / 2, bw, bh, 10); ctx.clip()
        g = cairo.RadialGradient(0, 0, 0, 0, 0, bw * 0.7)
        g.add_color_stop_rgba(0, *hexc(c['sea'])); g.add_color_stop_rgba(1, *hexc(c['sea2']))
        ctx.set_source(g); ctx.paint()
        # graticule each 2 deg
        ctx.set_source_rgba(*c['grid']); ctx.set_line_width(1.5)
        for lo in range(int(self.lon0) - 20, int(self.lon0) + 21, 2):
            x, _ = self.xy(lo, 0); ctx.move_to(x, -bh); ctx.line_to(x, bh)
        for la in range(int(self.lat0) - 20, int(self.lat0) + 21, 2):
            _, y = self.xy(0, la); ctx.move_to(-bw, y); ctx.line_to(bw, y)
        ctx.stroke()
        # coast ripple lines (animated) – subtle
        self._polys(UI._land(), c['land'])
        for nm in self.hl:
            self._polys(UI._country(nm), c['hl'])
        ctx.restore()
        rrect(ctx, -bw / 2, -bh / 2, bw, bh, 10); set_col(ctx, PAL.WHITE if self.style != 'sepia' else INK, 0.85)
        ctx.set_line_width(3); ctx.stroke()
        for (txt, lo, la, tl, sz) in self.labels:
            if t < tl: continue
            a = min(1, (t - tl) / 0.15)
            x, y = self.xy(lo, la)
            draw_text(ctx, txt, x, y, 'bold', sz, c['text'], 0.22, 'center', shadow=self.style != 'sepia', alpha=a)
        for (lo, la, tp) in self.pins:
            if t < tp: continue
            x, y = self.xy(lo, la)
            lt = t - tp
            s = ease('back', min(1, lt / 0.2))
            pulse = (lt % 1.4) / 1.4
            circle(ctx, x, y, self.pin_r + 30 * pulse); set_col(ctx, PAL.RED, 0.55 * (1 - pulse)); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, x, y, self.pin_r * s); set_col(ctx, PAL.RED); ctx.fill_preserve()
            set_col(ctx, PAL.WHITE); ctx.set_line_width(3); ctx.stroke()


# ------------------------------------------------------------------ newspaper clipping
class Newspaper(Element):
    """1972-style clipping: torn paper, masthead rule, big headline, columns of
    grey text lines, halftone illustration box drawn by `art(ctx, t, w, h)`."""
    def __init__(self, headline, kicker='', dateline='', art=None, w=1080, h=720, **kw):
        super().__init__(**kw)
        self.hl, self.kicker, self.dateline, self.art, self.w, self.h = headline, kicker, dateline, art, w, h
        r = rng(9)
        self.torn = [(r.uniform(-6, 6)) for _ in range(80)]
        self.lines = [r.uniform(0.55, 1.0) for _ in range(60)]

    def _outline(self, ctx):
        w, h = self.w, self.h
        n = 40
        ctx.move_to(-w / 2, -h / 2)
        for i in range(n + 1): ctx.line_to(-w / 2 + w * i / n, -h / 2 + self.torn[i])
        for i in range(n + 1): ctx.line_to(w / 2 + self.torn[(i + 40) % 80], -h / 2 + h * i / n)
        for i in range(n + 1): ctx.line_to(w / 2 - w * i / n, h / 2 + self.torn[(i + 13) % 80])
        for i in range(n + 1): ctx.line_to(-w / 2 + self.torn[(i + 57) % 80], h / 2 - h * i / n)
        ctx.close_path()

    def draw(self, ctx, t):
        w, h = self.w, self.h
        ctx.save(); ctx.translate(10, 16); self._outline(ctx); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill(); ctx.restore()
        self._outline(ctx); set_col(ctx, '#EBDFC2'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.RadialGradient(0, 0, 0, 0, 0, w * 0.7)
        g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.45, 0.3, 0.12, 0.35)
        ctx.set_source(g); ctx.paint()
        x0 = -w / 2 + 50
        # masthead
        draw_text(ctx, self.kicker, 0, -h / 2 + 70, 'black', 30, INK, 0.3, 'center', shadow=False)
        ctx.rectangle(x0, -h / 2 + 90, w - 100, 4); set_col(ctx, INK); ctx.fill()
        ctx.rectangle(x0, -h / 2 + 98, w - 100, 1.5); ctx.fill()
        draw_text(ctx, self.dateline, x0, -h / 2 + 128, 'bold', 20, INK, 0.2, shadow=False)
        # headline (types on)
        k = min(1, t / 0.5)
        hl = self.hl[:max(0, int(len(self.hl) * k))]
        draw_text(ctx, hl, 0, -h / 2 + 220, 'black', 74, '#1E140C', 0.0, 'center', shadow=False)
        # art box (right) + text columns (left)
        ay = -h / 2 + 270; aw, ah = w * 0.46, h - 330
        ax = w / 2 - 50 - aw
        ctx.save(); ctx.rectangle(ax, ay, aw, ah); ctx.clip()
        set_col(ctx, '#CDBB93'); ctx.paint()
        if self.art: ctx.translate(ax, ay); self.art(ctx, t, aw, ah)
        ctx.restore()
        ctx.rectangle(ax, ay, aw, ah); set_col(ctx, INK); ctx.set_line_width(3); ctx.stroke()
        cw = (ax - x0 - 40) / 2
        for col in range(2):
            for i in range(17):
                y = ay + 10 + i * 22
                if y > h / 2 - 50: break
                L = cw * self.lines[(col * 17 + i) % 60]
                ctx.rectangle(x0 + col * (cw + 30), y, L, 8); ctx.set_source_rgba(0.24, 0.17, 0.1, 0.45); ctx.fill()
        ctx.restore()


def surfer_art(ctx, t, w, h):
    """Halftone-ish sepia sketch: horizon, a wave, a surfer sitting on a board."""
    ctx.rectangle(0, 0, w, h * 0.45); set_col(ctx, '#DCCCA6'); ctx.fill()
    ctx.rectangle(0, h * 0.45, w, h); set_col(ctx, '#A8916A'); ctx.fill()
    # halftone dots on water
    for yy in range(int(h * 0.47), int(h), 14):
        for xx in range(0, int(w), 14):
            r = 1.2 + 2.6 * (yy - h * 0.45) / (h * 0.6)
            circle(ctx, xx + (yy // 14 % 2) * 7, yy, r); ctx.set_source_rgba(0.25, 0.17, 0.08, 0.35); ctx.fill()
    # headland (Point Sur rock silhouette)
    ctx.move_to(w * 0.55, h * 0.46); ctx.curve_to(w * 0.62, h * 0.30, w * 0.70, h * 0.22, w * 0.78, h * 0.26)
    ctx.curve_to(w * 0.86, h * 0.32, w * 0.95, h * 0.40, w * 1.0, h * 0.46); ctx.close_path()
    set_col(ctx, '#6B5536'); ctx.fill()
    bob = 4 * math.sin(t * 2.2)
    ctx.save(); ctx.translate(w * 0.35, h * 0.62 + bob); ctx.scale(0.9, 0.9)
    _surfer_side(ctx, t, 1.0, ink=True)
    ctx.restore()


# ------------------------------------------------------------------ surfer
def _surfer_side(ctx, t, s=1.0, ink=False, jolt=0.0, kick=1.0):
    """Surfer sitting on a board, seen from the side, origin = board at waterline.
    Board ~360 units long. Legs dangle below (y>0)."""
    suit = '#14181C' if not ink else '#2C2014'
    ow = 4
    # legs (below water)
    for i, ph in enumerate((0.0, 1.7)):
        sw = kick * 18 * math.sin(t * 2.4 + ph) + jolt * (30 if i == 0 else 10)
        hip = (-10 + i * 16, -14)
        knee = (20 + i * 12, 70)
        foot = (knee[0] - 20 + sw, 150 + i * 6)
        ctx.move_to(*hip); ctx.line_to(*knee); ctx.line_to(*foot)
        set_col(ctx, OUT if not ink else INK); ctx.set_line_width(30 + ow * 2); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.move_to(*hip); ctx.line_to(*knee); ctx.line_to(*foot)
        set_col(ctx, suit); ctx.set_line_width(30); ctx.stroke()
    # board
    ctx.save(); ctx.rotate(math.radians(-2 + jolt * 6))
    ctx.move_to(-190, 0); ctx.curve_to(-170, -16, 120, -20, 190, -6); ctx.curve_to(150, 12, -150, 14, -190, 0); ctx.close_path()
    set_col(ctx, '#E9DFC8' if not ink else '#E6D7B4'); ctx.fill_preserve(); set_col(ctx, OUT if not ink else INK); ctx.set_line_width(ow); ctx.stroke()
    ctx.move_to(-180, 2); ctx.curve_to(-100, 4, 100, 2, 182, -5); set_col(ctx, '#C0462F' if not ink else '#8A5A30'); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    # torso
    lean = 4 * math.sin(t * 1.3) + jolt * -14
    ctx.save(); ctx.rotate(math.radians(lean))
    rrect(ctx, -26, -150, 52, 140, 22); set_col(ctx, suit); ctx.fill_preserve(); set_col(ctx, OUT if not ink else INK); ctx.set_line_width(ow); ctx.stroke()
    # arm resting
    ctx.move_to(0, -120); ctx.line_to(30, -60); ctx.line_to(60, -20)
    set_col(ctx, OUT if not ink else INK); ctx.set_line_width(22 + 8); ctx.stroke()
    ctx.move_to(0, -120); ctx.line_to(30, -60); ctx.line_to(60, -20); set_col(ctx, suit); ctx.set_line_width(22); ctx.stroke()
    # head (looks back with jolt)
    circle(ctx, 4, -182, 30); set_col(ctx, '#D9A97F' if not ink else '#B48D62'); ctx.fill_preserve()
    set_col(ctx, OUT if not ink else INK); ctx.set_line_width(ow); ctx.stroke()
    ctx.move_to(-28, -186); ctx.curve_to(-26, -222, 30, -222, 34, -190); ctx.curve_to(10, -200, -10, -196, -28, -186)
    set_col(ctx, '#3A2A1C'); ctx.fill()
    ex = 16 if jolt < 0.5 else -12
    circle(ctx, ex, -182, 4); set_col(ctx, '#0A0A0A'); ctx.fill()
    ctx.restore()


class Surfer(Element):
    """Surfer on a board (side view). plate=<Surface> floats it. jolt: 0..1 (callable/K)."""
    def __init__(self, plate=None, jolt=0.0, kick=1.0, ink=False, **kw):
        super().__init__(**kw); self.plate, self.jolt, self.kick, self.ink = plate, jolt, kick, ink
        self.proc(self._float)
    def _float(self, el, t):
        if self.plate is None: return {}
        x = ev(self.pos, t)[0]
        y = self.plate.water_y(x, t + self.t0) - self.plate.wl
        sl = (self.plate.water_y(x + 60, t + self.t0) - self.plate.water_y(x - 60, t + self.t0)) / 120
        return {'dpos': (0, y), 'drot': math.degrees(math.atan(sl))}
    def draw(self, ctx, t):
        _surfer_side(ctx, t, 1.0, self.ink, ev(self.jolt, t), ev(self.kick, t))


# ------------------------------------------------------------------ silhouettes from below
class SurferBelow(Element):
    """Seen from below against the surface: board + prone paddling surfer (head = -x)."""
    def __init__(self, color='#05121A', paddle=1.0, **kw):
        super().__init__(**kw); self.c, self.paddle = color, paddle
    def draw(self, ctx, t):
        c = self.c
        # board
        ctx.move_to(-260, 0); ctx.curve_to(-240, -58, 200, -54, 250, 0); ctx.curve_to(200, 54, -240, 58, -260, 0)
        set_col(ctx, c); ctx.fill()
        # body: head, torso, legs
        circle(ctx, -170, 0, 30); set_col(ctx, c); ctx.fill()
        rrect(ctx, -150, -42, 210, 84, 34); ctx.fill()
        for s in (1, -1):
            ctx.move_to(50, 20 * s); ctx.line_to(150, 30 * s); ctx.line_to(250, 34 * s)
            ctx.set_line_width(30); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            # paddling arms sweeping
            a = math.sin(t * 3.2 + (0 if s > 0 else math.pi)) * self.paddle
            ctx.move_to(-120, 36 * s); ctx.line_to(-140 + 80 * a, (100 + 20 * abs(a)) * s); ctx.line_to(-170 + 140 * a, (150) * s)
            ctx.set_line_width(24); ctx.stroke()


class SeaLionBelow(Element):
    """Sea lion seen from below (silhouette): torpedo body, fore flippers out, hind flippers."""
    def __init__(self, color='#05121A', **kw):
        super().__init__(**kw); self.c = color
    def draw(self, ctx, t):
        set_col(ctx, self.c)
        k = math.sin(t * 2.6)
        body = catmull([(-250, 0), (-225, -34), (-160, -52), (-40, -76), (80, -64), (180, -34), (240, -14), (240, 14),
                        (180, 34), (80, 64), (-40, 76), (-160, 52), (-225, 34)], 6, closed=True)
        poly(ctx, body); ctx.fill()
        for s in (1, -1):
            ctx.save(); ctx.translate(-60, 60 * s); ctx.rotate(math.radians((20 + 14 * k * s) * s))
            ctx.move_to(0, -20 * s); ctx.curve_to(40, 40 * s, 110, 120 * s, 150, 150 * s); ctx.curve_to(110, 150 * s, 30, 90 * s, -40, 10 * s)
            ctx.close_path(); ctx.fill(); ctx.restore()
            ctx.save(); ctx.translate(230, 10 * s); ctx.rotate(math.radians((12 + 6 * k) * s))
            ctx.move_to(0, -8 * s); ctx.line_to(110, 40 * s); ctx.line_to(96, 4 * s); ctx.close_path(); ctx.fill(); ctx.restore()


# ------------------------------------------------------------------ x-ray leg + stitches
class LegStitches(Element):
    """Blueprint leg outline (side, knee bent slightly) with a wound line that
    receives `n(t)` stitches (0..100). Cyan x-ray look."""
    def __init__(self, n=0, total=100, **kw):
        super().__init__(**kw); self.n, self.total = n, total
        # wound path along calf/thigh (local coords)
        self.path = catmull([(-420, -40), (-300, -70), (-160, -60), (-40, -10), (80, 20), (200, 10), (330, -20), (420, -10)], 14)
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(self.path, axis=0).T))]
        self.d = d
    def _leg(self, ctx):
        ctx.move_to(-620, -110); ctx.curve_to(-400, -150, -200, -140, -20, -110)   # thigh top
        ctx.curve_to(80, -95, 140, -120, 220, -110)                                   # knee
        ctx.curve_to(380, -90, 520, -60, 600, -60)                                     # shin
        ctx.curve_to(660, -110, 760, -110, 790, -60); ctx.curve_to(800, -10, 780, 40, 740, 50)  # foot
        ctx.curve_to(660, 50, 600, 46, 560, 40)
        ctx.curve_to(420, 60, 300, 90, 160, 70)                                        # calf
        ctx.curve_to(60, 60, -20, 80, -120, 90); ctx.curve_to(-300, 110, -460, 110, -620, 90)
    def draw(self, ctx, t):
        self._leg(ctx)
        ctx.set_source_rgba(0.5, 0.76, 0.8, 0.10); ctx.fill_preserve()
        set_col(ctx, PAL.CYAN, 0.25); ctx.set_line_width(12); ctx.stroke_preserve()
        set_col(ctx, PAL.CYAN_HI); ctx.set_line_width(4); ctx.stroke()
        # bones
        ctx.set_source_rgba(0.5, 0.76, 0.8, 0.35); ctx.set_line_width(16); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-600, -10); ctx.line_to(60, 0); ctx.stroke()
        ctx.move_to(110, 0); ctx.line_to(620, -5); ctx.stroke()
        circle(ctx, 85, -2, 26); ctx.stroke()
        # wound
        P = self.path
        poly(ctx, P, close=False); set_col(ctx, PAL.RED, 0.9); ctx.set_line_width(6); ctx.stroke()
        n = int(round(ev(self.n, t)))
        L = self.d[-1]
        for i in range(n):
            s = (i + 0.5) / self.total * L
            j = int(np.searchsorted(self.d, s)); j = max(1, min(j, len(P) - 1))
            p0, p1 = P[j - 1], P[j]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]; ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            f = (s - self.d[j - 1]) / max(1e-6, self.d[j] - self.d[j - 1])
            x, y = p0[0] + dx * f, p0[1] + dy * f
            ctx.move_to(x - nx * 14 - dx / ln * 3, y - ny * 14 - dy / ln * 3); ctx.line_to(x + nx * 14 + dx / ln * 3, y + ny * 14 + dy / ln * 3)
        set_col(ctx, PAL.WHITE); ctx.set_line_width(3.2); ctx.stroke()


# ------------------------------------------------------------------ reticle
class Reticle(Element):
    """Red lock-on reticle: rotating dashed ring + 4 ticks, snaps in from 2x."""
    def __init__(self, r=70, color=PAL.RED, **kw):
        super().__init__(**kw); self.r, self.c = r, color
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.25)); r = self.r * (2.2 - 1.2 * k)
        a = min(1, t / 0.1)
        ctx.save(); ctx.rotate(t * 1.2)
        ctx.set_dash([18, 10]); circle(ctx, 0, 0, r); set_col(ctx, self.c, a); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])
        ctx.restore()
        circle(ctx, 0, 0, r * 0.62); set_col(ctx, self.c, a * 0.7); ctx.set_line_width(3); ctx.stroke()
        for i in range(4):
            ang = i * math.pi / 2
            ctx.move_to(math.cos(ang) * r * 0.75, math.sin(ang) * r * 0.75); ctx.line_to(math.cos(ang) * r * 1.3, math.sin(ang) * r * 1.3)
        set_col(ctx, self.c, a); ctx.set_line_width(5); ctx.stroke()
        circle(ctx, 0, 0, 5); ctx.fill()


# ------------------------------------------------------------------ top-down sailboat
class SailboatTop(Element):
    """Top-down sailboat, bow at +x, ~520 units long. rudder angle (deg) shown at the stern."""
    def __init__(self, rudder=0.0, wake=1.0, crew=2, **kw):
        super().__init__(**kw); self.rudder, self.wake, self.crew = rudder, wake, crew
    def draw(self, ctx, t):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        wk = ev(self.wake, t)
        if wk > 0:
            for i in range(6):
                ph = (t * 0.8 + i / 6) % 1
                x = -250 - ph * 380
                w = 40 + ph * 160
                ctx.move_to(x, -w); ctx.curve_to(x + 40, -w * 0.5, x + 40, w * 0.5, x, w)
                ctx.set_source_rgba(0.92, 0.98, 1, 0.45 * (1 - ph) * wk); ctx.set_line_width(4); ctx.stroke()
        # rudder
        ra = math.radians(ev(self.rudder, t))
        ctx.save(); ctx.translate(-250, 0); ctx.rotate(ra)
        rrect(ctx, -60, -7, 60, 14, 6); set_col(ctx, '#2A3238'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        hull = catmull([(-255, -70), (-120, -100), (60, -100), (180, -78), (270, 0), (180, 78), (60, 100), (-120, 100), (-255, 70)], 8, closed=True)
        ctx.save(); ctx.translate(8, 12); poly(ctx, hull); ctx.set_source_rgba(0, 0.05, 0.08, 0.35); ctx.fill(); ctx.restore()
        poly(ctx, hull); set_col(ctx, '#F2F1EC'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        deck = catmull([(-235, -55), (-110, -80), (50, -80), (160, -62), (230, 0), (160, 62), (50, 80), (-110, 80), (-235, 55)], 8, closed=True)
        poly(ctx, deck); set_col(ctx, '#C9A877'); ctx.fill()
        rrect(ctx, -120, -55, 180, 110, 18); set_col(ctx, '#E4E5E0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        for x in (-90, -30, 30):
            rrect(ctx, x, -14, 30, 28, 6); set_col(ctx, '#2B4A5C'); ctx.fill()
        # boom + sail (curved)
        sw = 6 * math.sin(t * 1.4)
        ctx.move_to(60, 0); ctx.curve_to(0, 40 + sw, -100, 70 + sw, -190, 90 + sw)
        set_col(ctx, '#F4EFE4'); ctx.set_line_width(14); ctx.stroke()
        ctx.move_to(60, 0); ctx.curve_to(0, 40 + sw, -100, 70 + sw, -190, 90 + sw); set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()
        circle(ctx, 60, 0, 12); set_col(ctx, '#C9CCCB'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        # crew (heads from above)
        for i in range(self.crew):
            cx, cy = -190 + i * 0, -30 + i * 60
            circle(ctx, cx, cy, 20); set_col(ctx, ['#C8453A', '#2F6FA0'][i % 2]); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, cx + 4, cy, 12); set_col(ctx, '#E2B58F'); ctx.fill()


# ------------------------------------------------------------------ sinking boat icon
class SinkingBoat(Element):
    """Flat boat icon floating on a short waterline; sinks (tilt + drop + bubbles) from t_sink."""
    def __init__(self, t_sink=None, color=PAL.WHITE, **kw):
        super().__init__(**kw); self.ts, self.c = t_sink, color
    def draw(self, ctx, t):
        bob = 3 * math.sin(t * 2.4 + ev(self.pos, 0)[0] * 0.01)
        k = 0.0 if self.ts is None or t < self.ts else ease('ei', min(1, (t - self.ts) / 0.9))
        # water strip
        ctx.save(); ctx.rectangle(-90, 4, 180, 220); ctx.clip()
        ctx.rectangle(-90, 4, 180, 220); ctx.set_source_rgba(0.1, 0.35, 0.45, 0.35); ctx.fill()
        ctx.restore()
        ctx.save(); ctx.rectangle(-95, -200, 190, 204 + 120 * k + 130); ctx.clip()
        ctx.save(); ctx.translate(0, bob + 150 * k); ctx.rotate(math.radians(-38 * k))
        alpha = 1 - 0.7 * k
        set_col(ctx, self.c, alpha); ctx.set_line_width(5); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(-70, -6); ctx.line_to(70, -6); ctx.line_to(48, 22); ctx.line_to(-54, 22); ctx.close_path(); ctx.fill()
        ctx.move_to(0, -10); ctx.line_to(0, -110); ctx.line_to(50, -20); ctx.close_path(); ctx.stroke()
        ctx.move_to(-6, -100); ctx.line_to(-50, -22); ctx.line_to(-6, -22); ctx.close_path(); ctx.stroke()
        ctx.restore(); ctx.restore()
        # waterline
        ctx.move_to(-90, 4)
        for i in range(19):
            x = -90 + i * 10; ctx.line_to(x, 4 + 3 * math.sin(x * 0.08 + t * 3))
        set_col(ctx, PAL.WHITE, 0.9); ctx.set_line_width(3); ctx.stroke()
        if k > 0:
            r = rng(int(ev(self.pos, 0)[0]))
            for i in range(8):
                ph = ((t - self.ts) * 0.9 + i / 8) % 1
                if (t - self.ts) < i / 8: continue
                circle(ctx, r.uniform(-40, 40) + 6 * math.sin(t * 5 + i), 100 - ph * 100, 3 + 4 * r.random())
                set_col(ctx, PAL.WHITE, 0.6 * (1 - ph)); ctx.set_line_width(2); ctx.stroke()


class PersonIcon(Element):
    """Person icon in a circle; green ring (safe)."""
    def __init__(self, color=PAL.GREEN, t_tick=None, **kw):
        super().__init__(**kw); self.c, self.tt = color, t_tick
    def draw(self, ctx, t):
        b = 2 * math.sin(t * 2 + ev(self.pos, 0)[0] * 0.02)
        circle(ctx, 0, b, 44); set_col(ctx, '#0E2A38'); ctx.fill_preserve(); set_col(ctx, self.c); ctx.set_line_width(4); ctx.stroke()
        ctx.save(); ctx.translate(0, b + 4); UI.icon(ctx, 'person', 30, PAL.WHITE); ctx.restore()
        if self.tt is not None and t >= self.tt:
            k = ease('eo', min(1, (t - self.tt) / 0.25))
            circle(ctx, 34, b - 32, 16); set_col(ctx, PAL.GREEN); ctx.fill()
            UI.tick_path(ctx, 26, b - 32, 15, k); set_col(ctx, PAL.WHITE); ctx.set_line_width(4); ctx.stroke()


# ------------------------------------------------------------------ orcas with headgear
class HatOrca(Orca):
    """Side orca with headgear: hat='helmet' (Roman gladiator galea + red crest) or 'salmon'."""
    def __init__(self, hat='helmet', crest='#C8453A', **kw):
        super().__init__(**kw); self.hat, self.crest = hat, crest
    def draw(self, ctx, t):
        super().draw(ctx, t)
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        P = self.pose(t)
        D = P['D']
        # anchor on deformed head-top point
        top = P['top']
        i_ = int(len(top) * 0.33)
        hx, hy = float(top[i_][0]), float(top[i_][1]) + 18
        ctx.translate(hx, hy)
        if self.hat == 'helmet': self._helmet(ctx, t)
        elif self.hat == 'salmon': self._salmon(ctx, t)
        ctx.restore()

    def _helmet(self, ctx, t):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.rotate(math.radians(-14))
        bronze = '#C89048'
        # crest (brush) – wobble
        wob = 4 * math.sin(t * 5)
        ctx.move_to(-130, -60); ctx.curve_to(-100, -150 + wob, 90, -160 + wob, 140, -70)
        ctx.curve_to(80, -110, -60, -110, -130, -60); ctx.close_path()
        set_col(ctx, self.crest); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        ctx.set_source_rgba(0, 0, 0, 0.25); ctx.set_line_width(2.5)
        for i in range(9):
            x = -100 + i * 26
            ctx.move_to(x, -78); ctx.line_to(x + 10, -118 + abs(x) * 0.12); ctx.stroke()
        # dome
        ctx.move_to(-150, 30); ctx.curve_to(-160, -70, 150, -100, 170, 10); ctx.line_to(170, 40); ctx.line_to(-150, 55); ctx.close_path()
        set_col(ctx, bronze); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(7); ctx.stroke()
        # sheen
        ctx.move_to(-90, -20); ctx.curve_to(-60, -55, 20, -66, 70, -50); ctx.set_source_rgba(1, 0.95, 0.75, 0.6); ctx.set_line_width(8); ctx.stroke()
        # brim band
        ctx.move_to(-165, 50); ctx.line_to(185, 34); ctx.line_to(185, 56); ctx.line_to(-165, 72); ctx.close_path()
        set_col(ctx, '#8E5F28'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        for x in (-120, -40, 40, 120):
            circle(ctx, x, 55 - (x + 165) * 0.045, 6); set_col(ctx, '#F0D08A'); ctx.fill()

    def _salmon(self, ctx, t):
        ctx.translate(0, -18); ctx.rotate(math.radians(-8)); ctx.scale(0.8, 0.8)
        sag = 6 * math.sin(t * 2.0)
        body = catmull([(-190, 30), (-140, -10), (-40, -36), (60, -36), (150, -14), (200, 20 + sag), (150, 30), (60, 36),
                        (-40, 34), (-140, 40)], 8, closed=True)
        poly(ctx, body); set_col(ctx, '#C8D2D6'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        ctx.rectangle(-220, -60, 440, 50); set_col(ctx, '#5F7E8C'); ctx.fill()
        ctx.rectangle(-220, 0, 440, 12); set_col(ctx, '#E59A8C', 0.8); ctx.fill()
        r = rng(4)
        for _ in range(14):
            circle(ctx, r.uniform(-120, 140), r.uniform(-30, -12), 3); set_col(ctx, '#2E3E46'); ctx.fill()
        ctx.restore()
        poly(ctx, body); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # tail drooping down past the orca's eye side
        ctx.move_to(195, 18 + sag); ctx.line_to(270, -10 + sag); ctx.line_to(255, 50 + sag); ctx.close_path()
        set_col(ctx, '#7F97A2'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        # head with X eye (dead)
        ctx.move_to(-150, 0); ctx.line_to(-128, 26); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        UI.x_path(ctx, -165, 6, 16); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-190, 30); ctx.line_to(-170, 22); ctx.stroke()


# ------------------------------------------------------------------ hypothesis badge
class HypoBadge(Element):
    """Big circular badge with custom content fn(ctx, t), caption pill below,
    pops with overshoot 0.25 s."""
    def __init__(self, content, caption, r=150, kind='dark', **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.content, self.cap, self.r, self.kind = content, caption, r, kind
    def draw(self, ctx, t):
        s = ease('back', min(1, t / 0.25)); a = min(1, t / 0.08)
        ctx.save(); ctx.scale(s, s)
        circle(ctx, 4, 8, self.r); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        circle(ctx, 0, 0, self.r); set_col(ctx, '#0E2A38', a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, a); ctx.set_line_width(5); ctx.stroke()
        circle(ctx, 0, 0, self.r - 14); set_col(ctx, PAL.WHITE, 0.25 * a); ctx.set_line_width(2); ctx.stroke()
        ctx.save(); circle(ctx, 0, 0, self.r - 16); ctx.clip()
        self.content(ctx, t)
        ctx.restore()
        ctx.restore()
        if t > 0.12:
            UI.Pill(self.cap, self.kind, size=40, pos=(0, self.r + 54)).render(ctx, t - 0.12)


def ball_content(ctx, t):
    """Beach ball bouncing on an orca's nose (play)."""
    y = -40 - 60 * abs(math.sin(t * 3.0))
    ctx.save(); ctx.translate(-10, y); ctx.rotate(t * 2)
    cols = ['#D73F3C', '#F2F0EB', '#F0A54A', '#F2F0EB', '#4C9BD0', '#F2F0EB']
    for i in range(6):
        ctx.move_to(0, 0); ctx.arc(0, 0, 42, i * TAU / 6, (i + 1) * TAU / 6); ctx.close_path(); set_col(ctx, cols[i]); ctx.fill()
    circle(ctx, 0, 0, 42); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
    ctx.restore()
    o = Orca(pos=(30, 120), scale=0.2, rot=-28, facing='left', swim=0.6, outline=10)
    o.render(ctx, t)


def salmon_content(ctx, t):
    o = HatOrca(hat='salmon', pos=(40, 40), scale=0.24, rot=0, facing='left', swim=0.6, outline=10)
    o.render(ctx, t)
    draw_text(ctx, '1987', 0, 112, 'marker', 36, PAL.ORANGE, 0, 'center')


def boat_bandage_content(ctx, t):
    ctx.save(); ctx.translate(0, 10 + 4 * math.sin(t * 2)); ctx.scale(1.25, 1.25)
    set_col(ctx, PAL.WHITE); ctx.set_line_width(5); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-70, -6); ctx.line_to(70, -6); ctx.line_to(48, 22); ctx.line_to(-54, 22); ctx.close_path(); ctx.fill()
    ctx.move_to(0, -10); ctx.line_to(0, -90); ctx.line_to(44, -18); ctx.close_path(); ctx.stroke()
    ctx.restore()
    # bandage cross (on an orca fin below)
    ctx.save(); ctx.translate(0, 80)
    ctx.move_to(-60, 30); ctx.curve_to(-20, 20, -10, -20, 6, -50); ctx.curve_to(10, -20, 30, 20, 60, 30); ctx.close_path()
    set_col(ctx, '#12171C'); ctx.fill_preserve(); set_col(ctx, PAL.WHITE); ctx.set_line_width(3); ctx.stroke()
    ctx.rotate(math.radians(-20)); rrect(ctx, -34, -14, 68, 22, 6); set_col(ctx, '#F0D9B5'); ctx.fill()
    ctx.rectangle(-8, -14, 16, 22); set_col(ctx, '#D7BF98'); ctx.fill()
    ctx.restore()


# ------------------------------------------------------------------ naturalist card
class NaturalistCard(Element):
    """Old naturalist plate: aged paper card, double rule border, 'engraved'
    orca (ink silhouette + hatching) and a typed name line."""
    def __init__(self, name='ORCINUS GLADIATOR', t_type=0.3, cps=22, w=1400, h=760, **kw):
        super().__init__(**kw); self.name, self.tt, self.cps, self.w, self.h = name, t_type, cps, w, h
        self.orca = Orca(pos=(0, -60), scale=0.95, facing='left', variant='silhouette', sil_color='#3B2A1A', swim=0.5)
    def draw(self, ctx, t):
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 10, -h / 2 + 16, w, h, 6); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, '#EADCB8'); ctx.fill()
        ctx.rectangle(-w / 2 + 26, -h / 2 + 26, w - 52, h - 52); set_col(ctx, INK); ctx.set_line_width(4); ctx.stroke()
        ctx.rectangle(-w / 2 + 38, -h / 2 + 38, w - 76, h - 76); ctx.set_line_width(1.5); ctx.stroke()
        draw_text(ctx, 'FIG. IV', -w / 2 + 70, -h / 2 + 90, 'bold', 24, INK, 0.3, shadow=False)
        self.orca.render(ctx, t)
        # hatching over the orca (engraving feel)
        ctx.save()
        ctx.set_source_rgba(0.92, 0.86, 0.72, 0.35); ctx.set_line_width(2)
        for i in range(-40, 40):
            ctx.move_to(i * 22 - 200, -400); ctx.line_to(i * 22 + 200, 200)
        ctx.stroke()
        ctx.restore()
        n = max(0, min(len(self.name), int((t - self.tt) * self.cps)))
        if t >= self.tt:
            draw_text(ctx, self.name[:n], 0, h / 2 - 110, 'black', 80, INK, 0.12, 'center', shadow=False)
            ctx.move_to(-420, h / 2 - 82); ctx.line_to(420, h / 2 - 82); set_col(ctx, INK); ctx.set_line_width(2); ctx.stroke()
