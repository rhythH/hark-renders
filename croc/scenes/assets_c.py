"""Act C custom assets (bite force / death roll / stomach). Pure code, engine-only imports."""
import math
import cairocffi as cairo
from engine import *
from engine.core import set_col, circle, rrect, W, H, ease, ev
from engine.text import draw_text

TAU = math.tau


class FadeIn(Element):
    def __init__(self, dur=0.4, **kw):
        kw.setdefault('layer', 'overlay'); kw.setdefault('z', 99)
        super().__init__(**kw); self.d = dur
    def draw(self, ctx, t):
        a = 1 - ease('eo', min(1, t / self.d))
        if a > 0: ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(0, 0, W, H); ctx.fill()


def _pop(t, d=0.18):
    k = min(1, max(0, t / d)); return min(1, t / 0.08) if t > 0 else 0, ease('back', k)


# ---------------------------------------------------------------- species icons
def croc_icon(ctx, kind, w, col, alpha=1.0):
    """Profile head icon, facing left, centred, width w. kind 0 croc, 1 alligator (broad), 2 gharial (thin), 3 caiman."""
    s = w / 200.0
    ctx.save(); ctx.scale(s, s)
    snout_h = {0: 22, 1: 30, 2: 10, 3: 26}[kind]
    tip = {0: -100, 1: -92, 2: -110, 3: -90}[kind]
    ctx.move_to(tip, -snout_h * 0.4)
    ctx.curve_to(tip + 30, -snout_h, -20, -snout_h * 1.05, 10, -28)   # snout top to brow
    ctx.curve_to(18, -48, 38, -48, 46, -34)                              # eye bump
    ctx.line_to(100, -30); ctx.line_to(100, 30)
    ctx.curve_to(60, 34, 20, 26, -10, snout_h * 0.9)
    ctx.curve_to(-40, snout_h * 0.9, tip + 14, snout_h * 0.75, tip, snout_h * 0.2)
    ctx.close_path()
    set_col(ctx, col, alpha); ctx.fill_preserve()
    ctx.set_source_rgba(0, 0, 0, 0.35 * alpha); ctx.set_line_width(4); ctx.stroke()
    # mouth line + eye
    ctx.move_to(tip + 8, snout_h * 0.05); ctx.curve_to(-20, 4, 30, 8, 70, 4)
    ctx.set_source_rgba(0, 0, 0, 0.5 * alpha); ctx.set_line_width(4); ctx.stroke()
    circle(ctx, 32, -36, 6); ctx.set_source_rgba(0.05, 0.08, 0.08, alpha); ctx.fill()
    if kind == 0:   # visible teeth zigzag for true crocs
        for i in range(5):
            x = tip + 18 + i * 16
            ctx.move_to(x, 2); ctx.line_to(x + 5, 12); ctx.line_to(x + 10, 2)
        ctx.set_source_rgba(1, 1, 1, 0.8 * alpha); ctx.fill()
    ctx.restore()


class SpeciesGrid(Element):
    """23 crocodilian head icons in rows, popping row-by-row from t_in; at t_dim all but `winner` dim."""
    KINDS = [0, 1, 0, 3, 2, 0, 3, 0, 1, 0, 3, 0, 2, 0, 0, 3, 0, 0, 3, 0, 0, 3, 0]
    def __init__(self, n=23, cols=6, cell=(230, 150), t_in=0.0, stagger=0.06, winner=None, t_dim=None, **kw):
        super().__init__(**kw)
        self.n, self.cols, self.cell, self.tin, self.stg, self.win, self.tdim = n, cols, cell, t_in, stagger, winner, t_dim
    def draw(self, ctx, t):
        rows = math.ceil(self.n / self.cols)
        cw, chh = self.cell
        for i in range(self.n):
            r, c = divmod(i, self.cols)
            nrow = min(self.cols, self.n - r * self.cols)
            x = (c - (nrow - 1) / 2) * cw; y = (r - (rows - 1) / 2) * chh
            ti = self.tin + i * self.stg
            if t < ti: continue
            a, s = _pop(t - ti)
            bob = 4 * math.sin(t * 2.2 + i * 0.9)
            col = PAL.WHITE; alpha = a
            sc = s
            if self.tdim is not None and t >= self.tdim:
                k = ease('eo', min(1, (t - self.tdim) / 0.35))
                if i == self.win:
                    col = PAL.ORANGE; sc = 1 + 0.5 * k
                else:
                    alpha = a * (1 - 0.75 * k)
            ctx.save(); ctx.translate(x, y + bob); ctx.scale(sc, sc)
            if self.win == i and self.tdim is not None and t >= self.tdim:
                k = min(1, (t - self.tdim) / 0.3)
                circle(ctx, 0, 0, 95 + 6 * math.sin(t * 6)); set_col(ctx, PAL.ORANGE, 0.9 * k); ctx.set_line_width(4); ctx.stroke()
            croc_icon(ctx, self.KINDS[i % len(self.KINDS)], 170, col, alpha)
            ctx.restore()


# ---------------------------------------------------------------- bite meter (research rig)
class BiteBar(Element):
    """Padded bite-force bar from the croc's mouth to a readout box. p_tip = world point in the jaws,
    box = readout centre. value(t) = displayed reading (no unit, 'TESTING' look)."""
    def __init__(self, p_tip, box, t_bite, **kw):
        super().__init__(**kw); self.tip, self.box, self.tb = p_tip, box, t_bite
    def draw(self, ctx, t):
        tx, ty = self.tip; bx, by = self.box
        # rod
        ctx.move_to(tx - 230, ty); ctx.line_to(tx + 40, ty)
        set_col(ctx, '#B8C2C4'); ctx.set_line_width(16); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        # padded sensor (leather pads)
        rrect(ctx, tx - 30, ty - 22, 90, 44, 14); set_col(ctx, '#8A5A34'); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.45); ctx.set_line_width(3); ctx.stroke()
        # cable
        ctx.move_to(tx - 230, ty); ctx.curve_to(tx - 330, ty + 200, bx - 260, by + 180, bx - 110, by)
        set_col(ctx, '#202A2C'); ctx.set_line_width(5); ctx.stroke()
        # readout box
        rrect(ctx, bx - 120, by - 60, 240, 120, 12); set_col(ctx, '#0A1418'); ctx.fill_preserve()
        set_col(ctx, PAL.CYAN); ctx.set_line_width(3); ctx.stroke()
        k = 0 if t < self.tb else ease('eo', min(1, (t - self.tb) / 0.6))
        jitter = 0.03 * math.sin(t * 40) if t >= self.tb else 0
        # bar meter
        rrect(ctx, bx - 95, by + 14, 190, 22, 5); ctx.set_source_rgba(1, 1, 1, 0.12); ctx.fill()
        if k > 0:
            rrect(ctx, bx - 95, by + 14, 190 * min(1, k + jitter), 22, 5); set_col(ctx, PAL.RED); ctx.fill()
        txt = 'BITE!' if t >= self.tb else ('READY' if int(t * 2) % 2 == 0 else '')
        draw_text(ctx, txt, bx, by - 8, 'xb', 34, PAL.CYAN_HI if t < self.tb else PAL.RED, 0.1, 'center', shadow=False)


# ---------------------------------------------------------------- gauge
class Gauge(Element):
    """Big dial: 0..vmax over a 240-degree arc, red zone at the top end. needle = callable/K value."""
    def __init__(self, needle, vmax=18000, r=330, ticks=(0, 3000, 6000, 9000, 12000, 15000, 18000), **kw):
        super().__init__(**kw); self.nd, self.vmax, self.r, self.ticks = needle, vmax, r, ticks
    def ang(self, v):
        return math.radians(150 + 240 * v / self.vmax)
    def draw(self, ctx, t):
        r = self.r
        circle(ctx, 0, 0, r + 26); set_col(ctx, '#0E1B17'); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.85); ctx.set_line_width(5); ctx.stroke()
        # arc base + red zone
        ctx.arc(0, 0, r - 20, self.ang(0), self.ang(self.vmax)); set_col(ctx, PAL.WHITE, 0.25); ctx.set_line_width(18); ctx.stroke()
        ctx.arc(0, 0, r - 20, self.ang(13000), self.ang(self.vmax)); set_col(ctx, PAL.RED); ctx.set_line_width(18); ctx.stroke()
        for i in range(0, self.vmax + 1, 1000):
            a = self.ang(i); big = i % 3000 == 0
            r0 = r - (60 if big else 44)
            ctx.move_to(r0 * math.cos(a), r0 * math.sin(a)); ctx.line_to((r - 32) * math.cos(a), (r - 32) * math.sin(a))
            set_col(ctx, PAL.WHITE, 0.9 if big else 0.5); ctx.set_line_width(4 if big else 2); ctx.stroke()
            if big:
                rr = r - 100
                draw_text(ctx, f'{i // 1000}K', rr * math.cos(a), rr * math.sin(a) + 12, 'bold', 30, PAL.WHITE, 0.05, 'center', shadow=False, alpha=0.8)
        v = ev(self.nd, t)
        v += 120 * math.sin(t * 37) * (1 if v > 15000 else 0)  # quiver at the top
        a = self.ang(max(0, v))
        ctx.save(); ctx.rotate(a)
        ctx.move_to(-40, -10); ctx.line_to(r - 50, -2); ctx.line_to(r - 50, 2); ctx.line_to(-40, 10); ctx.close_path()
        set_col(ctx, PAL.ORANGE); ctx.fill()
        ctx.restore()
        circle(ctx, 0, 0, 26); set_col(ctx, PAL.WHITE); ctx.fill()
        circle(ctx, 0, 0, 10); set_col(ctx, '#0E1B17'); ctx.fill()


# ---------------------------------------------------------------- weight block
class WeightBlock(Element):
    """Trapezoid iron weight with a label."""
    def __init__(self, text='>1.5 TONNES', w=360, h=230, **kw):
        super().__init__(**kw); self.text, self.w, self.h = text, w, h
    def draw(self, ctx, t):
        w, h = self.w, self.h
        ctx.move_to(-w / 2, 0); ctx.line_to(w / 2, 0); ctx.line_to(w / 2 - 40, -h); ctx.line_to(-w / 2 + 40, -h); ctx.close_path()
        set_col(ctx, '#3A4245'); ctx.fill_preserve(); set_col(ctx, '#111618'); ctx.set_line_width(6); ctx.stroke()
        ctx.move_to(-w / 2 + 50, -h + 18); ctx.line_to(-w / 2 + 70, -18); set_col(ctx, '#FFFFFF', 0.12); ctx.set_line_width(10); ctx.stroke()
        # handle
        ctx.arc(0, -h, 46, math.pi, 0); set_col(ctx, '#111618'); ctx.set_line_width(14); ctx.stroke()
        draw_text(ctx, self.text, 0, -h / 2 + 18, 'black', 50, PAL.WHITE, 0.02, 'center', shadow=True)


class DownArrows(Element):
    """Pulsing downward pressure arrows."""
    def __init__(self, n=3, gap=90, **kw):
        super().__init__(**kw); self.n, self.gap = n, gap
    def draw(self, ctx, t):
        for i in range(self.n):
            x = (i - (self.n - 1) / 2) * self.gap
            y = 22 * ((t * 1.6 + i * 0.33) % 1)
            a = min(1, t / 0.2) * (1 - ((t * 1.6 + i * 0.33) % 1) * 0.6)
            ctx.move_to(x - 22, y - 30); ctx.line_to(x, y); ctx.line_to(x + 22, y - 30)
            set_col(ctx, PAL.RED, a); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


# ---------------------------------------------------------------- horizontal bar chart
class HBar(Element):
    """One horizontal bar growing from x=0 to length L at t=0 (0.7 s ease-out), with label + value text."""
    def __init__(self, length, label, value_text, color=PAL.WHITE, t_value=0.0, h=70, **kw):
        super().__init__(**kw); self.L, self.lab, self.vt, self.c, self.tv, self.h = length, label, value_text, color, t_value, h
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.7))
        draw_text(ctx, self.lab, 0, -self.h / 2 - 16, 'bold', 26, PAL.WHITE, 0.22, shadow=False, alpha=min(1, t / 0.15))
        rrect(ctx, 0, -self.h / 2, max(1, self.L * k), self.h, 6); set_col(ctx, self.c); ctx.fill()
        if t >= self.tv:
            a = min(1, (t - self.tv) / 0.12)
            draw_text(ctx, self.vt, self.L * k + 24, 18, 'xb', 56, self.c, 0.02, alpha=a)


# ---------------------------------------------------------------- muscles + tape
class MuscleBlob(Element):
    """Rounded muscle ellipse with striations; grows in at t=0; pulses with `pulse`."""
    def __init__(self, rx, ry, color=PAL.RED, angle=0, pulse=1.0, **kw):
        super().__init__(**kw); self.rx, self.ry, self.c, self.ang, self.pulse = rx, ry, color, angle, pulse
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.3))
        p = 1 + 0.05 * self.pulse * math.sin(t * 7)
        ctx.save(); ctx.rotate(math.radians(self.ang)); ctx.scale(self.rx * k * p, self.ry * k * p)
        ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        set_col(ctx, self.c, 0.88); ctx.fill_preserve(); ctx.set_source_rgba(0, 0, 0, 0.5); ctx.set_line_width(3); ctx.stroke()
        ctx.save(); ctx.rotate(math.radians(self.ang))
        for i in range(-3, 4):
            x = i * self.rx * 0.22 * k
            yy = self.ry * k * math.sqrt(max(0, 1 - (i * 0.22) ** 2)) * 0.8
            ctx.move_to(x, -yy); ctx.curve_to(x + 8, -yy / 3, x - 8, yy / 3, x, yy)
        ctx.set_source_rgba(1, 1, 1, 0.25); ctx.set_line_width(2); ctx.stroke()
        ctx.restore()


class TapeBand(Element):
    """Grey duct-tape band wrapping vertically round a snout, wipes on top->bottom over 0.3 s. h = band height."""
    def __init__(self, h=200, w=52, tilt=-8, **kw):
        kw.setdefault('rot', tilt)
        super().__init__(**kw); self.h, self.w = h, w
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.3))
        hh = self.h * k
        rrect(ctx, -self.w / 2, -self.h / 2, self.w, hh, 6); set_col(ctx, '#A9ADAA'); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.45); ctx.set_line_width(3); ctx.stroke()
        for i in range(4):
            y = -self.h / 2 + 12 + i * self.h / 4
            if y < -self.h / 2 + hh:
                ctx.move_to(-self.w / 2 + 4, y); ctx.line_to(self.w / 2 - 4, y + 6)
        ctx.set_source_rgba(1, 1, 1, 0.3); ctx.set_line_width(2); ctx.stroke()
        if k < 1:   # tape roll riding the leading edge
            circle(ctx, 0, -self.h / 2 + hh, 30); set_col(ctx, '#C9CCC9'); ctx.fill_preserve()
            ctx.set_source_rgba(0, 0, 0, 0.5); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, 0, -self.h / 2 + hh, 14); set_col(ctx, '#5A5F5C'); ctx.fill()


# ---------------------------------------------------------------- roll FX
class RollArcs(Element):
    """Curved white motion arcs circling an axis (an ellipse seen edge-on), rotating."""
    def __init__(self, rx=420, ry=170, speed=1.0, color=PAL.WHITE, alpha=0.7, n=3, **kw):
        super().__init__(**kw); self.rx, self.ry, self.sp, self.c, self.al, self.n = rx, ry, speed, color, alpha, n
    def draw(self, ctx, t):
        a0 = -t * TAU * self.sp
        fa = min(1, t / 0.2)
        for i in range(self.n):
            st = a0 + i * TAU / self.n
            ctx.save(); ctx.scale(self.rx, self.ry)
            ctx.arc(0, 0, 1, st, st + 1.3); ctx.restore()
            set_col(ctx, self.c, self.al * fa); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            # arrow head at the end
            e = st + 1.3
            ex, ey = self.rx * math.cos(e), self.ry * math.sin(e)
            dx, dy = -self.rx * math.sin(e), self.ry * math.cos(e); L = math.hypot(dx, dy) or 1
            dx, dy = dx / L, dy / L; nx, ny = -dy, dx
            ctx.move_to(ex + dx * 26, ey + dy * 26); ctx.line_to(ex + nx * 16, ey + ny * 16); ctx.line_to(ex - nx * 16, ey - ny * 16); ctx.close_path()
            set_col(ctx, self.c, self.al * fa); ctx.fill()


class Log(Element):
    """Generic log-shaped prey (abstract), length L, seen side-on across the jaws; spin = bark phase."""
    def __init__(self, L=300, r=34, spin=0.0, **kw):
        super().__init__(**kw); self.L, self.r, self.spin = L, r, spin
    def draw(self, ctx, t):
        L, r = max(2 * self.r + 1, ev(self.L, t)), self.r
        rrect(ctx, -L / 2, -r, L, 2 * r, r); set_col(ctx, '#6B4E33'); ctx.fill_preserve()
        set_col(ctx, '#1F150D'); ctx.set_line_width(5); ctx.stroke()
        ph = ev(self.spin, t)
        for i in range(5):
            y = r * math.sin(ph + i * 1.26)
            if math.cos(ph + i * 1.26) > 0:
                ctx.move_to(-L / 2 + 20, y); ctx.line_to(L / 2 - 20, y)
        set_col(ctx, '#3D2B1C'); ctx.set_line_width(4); ctx.stroke()
        ctx.save(); ctx.translate(L / 2 - r * 0.4, 0); ctx.scale(r * 0.4, r * 0.95); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        set_col(ctx, '#B08A5E'); ctx.fill()


# ---------------------------------------------------------------- basketball + calendar
class Basketball(Element):
    def __init__(self, r=60, **kw):
        super().__init__(**kw); self.r = r
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.3)); r = self.r * k
        if r <= 0: return
        ctx.save(); ctx.rotate(0.3 * math.sin(t * 1.5))
        circle(ctx, 0, 0, r); set_col(ctx, '#E07A2E'); ctx.fill_preserve(); set_col(ctx, '#2A1408'); ctx.set_line_width(max(1, r * 0.06)); ctx.stroke()
        ctx.move_to(-r, 0); ctx.line_to(r, 0); ctx.move_to(0, -r); ctx.line_to(0, r)
        ctx.stroke()
        ctx.arc(-r * 1.25, 0, r * 0.85, -0.85, 0.85); ctx.stroke()
        ctx.arc_negative(r * 1.25, 0, r * 0.85, math.pi + 0.85, math.pi - 0.85); ctx.stroke()
        ctx.restore()


class Calendar(Element):
    """Tear-off calendar card. flips = [t1, t2, ...]; shows labels[i] after flips[i-1]. Page tears upward."""
    def __init__(self, labels=('DAY 1', 'DAY 2', 'DAY 3'), flips=(1.0, 2.0), w=300, h=320, **kw):
        super().__init__(**kw); self.labels, self.flips, self.w, self.h = labels, flips, w, h
    def page(self, ctx, txt, a=1.0):
        w, h = self.w, self.h
        rrect(ctx, -w / 2, -h / 2, w, h, 14); set_col(ctx, '#F6F1E2', a); ctx.fill()
        ctx.rectangle(-w / 2, -h / 2, w, 80); set_col(ctx, PAL.RED, a); ctx.fill()
        for i in range(5):
            circle(ctx, -w / 2 + 40 + i * (w - 80) / 4, -h / 2 + 6, 9); set_col(ctx, '#2A2A2A', a); ctx.fill()
        n = txt.split(' ')
        draw_text(ctx, n[0], 0, -h / 2 + 58, 'black', 40, PAL.WHITE, 0.2, 'center', shadow=False, alpha=a)
        draw_text(ctx, n[1], 0, h / 2 - 50, 'black', 170, '#1A1410', 0.0, 'center', shadow=False, alpha=a)
    def draw(self, ctx, t):
        a, s = _pop(t)
        ctx.save(); ctx.scale(s, s)
        rrect(ctx, -self.w / 2 + 6, -self.h / 2 + 10, self.w, self.h, 14); ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.fill()
        i = sum(1 for f in self.flips if t >= f)
        self.page(ctx, self.labels[min(i, len(self.labels) - 1)], a)
        if i > 0:  # tearing page from the previous label
            dt = t - self.flips[i - 1]
            if dt < 0.35:
                k = ease('ei', dt / 0.35)
                ctx.save(); ctx.translate(40 * k, -260 * k); ctx.rotate(0.6 * k)
                self.page(ctx, self.labels[i - 1], 1 - k)
                ctx.restore()
        ctx.restore()


class RollCount(Element):
    """'1 / 2 / 3 ROLLS' counter that bumps at the given times."""
    def __init__(self, times, size=110, **kw):
        super().__init__(**kw); self.times, self.size = times, size
    def draw(self, ctx, t):
        n = sum(1 for x in self.times if t >= x)
        if n == 0: return
        dt = t - self.times[n - 1]
        s = 1 + 0.35 * max(0, 1 - dt / 0.18)
        ctx.save(); ctx.scale(s, s)
        draw_text(ctx, f'\u00D7{n}', 0, 0, 'black', self.size, PAL.ORANGE, 0.02, 'center')
        ctx.restore()
        draw_text(ctx, 'ROLLS', 0, self.size * 0.5, 'bold', 28, PAL.WHITE, 0.24, 'center')


class Lump(Element):
    """Dark submerged carcass-shape stashed under roots (abstract, no gore)."""
    def draw(self, ctx, t):
        ctx.save(); ctx.scale(150, 46); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        set_col(ctx, '#152820', 0.9); ctx.fill()
        ctx.save(); ctx.translate(120, -20); ctx.scale(60, 30); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        set_col(ctx, '#152820', 0.9); ctx.fill()


class SharkFin(Element):
    """Dorsal fin cutting the water surface (local y=0 = waterline)."""
    def __init__(self, h=70, color='#3A4A50', **kw):
        super().__init__(**kw); self.h, self.c = h, color
    def draw(self, ctx, t):
        h = self.h
        ctx.move_to(-h * 0.6, 0); ctx.curve_to(-h * 0.3, -h * 0.5, -h * 0.05, -h * 0.9, h * 0.1, -h)
        ctx.curve_to(h * 0.15, -h * 0.6, h * 0.3, -h * 0.2, h * 0.55, 0); ctx.close_path()
        set_col(ctx, self.c); ctx.fill()
        ctx.move_to(-h * 0.9, 2); ctx.line_to(h * 0.9, 2); ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(2); ctx.stroke()
