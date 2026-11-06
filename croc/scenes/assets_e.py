"""Act E assets (pure code): flat maps, soldiers, book, record rosette, pie chart, credit roll, sepia wash."""
import math
import numpy as np
import cairocffi as cairo
from engine import *
from engine.core import TAU
from engine.ui import _land, _country
from engine.text import draw_text, measure

_LANDDEG = None
def _land_deg():
    global _LANDDEG
    if _LANDDEG is None:
        _LANDDEG = [np.degrees(p) for p in _land()]
    return _LANDDEG

_CDEG = {}
def _cdeg(name):
    if name not in _CDEG:
        _CDEG[name] = [np.degrees(p) for p in _country(name)]
    return _CDEG[name]

STYLES = {
    'board': dict(land='#1C4B57', edge=(0.50, 0.76, 0.80, 0.55), grat=(1, 1, 1, 0.05)),
    'sepia': dict(land='#D8C397', edge=(0.30, 0.22, 0.12, 0.85), grat=(0.30, 0.22, 0.12, 0.12)),
}

# Ramree Island approx outline (lon, lat)
RAMREE = [(93.55, 19.45), (93.75, 19.42), (93.95, 19.22), (94.05, 19.0), (93.98, 18.82), (93.85, 18.75),
          (93.72, 18.85), (93.6, 19.05), (93.52, 19.25)]


class FlatMap(Element):
    """Equirectangular map filling the frame. center=(lon,lat)|K, zoom=px per degree|K.
    hl = list of dict(name, color, t, alpha=0.85, lat_min=None, pulse=False);
    dots = [(lon,lat,t)] small red pops; island=True draws Ramree; circle=(lon,lat,r_px,t) red hand circle;
    smoke=[(lon,lat,t)] battle puffs."""
    def __init__(self, center=(110, 5), zoom=20, style='board', hl=None, dots=None, island=False, circle_=None,
                 smoke=None, dim=None, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw)
        self.c, self.zm, self.st = center, zoom, STYLES[style]
        self.hl, self.dots, self.island, self.circ, self.smoke = hl or [], dots or [], island, circle_, smoke or []
        self.dim = dim

    def xy(self, lon, lat, t):
        c = ev(self.c, t); z = ev(self.zm, t)
        return (960 + (lon - c[0]) * z, 540 - (lat - c[1]) * z)

    def _path(self, ctx, polys, t):
        c = ev(self.c, t); z = ev(self.zm, t)
        for p in polys:
            x = 960 + (p[:, 0] - c[0]) * z; y = 540 - (p[:, 1] - c[1]) * z
            if x.max() < -50 or x.min() > 1970 or y.max() < -50 or y.min() > 1130: continue
            ctx.move_to(x[0], y[0])
            for xx, yy in zip(x[1:], y[1:]): ctx.line_to(xx, yy)
            ctx.close_path()

    def draw(self, ctx, t):
        st = self.st; c = ev(self.c, t); z = ev(self.zm, t)
        # graticule every 10 deg
        ctx.set_source_rgba(*st['grat']); ctx.set_line_width(1.5)
        for lo in range(0, 200, 10):
            x = 960 + (lo - c[0]) * z
            if -10 < x < 1930: ctx.move_to(x, -100); ctx.line_to(x, 1180)
        for la in range(-60, 70, 10):
            y = 540 - (la - c[1]) * z
            if -10 < y < 1090: ctx.move_to(-100, y); ctx.line_to(2020, y)
        ctx.stroke()
        self._path(ctx, _land_deg(), t); set_col(ctx, st['land']); ctx.fill_preserve()
        ctx.set_source_rgba(*st['edge']); ctx.set_line_width(2); ctx.stroke()
        for h in self.hl:
            if t < h['t']: continue
            k = ease('eo', min(1, (t - h['t']) / 0.35))
            a = h.get('alpha', 0.85) * k
            if 'off' in h and t > h['off']:
                a *= max(0.25, 1 - (t - h['off']) / 0.4)
            if h.get('pulse'): a *= 0.85 + 0.15 * math.sin(TAU * t / 1.2)
            ctx.save()
            if h.get('lat_min') is not None:
                y = 540 - (h['lat_min'] - c[1]) * z; ctx.rectangle(-200, -200, 2400, y + 200); ctx.clip()
            self._path(ctx, _cdeg(h['name']), t); set_col(ctx, h['color'], a); ctx.fill_preserve()
            set_col(ctx, PAL.WHITE, 0.5 * a); ctx.set_line_width(2); ctx.stroke()
            ctx.restore()
        if self.island:
            pts = [self.xy(lo, la, t) for lo, la in RAMREE]
            ctx.move_to(*pts[0])
            for p in pts[1:]: ctx.line_to(*p)
            ctx.close_path(); set_col(ctx, '#C9AF7C'); ctx.fill_preserve()
            ctx.set_source_rgba(*st['edge']); ctx.set_line_width(3); ctx.stroke()
            # hatch = mangroves
            ctx.save(); ctx.move_to(*pts[0])
            for p in pts[1:]: ctx.line_to(*p)
            ctx.close_path(); ctx.clip()
            ctx.set_source_rgba(0.3, 0.35, 0.18, 0.35); ctx.set_line_width(2)
            for i in range(-40, 40):
                x0 = pts[0][0] + i * 14
                ctx.move_to(x0, pts[0][1] - 400); ctx.line_to(x0 + 400, pts[0][1] + 400)
            ctx.stroke(); ctx.restore()
        for (lo, la, td) in self.dots:
            if t < td: continue
            x, y = self.xy(lo, la, t); k = min(1, (t - td) / 0.15)
            r = 6 * (1.4 - 0.4 * k)
            pr = min(1, (t - td) / 0.6)
            if pr < 1:
                circle(ctx, x, y, 6 + 18 * pr); set_col(ctx, PAL.RED, 0.6 * (1 - pr)); ctx.set_line_width(2); ctx.stroke()
            circle(ctx, x, y, r); set_col(ctx, PAL.RED, 0.95 * k); ctx.fill()
        for (lo, la, ts) in self.smoke:
            if t < ts: continue
            x, y = self.xy(lo, la, t); lt = t - ts
            for j in range(3):
                ph = (lt * 0.6 + j / 3) % 1
                circle(ctx, x + 30 * ph * (j - 1), y - 70 * ph, 14 + 34 * ph)
                ctx.set_source_rgba(0.25, 0.2, 0.15, 0.45 * (1 - ph)); ctx.fill()
            fl = 0.5 + 0.5 * math.sin(lt * 23 + lo)
            circle(ctx, x, y, 6 + 4 * fl); set_col(ctx, PAL.ORANGE, 0.9); ctx.fill()
        if self.circ:
            lo, la, r, tc = self.circ
            if t >= tc:
                x, y = self.xy(lo, la, t); k = ease('eo', min(1, (t - tc) / 0.5))
                ctx.new_path()
                n = 60
                for i in range(int(n * 1.15 * k) + 1):
                    a = -1.2 + TAU * 1.15 * i / n
                    rr = r * (1 + 0.06 * math.sin(i * 0.37))
                    px, py = x + rr * math.cos(a) * 1.15, y + rr * math.sin(a) * 0.95
                    (ctx.line_to if i else ctx.move_to)(px, py)
                set_col(ctx, PAL.RED); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def range_dots(names, n, t0, t1, seed=3, lat_min=None, lon_range=None):
    """Random land-ish points: vertices of the given countries' polygons, pop times spread t0..t1."""
    r = np.random.default_rng(seed)
    pts = []
    for nm in names:
        for p in _cdeg(nm):
            for q in p:
                if lat_min is not None and q[1] < lat_min: continue
                if lon_range and not (lon_range[0] <= q[0] <= lon_range[1]): continue
                pts.append(q)
    pts = np.array(pts)
    idx = r.choice(len(pts), size=min(n, len(pts)), replace=False)
    ts = np.sort(r.uniform(t0, t1, len(idx)))
    out = []
    for i, tt in zip(idx, ts):
        lo, la = pts[i]
        out.append((lo + r.uniform(-0.6, 0.6), la + r.uniform(-0.6, 0.6), float(tt)))
    return out


class Panel(Element):
    """Dark translucent rounded panel (behind counters)."""
    def __init__(self, w=700, h=260, alpha=0.78, t_in=0.0, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.w, self.h, self.a, self.ti = w, h, alpha, t_in
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.2))
        w, h = self.w * (0.9 + 0.1 * k), self.h * (0.9 + 0.1 * k)
        rrect(ctx, -w / 2, -h / 2, w, h, 14); ctx.set_source_rgba(0.03, 0.07, 0.09, self.a * k); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.5 * k); ctx.set_line_width(2); ctx.stroke()


class Soldiers(Element):
    """Group of tiny WW2 soldier silhouettes. wade=True: only the part above local y=0 (waterline)
    is drawn + a ripple. Origin = group centre on the waterline/ground. walk bob animated."""
    def __init__(self, n=14, spread=(520, 90), color='#2A2418', wade=True, seed=4, size=1.0, ripple='#C9C2A2', **kw):
        super().__init__(**kw)
        r = np.random.default_rng(seed)
        self.fs = sorted([(r.uniform(-0.5, 0.5) * spread[0], r.uniform(-0.5, 0.5) * spread[1], r.uniform(0, TAU),
                           r.uniform(0.85, 1.1)) for _ in range(n)], key=lambda f: f[1])
        self.col, self.wade, self.size, self.rip = color, wade, size, ripple

    def draw(self, ctx, t):
        for (fx, fy, ph, s) in self.fs:
            s *= self.size * (1 + fy / 400)
            ctx.save(); ctx.translate(fx, fy)
            if self.wade:
                ctx.save(); ctx.rectangle(-60 * s, -200 * s, 120 * s, 200 * s - 2 + 30 * s * 0); ctx.clip()
                ctx.translate(0, 34 * s)    # sunk to the chest
            bob = 3 * s * abs(math.sin(t * 4 + ph))
            ctx.translate(0, -bob)
            set_col(ctx, self.col)
            sw = math.sin(t * 4 + ph)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(9 * s)
            # legs
            ctx.move_to(0, -48 * s); ctx.line_to(-10 * s * sw, 0); ctx.move_to(0, -48 * s); ctx.line_to(10 * s * sw, 0); ctx.stroke()
            # torso
            rrect(ctx, -10 * s, -92 * s, 20 * s, 48 * s, 6 * s); ctx.fill()
            # rifle over shoulder
            ctx.set_line_width(4 * s); ctx.move_to(-6 * s, -70 * s); ctx.line_to(16 * s, -118 * s); ctx.stroke()
            # arm
            ctx.set_line_width(7 * s); ctx.move_to(0, -86 * s); ctx.line_to(8 * s, -62 * s + 4 * s * sw); ctx.stroke()
            # head + helmet
            circle(ctx, 0, -102 * s, 9 * s); ctx.fill()
            ctx.arc(0, -104 * s, 13 * s, math.pi, TAU); ctx.close_path(); ctx.fill()
            if self.wade:
                ctx.restore()
                k = (t * 0.8 + ph) % 1
                ctx.save(); ctx.scale(1, 0.25)
                circle(ctx, 0, 0, (16 + 30 * k) * s); set_col(ctx, self.rip, 0.5 * (1 - k)); ctx.set_line_width(3 / 0.25 * 0.5); ctx.stroke()
                ctx.restore()
            ctx.restore()


class Book(Element):
    """Old open book on paper. Scribble lines; the number '20' sits on the right page and gets a
    red hand circle at t_circle. Slides up in 0.4 s."""
    def __init__(self, t_circle=1.0, title='FIELD NOTES', **kw):
        super().__init__(**kw); self.tc, self.title = t_circle, title
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.4))
        ctx.save(); ctx.translate(0, 300 * (1 - k))
        Wp, Hp = 520, 640
        # shadow + cover
        rrect(ctx, -Wp - 30, -Hp / 2 - 10, 2 * Wp + 60, Hp + 40, 10); ctx.set_source_rgba(0.2, 0.12, 0.05, 0.35); ctx.fill()
        rrect(ctx, -Wp - 22, -Hp / 2 - 18, 2 * Wp + 44, Hp + 36, 10); set_col(ctx, '#5B2E22'); ctx.fill()
        for side in (-1, 1):
            ctx.save(); ctx.scale(side, 1)
            ctx.move_to(0, -Hp / 2); ctx.curve_to(Wp * 0.3, -Hp / 2 - 20, Wp * 0.7, -Hp / 2 - 10, Wp, -Hp / 2)
            ctx.line_to(Wp, Hp / 2); ctx.curve_to(Wp * 0.7, Hp / 2 - 10, Wp * 0.3, Hp / 2 - 18, 0, Hp / 2); ctx.close_path()
            g = cairo.LinearGradient(0, 0, Wp, 0); g.add_color_stop_rgb(0, *hexc('#CDBB92')[:3]); g.add_color_stop_rgb(0.12, *hexc('#EFE4C8')[:3])
            g.add_color_stop_rgb(1, *hexc('#E6D8B6')[:3]); ctx.set_source(g); ctx.fill()
            ctx.restore()
        r = np.random.default_rng(2)
        ink = (0.25, 0.2, 0.14)
        # left page: title + lines
        draw_text(ctx, self.title, -Wp / 2, -Hp / 2 + 80, 'black', 26, '#3A2A1C', 0.12, 'center', shadow=False)
        ctx.set_line_width(3)
        for side, y0 in ((-1, -Hp / 2 + 130), (1, -Hp / 2 + 70)):
            for i in range(13):
                y = y0 + i * 40
                if y > Hp / 2 - 50: break
                x0 = 50 if side > 0 else -Wp + 50
                L = (Wp - 110) * (0.6 + 0.4 * r.random())
                if side > 0 and i == 6:   # line holding the number
                    ctx.move_to(x0, y);
                    for j in range(12): ctx.line_to(x0 + j * 14, y + 4 * math.sin(j * 1.7))
                    ctx.set_source_rgba(*ink, 0.55); ctx.stroke()
                    draw_text(ctx, '20', x0 + 230, y + 14, 'marker', 64, '#2A1E14', 0, 'center', shadow=False)
                    ctx.move_to(x0 + 300, y)
                    for j in range(10): ctx.line_to(x0 + 300 + j * 13, y + 4 * math.sin(j * 1.3))
                    ctx.set_source_rgba(*ink, 0.55); ctx.stroke()
                    continue
                ctx.move_to(x0, y); n = int(L / 13)
                for j in range(n): ctx.line_to(x0 + j * 13, y + 4 * math.sin(j * 1.7 + i))
                ctx.set_source_rgba(*ink, 0.5); ctx.stroke()
        if t >= self.tc:
            kc = ease('eo', min(1, (t - self.tc) / 0.45))
            cx, cy = 50 + 230, -Hp / 2 + 70 + 6 * 40 - 8
            ctx.new_path()
            for i in range(int(70 * kc) + 1):
                a = -2.0 + TAU * 1.15 * i / 60
                (ctx.line_to if i else ctx.move_to)(cx + 70 * math.cos(a), cy + 48 * math.sin(a) + i * 0.15)
            set_col(ctx, PAL.RED); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()


class RecordBook(Element):
    """Gold 'BOOK OF RECORDS' cover sliding in from the left."""
    def __init__(self, **kw):
        super().__init__(**kw)
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.4))
        ctx.save(); ctx.translate(-700 * (1 - k), 0); ctx.rotate(math.radians(-4))
        w, h = 470, 620
        rrect(ctx, -w / 2 + 14, -h / 2 + 18, w, h, 12); ctx.set_source_rgba(0.2, 0.12, 0.05, 0.35); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 12); set_col(ctx, '#1F3E6E'); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, 40, h, 8); set_col(ctx, '#142B4E'); ctx.fill()
        rrect(ctx, -w / 2 + 70, -h / 2 + 50, w - 120, h - 100, 8); set_col(ctx, '#E1B54A'); ctx.set_line_width(5); ctx.stroke()
        draw_text(ctx, 'BOOK', 20, -150, 'black', 64, '#E1B54A', 0.06, 'center', shadow=False)
        draw_text(ctx, 'OF', 20, -95, 'black', 36, '#E1B54A', 0.2, 'center', shadow=False)
        draw_text(ctx, 'RECORDS', 20, -30, 'black', 60, '#E1B54A', 0.04, 'center', shadow=False)
        ctx.save(); ctx.translate(20, 120); ctx.scale(0.9, 0.9)
        # croc emblem: simple line croc
        set_col(ctx, '#E1B54A'); ctx.set_line_width(6); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(-130, 0); ctx.curve_to(-60, -40, 60, -40, 140, 10); ctx.line_to(60, 20); ctx.curve_to(0, 30, -80, 25, -130, 0)
        ctx.stroke()
        for x in (-60, 0, 60): ctx.move_to(x, 22); ctx.line_to(x - 8, 50)
        ctx.stroke()
        ctx.restore()
        ctx.restore()


class Rosette(Element):
    """Gold award rosette with two tails + banner text lines. strike=(line_index, t) draws a red
    strike through one line."""
    def __init__(self, lines=('WORST ANIMAL', 'ATTACK EVER', 'RECORDED'), strike=None, **kw):
        super().__init__(**kw); self.lines, self.strike = lines, strike
    def draw(self, ctx, t):
        R = 150
        spin = 0.15 * t
        # tails
        for s in (-1, 1):
            ctx.move_to(s * 30, 60); ctx.line_to(s * 110, 330); ctx.line_to(s * 70, 300); ctx.line_to(s * 40, 340); ctx.line_to(s * -30 + s * 60, 70)
            ctx.close_path(); set_col(ctx, '#B8322F' if s < 0 else '#C9403A'); ctx.fill()
        # scalloped disc
        ctx.new_path()
        for i in range(73):
            a = TAU * i / 72 + spin
            rr = R * (1 + 0.07 * (1 if i % 2 else -1))
            (ctx.line_to if i else ctx.move_to)(rr * math.cos(a), rr * math.sin(a))
        ctx.close_path(); set_col(ctx, '#C8962E'); ctx.fill()
        circle(ctx, 0, 0, R * 0.82); set_col(ctx, '#E9C35A'); ctx.fill()
        circle(ctx, 0, 0, R * 0.74); set_col(ctx, '#B07E22'); ctx.set_line_width(3); ctx.stroke()
        # glint
        g = (t * 0.5) % 1.6
        if g < 1:
            ctx.save(); circle(ctx, 0, 0, R * 0.82); ctx.clip()
            x = -R + 2 * R * g
            ctx.move_to(x - 30, -R); ctx.line_to(x + 10, -R); ctx.line_to(x + 60, R); ctx.line_to(x + 20, R); ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 0.35); ctx.fill(); ctx.restore()
        draw_text(ctx, '#1', 0, 30, 'black', 96, '#6E4A12', 0, 'center', shadow=False)
        # banner
        bw, bh = 760, 64 * len(self.lines) + 30
        y0 = R + 30
        rrect(ctx, -bw / 2, y0, bw, bh, 8); set_col(ctx, '#2A2F30'); ctx.fill()
        for i, ln in enumerate(self.lines):
            y = y0 + 70 + i * 64
            w = draw_text(ctx, ln, 0, y, 'black', 54, '#E9C35A', 0.04, 'center', shadow=False)
            if self.strike and i in self.strike[0] and t >= self.strike[1] + 0.2 * self.strike[0].index(i):
                k = ease('eo', min(1, (t - self.strike[1] - 0.2 * self.strike[0].index(i)) / 0.3))
                tw = measure(ctx, ln, 'black', 54, 0.04)[0]
                ctx.move_to(-tw / 2 - 20, y - 20); ctx.line_to(-tw / 2 - 20 + (tw + 40) * k, y - 18)
                set_col(ctx, PAL.RED); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


class Pie(Element):
    """Pie chart drawing on: slices=[(label, frac, color, t_on)]. Labels pop outside with leaders."""
    def __init__(self, slices, R=300, start=-90, label_size=34, **kw):
        super().__init__(**kw); self.sl, self.R, self.a0, self.ls = slices, R, start, label_size
    def draw(self, ctx, t):
        R = self.R; a = math.radians(self.a0 + 4 * t)
        circle(ctx, 0, 0, R + 8); ctx.set_source_rgba(1, 1, 1, 0.15); ctx.set_line_width(2); ctx.stroke()
        for (lab, fr, col, ton) in self.sl:
            span = TAU * fr
            if t >= ton:
                k = ease('eo', min(1, (t - ton) / 0.35))
                pop = 22 * (1 - k) + (14 if col == PAL.RED else 0)
                mid = a + span / 2
                ctx.save(); ctx.translate(pop * math.cos(mid), pop * math.sin(mid))
                ctx.move_to(0, 0); ctx.arc(0, 0, R, a, a + span * k); ctx.close_path()
                set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, PAL.BOARD if hasattr(PAL, 'BOARD') else '#0B2530'); ctx.set_line_width(5); ctx.stroke()
                ctx.restore()
                # label
                lx, ly = (R + 60) * math.cos(mid), (R + 60) * math.sin(mid)
                ex, ey = (R + 10) * math.cos(mid), (R + 10) * math.sin(mid)
                ctx.move_to(ex, ey); ctx.line_to(lx, ly); set_col(ctx, PAL.WHITE, k); ctx.set_line_width(2.5); ctx.stroke()
                al = 'left' if math.cos(mid) >= 0 else 'right'
                ox = 14 if al == 'left' else -14
                draw_text(ctx, lab, lx + ox, ly + self.ls * 0.35, 'xb', self.ls, PAL.RED if col == PAL.RED else PAL.WHITE, 0.04, al, alpha=k)
            a += span


class SpeechBubble(Element):
    """Speech bubble with animated '…' dots (no invented quote). tail toward (+x,+y)."""
    def __init__(self, w=150, h=90, tail=(-1, 1), **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.w, self.h, self.tail = w, h, tail
    def draw(self, ctx, t):
        k = ease('back', min(1, t / 0.2))
        ctx.save(); ctx.scale(k, k)
        w, h = self.w, self.h
        rrect(ctx, -w / 2, -h / 2, w, h, 22); set_col(ctx, PAL.WHITE); ctx.fill()
        tx = self.tail[0]
        ctx.move_to(tx * 20, h / 2 - 4); ctx.line_to(tx * 50, h / 2 + 34); ctx.line_to(tx * -10, h / 2 - 4); ctx.close_path(); ctx.fill()
        for i in range(3):
            ph = (t * 2.2 - i * 0.25) % 1
            dy = -8 * max(0, math.sin(ph * math.pi)) if ph < 0.5 else 0
            circle(ctx, -32 + 32 * i, dy, 9); set_col(ctx, '#2A2F30'); ctx.fill()
        ctx.restore()


class CreditRoll(Element):
    """Movie credit roll: lines scroll upward at speed px/s. lines=[(text, size, color)]."""
    def __init__(self, lines, speed=60, gap=1.0, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.lines, self.sp, self.gap = lines, speed, gap
    def draw(self, ctx, t):
        y = -self.sp * t
        for (txt, size, col) in self.lines:
            y += size * 1.25 * self.gap
            if txt:
                draw_text(ctx, txt, 0, y, 'black' if size > 60 else 'bold', size, col, 0.06 if size > 60 else 0.24, 'center')


def sepia_wash(strength=0.75, grain=True, seed=1):
    """post fn: colour-blend everything to sepia + flicker grain (screen space)."""
    r = np.random.default_rng(seed)
    pts = r.uniform(0, 1, (400, 3))
    def f(ctx, t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_HSL_COLOR)
        ctx.set_source_rgba(0.62, 0.48, 0.28, strength); ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        if grain:
            fr = int(t * 30)
            for i in range(140):
                u, v, s = pts[(i * 7 + fr * 13) % 400]
                circle(ctx, u * 1920, v * 1080, 0.8 + 1.6 * s); ctx.set_source_rgba(0.2, 0.14, 0.08, 0.25); ctx.fill()
            ctx.set_source_rgba(0.95, 0.85, 0.6, 0.04 + 0.02 * math.sin(t * 31)); ctx.paint()
        ctx.restore()
    return f


def fade_from_black(dur=0.35):
    def f(ctx, t):
        if t < dur:
            ctx.set_source_rgba(0, 0, 0, 1 - t / dur); ctx.rectangle(0, 0, 1920, 1080); ctx.fill()
    return f


class PersonRow(Element):
    """Row(s) of person icons popping in one after another between t0 and t1 (red)."""
    def __init__(self, n=22, cols=11, cell=62, t_a=0.0, t_b=1.5, color=PAL.RED, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw); self.n, self.cols, self.cell, self.ta, self.tb, self.c = n, cols, cell, t_a, t_b, color
    def draw(self, ctx, t):
        rows = math.ceil(self.n / self.cols)
        for i in range(self.n):
            ti = self.ta + (self.tb - self.ta) * i / max(1, self.n - 1)
            if t < ti: continue
            k = ease('back', min(1, (t - ti) / 0.15))
            cx = (i % self.cols - (self.cols - 1) / 2) * self.cell; cy = (i // self.cols - (rows - 1) / 2) * self.cell * 1.3
            ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k); icon(ctx, 'person', self.cell * 0.42, self.c); ctx.restore()
