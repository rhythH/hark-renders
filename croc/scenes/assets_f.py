"""Act F (chapter 5/6 YOUR MOVE, croc) custom rigs. Pure code; only used by scenes/act_f.py."""
import math
import cairocffi as cairo
from engine.core import Element, ev, ease, hexc, mix, set_col, rrect, circle, rng, TAU, W, H, PAL
from engine.text import draw_text, draw_text_reveal, measure, cap_height
from engine.ui import UI, Stamp, tick_path, x_path

FPS = 30
OUT = PAL.OUTLINE


def _k(t, d):
    return max(0.0, min(1.0, t / d)) if d > 0 else 1.0


def fade_from_black(dur=0.4):
    def f(ctx, t):
        if t < dur:
            ctx.set_source_rgba(0, 0, 0, 1 - t / dur); ctx.rectangle(0, 0, W, H); ctx.fill()
    return f


# ---------------------------------------------------------------- YOUR OPTIONS menu
class MovesMenu(UI):
    """Numbered 'YOUR OPTIONS' card. items: list of str; t_items appear times (None = already there).
    sel: [(t, index)] red highlight box slides between items. strikes {i: t}; ticks {i: t} (green tick
    right of the item, item stays white); stamps {i: (text, t, color)} small verdict stamp right of the item."""
    def __init__(self, items, t_items=None, sel=None, strikes=None, ticks=None, stamps=None, size=54, gap=110, **kw):
        kw.setdefault('pos', (960, 250))
        super().__init__(**kw)
        self.items, self.size, self.gap = items, size, gap
        self.ti = t_items or [-1] * len(items)
        self.sel = sel or []; self.strikes = strikes or {}; self.ticks = ticks or {}; self.stamps = stamps or {}
        self._st = {i: Stamp(v[0], v[2] if len(v) > 2 else PAL.RED, 30, angle=-7, seed=i + 5)
                    for i, v in self.stamps.items()}

    def draw(self, ctx, t):
        size, gap = self.size, self.gap
        a0 = min(1, t / 0.12) if self.ti[0] >= 0 else 1
        draw_text(ctx, 'YOUR OPTIONS', 0, 0, 'black', size * 1.1, PAL.WHITE, 0.06, 'center', alpha=a0)
        labels = [f'{i + 1}. {s.upper()}' for i, s in enumerate(self.items)]
        lw = max(measure(ctx, s, 'black', size, 0.04)[0] for s in labels)
        x0 = -lw / 2 - 60
        ch = cap_height(ctx, 'black', size)
        ys = [(i + 1) * gap + 40 for i in range(len(self.items))]
        cur = None
        for i, (ts, idx) in enumerate(self.sel):
            if t >= ts:
                cur = (ts, idx, self.sel[i - 1][1] if i > 0 else None)
        if cur is not None:
            ts, idx, prev = cur
            k = ease('eio', _k(t - ts, 0.22))
            y = ys[idx] if prev is None else ys[prev] + (ys[idx] - ys[prev]) * k
            a = k if prev is None else 1
            bx, bw = x0 - 36, lw + 72
            rrect(ctx, bx, y - ch - 24, bw, ch + 48, 10)
            ctx.set_source_rgba(0.30, 0.08, 0.08, 0.6 * a); ctx.fill_preserve()
            set_col(ctx, PAL.RED, a); ctx.set_line_width(4); ctx.stroke()
        for i, s in enumerate(labels):
            if t < self.ti[i]: continue
            a = min(1, (t - self.ti[i]) / 0.12) if self.ti[i] >= 0 else 1
            slide = (1 - ease('eo', _k(t - self.ti[i], 0.25))) * -40 if self.ti[i] >= 0 else 0
            st = self.strikes.get(i)
            struck = st is not None and t >= st
            col = mix(PAL.WHITE, '#B04844', 0.55) if struck else PAL.WHITE
            w = draw_text(ctx, s, x0 + slide, ys[i], 'black', size, col, 0.04, alpha=a * (0.8 if struck else 1))
            if struck:
                k = ease('eo', _k(t - st, 10 / FPS))
                ym = ys[i] - ch * 0.45
                ctx.move_to(x0 - 14, ym); ctx.line_to(x0 - 14 + (w + 28) * k, ym)
                set_col(ctx, PAL.RED); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            tk = self.ticks.get(i)
            if tk is not None and t >= tk:
                kk = ease('eo', _k(t - tk, 0.3))
                tick_path(ctx, x0 + w + 40, ys[i] - ch * 0.45, size * 0.8, kk)
                set_col(ctx, PAL.GREEN_LT); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            if i in self.stamps:
                tx, tst = self.stamps[i][0], self.stamps[i][1]
                if t >= tst:
                    sw = measure(ctx, tx, 'black', 30, 0.03)[0]
                    ctx.save(); ctx.translate(x0 + lw + 130 + sw / 2, ys[i] - ch / 2)
                    self._st[i].draw(ctx, t - tst)
                    ctx.restore()


class OptionCard(UI):
    """Numbered option card top-left: orange disc + title, slides in from the left."""
    def __init__(self, n, title, **kw):
        kw.setdefault('pos', (96, 96))
        super().__init__(**kw); self.n, self.title = n, title.upper()

    def draw(self, ctx, t):
        k = ease('eo', _k(t, 0.25)); a = _k(t, 0.1)
        ctx.save(); ctx.translate(-60 * (1 - k), 0)
        tw = measure(ctx, self.title, 'xb', 44, 0.04)[0]
        rrect(ctx, 0, 0, tw + 130, 84, 10); ctx.set_source_rgba(0.03, 0.05, 0.06, 0.88 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.85 * a); ctx.set_line_width(2.4); ctx.stroke()
        circle(ctx, 44, 42, 28); set_col(ctx, PAL.ORANGE, a); ctx.fill()
        draw_text(ctx, str(self.n), 44, 58, 'black', 40, '#1A1410', 0, 'center', shadow=False, alpha=a)
        draw_text(ctx, self.title, 92, 59, 'xb', 44, PAL.WHITE, 0.04, shadow=False, alpha=a)
        ctx.restore()


# ---------------------------------------------------------------- horizontal speed bars
class HBars(UI):
    """rows: dicts(label, frac (0..1 of length), lo=None (frac where a hatched range starts), text, color, t).
    Bars grow from pos to the right; label above-left, value text at the bar end."""
    def __init__(self, rows, length=1200, gap=210, bar_h=64, **kw):
        super().__init__(**kw); self.rows, self.L, self.gap, self.bh = rows, length, gap, bar_h

    def draw(self, ctx, t):
        for i, r in enumerate(self.rows):
            if t < r['t']: continue
            lt = t - r['t']; y = i * self.gap
            a = _k(lt, 0.12)
            draw_text(ctx, r['label'].upper(), 0, y - 22, 'bold', 28, PAL.WHITE, 0.22, alpha=a)
            k = ease('eo', _k(lt, 0.7))
            w = self.L * r['frac'] * k
            rrect(ctx, 0, y, max(w, 1), self.bh, 6); set_col(ctx, r['color'], a); ctx.fill()
            if r.get('lo') is not None and k > 0.95:
                x1 = self.L * r['lo']
                ctx.save(); rrect(ctx, x1, y, w - x1, self.bh, 6); ctx.clip()
                for xx in range(int(x1) - 80, int(w) + 80, 18):
                    ctx.move_to(xx, y + self.bh); ctx.line_to(xx + 40, y)
                ctx.set_source_rgba(0, 0, 0, 0.28); ctx.set_line_width(6); ctx.stroke(); ctx.restore()
            if r.get('rider'):
                ctx.save(); ctx.translate(w + 50, y + self.bh / 2); r['rider'](ctx, lt); ctx.restore()
            if r.get('text') and k > 0.6:
                draw_text(ctx, r['text'], w + 110, y + self.bh / 2 + 18, 'xb', 52, r.get('tcol', r['color']), 0.02,
                          alpha=_k(lt - 0.42, 0.15))


# ---------------------------------------------------------------- top-down riverbank
class TopBank(Element):
    """Top-down river edge: olive water on the left of x=edge (wavy), mud bank + grass to the right.
    Drawn as a big world-space element (put on layer 'mid', z=-10)."""
    def __init__(self, edge=760, seed=2, **kw):
        kw.setdefault('layer', 'mid'); kw.setdefault('z', -10)
        super().__init__(**kw); self.edge = edge
        r = rng(seed)
        self.rip = [(r.uniform(-300, edge - 60), r.uniform(-200, H + 200), r.uniform(60, 180), r.random() * TAU)
                    for _ in range(40)]
        self.tufts = [(r.uniform(edge + 330, W + 300), r.uniform(-200, H + 200), r.uniform(10, 26)) for _ in range(90)]
        self.pebbles = [(r.uniform(edge + 40, edge + 360), r.uniform(-200, H + 200), r.uniform(3, 8)) for _ in range(60)]

    def edge_x(self, y, t=0):
        return self.edge + 26 * math.sin(y * 0.006) + 12 * math.sin(y * 0.017 + 1.3) + 3 * math.sin(t * 1.2 + y * 0.01)

    def draw(self, ctx, t):
        ctx.rectangle(-400, -400, W + 800, H + 800); set_col(ctx, '#1E3A34'); ctx.fill()
        # mud
        ctx.move_to(W + 400, -400)
        for yy in range(-400, H + 401, 20): ctx.line_to(self.edge_x(yy, t), yy)
        ctx.line_to(W + 400, H + 400); ctx.close_path(); set_col(ctx, '#6B5A3E'); ctx.fill()
        # wet strip
        for yy in range(-400, H + 401, 20):
            (ctx.move_to if yy == -400 else ctx.line_to)(self.edge_x(yy, t) + 30, yy)
        ctx.set_source_rgba(0.25, 0.2, 0.13, 0.5); ctx.set_line_width(60); ctx.stroke()
        # grass zone
        ctx.rectangle(self.edge + 360, -400, W + 400, H + 800); set_col(ctx, '#55603A'); ctx.fill()
        for (x, y, s) in self.tufts:
            for d in (-1, 0, 1):
                ctx.move_to(x + d * s * 0.4, y + s * 0.5); ctx.line_to(x + d * s * 0.7, y - s * 0.6)
            ctx.set_source_rgba(0.24, 0.3, 0.16, 0.9); ctx.set_line_width(3); ctx.stroke()
        for (x, y, s) in self.pebbles:
            circle(ctx, x, y, s); ctx.set_source_rgba(0.35, 0.29, 0.2, 0.9); ctx.fill()
        # water ripples
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, y, L, ph) in self.rip:
            xx = x + 6 * math.sin(t * 0.7 + ph); yy = y + 10 * t
            ctx.move_to(xx, yy); ctx.curve_to(xx + L * .3, yy - 8, xx + L * .6, yy + 8, xx + L, yy)
            ctx.set_source_rgba(0.75, 0.88, 0.8, 0.13 + 0.06 * math.sin(t + ph)); ctx.set_line_width(2.4); ctx.stroke()


class PathDraw(Element):
    """Polyline drawn on over `dur` seconds; solid or dashed, arrowhead at the end."""
    def __init__(self, pts, color=PAL.RED, width=10, dur=1.0, dash=None, arrow=True, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.pts, self.c, self.w, self.d, self.dash, self.arrow = pts, color, width, dur, dash, arrow
        segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]; self.segs, self.total = segs, sum(segs)

    def draw(self, ctx, t):
        k = ease('eio', _k(t, self.d)); L = self.total * k
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(*self.pts[0]); acc = 0; end = self.pts[0]; ang = 0
        for (a, b), s in zip(zip(self.pts, self.pts[1:]), self.segs):
            if acc + s <= L:
                ctx.line_to(*b); end = b; acc += s; ang = math.atan2(b[1] - a[1], b[0] - a[0])
            else:
                f = (L - acc) / s if s else 0
                end = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f); ctx.line_to(*end)
                ang = math.atan2(b[1] - a[1], b[0] - a[0]); break
        if self.dash: ctx.set_dash(self.dash)
        path = ctx.copy_path()
        ctx.set_source_rgba(0, 0, 0, 0.35); ctx.set_line_width(self.w + 5); ctx.stroke()
        ctx.append_path(path); set_col(ctx, self.c); ctx.set_line_width(self.w); ctx.stroke()
        ctx.set_dash([])
        if self.arrow and L > 10:
            s = self.w * 3
            ctx.save(); ctx.translate(*end); ctx.rotate(ang)
            ctx.move_to(s * 0.6, 0); ctx.line_to(-s * 0.6, -s * 0.7); ctx.line_to(-s * 0.6, s * 0.7); ctx.close_path()
            set_col(ctx, self.c); ctx.fill(); ctx.restore()


class ZoneBand(Element):
    """Dashed band (a strip of width `w` px right of x0, full height) with a faint fill: the charge zone."""
    def __init__(self, x0, w, color=PAL.RED, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.x0, self.w, self.c = x0, w, color

    def draw(self, ctx, t):
        k = ease('eo', _k(t, 0.5))
        ww = self.w * k
        ctx.rectangle(self.x0, -400, ww, H + 800); c = hexc(self.c)
        ctx.set_source_rgba(c[0], c[1], c[2], 0.16 + 0.05 * math.sin(t * 3)); ctx.fill()
        ctx.set_dash([26, 18]); ctx.move_to(self.x0 + ww, -400); ctx.line_to(self.x0 + ww, H + 400)
        set_col(ctx, self.c); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])


class TopPerson(Element):
    """Top-down person: head disc + shoulders, arms swinging as it moves (heading in degrees, 0 = right)."""
    def __init__(self, heading=0, color='#2F6FA0', run=1.0, **kw):
        super().__init__(**kw); self.h, self.c, self.run = heading, color, run

    def draw(self, ctx, t):
        ctx.save(); ctx.rotate(math.radians(ev(self.h, t)))
        sw = math.sin(t * 14) * 14 * self.run
        for sgn in (-1, 1):
            ctx.move_to(0, sgn * 22); ctx.line_to(-sgn * sw * 0 + sw * sgn, sgn * 30)
        for sgn, d in ((-1, 1), (1, -1)):
            rrect(ctx, -8 + d * sw, sgn * 30 - 7, 22, 14, 6); set_col(ctx, '#E2B48A'); ctx.fill()
        rrect(ctx, -14, -28, 28, 56, 12); set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        circle(ctx, 2, 0, 15); set_col(ctx, '#3A2A20'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()


# ---------------------------------------------------------------- helicopter
class Helicopter(Element):
    """Rescue helicopter side silhouette facing right, spinning main rotor + tail rotor. ~420 units long."""
    def __init__(self, color='#1C2A30', accent=PAL.RED, **kw):
        super().__init__(**kw); self.c, self.acc = color, accent

    def draw(self, ctx, t):
        ctx.save(); ctx.rotate(math.radians(4 + 1.5 * math.sin(t * 1.3)))
        # tail boom
        ctx.move_to(-40, -20); ctx.line_to(-230, -36); ctx.line_to(-230, -22); ctx.line_to(-40, 8); ctx.close_path()
        set_col(ctx, self.c); ctx.fill()
        rrect(ctx, -250, -80, 26, 58, 6); set_col(ctx, self.c); ctx.fill()
        # body
        ctx.move_to(-70, -40); ctx.curve_to(-30, -78, 90, -82, 140, -40)
        ctx.curve_to(175, -10, 160, 30, 110, 36); ctx.line_to(-50, 36); ctx.curve_to(-90, 30, -100, -10, -70, -40)
        set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.rectangle(-60, -2, 190, 12); set_col(ctx, self.acc); ctx.fill()
        ctx.move_to(70, -60); ctx.curve_to(110, -62, 140, -40, 148, -22); ctx.line_to(70, -22); ctx.close_path()
        ctx.set_source_rgba(0.55, 0.78, 0.86, 0.85); ctx.fill()
        # skids
        for x in (-30, 90):
            ctx.move_to(x, 36); ctx.line_to(x - 8, 62)
        ctx.move_to(-70, 62); ctx.line_to(140, 62); ctx.curve_to(150, 62, 158, 58, 160, 52)
        set_col(ctx, self.c); ctx.set_line_width(7); ctx.stroke()
        # mast + rotor (blur disc + blade)
        ctx.rectangle(30, -96, 14, 22); set_col(ctx, self.c); ctx.fill()
        ctx.save(); ctx.translate(37, -98); ctx.scale(1, 0.07)
        circle(ctx, 0, 0, 260); ctx.set_source_rgba(0.1, 0.15, 0.18, 0.22); ctx.fill(); ctx.restore()
        ph = math.cos(t * 40)
        ctx.move_to(37 - 260 * ph, -98); ctx.line_to(37 + 260 * ph, -98)
        set_col(ctx, self.c); ctx.set_line_width(6); ctx.stroke()
        ctx.save(); ctx.translate(-237, -52); ctx.rotate(t * 30)
        ctx.move_to(-34, 0); ctx.line_to(34, 0); set_col(ctx, self.c); ctx.set_line_width(5); ctx.stroke(); ctx.restore()
        ctx.restore()


# ---------------------------------------------------------------- railing / barrier
class Railing(Element):
    """Sturdy wooden barrier (posts + 3 rails), origin = ground at its centre, `w` wide, ~150 tall."""
    def __init__(self, w=260, h=150, **kw):
        super().__init__(**kw); self.w, self.h = w, h

    def draw(self, ctx, t):
        w, h = self.w, self.h
        for yy in (-h * 0.9, -h * 0.55, -h * 0.22):
            rrect(ctx, -w / 2 - 10, yy - 9, w + 20, 18, 4); set_col(ctx, '#8B6A43'); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        for x in (-w / 2, 0, w / 2):
            rrect(ctx, x - 13, -h - 8, 26, h + 18, 4); set_col(ctx, '#6E5233'); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(3.5); ctx.stroke()


# ---------------------------------------------------------------- reticle
class Reticle(UI):
    """Orange lock-on reticle: spins in from 2x and locks; label beside it."""
    def __init__(self, r=70, label='EYES', color=PAL.ORANGE, **kw):
        kw.setdefault('world', True)
        super().__init__(**kw); self.r, self.label, self.c = r, label, color

    def draw(self, ctx, t):
        k = ease('eo', _k(t, 0.35)); a = _k(t, 0.1)
        r = self.r * (2 - k)
        ctx.save(); ctx.rotate((1 - k) * 1.6 + 0.15 * math.sin(t * 2))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for q in range(4):
            a0 = q * TAU / 4 + 0.25
            ctx.new_sub_path(); ctx.arc(0, 0, r, a0, a0 + TAU / 4 - 0.5)
        set_col(ctx, self.c, a); ctx.set_line_width(6); ctx.stroke()
        for q in range(4):
            ang = q * TAU / 4
            ctx.move_to(math.cos(ang) * (r + 18), math.sin(ang) * (r + 18))
            ctx.line_to(math.cos(ang) * (r - 16), math.sin(ang) * (r - 16))
        set_col(ctx, self.c, a); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
        if k >= 1 and int(t * 4) % 2 == 0:
            circle(ctx, 0, 0, 7); set_col(ctx, PAL.RED); ctx.fill()
        if self.label:
            draw_text(ctx, self.label, self.r + 34, -self.r * 0.5, 'black', 54, self.c, 0.06, alpha=_k(t - 0.3, 0.12))


# ---------------------------------------------------------------- night wash (layer 'back')
class NightWash(Element):
    """Dark blue-black wash over the plate (put on layer 'back' so characters stay readable)."""
    def __init__(self, alpha=0.62, **kw):
        kw.setdefault('layer', 'back'); kw.setdefault('z', -20)
        super().__init__(**kw); self.a = alpha

    def draw(self, ctx, t):
        ctx.rectangle(-600, -600, W + 1200, H + 1200); ctx.set_source_rgba(0.01, 0.03, 0.05, self.a); ctx.fill()


# ---------------------------------------------------------------- jaw-opening arrows (x-ray board)
class CurlArrow(Element):
    """Small curved arrow (arc) with a head; 'weak' look: thin, wobbling. color, r, a0..a1 radians."""
    def __init__(self, r=90, a0=-0.2, a1=0.9, color=PAL.CYAN, width=6, **kw):
        super().__init__(**kw); self.r, self.a0, self.a1, self.c, self.w = r, a0, a1, color, width

    def draw(self, ctx, t):
        k = ease('eo', _k(t, 0.4)); a1 = self.a0 + (self.a1 - self.a0) * k
        ctx.arc(0, 0, self.r, self.a0, a1); set_col(ctx, self.c); ctx.set_line_width(self.w); ctx.stroke()
        ex, ey = math.cos(a1) * self.r, math.sin(a1) * self.r
        ctx.save(); ctx.translate(ex, ey); ctx.rotate(a1 + math.pi / 2)
        s = self.w * 2.6
        ctx.move_to(s, 0); ctx.line_to(-s * 0.6, -s * 0.8); ctx.line_to(-s * 0.6, s * 0.8); ctx.close_path()
        set_col(ctx, self.c); ctx.fill(); ctx.restore()


# ---------------------------------------------------------------- sepia instruction card
class InstructionHeader(UI):
    """Ink instruction header on paper: big step text + thin rule, written on (wipe)."""
    def __init__(self, text, color=PAL.INK, size=64, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.text, self.c, self.size = text, color, size

    def draw(self, ctx, t):
        k = _k(t, 0.35)
        draw_text_reveal(ctx, self.text, 0, 0, k, 'black', self.size, self.c, 0.04, 'center', 'wipe', False)
        w = measure(ctx, self.text, 'black', self.size, 0.04)[0]
        ctx.move_to(-w / 2, 22); ctx.line_to(-w / 2 + w * ease('eo', _k(t - 0.2, 0.4)), 22)
        set_col(ctx, self.c); ctx.set_line_width(3); ctx.stroke()


class Hands(Element):
    """Two ink-outlined hands gripping (top + bottom) - for the 'hold jaws shut' diagram. Squeeze wobble."""
    def __init__(self, color='#E2B48A', **kw):
        super().__init__(**kw); self.c = color

    def draw(self, ctx, t):
        sq = 2 * math.sin(t * 9)
        for sgn in (-1, 1):
            ctx.save(); ctx.translate(0, sgn * (46 - sq)); ctx.scale(1, sgn)
            # palm
            rrect(ctx, -46, -40, 92, 44, 16); set_col(ctx, self.c); ctx.fill_preserve()
            set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
            for i in range(4):
                x = -36 + i * 24
                rrect(ctx, x - 9, -6, 18, 30, 8); set_col(ctx, self.c); ctx.fill_preserve()
                set_col(ctx, PAL.INK); ctx.set_line_width(3.5); ctx.stroke()
            # sleeve
            ctx.rectangle(-30, -110, 60, 72); set_col(ctx, '#2F6FA0'); ctx.fill_preserve()
            set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
            ctx.restore()


class SpotMap(Element):
    """Top-down strip of riverbank with visit dots: each appears with a day label, all in different spots.
    spots: [(x, y, label, t)]. Draws a dashed connector between successive dots."""
    def __init__(self, spots, color=PAL.GREEN_LT, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.spots, self.c = spots, color

    def draw(self, ctx, t):
        prev = None
        for (x, y, lab, ts) in self.spots:
            if t < ts: break
            k = ease('back', _k(t - ts, 0.25))
            if prev:
                ctx.set_dash([10, 10]); ctx.move_to(*prev); ctx.line_to(x, y)
                ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(3); ctx.stroke(); ctx.set_dash([])
            circle(ctx, x, y, 26 * k); set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
            draw_text(ctx, lab, x, y - 46, 'xb', 32, PAL.WHITE, 0.08, 'center', alpha=_k(t - ts, 0.15))
            prev = (x, y)
