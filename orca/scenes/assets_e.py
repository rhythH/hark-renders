"""Act E (chapter 5/6 YOUR MOVE) custom rigs. Only used by scenes/act_e.py."""
import math
import cairocffi as cairo
from engine.core import Element, ev, ease, hexc, mix, set_col, rrect, circle, catmull, rng, TAU, W, H, PAL, remap
from engine.text import draw_text, draw_text_reveal, measure, cap_height
from engine.ui import UI, Stamp, tick_path

FPS = 30
OUT = PAL.OUTLINE

def _k(t, d):
    return max(0.0, min(1.0, t / d)) if d > 0 else 1.0

# ---------------------------------------------------------------- YOUR OPTIONS menu
class MovesMenu(UI):
    """Numbered 'YOUR OPTIONS' card (sperm-video menu device).
    items: list of str; t_items: appear times (None = already there).
    sel: list of (t, index) keyframes; the red highlight box slides between items.
    strikes: {i: t}; stamps: {i: (text, t)} small verdict stamp right of a struck item.
    dim: (t, alpha) dims the four options; extra: (text, t) green fifth line written on."""
    def __init__(self, items, t_items=None, sel=None, strikes=None, stamps=None, dim=None, extra=None,
                 size=50, gap=104, **kw):
        kw.setdefault('pos', (960, 250))
        super().__init__(**kw)
        self.items, self.size, self.gap = items, size, gap
        self.ti = t_items or [-1] * len(items)
        self.sel = sel or []; self.strikes = strikes or {}; self.stamps = stamps or {}
        self.dim, self.extra = dim, extra
        self._st = {i: Stamp(tx, PAL.RED, 30, angle=-7, seed=i + 5) for i, (tx, _) in self.stamps.items()}

    def draw(self, ctx, t):
        size, gap = self.size, self.gap
        a0 = min(1, (t + 0.0) / 0.12) if self.ti[0] >= 0 else 1
        draw_text(ctx, 'YOUR OPTIONS', 0, 0, 'black', size * 1.1, PAL.WHITE, 0.06, 'center', alpha=a0)
        labels = [f'{i + 1}. {s.upper()}' for i, s in enumerate(self.items)]
        lw = max(measure(ctx, s, 'black', size, 0.04)[0] for s in labels)
        x0 = -lw / 2 - 60
        ch = cap_height(ctx, 'black', size)
        ys = [(i + 1) * gap + 30 for i in range(len(self.items))]
        dk = 1.0
        if self.dim and t >= self.dim[0]:
            dk = 1 - (1 - self.dim[1]) * ease('eo', _k(t - self.dim[0], 0.5))
        # highlight box (slides)
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
            ctx.set_source_rgba(0.30, 0.08, 0.08, 0.6 * a * dk); ctx.fill_preserve()
            set_col(ctx, PAL.RED, a * dk); ctx.set_line_width(4); ctx.stroke()
        for i, s in enumerate(labels):
            if t < self.ti[i]: continue
            a = min(1, (t - self.ti[i]) / 0.12) if self.ti[i] >= 0 else 1
            slide = (1 - ease('eo', _k(t - self.ti[i], 0.25))) * -40 if self.ti[i] >= 0 else 0
            st = self.strikes.get(i)
            struck = st is not None and t >= st
            col = mix(PAL.WHITE, '#B04844', 0.55) if struck else PAL.WHITE
            w = draw_text(ctx, s, x0 + slide, ys[i], 'black', size, col, 0.04, alpha=a * dk * (0.8 if struck else 1))
            if struck:
                k = ease('eo', _k(t - st, 10 / FPS))
                ym = ys[i] - ch * 0.45
                ctx.move_to(x0 - 14, ym); ctx.line_to(x0 - 14 + (w + 28) * k, ym)
                set_col(ctx, PAL.RED, dk); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            if i in self.stamps:
                tx, tst = self.stamps[i]
                if t >= tst:
                    sw = measure(ctx, tx, 'black', 30, 0.03)[0]
                    ctx.save(); ctx.translate(x0 + lw + 110 + sw / 2, ys[i] - ch / 2)
                    ctx.push_group(); self._st[i].draw(ctx, t - tst); ctx.pop_group_to_source(); ctx.paint_with_alpha(max(dk, 0.5))
                    ctx.restore()
        if self.extra and t >= self.extra[1]:
            tx, te = self.extra
            y = (len(self.items) + 1) * gap + 60
            k = _k(t - te, 0.55)
            s = f'{len(self.items) + 1}. {tx.upper()}'
            draw_text_reveal(ctx, s, x0, y, k, 'black', size, PAL.GREEN_LT, 0.04, 'left', 'wipe', True)
            if k >= 1:
                kk = ease('eo', _k(t - te - 0.55, 0.3))
                sw = measure(ctx, s, 'black', size, 0.04)[0]
                tick_path(ctx, x0 + sw + 34, y - ch * 0.45, size * 0.8, kk)
                set_col(ctx, PAL.GREEN_LT); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


class OptionCard(UI):
    """Big numbered option card: orange disc with the number + title, slides in from left."""
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


# ---------------------------------------------------------------- race bars (horizontal)
class RaceBars(UI):
    """Horizontal speed bars. rows: list of dict(label, value, vtext, color, t, rider=fn(ctx,t)).
    Bars grow 0.63 s ease-out from x=0 (pos = left end of first bar). vmax km/h -> length px."""
    def __init__(self, rows, length=1150, vmax=50, gap=190, bar_h=56, **kw):
        super().__init__(**kw); self.rows, self.L, self.vmax, self.gap, self.bh = rows, length, vmax, gap, bar_h
    def draw(self, ctx, t):
        # axis
        n = len(self.rows)
        ctx.move_to(0, -self.gap * 0.55); ctx.line_to(0, self.gap * (n - 0.45))
        set_col(ctx, PAL.WHITE, 0.7); ctx.set_line_width(3); ctx.stroke()
        for v in range(0, self.vmax + 1, 10):
            x = self.L * v / self.vmax
            ctx.move_to(x, self.gap * (n - 0.45)); ctx.line_to(x, self.gap * (n - 0.45) + 12)
            set_col(ctx, PAL.WHITE, 0.45); ctx.set_line_width(2); ctx.stroke()
            draw_text(ctx, str(v), x, self.gap * (n - 0.45) + 44, 'bold', 22, PAL.GREY, 0.1, 'center', shadow=False)
        draw_text(ctx, 'KM/H', self.L + 40, self.gap * (n - 0.45) + 44, 'bold', 22, PAL.GREY, 0.2, 'left', shadow=False)
        for i, r in enumerate(self.rows):
            if t < r['t']: continue
            lt = t - r['t']
            y = i * self.gap
            a = _k(lt, 0.1)
            draw_text(ctx, r['label'].upper(), 0, y - self.bh / 2 - 18, 'bold', 26, PAL.WHITE, 0.22, alpha=a)
            k = ease('eo', _k(lt, 0.63))
            w = max(4, self.L * r['value'] / self.vmax * k)
            rrect(ctx, 0, y - self.bh / 2, w, self.bh, 6); set_col(ctx, r['color'], a); ctx.fill()
            # shine
            rrect(ctx, 0, y - self.bh / 2, w, self.bh * 0.35, 6); ctx.set_source_rgba(1, 1, 1, 0.12 * a); ctx.fill()
            if k > 0.5:
                aa = _k(k - 0.5, 0.3)
                draw_text(ctx, r['vtext'], w + 22 + (90 if r.get('rider') else 0), y + 16, 'xb', 48, r['color'], 0.02, alpha=aa)
            if r.get('rider'):
                ctx.save(); ctx.translate(w + 50, y); r['rider'](ctx, lt); ctx.restore()


# ---------------------------------------------------------------- breath tanks
class BreathTank(UI):
    """Vertical capsule gauge. level: fn(t)->0..1. label under, colour."""
    def __init__(self, level, label, color, w=150, h=480, warn=0.2, **kw):
        super().__init__(**kw); self.level, self.label, self.c, self.w, self.h, self.warn = level, label, color, w, h, warn
    def draw(self, ctx, t):
        a, sc = _k(t, 0.1), 0.9 + 0.1 * ease('eo', _k(t, 0.15))
        ctx.save(); ctx.scale(sc, sc)
        w, h = self.w, self.h
        lv = max(0.0, min(1.0, self.level(t)))
        rrect(ctx, -w / 2, -h, w, h, w / 2); ctx.set_source_rgba(0.02, 0.05, 0.07, 0.8 * a); ctx.fill()
        col = self.c
        if lv < self.warn:
            col = PAL.RED if int(t * 6) % 2 == 0 else mix(PAL.RED, '#000000', 0.4)
        ctx.save(); rrect(ctx, -w / 2 + 10, -h + 10, w - 20, h - 20, w / 2 - 10); ctx.clip()
        fh = (h - 20) * lv
        wob = 6 * math.sin(t * 5)
        ctx.move_to(-w / 2, -10 - fh + wob); ctx.curve_to(-w / 6, -10 - fh - 8 + wob, w / 6, -10 - fh + 8 - wob, w / 2, -10 - fh - wob)
        ctx.line_to(w / 2, 0); ctx.line_to(-w / 2, 0); ctx.close_path(); set_col(ctx, col, a); ctx.fill()
        # bubbles inside
        r = rng(9)
        for j in range(7):
            bx = r.uniform(-w / 3, w / 3); ph = r.random()
            yy = -10 - ((t * 0.35 + ph) % 1.0) * fh
            circle(ctx, bx, yy, r.uniform(4, 8)); ctx.set_source_rgba(1, 1, 1, 0.35 * a); ctx.fill()
        ctx.restore()
        rrect(ctx, -w / 2, -h, w, h, w / 2); set_col(ctx, PAL.WHITE, a); ctx.set_line_width(4); ctx.stroke()
        for q in (0.25, 0.5, 0.75):
            ctx.move_to(w / 2 - 4, -h * q); ctx.line_to(w / 2 + 16, -h * q); set_col(ctx, PAL.WHITE, 0.6 * a); ctx.set_line_width(2.5); ctx.stroke()
        draw_text(ctx, self.label.upper(), 0, 54, 'bold', 28, PAL.WHITE, 0.22, 'center', alpha=a)
        ctx.restore()


class DepthRuler(UI):
    """Scrolling depth ticks at the right edge (descent motion cue, no numbers)."""
    def __init__(self, speed=160, x=1800, **kw):
        super().__init__(**kw); self.sp, self.x = speed, x
    def draw(self, ctx, t):
        off = (t * self.sp) % 60
        for j in range(-1, 20):
            y = 120 + j * 60 - off
            if y < 100 or y > 980: continue
            big = (j + int(t * self.sp // 60)) % 5 == 0
            ctx.move_to(self.x, y); ctx.line_to(self.x + (46 if big else 24), y)
            set_col(ctx, PAL.WHITE, 0.75 if big else 0.4); ctx.set_line_width(3 if big else 2); ctx.stroke()
        ctx.move_to(self.x, 100); ctx.line_to(self.x, 980); set_col(ctx, PAL.WHITE, 0.6); ctx.set_line_width(2.5); ctx.stroke()
        draw_text(ctx, 'DEPTH', self.x + 20, 80, 'bold', 22, PAL.WHITE, 0.22, 'center')
        # down arrow
        y = 1010 + 6 * math.sin(t * 6)
        ctx.move_to(self.x - 12, y - 10); ctx.line_to(self.x, y + 4); ctx.line_to(self.x + 12, y - 10)
        set_col(ctx, PAL.ORANGE); ctx.set_line_width(4); ctx.stroke()


# ---------------------------------------------------------------- top-down boat
class TopBoat(Element):
    """Top-down sailboat, bow pointing `heading` (deg, 0 = right). sails: 0..1 (1 = up, sheeted out),
    speed: wake strength 0..1 (callable ok). fight: crew wrestling the wheel (wheel spins, arms jerk)."""
    def __init__(self, heading=0.0, sails=1.0, speed=0.0, fight=0.0, crew=2, **kw):
        super().__init__(**kw); self.hd, self.sails, self.speed, self.fight, self.crew = heading, sails, speed, fight, crew
    def draw(self, ctx, t):
        sp = ev(self.speed, t); fg = ev(self.fight, t); sl = ev(self.sails, t)
        ctx.save(); ctx.rotate(math.radians(ev(self.hd, t) + 1.5 * math.sin(t * 1.4)))
        # wake
        if sp > 0.02:
            for side in (1, -1):
                for j in range(5):
                    ph = (t * 1.6 + j / 5) % 1
                    x = -150 - ph * 420; yy = side * (40 + ph * 160)
                    ctx.move_to(-150, side * 30); ctx.curve_to(-250, side * 50, x + 60, yy * 0.8, x, yy)
                    ctx.set_source_rgba(1, 1, 1, 0.5 * sp * (1 - ph)); ctx.set_line_width(5 - 3 * ph); ctx.stroke()
            for j in range(6):
                ph = (t * 2.2 + j / 6) % 1
                circle(ctx, -170 - ph * 380, 12 * math.sin(j * 3 + t * 3), 6 + ph * 10)
                ctx.set_source_rgba(1, 1, 1, 0.35 * sp * (1 - ph)); ctx.fill()
        # hull shadow
        def hull(c, dx=0, dy=0):
            c.move_to(190 + dx, 0 + dy)
            c.curve_to(120 + dx, -70 + dy, -60 + dx, -78 + dy, -170 + dx, -58 + dy)
            c.line_to(-170 + dx, 58 + dy)
            c.curve_to(-60 + dx, 78 + dy, 120 + dx, 70 + dy, 190 + dx, 0 + dy); c.close_path()
        hull(ctx, 8, 12); ctx.set_source_rgba(0, 0.08, 0.12, 0.35); ctx.fill()
        hull(ctx); set_col(ctx, '#F2F1EC'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # deck
        ctx.move_to(150, 0); ctx.curve_to(100, -48, -40, -56, -150, -42); ctx.line_to(-150, 42)
        ctx.curve_to(-40, 56, 100, 48, 150, 0); ctx.close_path(); set_col(ctx, '#C9B48E'); ctx.fill()
        for yy in range(-40, 41, 14):
            ctx.move_to(-150, yy); ctx.line_to(110 - abs(yy) * 1.2, yy); ctx.set_source_rgba(0.45, 0.35, 0.2, 0.35); ctx.set_line_width(1.5); ctx.stroke()
        # cabin
        rrect(ctx, -40, -30, 120, 60, 14); set_col(ctx, '#E9E7E0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        # cockpit + wheel
        rrect(ctx, -150, -34, 90, 68, 10); set_col(ctx, '#8C7A5C'); ctx.fill()
        wa = (t * 9 * fg + 0.6 * math.sin(t * 13) * fg)
        ctx.save(); ctx.translate(-130, 0); ctx.rotate(wa)
        circle(ctx, 0, 0, 20); set_col(ctx, '#2A2F35'); ctx.set_line_width(5); ctx.stroke()
        for k in range(4):
            a = k * math.pi / 2; ctx.move_to(0, 0); ctx.line_to(20 * math.cos(a), 20 * math.sin(a)); ctx.stroke()
        ctx.restore()
        # crew (heads from above)
        for j in range(self.crew):
            jig = 6 * fg * math.sin(t * 15 + j * 2)
            cx, cy = -100 + j * 12, (-22 if j == 0 else 22) + jig
            if fg > 0.05:
                ctx.move_to(cx, cy); ctx.line_to(-130 + 14 * math.cos(wa + j * 2), 14 * math.sin(wa + j * 2))
                set_col(ctx, '#E1A05A'); ctx.set_line_width(7); ctx.stroke()
            circle(ctx, cx, cy, 15); set_col(ctx, '#D73F3C' if j == 0 else '#F0A54A'); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, cx + 3, cy, 9); set_col(ctx, '#3A2A20'); ctx.fill()
        # mast + boom + sail
        ctx.save(); ctx.translate(90, 0)
        if sl > 0.02:
            boom = math.radians(160 + 6 * math.sin(t * 2))
            bx, by = 230 * math.cos(boom), 230 * math.sin(boom) - 60 * sl
            ctx.move_to(0, 0); ctx.curve_to(bx * 0.3, by * 0.3 - 50 * sl, bx * 0.7, by * 0.7 - 40 * sl, bx, by); ctx.line_to(0, 0)
            ctx.set_source_rgba(0.97, 0.97, 0.95, 0.95); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        else:
            ctx.move_to(0, 0); ctx.line_to(-200, 4); set_col(ctx, '#E6E3DA'); ctx.set_line_width(14); ctx.stroke()
            ctx.move_to(0, 0); ctx.line_to(-200, 4); set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()
        circle(ctx, 0, 0, 10); set_col(ctx, '#B8BDC0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        ctx.restore()


class PushArrow(Element):
    """Fat red arrow pointing +x; size(t) scales it (callable/K)."""
    def __init__(self, size=1.0, color=PAL.RED, **kw):
        super().__init__(**kw); self.size, self.c = size, color
    def draw(self, ctx, t):
        s = ev(self.size, t)
        if s <= 0.01: return
        pul = 1 + 0.06 * math.sin(t * 12)
        ctx.save(); ctx.scale(s * pul, s * pul)
        pts = [(-90, -18), (20, -18), (20, -42), (90, 0), (20, 42), (20, 18), (-90, 18)]
        ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.close_path(); set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()


class Zzz(Element):
    """Yawn / sleepy bubble: 'z' letters drifting up and fading (loop)."""
    def __init__(self, color=PAL.WHITE, **kw):
        super().__init__(**kw); self.c = color
    def draw(self, ctx, t):
        for j in range(3):
            ph = ((t * 0.7) + j / 3) % 1
            a = math.sin(ph * math.pi)
            draw_text(ctx, 'z', 30 * j + 14 * math.sin(ph * 6), -ph * 120, 'black', 34 + 16 * j, self.c, 0, alpha=a)


# ---------------------------------------------------------------- wave over the floe
class WaveWash(Element):
    """Cross-section wave: a raised hump of water travelling +x along the waterline.
    x(t) given by `front` (callable/K, world x of crest). Draws water body + foam crest."""
    def __init__(self, front, plate, height=230, length=900, color=('#3E8C99', '#1F5E6E'), **kw):
        super().__init__(**kw); self.front, self.plate, self.h, self.L, self.c = front, plate, height, length, color
    def draw(self, ctx, t):
        xf = ev(self.front, t)
        wl = self.plate.wl
        h = self.h
        pts = []
        for i in range(0, 61):
            u = i / 60  # 0 back .. 1 crest
            x = xf - self.L * (1 - u)
            y = wl - h * (math.sin(u * math.pi * 0.5) ** 2.2) * (0.6 + 0.4 * u)
            pts.append((x, y))
        # crest curl
        pts += [(xf + 50, wl - h * 0.92), (xf + 85, wl - h * 0.7), (xf + 60, wl - h * 0.55), (xf + 110, wl - h * 0.35), (xf + 170, wl + 6)]
        ctx.move_to(xf - self.L - 300, wl + 6); ctx.line_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.line_to(xf + 170, wl + 160); ctx.line_to(xf - self.L - 300, wl + 160); ctx.close_path()
        g = cairo.LinearGradient(0, wl - h, 0, wl + 120)
        g.add_color_stop_rgba(0, *hexc('#5FB2BE')); g.add_color_stop_rgba(0.6, *hexc(self.c[0])); g.add_color_stop_rgba(1, *hexc(self.c[1], 0.0))
        ctx.set_source(g); ctx.fill()
        # foam line along the top
        ctx.move_to(*pts[20])
        for p in pts[21:]: ctx.line_to(*p)
        set_col(ctx, '#FFFFFF', 0.95); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        r = rng(int(t * 10) % 7 + 1)
        for _ in range(26):
            u = r.random()
            circle(ctx, xf + 40 + 120 * u, wl - h * (0.95 - 0.8 * u) + r.uniform(-30, 30), r.uniform(4, 11))
            ctx.set_source_rgba(1, 1, 1, 0.8); ctx.fill()


# ---------------------------------------------------------------- 1972 sepia bits
class Clipping(UI):
    """Newspaper clipping on sepia: masthead year, headline, grey text bars, photo box (fn)."""
    def __init__(self, year, headline, photo=None, w=760, h=520, angle=-3, **kw):
        kw.setdefault('rot', angle); kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.year, self.head, self.photo, self.w, self.h = year, headline, photo, w, h
    def draw(self, ctx, t):
        k = ease('eo', _k(t, 0.3))
        ctx.save(); ctx.translate(0, 120 * (1 - k))
        w, h = self.w, self.h
        rrect(ctx, -w / 2 + 10, -h / 2 + 14, w, h, 3); ctx.set_source_rgba(0.2, 0.15, 0.08, 0.35); ctx.fill()
        ctx.move_to(-w / 2, -h / 2)
        r = rng(4)
        for i in range(1, 21): ctx.line_to(-w / 2 + w * i / 20, -h / 2 + r.uniform(-5, 5))
        for i in range(1, 15): ctx.line_to(w / 2 + r.uniform(-5, 5), -h / 2 + h * i / 14)
        for i in range(1, 21): ctx.line_to(w / 2 - w * i / 20, h / 2 + r.uniform(-5, 5))
        ctx.close_path(); set_col(ctx, '#F1E9D2'); ctx.fill()
        draw_text(ctx, self.year, -w / 2 + 34, -h / 2 + 62, 'black', 44, PAL.INK, 0.04, shadow=False)
        ctx.move_to(-w / 2 + 30, -h / 2 + 80); ctx.line_to(w / 2 - 30, -h / 2 + 80); set_col(ctx, PAL.INK); ctx.set_line_width(3); ctx.stroke()
        draw_text(ctx, self.head, -w / 2 + 34, -h / 2 + 140, 'black', 46, PAL.INK, 0.02, shadow=False)
        # photo
        px, py, pw, ph = -w / 2 + 34, -h / 2 + 170, w * 0.5, h - 210
        ctx.save(); ctx.rectangle(px, py, pw, ph); ctx.clip()
        set_col(ctx, '#B9AA86'); ctx.paint()
        if self.photo: ctx.translate(px, py); self.photo(ctx, t, pw, ph)
        ctx.restore()
        ctx.rectangle(px, py, pw, ph); set_col(ctx, PAL.INK, 0.8); ctx.set_line_width(2); ctx.stroke()
        # text bars
        x1 = px + pw + 26
        for j in range(9):
            ww = (w / 2 - 30 - x1) * (0.6 + 0.4 * ((j * 37) % 10) / 10)
            ctx.rectangle(x1, py + 8 + j * 34, ww, 12); ctx.set_source_rgba(0.16, 0.18, 0.18, 0.35); ctx.fill()
        ctx.restore()


def surfer_photo(ctx, t, w, h, sepia=True):
    """Little scene: surfer lying on a board, black orca head clamped near the leg."""
    sea = '#7C8F86' if sepia else '#2E7A8A'
    sky = '#D9CCAA' if sepia else '#BFD8E2'
    ctx.rectangle(0, 0, w, h * 0.42); set_col(ctx, sky); ctx.fill()
    ctx.rectangle(0, h * 0.42, w, h); set_col(ctx, sea); ctx.fill()
    wl = h * 0.5 + 4 * math.sin(t * 2)
    ctx.move_to(0, wl)
    for i in range(1, 21): ctx.line_to(w * i / 20, wl + 4 * math.sin(i * 1.3 + t * 3))
    set_col(ctx, '#F4EEDC'); ctx.set_line_width(2.5); ctx.stroke()
    cx = w * 0.45
    # board
    ctx.save(); ctx.translate(cx, wl - 4); ctx.rotate(-0.04 + 0.03 * math.sin(t * 2))
    ctx.scale(1, 0.18); circle(ctx, 0, 0, w * 0.3); ctx.restore()
    set_col(ctx, '#E8D9B0' if sepia else '#F0A54A'); ctx.fill_preserve(); set_col(ctx, '#2A2F30'); ctx.set_line_width(2); ctx.stroke()
    # surfer lying (head left)
    set_col(ctx, '#2A2F30')
    circle(ctx, cx - w * 0.2, wl - 18, 11); ctx.fill()
    ctx.move_to(cx - w * 0.19, wl - 12); ctx.line_to(cx + w * 0.1, wl - 10); ctx.set_line_width(14); ctx.stroke()
    ctx.move_to(cx + w * 0.1, wl - 10); ctx.line_to(cx + w * 0.27, wl + 2); ctx.set_line_width(10); ctx.stroke()
    # orca head on the leg
    ox, oy = cx + w * 0.3, wl + 6
    ctx.move_to(ox - 40, oy + 8); ctx.curve_to(ox - 30, oy - 26, ox + 30, oy - 32, ox + 70, oy - 6)
    ctx.line_to(ox + 80, oy + 40); ctx.line_to(ox - 40, oy + 40); ctx.close_path()
    set_col(ctx, '#15181B'); ctx.fill()
    ctx.save(); ctx.translate(ox + 22, oy - 8); ctx.scale(1, 0.45); circle(ctx, 0, 0, 12); ctx.restore()
    set_col(ctx, '#EDE8DA'); ctx.fill()
    # splash specks
    r = rng(int(t * 8) % 5 + 2)
    for _ in range(10):
        circle(ctx, ox + r.uniform(-50, 60), oy - r.uniform(0, 40), r.uniform(2, 4)); set_col(ctx, '#F4EEDC'); ctx.fill()
    if sepia:
        ctx.set_operator(cairo.OPERATOR_MULTIPLY); ctx.set_source_rgba(0.85, 0.72, 0.5, 0.5); ctx.paint(); ctx.set_operator(cairo.OPERATOR_OVER)


class Fist(Element):
    """Flat fist icon (side view, knuckles +x) with motion streaks when moving."""
    def __init__(self, color='#E7B98A', streak=0.0, **kw):
        super().__init__(**kw); self.c, self.streak = color, streak
    def draw(self, ctx, t):
        st = ev(self.streak, t)
        for j in range(4):
            if st <= 0.01: break
            y = -50 + j * 33
            ctx.move_to(-130 - 80 * st, y); ctx.line_to(-110, y); set_col(ctx, PAL.WHITE, 0.7 * st); ctx.set_line_width(5); ctx.stroke()
        # wrist / sleeve
        rrect(ctx, -150, -42, 70, 84, 10); set_col(ctx, '#2F6FA0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -95, -70, 150, 140, 40); set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        for j in range(3):
            y = -40 + j * 36
            ctx.move_to(10, y); ctx.curve_to(40, y - 4, 52, y + 8, 50, y + 22)
            set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-60, 20); ctx.curve_to(-20, 10, 10, 26, 20, 50); ctx.set_line_width(4); ctx.stroke()


class Leg(Element):
    """Flat leg (calf) on its side with a bite arc of stitches; n_stitch(t) -> count drawn (0..total)."""
    def __init__(self, n_stitch, total=100, **kw):
        super().__init__(**kw); self.n, self.total = n_stitch, total
    def draw(self, ctx, t):
        ctx.move_to(-520, -90); ctx.curve_to(-200, -130, 150, -110, 420, -70); ctx.curve_to(520, -60, 560, 40, 470, 80)
        ctx.curve_to(200, 110, -200, 120, -520, 90); ctx.close_path()
        set_col(ctx, '#E1B48A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # foot hint
        ctx.move_to(470, 80); ctx.curve_to(560, 120, 640, 120, 660, 70); ctx.curve_to(650, 20, 560, -40, 520, -60)
        set_col(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
        # bite arcs
        n = int(ev(self.n, t))
        arcs = [(-330, 280, -80, 0.5), (-310, 290, 60, -0.5)]
        per = self.total // 2
        for ai, (x0, x1, y, bend) in enumerate(arcs):
            pts = []
            for j in range(per):
                u = j / (per - 1)
                x = x0 + (x1 - x0) * u; yy = y + bend * 120 * math.sin(u * math.pi)
                pts.append((x, yy))
            ctx.move_to(*pts[0])
            for p in pts[1:]: ctx.line_to(*p)
            set_col(ctx, '#9E3B33', 0.8); ctx.set_line_width(5); ctx.stroke()
            for j, (x, yy) in enumerate(pts):
                if ai * per + j >= n: break
                ctx.move_to(x - 4, yy - 14); ctx.line_to(x + 4, yy + 14)
                set_col(ctx, '#1A1E22'); ctx.set_line_width(3.2); ctx.stroke()


def fade_from_black(dur=0.35):
    def f(ctx, t):
        if t < dur:
            ctx.set_source_rgba(0, 0, 0, 1 - t / dur); ctx.rectangle(0, 0, W, H); ctx.fill()
    return f
