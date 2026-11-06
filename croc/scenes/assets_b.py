"""Act B (croc) custom assets: chapters 1 SIZE + 2 BITE. Pure code; engine not modified.
Some helpers (FadeIn, StrikeLabel, BalanceRig, SplitFlap, MenuCard) adapted from the approved orca episode."""
import math
import cairocffi as cairo
from engine.core import (Element, ev, hexc, mix, set_col, rrect, circle, poly, catmull, TAU, W, H, PAL, remap, ease,
                         rng, lerp)
from engine.text import draw_text, measure, cap_height, set_font
from engine.ui import UI, ChapterTitle, icon as ui_icon, _pop, Pill
from engine.chars.props import Person

OUT = PAL.OUTLINE
FPS = 30
INK = '#2A2F30'


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


class Clip(Element):
    """Render `el` clipped to x < x_cut (local coords) — half a person."""
    def __init__(self, el, x_cut, **kw):
        super().__init__(**kw); self.el, self.xc = el, x_cut
    def draw(self, ctx, t):
        ctx.save(); ctx.rectangle(-4000, -4000, 4000 + self.xc, 8000); ctx.clip(); self.el.render(ctx, t); ctx.restore()


class LyingPeople(Element):
    """n (float, e.g. 3.5) person silhouettes lying head-to-toe along +x from the origin (origin = ground,
    feet of the first at x=0). Each pops in at times[i]. height = person length in px."""
    def __init__(self, n=3.5, length=300, times=None, color='#DDE3E3', **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.n, self.L, self.c = n, length, color
        self.times = times or [0.2 * i for i in range(int(math.ceil(n)))]
    def draw(self, ctx, t):
        L = self.L; k = int(math.ceil(self.n))
        for i in range(k):
            ti = self.times[i]
            if t < ti: continue
            a = min(1, (t - ti) / 0.12); s = ease('back', min(1, (t - ti) / 0.2))
            frac = min(1.0, self.n - i)
            ctx.save(); ctx.translate(i * L, 0)
            if frac < 1:
                ctx.rectangle(-10, -400, L * frac, 800); ctx.clip()
            # lying: feet at x=0, head at x=L; body thickness ~ 0.26 L
            ctx.translate(L / 2, -L * 0.13); ctx.scale(s, s); ctx.translate(-L / 2, L * 0.13)
            ctx.translate(0, -L * 0.13); ctx.rotate(math.pi / 2)  # standing (head at -y) -> head at +x
            ctx.push_group()
            p = Person(height=L, color=self.c); p.draw(ctx, t)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
            ctx.restore()
            if frac < 1:   # dashed cut line
                x = i * L + L * frac
                ctx.move_to(x, -L * 0.36); ctx.line_to(x, L * 0.08); ctx.set_dash([10, 8]); set_col(ctx, PAL.RED)
                ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])


class PersonPile(Element):
    """14 little people stacked in a pyramid, each popping in at times[i] (local)."""
    def __init__(self, n=14, h=70, times=None, color='#DDE3E3', **kw):
        super().__init__(**kw); self.n, self.h, self.c = n, h, color
        self.times = times or [0.12 * i for i in range(n)]
        rows = [5, 4, 3, 2]; self.slots = []
        for r, cnt in enumerate(rows):
            for j in range(cnt):
                self.slots.append(((j - (cnt - 1) / 2) * h * 0.42, -r * h * 0.78))
    def draw(self, ctx, t):
        for i in range(self.n):
            if t < self.times[i]: continue
            k = min(1, (t - self.times[i]) / 0.18)
            x, y = self.slots[i]; drop = (1 - ease('eo', k)) * -120
            ctx.save(); ctx.translate(x, y + drop)
            ctx.push_group(); Person(height=self.h, color=self.c).draw(ctx, t)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, k * 2)); ctx.restore()


class ECG(UI):
    """HUD heart monitor: scrolling trace with a spike at each beat time (local), heart icon pulses."""
    def __init__(self, beats=(), w=620, h=150, label='', speed=160, **kw):
        super().__init__(**kw); self.beats, self.w, self.h, self.label, self.sp = list(beats), w, h, label, speed
    def draw(self, ctx, t):
        a, s = _pop(t)
        w, h = self.w, self.h
        rrect(ctx, 0, 0, w, h, 12); ctx.set_source_rgba(0.02, 0.05, 0.05, 0.82 * a); ctx.fill_preserve()
        set_col(ctx, '#4DB271', 0.5 * a); ctx.set_line_width(2); ctx.stroke()
        for gx in range(1, 12):
            ctx.move_to(gx * w / 12, 8); ctx.line_to(gx * w / 12, h - 8)
        set_col(ctx, '#4DB271', 0.10 * a); ctx.set_line_width(1); ctx.stroke()
        # trace: x maps to time t - (w - x)/speed
        ctx.save(); rrect(ctx, 0, 0, w, h, 12); ctx.clip()
        y0 = h * 0.6; first = True
        for xi in range(0, int(w * 0.9), 3):
            tt = t - (w * 0.9 - xi) / self.sp
            y = y0
            for b in self.beats:
                d = tt - b
                if -0.05 < d < 0.25:
                    if d < 0: y = y0 + 10 * (d + 0.05) / 0.05
                    elif d < 0.06: y = y0 + 10 - (h * 0.55 + 10) * (d / 0.06)
                    elif d < 0.13: y = y0 - h * 0.45 + (h * 0.6) * ((d - 0.06) / 0.07)
                    else: y = y0 + h * 0.15 * (1 - (d - 0.13) / 0.12)
            y += 1.2 * math.sin(xi * 0.21 + t * 3)
            if first: ctx.move_to(xi, y); first = False
            else: ctx.line_to(xi, y)
        set_col(ctx, '#7CF2A2', a); ctx.set_line_width(3.5); ctx.stroke()
        ctx.restore()
        hx = w * 0.9; hy = y0 - 4
        circle(ctx, hx, hy, 6); set_col(ctx, '#7CF2A2', a); ctx.fill()
        # heart pulse
        pulse = 0
        for b in self.beats:
            if 0 <= t - b < 0.4: pulse = 1 - (t - b) / 0.4
        ctx.save(); ctx.translate(w + 70, h / 2); sc = 1 + 0.35 * pulse; ctx.scale(sc, sc)
        ui_icon(ctx, 'heart', 40, PAL.RED); ctx.restore()
        if self.label:
            draw_text(ctx, self.label, 0, h + 56, 'xb', 50, PAL.WHITE, 0.03, alpha=a)


class JawGauge(UI):
    """Dial gauge 0..1 with green->red arc; needle value = K/float in 0..1; title under."""
    def __init__(self, value=0.0, r=170, title='BITE FORCE', **kw):
        super().__init__(**kw); self.v, self.r, self.title = value, r, title
    def draw(self, ctx, t):
        a, s = _pop(t)
        r = self.r; ctx.save(); ctx.scale(s, s)
        circle(ctx, 0, 0, r + 22); ctx.set_source_rgba(0.03, 0.08, 0.1, 0.85 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.8 * a); ctx.set_line_width(4); ctx.stroke()
        a0, a1 = math.pi * 0.8, math.pi * 2.2
        cols = ['#4DB271', '#D9C24A', PAL.ORANGE, PAL.RED]
        for i, c in enumerate(cols):
            ctx.new_sub_path(); ctx.arc(0, 0, r * 0.82, a0 + (a1 - a0) * i / 4, a0 + (a1 - a0) * (i + 1) / 4)
            set_col(ctx, c, a); ctx.set_line_width(22); ctx.stroke()
        for i in range(11):
            an = a0 + (a1 - a0) * i / 10
            ctx.move_to(math.cos(an) * r * 0.6, math.sin(an) * r * 0.6); ctx.line_to(math.cos(an) * r * 0.68, math.sin(an) * r * 0.68)
            set_col(ctx, PAL.WHITE, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
        v = float(ev(self.v, t)); v += 0.012 * math.sin(t * 40) * (v > 0.9)
        an = a0 + (a1 - a0) * max(0, min(1.02, v))
        ctx.move_to(0, 0); ctx.line_to(math.cos(an) * r * 0.78, math.sin(an) * r * 0.78)
        set_col(ctx, PAL.WHITE, a); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        circle(ctx, 0, 0, 14); set_col(ctx, PAL.RED, a); ctx.fill()
        draw_text(ctx, self.title, 0, r * 0.62, 'bold', 22, PAL.WHITE, 0.24, 'center', alpha=a)
        ctx.restore()


class Readout(UI):
    """LCD radar readout: dark box, label, big red digits text_fn(t)->str."""
    def __init__(self, text_fn, label='RADAR', w=440, h=170, color=PAL.RED, **kw):
        super().__init__(**kw); self.fn, self.label, self.w, self.h, self.c = text_fn, label, w, h, color
    def draw(self, ctx, t):
        a, s = _pop(t); w, h = self.w, self.h
        ctx.save(); ctx.scale(s, s)
        rrect(ctx, -w / 2 + 8, -h / 2 + 10, w, h, 14); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 14); ctx.set_source_rgba(0.04, 0.05, 0.06, 0.95 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.3 * a); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, self.label, -w / 2 + 24, -h / 2 + 36, 'bold', 20, PAL.ORANGE, 0.24, alpha=a)
        circle(ctx, w / 2 - 28, -h / 2 + 28, 7); set_col(ctx, PAL.RED, a * (0.4 + 0.6 * (int(t * 3) % 2))); ctx.fill()
        draw_text(ctx, self.fn(t), 0, h / 2 - 34, 'xb', 84, self.c, 0.04, 'center', alpha=a)
        ctx.restore()


class ReactionBar(UI):
    """Grey 'YOUR REACTION' bar filling from t_fill over dur; red marker 'CROC ARRIVES' at frac_arrive."""
    def __init__(self, t_fill=0.3, dur=1.6, w=900, frac_arrive=0.3, t_arrive=None, label='YOUR REACTION', **kw):
        super().__init__(**kw); self.tf, self.d, self.w, self.fa, self.ta, self.label = t_fill, dur, w, frac_arrive, t_arrive, label
    def draw(self, ctx, t):
        a, s = _pop(t); w = self.w
        draw_text(ctx, self.label, 0, -24, 'bold', 26, '#AEB4B6', 0.24, alpha=a)
        rrect(ctx, 0, 0, w, 46, 23); ctx.set_source_rgba(1, 1, 1, 0.12 * a); ctx.fill()
        k = max(0, min(1, (t - self.tf) / self.d))
        if k > 0:
            rrect(ctx, 0, 0, max(46, w * k), 46, 23); set_col(ctx, '#8E9496', a); ctx.fill()
        if self.ta is not None and t >= self.ta:
            x = w * self.fa; ka = min(1, (t - self.ta) / 0.15)
            ctx.move_to(x, -14); ctx.line_to(x, 62); set_col(ctx, PAL.RED, ka); ctx.set_line_width(6); ctx.stroke()
            draw_text(ctx, 'CROC ARRIVES', x, 104, 'xb', 30, PAL.RED, 0.06, 'center', alpha=ka)


class Bang(Element):
    """'!' speech bubble over a head, pops at t0."""
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.18))
        ctx.save(); ctx.scale(k, k)
        circle(ctx, 0, 0, 40); set_col(ctx, PAL.WHITE); ctx.fill()
        ctx.move_to(-10, 34); ctx.line_to(-24, 62); ctx.line_to(8, 38); ctx.fill()
        draw_text(ctx, '!', 0, 22, 'black', 62, PAL.RED, 0, 'center', shadow=False)
        ctx.restore()


class DashedGate(Element):
    """Vertical dashed line (speed-trap gate) with small label on top."""
    def __init__(self, h=420, label='', **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.h, self.label = h, label
    def draw(self, ctx, t):
        ctx.move_to(0, 0); ctx.line_to(0, -self.h); ctx.set_dash([18, 12], -t * 30)
        set_col(ctx, PAL.WHITE, 0.85); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
        if self.label:
            draw_text(ctx, self.label, 0, -self.h - 18, 'bold', 22, PAL.WHITE, 0.22, 'center')


class CafeMenu(Element):
    """Diner menu: header, items stamp in at their times. items: [(text, t_in, color, icon)]"""
    def __init__(self, header='TOP END CAFÉ', items=None, w=640, h=760, **kw):
        super().__init__(**kw); self.header, self.items, self.w, self.h = header, items or [], w, h
    def draw(self, ctx, t):
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 12, -h / 2 + 16, w, h, 8); ctx.set_source_rgba(0, 0, 0, 0.22); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 8); set_col(ctx, '#FBF6E8'); ctx.fill_preserve(); set_col(ctx, INK); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 4); set_col(ctx, PAL.RED); ctx.set_line_width(2.5); ctx.stroke()
        draw_text(ctx, self.header, 0, -h / 2 + 82, 'black', 46, INK, 0.03, 'center', shadow=False)
        ctx.move_to(-w / 2 + 50, -h / 2 + 108); ctx.line_to(w / 2 - 50, -h / 2 + 108); set_col(ctx, INK); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, "TODAY'S MENU", 0, -h / 2 + 146, 'bold', 20, PAL.RED_DARK, 0.3, 'center', shadow=False)
        y = -h / 2 + 222
        for (txt, ti, col, note) in self.items:
            if t >= ti:
                k = min(1, (t - ti) / (5 / FPS)); sc = 1.35 - 0.35 * ease('eo', k)
                ctx.save(); ctx.translate(-w / 2 + 64, y); ctx.scale(sc, sc)
                draw_text(ctx, txt, 0, 0, 'black', 40, col, 0.02, shadow=False, alpha=min(1, k * 2))
                ctx.restore()
                if note:
                    draw_text(ctx, note, w / 2 - 60, y, 'bold', 18, PAL.RED_DARK, 0.2, 'right', shadow=False, alpha=min(1, k * 2))
                else:
                    draw_text(ctx, '. . . . .', w / 2 - 60, y, 'xb', 26, '#8A8577', 0.02, 'right', shadow=False)
            y += 82


from engine.ui import Stopwatch as _SW


class CappedStopwatch(_SW):
    """Stopwatch whose value stops at `cap` (readout via fmt)."""
    def __init__(self, cap=60.0, **kw):
        super().__init__(**kw); self.cap = cap
    def draw(self, ctx, t):
        tc = min(t, (self.cap - self.s0) / self.rate) if self.rate else t
        super().draw(ctx, tc)
