"""Act B custom rigs/assets (chapters 1 SIZE + 2 MENU). Engine is not modified."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import (Element, ev, hexc, mix, set_col, rrect, circle, poly, catmull, TAU, W, H, PAL, remap, ease,
                         rng, lerp, stroke_glow)
from engine.text import draw_text, measure, cap_height, set_font
from engine.ui import UI, ChapterTitle, icon as ui_icon, Globe, _ortho, _pop, Pill
from engine.chars.orca import _path, Deform
from engine.chars import Seal, Orca

OUT = PAL.OUTLINE
FPS = 30

# ---------------------------------------------------------------- navigator icons
NAV_ICONS = ['ruler', 'fork', 'fin', 'wheel', 'diver', 'net']
NAV_LABELS = ['SIZE', 'MENU', 'SHARKS', 'BOATS', 'YOUR MOVE', 'THE REAL DANGER']

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
    elif name == 'fork':
        ctx.move_to(-s * 0.35, -s * 0.8); ctx.line_to(-s * 0.35, -s * 0.2); ctx.stroke()
        for dx in (-0.55, -0.35, -0.15):
            ctx.move_to(s * dx, -s * 0.8); ctx.line_to(s * dx, -s * 0.35); ctx.stroke()
        ctx.move_to(-s * 0.55, -s * 0.35); ctx.curve_to(-s * 0.55, -s * 0.1, -s * 0.15, -s * 0.1, -s * 0.15, -s * 0.35); ctx.stroke()
        ctx.move_to(-s * 0.35, -s * 0.2); ctx.line_to(-s * 0.35, s * 0.8); ctx.stroke()
        ctx.move_to(s * 0.1, s * 0.6); ctx.curve_to(s * 0.3, s * 0.3, s * 0.35, -s * 0.3, s * 0.45, -s * 0.75)
        ctx.curve_to(s * 0.55, -s * 0.3, s * 0.7, s * 0.3, s * 0.85, s * 0.6); ctx.close_path(); ctx.fill()
    elif name == 'wheel':
        circle(ctx, 0, 0, s * 0.5); ctx.stroke(); circle(ctx, 0, 0, s * 0.14); ctx.fill()
        for k in range(8):
            a = k * TAU / 8
            ctx.move_to(math.cos(a) * s * 0.15, math.sin(a) * s * 0.15); ctx.line_to(math.cos(a) * s * 0.85, math.sin(a) * s * 0.85); ctx.stroke()
    elif name == 'diver':
        circle(ctx, -s * 0.55, -s * 0.1, s * 0.2); ctx.fill()
        ctx.move_to(-s * 0.35, 0); ctx.line_to(s * 0.4, s * 0.05); ctx.stroke()
        ctx.move_to(s * 0.4, s * 0.05); ctx.line_to(s * 0.85, -s * 0.25); ctx.move_to(s * 0.4, s * 0.05); ctx.line_to(s * 0.85, s * 0.3); ctx.stroke()
        rrect(ctx, -s * 0.25, -s * 0.38, s * 0.45, s * 0.2, s * 0.08); ctx.fill()
    elif name == 'net':
        for i in range(-2, 3):
            ctx.move_to(-s * 0.8, i * s * 0.3); ctx.line_to(s * 0.8, i * s * 0.3 + s * 0.1); ctx.stroke()
            ctx.move_to(i * s * 0.3, -s * 0.8); ctx.line_to(i * s * 0.3 + s * 0.1, s * 0.8); ctx.stroke()
    else:
        ui_icon(ctx, name, r, color, lw)

class NavChapterTitle(ChapterTitle):
    """ChapterTitle with this video's six chapter icons (ruler, fork+fin, fin, wheel, diver, net)."""
    def __init__(self, title, subtitle, n, **kw):
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

class FadeIn(UI):
    """Black overlay fading out over dur (head of a shot after a dip)."""
    def __init__(self, dur=0.35, color=(0, 0, 0), **kw):
        kw.setdefault('z', 90); super().__init__(**kw); self.d, self.c = dur, color
    def draw(self, ctx, t):
        a = 1 - min(1, t / self.d)
        if a > 0: ctx.set_source_rgba(*self.c, a); ctx.rectangle(0, 0, W, H); ctx.fill()

class FadeOut(UI):
    def __init__(self, dur=0.35, **kw):
        kw.setdefault('z', 90); super().__init__(**kw); self.d = dur
    def draw(self, ctx, t):
        a = min(1, t / self.d)
        ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(0, 0, W, H); ctx.fill()

# ---------------------------------------------------------------- dolphins
class Dolphin(Element):
    """Side-view toothed whale facing LEFT, body ~1000 units like Orca.
    kind: 'bottlenose' (grey, beak), 'risso' (pale scarred, blunt), 'pilot' (black, bulbous melon)."""
    KINDS = {
        'bottlenose': dict(col='#7D8C96', belly='#C9D2D6', beak=70, melon=0.0, fin=1.0),
        'risso': dict(col='#A3ACB0', belly='#D9DEE0', beak=0, melon=0.35, fin=1.15),
        'pilot': dict(col='#22272C', belly='#3B444B', beak=0, melon=0.8, fin=0.8),
    }
    def __init__(self, kind='bottlenose', swim=1.0, period=2.2, phase=0.0, **kw):
        super().__init__(**kw); self.k = self.KINDS[kind]; self.kind = kind
        self.swim, self.period, self.phase = swim, period, phase
        b = self.k['beak']; m = self.k['melon']
        top = [(-500, 10), (-500 + b * 0.2, 0), (-430 + b * 0.0, -6), (-410, -30 - 40 * m), (-360, -70 - 25 * m),
               (-260, -96), (-120, -104), (40, -92), (200, -62), (330, -30), (420, -12)]
        if b == 0: top = [(-480, 6), (-488, -20 - 30 * m), (-460, -58 - 30 * m), (-400, -86 - 15 * m), (-300, -100),
                          (-140, -106), (40, -92), (200, -62), (330, -30), (420, -12)]
        bot = [(420, 10), (330, 24), (200, 50), (40, 80), (-120, 92), (-280, 80), (-380, 50), (-440, 26), (-480 if b == 0 else -500, 10)]
        self.top, self.bot = catmull(top, 6), catmull(bot, 6)
        self.fl = catmull([(420, -12), (450, -28), (500, -60), (512, -40), (490, 0), (512, 40), (500, 60), (450, 26), (420, 10)], 5)
        f = self.k['fin']
        self.dor = catmull([(-120, -100), (-80, -140 * f), (-30, -190 * f), (0, -200 * f), (-6, -170 * f), (10, -120 * f), (50, -94)], 6)
        self.pec = catmull([(-300, 40), (-260, 70), (-220, 120), (-230, 130), (-280, 90), (-320, 50)], 5, closed=True)

    def draw(self, ctx, t):
        D = Deform(t, 18 * ev(self.swim, t), self.period, 0.0, self.phase)
        top, bot, fl, dor = D(self.top), D(self.bot), D(self.fl, fluke=True), D(self.dor)
        k = self.k
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        _path(ctx, dor, close=False); ctx.line_to(float(dor[0, 0]) + 30, float(dor[0, 1]) + 30); ctx.close_path()
        set_col(ctx, k['col']); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(7); ctx.stroke()
        body = np.vstack([top, fl[1:], bot[1:]])
        _path(ctx, body); set_col(ctx, k['col']); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.LinearGradient(0, -20, 0, 100)
        bc = hexc(k['belly']); g.add_color_stop_rgba(0, bc[0], bc[1], bc[2], 0); g.add_color_stop_rgba(0.45, *bc); g.add_color_stop_rgba(1, *bc)
        ctx.set_source(g); ctx.rectangle(-560, -20, 1100, 200); ctx.fill()
        if self.kind == 'risso':
            r = rng(5); ctx.set_source_rgba(1, 1, 1, 0.55); ctx.set_line_width(2.5)
            for _ in range(18):
                x, y = r.uniform(-420, 300), r.uniform(-90, 40)
                ctx.move_to(x, y); ctx.line_to(x + r.uniform(20, 60), y + r.uniform(-8, 8)); ctx.stroke()
        ctx.restore()
        _path(ctx, body); set_col(ctx, OUT); ctx.set_line_width(7); ctx.stroke()
        pec = D(self.pec); _path(ctx, pec); set_col(ctx, mix(k['col'], '#000000', 0.2)); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        e = D(np.array([[-370.0, -18]]))[0]
        circle(ctx, e[0], e[1], 8); set_col(ctx, '#050607'); ctx.fill()
        circle(ctx, e[0] - 2, e[1] - 2, 2); set_col(ctx, '#E8EEF0'); ctx.fill()

# ---------------------------------------------------------------- strike-through label
class StrikeLabel(UI):
    """Text with a red strike-through drawn on at t_strike (10 frames)."""
    def __init__(self, text, size=56, t_strike=0.5, color=PAL.WHITE, font='xb', align='center', **kw):
        super().__init__(**kw); self.text, self.size, self.ts, self.c, self.font, self.align = text, size, t_strike, color, font, align
    def draw(self, ctx, t):
        a, s = _pop(t)
        w = measure(ctx, self.text, self.font, self.size, 0.04)[0]
        x0 = -w / 2 if self.align == 'center' else 0
        dim = 1.0 if t < self.ts else 1 - 0.4 * min(1, (t - self.ts) / 0.3)
        draw_text(ctx, self.text, x0, 0, self.font, self.size, self.c, 0.04, alpha=a * dim)
        if t >= self.ts:
            k = ease('eo', min(1, (t - self.ts) / (10 / FPS)))
            ch = cap_height(ctx, self.font, self.size)
            ctx.move_to(x0 - 12, -ch * 0.45 + 4); ctx.line_to(x0 - 12 + (w + 24) * k, -ch * 0.5 - 4)
            set_col(ctx, PAL.RED); ctx.set_line_width(self.size * 0.12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()

# ---------------------------------------------------------------- dorsal fin
class DorsalFin(Element):
    """Male orca dorsal fin standing on a base line. height in units (base at y=0).
    xray=True draws it as cyan glowing outline with no skeleton, plus scan line."""
    def __init__(self, height=600, xray=False, sway=1.0, scan=None, **kw):
        super().__init__(**kw); self.h, self.xray, self.sway, self.scan = height, xray, sway, scan
    def pts(self, t):
        h = self.h; sw = self.sway * 10 * math.sin(TAU * t / 3.0)
        base = [(-h * 0.36, 0), (-h * 0.30, -h * 0.25), (-h * 0.22, -h * 0.55), (-h * 0.12, -h * 0.85), (-h * 0.06, -h * 0.99),
                (h * 0.01, -h * 1.0), (h * 0.05, -h * 0.82), (h * 0.08, -h * 0.55), (h * 0.14, -h * 0.25), (h * 0.26, 0)]
        P = np.array(base, float)
        P[:, 0] += sw * (-P[:, 1] / h) ** 1.5
        return catmull(P, 8)
    def draw(self, ctx, t):
        P = self.pts(t)
        def path():
            _path(ctx, P, close=False); ctx.close_path()
        if not self.xray:
            path(); set_col(ctx, '#12171C'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(8); ctx.stroke()
            ctx.save(); path(); ctx.clip()
            g = cairo.LinearGradient(-self.h * 0.3, 0, self.h * 0.2, 0)
            g.add_color_stop_rgba(0, 0.35, 0.42, 0.5, 0.45); g.add_color_stop_rgba(1, 0.2, 0.25, 0.3, 0)
            ctx.set_source(g); ctx.paint(); ctx.restore()
            # rim light
            _path(ctx, P[:len(P) // 2], close=False); ctx.set_source_rgba(0.24, 0.4, 0.56, 0.6); ctx.set_line_width(5); ctx.stroke()
        else:
            path(); c = hexc(PAL.CYAN); ctx.set_source_rgba(c[0], c[1], c[2], 0.10); ctx.fill()
            stroke_glow(ctx, path, PAL.CYAN, 4, glow=3, glow_alpha=0.22)
            # cartilage fibre hint lines (no bone)
            ctx.set_source_rgba(c[0], c[1], c[2], 0.25); ctx.set_line_width(1.5)
            for k in (0.25, 0.5, 0.75):
                ctx.move_to(-self.h * 0.3 * (1 - k * 0.6), -self.h * k * 0.2); ctx.line_to(-self.h * 0.05, -self.h * (0.2 + k * 0.7)); ctx.stroke()
            if self.scan is not None:
                y = -self.h * ((t * self.scan) % 1.2)
                ctx.save(); path(); ctx.clip()
                g = cairo.LinearGradient(0, y - 40, 0, y + 4)
                g.add_color_stop_rgba(0, c[0], c[1], c[2], 0); g.add_color_stop_rgba(1, c[0], c[1], c[2], 0.5)
                ctx.set_source(g); ctx.rectangle(-self.h, y - 40, self.h * 2, 44); ctx.fill()
                ctx.restore()

# ---------------------------------------------------------------- balance rig
class BalanceRig(Element):
    """Balance scale with pans that hang plumb; children placed on pans via
    left_items / right_items: lists of (Element, (dx, dy)) relative to pan centre."""
    def __init__(self, tilt=0.0, width=900, post=420, left_items=None, right_items=None, color=PAL.WHITE, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw)
        self.tilt, self.w, self.post, self.li, self.ri, self.c = tilt, width, post, left_items or [], right_items or [], color
    def draw(self, ctx, t):
        a = math.radians(ev(self.tilt, t)); w = self.w / 2
        set_col(ctx, self.c); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(8); ctx.move_to(0, 0); ctx.line_to(0, self.post); ctx.stroke()
        rrect(ctx, -130, self.post, 260, 22, 6); ctx.fill()
        ctx.move_to(-34, 6); ctx.line_to(0, -46); ctx.line_to(34, 6); ctx.close_path(); ctx.fill()
        ends = [(-w * math.cos(a), -w * math.sin(a)), (w * math.cos(a), w * math.sin(a))]
        ctx.set_line_width(8); ctx.move_to(*ends[0]); ctx.line_to(*ends[1]); ctx.stroke()
        for (ex, ey), items in zip(ends, (self.li, self.ri)):
            py = ey + 120
            ctx.set_line_width(2.5); set_col(ctx, self.c, 0.8)
            ctx.move_to(ex, ey); ctx.line_to(ex - 190, py); ctx.move_to(ex, ey); ctx.line_to(ex + 190, py); ctx.stroke()
            ctx.move_to(ex - 230, py); ctx.curve_to(ex - 150, py + 40, ex + 150, py + 40, ex + 230, py); ctx.close_path()
            set_col(ctx, self.c); ctx.fill()
            for el, (dx, dy) in items:
                ctx.save(); ctx.translate(ex + dx, py + dy); el.render(ctx, t); ctx.restore()

# ---------------------------------------------------------------- split-flap board
class SplitFlap(UI):
    """Departure-board panel: header + one row of flap cells cycling through
    words, landing on `final` at t_final. words: list of (t, text)."""
    def __init__(self, words, header="TODAY'S SPECIAL", cells=14, cell=(58, 86), **kw):
        super().__init__(**kw); self.words, self.header, self.n, self.cell = words, header, cells, cell
        self.chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ'?"
    def text_at(self, t):
        cur = ''
        for (tw, s) in self.words:
            if t >= tw: cur = s
        return cur
    def draw(self, ctx, t):
        a, s = _pop(t, 4)
        cw, chh = self.cell; gap = 6; n = self.n
        Wb = n * (cw + gap) - gap + 60; Hb = chh + 130
        ctx.save(); ctx.scale(s, s)
        rrect(ctx, -Wb / 2 + 6, -Hb / 2 + 10, Wb, Hb, 14); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        rrect(ctx, -Wb / 2, -Hb / 2, Wb, Hb, 14); ctx.set_source_rgba(0.05, 0.07, 0.08, 0.96 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.25 * a); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, self.header, -Wb / 2 + 30, -Hb / 2 + 44, 'bold', 22, PAL.ORANGE, 0.24, alpha=a)
        circle(ctx, Wb / 2 - 36, -Hb / 2 + 36, 7); set_col(ctx, PAL.RED, a * (0.5 + 0.5 * (int(t * 2) % 2))); ctx.fill()
        # determine target text and flip phase
        cur = self.text_at(t); idx = max([i for i, (tw, _) in enumerate(self.words) if t >= tw] or [0])
        t_change = self.words[idx][0] if self.words and t >= self.words[0][0] else 0
        prev = self.words[idx - 1][1] if idx > 0 else ''
        txt = cur.center(n)[:n]; ptxt = prev.center(n)[:n]
        y0 = -Hb / 2 + 70
        for i in range(n):
            x = -Wb / 2 + 30 + i * (cw + gap)
            rrect(ctx, x, y0, cw, chh, 5); set_col(ctx, '#1A1F23', a); ctx.fill()
            # flipping: each cell cycles random letters for a short staggered time
            dt = t - t_change - i * 0.025
            ch = txt[i]
            if 0 <= dt < 0.22 and (txt[i] != ' ' or ptxt[i] != ' '):
                r = rng(int(t * 30) * 31 + i); ch = self.chars[r.randrange(1, len(self.chars))]
                flip = (dt * 30) % 1
            else:
                flip = None
            draw_text(ctx, ch, x + cw / 2, y0 + chh / 2 + 18, 'xb', 50, PAL.WHITE, 0, 'center', shadow=False, alpha=a)
            ctx.move_to(x, y0 + chh / 2); ctx.line_to(x + cw, y0 + chh / 2); ctx.set_source_rgba(0, 0, 0, 0.8 * a); ctx.set_line_width(2.5); ctx.stroke()
            if flip is not None:
                hh = chh / 2 * abs(math.cos(flip * math.pi))
                ctx.rectangle(x, y0 + chh / 2 - hh, cw, hh); ctx.set_source_rgba(0.16, 0.19, 0.22, 0.9 * a); ctx.fill()
        ctx.restore()

# ---------------------------------------------------------------- pin globe
class PinGlobe(Globe):
    """Globe whose pins pop in at their own times: pins=[(lon, lat, t_pop)];
    pinned labels: labels=[(lon, lat, text, t)]. zoom K on radius via R_track."""
    def __init__(self, timed_pins=None, R_track=None, **kw):
        super().__init__(pins=[], **kw); self.tp = timed_pins or []; self.Rt = R_track
    def draw(self, ctx, t):
        if self.Rt is not None: self.R = ev(self.Rt, t)
        super().draw(ctx, t)
        R = self.R
        lon0 = math.radians(self.c0[0] - self.spin * t); lat0 = math.radians(self.c0[1])
        for (lo, la, tp) in self.tp:
            if t < tp: continue
            x, y, c = _ortho(np.radians(np.array([[lo, la]], float)), lon0, lat0, R)
            if c[0] <= 0.02: continue
            k = min(1, (t - tp) / 0.15); s = ease('back', k)
            pulse = ((t - tp) % 1.2) / 1.2
            circle(ctx, x[0], y[0], 10 + 26 * pulse); set_col(ctx, PAL.RED, 0.6 * (1 - pulse) * min(1, c[0] * 4)); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, x[0], y[0], 11 * s); set_col(ctx, PAL.RED); ctx.fill_preserve(); set_col(ctx, PAL.WHITE); ctx.set_line_width(3); ctx.stroke()

# ---------------------------------------------------------------- waveform speech bubble
class CallWave(UI):
    """Little dark panel with a scrolling call waveform + label (dialect)."""
    def __init__(self, label='DIALECT A', color=PAL.ORANGE, seed=1, w=300, h=120, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.label, self.c, self.seed, self.w, self.h = label, color, seed, w, h
    def draw(self, ctx, t):
        a, s = _pop(t, 4)
        ctx.save(); ctx.scale(s, s)
        w, h = self.w, self.h
        rrect(ctx, -w / 2, -h / 2, w, h, 12); ctx.set_source_rgba(0.03, 0.06, 0.08, 0.88 * a); ctx.fill_preserve()
        set_col(ctx, self.c, 0.9 * a); ctx.set_line_width(2.5); ctx.stroke()
        # tail
        ctx.move_to(-20, h / 2); ctx.line_to(0, h / 2 + 26); ctx.line_to(20, h / 2); ctx.close_path(); ctx.set_source_rgba(0.03, 0.06, 0.08, 0.88 * a); ctx.fill()
        r = rng(self.seed); f1, f2, f3 = r.uniform(0.04, 0.09), r.uniform(0.15, 0.3), r.uniform(0.5, 1.2)
        ctx.save(); rrect(ctx, -w / 2 + 14, -h / 2 + 10, w - 28, h - 46, 4); ctx.clip()
        xs = np.arange(-w / 2 + 14, w / 2 - 14, 3)
        for xx in xs:
            ph = xx * 0.05 - t * 9
            env = 0.5 + 0.5 * math.sin(xx * f1 + t * 3 * f3 + self.seed)
            amp = (h - 60) / 2 * env * abs(math.sin(ph * f2 * 6 + self.seed))
            ctx.move_to(xx, -12 - amp); ctx.line_to(xx, -12 + amp)
        set_col(ctx, self.c, a); ctx.set_line_width(2); ctx.stroke()
        ctx.restore()
        draw_text(ctx, self.label, 0, h / 2 - 12, 'bold', 20, PAL.WHITE, 0.22, 'center', shadow=False, alpha=a)
        ctx.restore()

# ---------------------------------------------------------------- paper street
INK = '#2A2F30'
class House(Element):
    """Ink-and-paper house; window shows a tiny orca family (drawn by `family` fn)."""
    def __init__(self, wall='#D9C9A6', roof='#A9483B', door='#4E6B7E', family_dorsal='male', seed=1, **kw):
        super().__init__(**kw); self.wall, self.roof, self.door, self.seed = wall, roof, door, seed
        self.fam = [Orca(scale=0.11, facing='right', swim=0.5, phase=0.0), Orca(scale=0.07, facing='right', dorsal='female', swim=0.6, phase=1.3)]
    def draw(self, ctx, t):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        rrect(ctx, -230, -300, 460, 300, 4); set_col(ctx, self.wall); ctx.fill_preserve(); set_col(ctx, INK); ctx.set_line_width(5); ctx.stroke()
        ctx.move_to(-270, -296); ctx.line_to(0, -470); ctx.line_to(270, -296); ctx.close_path(); set_col(ctx, self.roof); ctx.fill_preserve(); set_col(ctx, INK); ctx.stroke()
        rrect(ctx, 120, -400, 50, 90, 2); set_col(ctx, '#8C7A66'); ctx.fill_preserve(); set_col(ctx, INK); ctx.stroke()
        # chimney smoke
        for i in range(3):
            k = ((t * 0.4 + i / 3) % 1)
            circle(ctx, 145 + 20 * math.sin(k * 6), -420 - k * 120, 14 + 16 * k); ctx.set_source_rgba(0.45, 0.45, 0.42, 0.35 * (1 - k)); ctx.fill()
        rrect(ctx, 60, -170, 90, 170, 3); set_col(ctx, self.door); ctx.fill_preserve(); set_col(ctx, INK); ctx.stroke()
        circle(ctx, 130, -85, 6); set_col(ctx, PAL.ORANGE); ctx.fill()
        # window
        wx, wy, ww, wh = -190, -240, 210, 150
        rrect(ctx, wx, wy, ww, wh, 3); set_col(ctx, '#3E8C99'); ctx.fill()
        ctx.save(); rrect(ctx, wx, wy, ww, wh, 3); ctx.clip()
        ctx.save(); ctx.translate(wx + 100, wy + 80); self.fam[0].render(ctx, t); ctx.restore()
        ctx.save(); ctx.translate(wx + 150, wy + 120); self.fam[1].render(ctx, t); ctx.restore()
        ctx.restore()
        rrect(ctx, wx, wy, ww, wh, 3); set_col(ctx, INK); ctx.set_line_width(6); ctx.stroke()
        ctx.move_to(wx + ww / 2, wy); ctx.line_to(wx + ww / 2, wy + wh); ctx.set_line_width(3); ctx.stroke()

class Envelope(Element):
    """Invite card (cream, ink) with title text."""
    def __init__(self, title='DINNER INVITE', **kw):
        super().__init__(**kw); self.title = title
    def draw(self, ctx, t):
        rrect(ctx, -150, -90, 300, 180, 6); set_col(ctx, '#FBF7EC'); ctx.fill_preserve(); set_col(ctx, INK); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-150, -90); ctx.line_to(0, 10); ctx.line_to(150, -90); ctx.set_line_width(3); ctx.stroke()
        draw_text(ctx, self.title, 0, 62, 'black', 30, INK, 0.04, 'center', shadow=False)
        circle(ctx, 0, 10, 14); set_col(ctx, PAL.RED); ctx.fill()

# ---------------------------------------------------------------- beach (Punta Norte)
class Beach(Element):
    """Shingle beach rising to the right out of the water. Surface waterline wl.
    Slope from (x0, wl+140) to (W+300, wl-200)."""
    def __init__(self, wl=640, x_water=900, **kw):
        kw.setdefault('layer', 'mid'); super().__init__(**kw); self.wl, self.xw = wl, x_water
        r = rng(11); self.peb = [(r.uniform(0, 1), r.uniform(0, 1), r.uniform(3, 9)) for _ in range(160)]
    def y_at(self, x):
        # beach surface height
        x0 = self.xw - 500
        k = (x - x0) / (W + 600 - x0)
        return self.wl + 220 - k * 520
    def draw(self, ctx, t):
        x0 = self.xw - 500; xs = np.linspace(x0, W + 600, 30)
        ys = [self.y_at(x) for x in xs]
        ctx.move_to(x0, H + 300)
        for x, y in zip(xs, ys): ctx.line_to(x, y)
        ctx.line_to(W + 600, H + 300); ctx.close_path()
        g = cairo.LinearGradient(0, self.wl - 300, 0, self.wl + 300)
        g.add_color_stop_rgba(0, *hexc('#CBBE9F')); g.add_color_stop_rgba(0.5, *hexc('#A99C80')); g.add_color_stop_rgba(0.52, *hexc('#4E6E6C'))
        g.add_color_stop_rgba(1, *hexc('#1F4048'))
        ctx.set_source(g); ctx.fill_preserve(); set_col(ctx, OUT, 0.8); ctx.set_line_width(5); ctx.stroke()
        for (u, v, r) in self.peb:
            x = x0 + 60 + u * (W + 500 - x0); y = self.y_at(x) + 8 + v * 60
            if y > self.wl + 6: continue
            circle(ctx, x, y, r); ctx.set_source_rgba(0.42, 0.38, 0.32, 0.45); ctx.fill()

class WaveCrest(Element):
    """Surf wave: a hump of water with white foam curl travelling along +x.
    x track = crest x; wl = waterline; height."""
    def __init__(self, xk, wl=640, height=120, width=420, life=None, **kw):
        kw.setdefault('layer', 'mid'); super().__init__(**kw); self.xk, self.wl, self.h, self.wd = xk, wl, height, width
    def draw(self, ctx, t):
        cx = ev(self.xk, t); h = self.h; w = self.wd
        pts = [(cx - w, self.wl + 4), (cx - w * 0.5, self.wl - h * 0.35), (cx - w * 0.12, self.wl - h), (cx + w * 0.05, self.wl - h * 0.9),
               (cx + w * 0.18, self.wl - h * 0.4), (cx + w * 0.3, self.wl + 4)]
        P = catmull(pts, 8)
        _path(ctx, P, close=False); ctx.line_to(cx + w * 0.3, self.wl + 30); ctx.line_to(cx - w, self.wl + 30); ctx.close_path()
        set_col(ctx, '#3E8C99'); ctx.fill()
        _path(ctx, P[: int(len(P) * 0.75)], close=False); ctx.set_source_rgba(1, 1, 1, 0.95); ctx.set_line_width(5); ctx.stroke()
        r = rng(int(t * 12))
        for _ in range(14):
            u = r.random(); x = cx - w * 0.2 + u * w * 0.45; y = self.wl - h * (0.9 - u * 0.8) + r.uniform(-14, 14)
            circle(ctx, x, y, r.uniform(4, 11)); ctx.set_source_rgba(1, 1, 1, 0.85); ctx.fill()

# ---------------------------------------------------------------- chalk sign
class ChalkSign(Element):
    def __init__(self, text='BEACH LESSONS', **kw):
        super().__init__(**kw); self.text = text
    def draw(self, ctx, t):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for x in (-110, 110):
            ctx.move_to(x, -40); ctx.line_to(x, 120); set_col(ctx, '#6B4A2E'); ctx.set_line_width(14); ctx.stroke()
        rrect(ctx, -160, -140, 320, 120, 6); set_col(ctx, '#7A5634'); ctx.fill()
        rrect(ctx, -148, -128, 296, 96, 3); set_col(ctx, '#23312C'); ctx.fill()
        draw_text(ctx, self.text, 0, -66, 'marker', 38, '#EDEBE2', 0.02, 'center', shadow=False)
        ctx.move_to(-120, -48); ctx.line_to(120, -50); ctx.set_source_rgba(0.93, 0.92, 0.88, 0.6); ctx.set_line_width(2.5); ctx.stroke()

# ---------------------------------------------------------------- top-down floe
class TopFloe(Element):
    """Ice floe seen from above, with an optional seal blob on it."""
    def __init__(self, r=230, seed=3, seal=True, **kw):
        super().__init__(**kw); self.r, self.seal = r, seal
        rr = rng(seed); n = 11
        self.P = catmull([(math.cos(a) * r * rr.uniform(0.8, 1.1), math.sin(a) * r * rr.uniform(0.75, 1.05))
                          for a in np.linspace(0, TAU, n, endpoint=False)], 4, closed=True)
    def draw(self, ctx, t):
        _path(ctx, self.P + np.array([10, 16])); ctx.set_source_rgba(0.05, 0.25, 0.32, 0.5); ctx.fill()
        _path(ctx, self.P); set_col(ctx, '#F4FAFB'); ctx.fill_preserve(); set_col(ctx, '#9FC7D1'); ctx.set_line_width(6); ctx.stroke()
        _path(ctx, self.P * 0.7 + np.array([-20, -10])); ctx.set_source_rgba(0.85, 0.93, 0.96, 0.8); ctx.fill()
        if self.seal:
            ctx.save(); ctx.rotate(0.3 + 0.03 * math.sin(t * 2))
            ctx.save(); ctx.scale(1, 0.42); circle(ctx, 0, 0, 70); set_col(ctx, '#6E747A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke(); ctx.restore()
            circle(ctx, -72, 0, 22); set_col(ctx, '#6E747A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
            ctx.move_to(64, 0); ctx.line_to(96, -14); ctx.line_to(96, 14); ctx.close_path(); set_col(ctx, '#5A6066'); ctx.fill()
            ctx.restore()

# ---------------------------------------------------------------- reticle HUD
class Reticle(UI):
    """Targeting reticle following a path pos (world=False screen coords)."""
    def __init__(self, r=70, color=PAL.RED, locked_at=None, **kw):
        super().__init__(**kw); self.r, self.c, self.lk = r, color, locked_at
    def draw(self, ctx, t):
        locked = self.lk is not None and t >= self.lk
        r = self.r * (1 if not locked else 1 - 0.25 * ease('eo', min(1, (t - self.lk) / 0.15)))
        rot = t * 1.2 if not locked else 0
        col = PAL.RED if locked else PAL.WHITE
        ctx.save(); ctx.rotate(rot)
        for k in range(4):
            a0 = k * math.pi / 2 + 0.25
            ctx.new_sub_path(); ctx.arc(0, 0, r, a0, a0 + math.pi / 2 - 0.5)
        set_col(ctx, col); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ctx.move_to(dx * r * 0.55, dy * r * 0.55); ctx.line_to(dx * r * 1.25, dy * r * 1.25)
        set_col(ctx, col); ctx.set_line_width(3); ctx.stroke()
        if locked:
            Pill('LOCKED', 'red', size=26, pos=(0, -r - 44)).render(ctx, t - self.lk)

# ---------------------------------------------------------------- menu card + glasses
class MenuCard(Element):
    """Diner menu card: header, items; some struck through, one circled red.
    items: list of (text, strike_t or None, circle_t or None)."""
    def __init__(self, header='ANTARCTIC SEAL CAFÉ', items=None, w=520, h=560, **kw):
        super().__init__(**kw); self.header, self.items, self.w, self.h = header, items or [], w, h
    def draw(self, ctx, t):
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 10, -h / 2 + 14, w, h, 8); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 8); set_col(ctx, '#FBF6E8'); ctx.fill_preserve(); set_col(ctx, INK); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 4); set_col(ctx, PAL.RED); ctx.set_line_width(2.5); ctx.stroke()
        draw_text(ctx, self.header, 0, -h / 2 + 76, 'black', 36, INK, 0.03, 'center', shadow=False)
        ctx.move_to(-w / 2 + 50, -h / 2 + 100); ctx.line_to(w / 2 - 50, -h / 2 + 100); set_col(ctx, INK); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, 'TODAY', 0, -h / 2 + 136, 'bold', 20, PAL.RED_DARK, 0.3, 'center', shadow=False)
        y = -h / 2 + 196
        for (txt, st, ci) in self.items:
            draw_text(ctx, txt, -w / 2 + 60, y, 'xb', 32, INK, 0.02, shadow=False)
            draw_text(ctx, '. . . . .', w / 2 - 60, y, 'xb', 26, '#8A8577', 0.02, 'right', shadow=False)
            tw = measure(ctx, txt, 'xb', 32, 0.02)[0]
            if st is not None and t >= st:
                k = ease('eo', min(1, (t - st) / 0.2))
                ctx.move_to(-w / 2 + 50, y - 11); ctx.line_to(-w / 2 + 50 + (tw + 20) * k, y - 13)
                set_col(ctx, INK); ctx.set_line_width(5); ctx.stroke()
            if ci is not None and t >= ci:
                k = min(1, (t - ci) / 0.35)
                ctx.save(); ctx.translate(-w / 2 + 60 + tw / 2, y - 12); ctx.scale((tw + 70) / 2, 36)
                ctx.new_sub_path(); ctx.arc(0, 0, 1, -2.0, -2.0 + TAU * 1.08 * ease('eo', k)); ctx.restore()
                set_col(ctx, PAL.RED); ctx.set_line_width(6); ctx.stroke()
            y += 66

def draw_glasses(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for dx in (-26, 26):
        circle(ctx, dx, 0, 22); ctx.set_source_rgba(0.85, 0.95, 1, 0.25); ctx.fill_preserve()
        set_col(ctx, '#0A0A0A'); ctx.set_line_width(6); ctx.stroke()
    ctx.move_to(-6, -2); ctx.line_to(6, -2); ctx.stroke()
    ctx.move_to(48, -4); ctx.line_to(110, -14); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()

# ---------------------------------------------------------------- tooth / ruler / zip
def tooth_shape(ctx, L=200):
    """Conical orca tooth, root at y=0 up to tip at y=-L (crown) — drawn pointing up."""
    w = L * 0.24
    ctx.move_to(-w * 0.8, L * 0.25); ctx.curve_to(-w, -L * 0.2, -w * 0.6, -L * 0.75, 0, -L)
    ctx.curve_to(w * 0.35, -L * 0.7, w * 0.9, -L * 0.25, w * 0.8, L * 0.25)
    ctx.curve_to(w * 0.4, L * 0.38, -w * 0.4, L * 0.38, -w * 0.8, L * 0.25); ctx.close_path()

class Tooth(Element):
    def __init__(self, L=300, **kw):
        super().__init__(**kw); self.L = L
    def draw(self, ctx, t):
        tooth_shape(ctx, self.L)
        g = cairo.LinearGradient(-self.L * 0.25, 0, self.L * 0.25, 0)
        g.add_color_stop_rgba(0, *hexc('#D9D3C2')); g.add_color_stop_rgba(0.4, *hexc('#F7F4EA')); g.add_color_stop_rgba(1, *hexc('#C8C0AA'))
        ctx.set_source(g); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # root line (gum-line)
        ctx.move_to(-self.L * 0.2, 0); ctx.curve_to(-self.L * 0.1, 10, self.L * 0.1, 10, self.L * 0.2, 0)
        ctx.set_source_rgba(0.5, 0.45, 0.38, 0.6); ctx.set_line_width(3); ctx.stroke()

class Ruler(Element):
    """Vertical ruler, 0 at bottom (y=0), `cm` centimetres, `px_per_cm`."""
    def __init__(self, cm=12, px_per_cm=40, **kw):
        super().__init__(**kw); self.cm, self.ppc = cm, px_per_cm
    def draw(self, ctx, t):
        L = self.cm * self.ppc
        rrect(ctx, -10, -L - 30, 90, L + 60, 6); set_col(ctx, '#E8C66A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        for i in range(self.cm * 2 + 1):
            y = -i * self.ppc / 2; l = 34 if i % 2 == 0 else 18
            ctx.move_to(-10, y); ctx.line_to(-10 + l, y); set_col(ctx, OUT); ctx.set_line_width(2.5); ctx.stroke()
            if i % 2 == 0 and i > 0:
                draw_text(ctx, str(i // 2), 50, y + 8, 'xb', 20, OUT, 0, 'center', shadow=False)

class ZipJaws(Element):
    """Close-up: two rows of conical teeth (upper pointing down, lower pointing up)
    in pink gums, closing together and interlocking at t_close (dur 0.35 s).
    width in units; also a zip-fastener strip below doing the same."""
    def __init__(self, t_close=1.0, n=9, width=1300, gap_open=300, **kw):
        super().__init__(**kw); self.tc, self.n, self.w, self.go = t_close, n, width, gap_open
    def draw(self, ctx, t):
        k = ease('ei2', min(1, max(0, (t - self.tc) / 0.35)))
        g = self.go * (1 - k) + 6 * math.sin(t * 2) * (1 - k)
        n, w = self.n, self.w; step = w / n; L = step * 1.25
        # mouth interior
        ctx.rectangle(-w / 2 - 80, -g / 2 - 20, w + 160, g + 40); set_col(ctx, '#3A1217'); ctx.fill()
        for up, yb, off in ((False, -g / 2, 0.0), (True, g / 2, 0.5)):
            for i in range(n):
                x = -w / 2 + (i + 0.5 + off - 0.25) * step
                ctx.save(); ctx.translate(x, yb + (-L * 0.25 if not up else L * 0.25))
                if not up: ctx.scale(1, -1)
                ctx.scale(0.75, 1)
                tooth_shape(ctx, L); set_col(ctx, '#F4F1E8'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
                ctx.restore()
            # gums
            gy = yb - (0 if up else 0)
            if up: ctx.rectangle(-w / 2 - 80, yb + L * 0.12, w + 160, 260)
            else: ctx.rectangle(-w / 2 - 80, yb - L * 0.12 - 260, w + 160, 260)
            set_col(ctx, '#B85A62'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
            # jaw skin (black/white)
            if up: ctx.rectangle(-w / 2 - 80, yb + L * 0.12 + 50, w + 160, 400); set_col(ctx, '#EEF2F3'); ctx.fill()
            else: ctx.rectangle(-w / 2 - 80, yb - L * 0.12 - 50 - 400, w + 160, 400); set_col(ctx, '#12171C'); ctx.fill()

class ZipStrip(Element):
    """Zip fastener: two tape strips with alternating teeth; slider runs left->right
    from t0 over dur, closing the teeth behind it."""
    def __init__(self, length=900, dur=0.8, n=26, **kw):
        super().__init__(**kw); self.L, self.d, self.n = length, dur, n
    def draw(self, ctx, t):
        L, n = self.L, self.n; step = L / n
        ks = ease('eio', min(1, max(0, t / self.d)))
        sx = -L / 2 + L * ks
        for side in (-1, 1):
            for i in range(n):
                x = -L / 2 + (i + (0.5 if side > 0 else 0)) * step
                closed = x < sx
                off = 0 if closed else 34
                y = side * (8 + off)
                rrect(ctx, x - step * 0.3, y - (16 if side < 0 else 0), step * 0.6, 16, 3); set_col(ctx, '#C9CDD0'); ctx.fill()
            ctx.move_to(-L / 2 - 20, side * 30); ctx.line_to(L / 2 + 20, side * 30)
        set_col(ctx, '#2F6F80'); ctx.set_line_width(26); ctx.stroke()
        # slider
        rrect(ctx, sx - 30, -34, 60, 68, 10); set_col(ctx, '#9EA6AB'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, sx + 20, -12, 70, 24, 10); set_col(ctx, '#9EA6AB'); ctx.fill_preserve(); ctx.stroke()

# ---------------------------------------------------------------- misc
class SoundRings(Element):
    """Expanding arcs (calls) from origin toward direction (deg)."""
    def __init__(self, direction=0, color=PAL.ORANGE, period=0.9, **kw):
        super().__init__(**kw); self.d, self.c, self.p = direction, color, period
    def draw(self, ctx, t):
        for i in range(3):
            k = ((t / self.p) + i / 3) % 1
            r = 30 + 160 * k; a = math.radians(self.d)
            ctx.new_sub_path(); ctx.arc(0, 0, r, a - 0.5, a + 0.5)
            set_col(ctx, self.c, 0.8 * (1 - k)); ctx.set_line_width(5); ctx.stroke()

class SpeechBubble(Element):
    """Paper/ink speech bubble with text."""
    def __init__(self, text, size=34, tail=(-1, 1), **kw):
        super().__init__(**kw); self.text, self.size, self.tail = text, size, tail
    def draw(self, ctx, t):
        a, s = _pop(t, 4)
        ctx.save(); ctx.scale(s, s)
        w = measure(ctx, self.text, 'black', self.size, 0.02)[0] + 60; h = self.size + 50
        rrect(ctx, -w / 2, -h / 2, w, h, h / 2)
        ctx.move_to(self.tail[0] * w * 0.2, h / 2 - 4); ctx.line_to(self.tail[0] * w * 0.32, h / 2 + 40); ctx.line_to(self.tail[0] * w * 0.05, h / 2 - 4)
        set_col(ctx, '#FFFFFF', a); ctx.fill_preserve(); set_col(ctx, INK, a); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, self.text, 0, self.size * 0.36, 'black', self.size, INK, 0.02, 'center', shadow=False, alpha=a)
        ctx.restore()

class HeartX(UI):
    """Heart icon with a red X drawn over at t_x."""
    def __init__(self, r=60, t_x=0.3, **kw):
        super().__init__(**kw); self.r, self.tx = r, t_x
    def draw(self, ctx, t):
        a, s = _pop(t, 4)
        ctx.save(); ctx.scale(s, s)
        circle(ctx, 0, 0, self.r * 1.25); set_col(ctx, '#0E2A38', a); ctx.fill_preserve(); set_col(ctx, PAL.WHITE, a); ctx.set_line_width(3); ctx.stroke()
        ui_icon(ctx, 'heart', self.r * 0.7, PAL.WHITE)
        if t > self.tx:
            k = min(1, (t - self.tx) / 0.2); rr = self.r * 0.8
            ctx.move_to(-rr, -rr); ctx.line_to(-rr + 2 * rr * k, -rr + 2 * rr * k)
            if k > 0.5: ctx.move_to(rr, -rr); ctx.line_to(rr - 2 * rr * (k - 0.5) * 2, -rr + 2 * rr * (k - 0.5) * 2)
            set_col(ctx, PAL.RED); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()

def orca_nose(pos, scale, rot, facing='left'):
    """World position of an Orca's nose tip for a given pos/scale/rot."""
    nx, ny = -492.0, 19.0
    if facing == 'right': nx = -nx
    a = math.radians(rot); nx, ny = nx * scale, ny * scale
    return (pos[0] + nx * math.cos(a) - ny * math.sin(a), pos[1] + nx * math.sin(a) + ny * math.cos(a))
