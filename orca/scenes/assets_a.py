"""Act A (cold open) custom assets. Never edits shared engine files."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import (W, H, TAU, PAL, Element, ev, set_col, hexc, mix, circle, rrect, poly, catmull, rng,
                         remap, ease, K)
from engine import plates as P
from engine.plates import Surface, Particles, vignette_builder, Plate
from engine.chars import Sailboat, Orca
from engine.text import draw_text, measure, cap_height, draw_text_reveal

OUT = '#0A0D10'

# ============================================================== night surface plate
class NightSurface(Surface):
    """Surface cross-section at night: navy sky, stars, moon + glint, coast lights."""
    NIGHT = dict(sky=('#02070C', '#06131C', '#0C2331'), sun='#DDE8EE',
                 sea=('#0B2B36', '#05171E', '#01080B'), far='#0A1F28')

    def __init__(self, waterline=620, moon=(0.70, 0.17), coast=True, wave_amp=4, stars=True, line_alpha=0.55,
                 haze=0.0, seed=5, **kw):
        kw.setdefault('rays', False)
        super().__init__('day', waterline=waterline, sun=moon, wave_amp=wave_amp, seed=seed, **kw)
        self.p = dict(self.NIGHT)
        self.coast, self.stars_on, self.line_alpha, self.haze = coast, stars, line_alpha, haze
        r = rng(seed + 11)
        self.stars = [(r.uniform(-200, W + 200), r.uniform(-120, waterline - 60), r.uniform(0.7, 2.0), r.random() * TAU)
                      for _ in range(120)] if stars else []
        self.lights = []
        if coast:
            for _ in range(26):   # Spain: right, a little higher
                self.lights.append((r.uniform(W * 0.55, W + 250), waterline - r.uniform(14, 34), r.uniform(1.4, 2.6), r.random() * TAU))
            for _ in range(16):   # Morocco: left
                self.lights.append((r.uniform(-250, W * 0.38), waterline - r.uniform(10, 22), r.uniform(1.2, 2.2), r.random() * TAU))
        self.mparts = Particles(n_specks=60, n_discs=8, alpha=0.28, region=(0, waterline + 20, W, H), color='#9CC7D3')
        self.parts = None

    def _sky(self, c, s):
        p = self.p; wl = self.wl
        g = cairo.LinearGradient(0, -H * 0.15, 0, wl)
        for k, col in zip((0, 0.6, 1), p['sky']): g.add_color_stop_rgba(k, *hexc(col))
        c.set_source(g); c.rectangle(-W, -H, W * 3, wl + H + 40); c.fill()
        mx, my = self.sun[0] * W, self.sun[1] * H
        rg = cairo.RadialGradient(mx, my, 0, mx, my, 260)
        rg.add_color_stop_rgba(0, 0.85, 0.92, 0.95, 0.30); rg.add_color_stop_rgba(0.3, 0.6, 0.75, 0.82, 0.10)
        rg.add_color_stop_rgba(1, 0.5, 0.6, 0.7, 0)
        c.set_source(rg); c.rectangle(-W, -H, W * 3, wl + H); c.fill()
        circle(c, mx, my, 34); set_col(c, '#E9EEEA'); c.fill()
        circle(c, mx + 10, my - 6, 30); set_col(c, mix('#06131C', '#0C2331', 0.4)); c.fill()   # crescent
        if self.coast:
            r = rng(self.seed)
            for side, (xa, xb, base, amp, col) in enumerate(((W * 0.5, W + 300, wl - 8, 70, '#071822'),
                                                           (-300, W * 0.42, wl - 6, 40, '#06141C'))):
                pts = []; x = xa
                while x < xb:
                    k = (x - xa) / (xb - xa)
                    env = math.sin(min(1, k * 3) * math.pi / 2) if side == 0 else math.sin(min(1, (1 - k) * 3) * math.pi / 2)
                    pts.append((x, base - amp * env * (0.45 + 0.55 * r.random()))); x += r.uniform(60, 150)
                pts.append((xb, base))
                sm = catmull(pts, 8)
                c.move_to(xa, wl + 6)
                for px, py in sm: c.line_to(px, py)
                c.line_to(xb, wl + 6); c.close_path(); set_col(c, col); c.fill()
        set_col(c, p['far']); c.rectangle(-W, wl - 6, W * 3, 20); c.fill()
        g = cairo.LinearGradient(0, wl, 0, H * 1.1)
        for k, col in zip((0, 0.45, 1), p['sea']): g.add_color_stop_rgba(k, *hexc(col))
        c.set_source(g); c.rectangle(-W, wl + 2, W * 3, H * 2); c.fill()
        if self.haze > 0:
            g = cairo.LinearGradient(0, wl - 220, 0, wl + 60)
            g.add_color_stop_rgba(0, 0.5, 0.6, 0.66, 0); g.add_color_stop_rgba(0.7, 0.5, 0.6, 0.66, self.haze)
            g.add_color_stop_rgba(1, 0.5, 0.6, 0.66, 0)
            c.set_source(g); c.rectangle(-W, wl - 220, W * 3, 280); c.fill()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'sky', self._sky, cam, t)
        ctx.save(); cam.apply(ctx, t, 1.0)
        for (x, y, r, ph) in self.stars:
            a = 0.35 + 0.35 * math.sin(t * 1.7 + ph * 5)
            ctx.set_source_rgba(0.9, 0.95, 1, a); circle(ctx, x, y, r); ctx.fill()
        for (x, y, r, ph) in self.lights:
            a = 0.55 + 0.3 * math.sin(t * 2.3 + ph * 3)
            ctx.set_source_rgba(1.0, 0.78, 0.45, a); circle(ctx, x, y, r); ctx.fill()
            ctx.set_source_rgba(1.0, 0.7, 0.4, a * 0.18); circle(ctx, x, y, r * 4); ctx.fill()
        # moon glint: shimmering dashes on the water under the moon
        mx = self.sun[0] * W
        rr = rng(3)
        for i in range(34):
            yy = self.wl + 8 + i * 9 + (i * i) * 0.25
            if yy > self.wl + 260: break
            wdt = (60 - i * 1.2) * (0.5 + 0.5 * math.sin(t * 2.0 + i * 1.7)) + 8
            off = 30 * math.sin(t * 0.9 + i * 0.8) + rr.uniform(-25, 25)
            a = 0.45 * (1 - i / 34) * (0.6 + 0.4 * math.sin(t * 3.1 + i))
            ctx.set_source_rgba(0.85, 0.93, 0.96, a)
            rrect(ctx, mx + off - wdt / 2, yy, wdt, 2.6, 1.3); ctx.fill()
        ctx.restore()
        self.mparts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        ctx.save(); cam.apply(ctx, t, 1.0)
        xs = np.arange(-500, W + 520, 24)
        ys = [self.water_y(x, t) for x in xs]
        ctx.move_to(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]): ctx.line_to(float(x), y)
        ctx.set_source_rgba(0.85, 0.93, 0.96, self.line_alpha); ctx.set_line_width(2.6); ctx.stroke()
        ctx.restore()
        self.paint_cached(ctx, 'vig', vignette_builder(0.55, '#000306'), None, t, parallax=0, margin=0)


class NightWater(P.Underwater):
    """Underwater at night: teal-black, no rays."""
    def __init__(self, **kw):
        kw.setdefault('depth', 0.78); kw.setdefault('rays', False); kw.setdefault('tint', '#020C12')
        super().__init__(**kw)


# ============================================================== night boat
class NightSailboat(Sailboat):
    """Sailboat dimmed for night (navy tint over the hull) + glowing nav lamps."""
    def __init__(self, night=0.45, lamps=True, sink=None, **kw):
        super().__init__(**kw); self.night, self.lamps = night, lamps

    def draw(self, ctx, t):
        ctx.push_group()
        Sailboat.draw(self, ctx, t)
        n = ev(self.night, t)
        if n > 0:
            ctx.set_operator(cairo.OPERATOR_ATOP)
            ctx.set_source_rgba(0.02, 0.07, 0.11, n); ctx.rectangle(-900, -900, 1800, 1400); ctx.fill()
            ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source(); ctx.paint()
        if self.lamps:
            sx = 1 if self.facing == 'right' else -1
            fl = 0.85 + 0.15 * math.sin(t * 9.0)
            for (x, y, col, r) in ((-306 * sx, -44, (1.0, 0.92, 0.7), 7), (-20 * sx, -648, (1.0, 1.0, 0.95), 6),
                                   (300 * sx, -54, (0.4, 1.0, 0.5), 5)):
                g = cairo.RadialGradient(x, y, 0, x, y, r * 8)
                g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.55 * fl); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
                ctx.set_source(g); circle(ctx, x, y, r * 8); ctx.fill()
                circle(ctx, x, y, r); ctx.set_source_rgba(col[0], col[1], col[2], 1); ctx.fill()


# ============================================================== dorsal fin cutting the surface
class Fin(Element):
    """Tall black dorsal fin above the waterline + wake. pos y = waterline (world).
    rise: 0..1 (callable/K) how far it is out of the water. plate gives water_y."""
    def __init__(self, plate=None, height=260, rise=1.0, facing='right', wake=True, **kw):
        super().__init__(**kw); self.plate, self.h, self.rise, self.facing, self.wake = plate, height, rise, facing, wake

    def draw(self, ctx, t):
        T = t + self.t0
        pos = ev(self.pos, t)
        wy = (self.plate.water_y(pos[0], T) - pos[1]) if self.plate else 0
        h = self.h; r = ev(self.rise, t)
        sx = 1 if self.facing == 'right' else -1
        bob = 4 * math.sin(t * 2.2)
        ctx.save(); ctx.translate(0, wy)
        # wake (behind the fin)
        if self.wake and r > 0.05:
            for i in range(16):
                k = i / 16
                xx = -sx * (30 + i * 26)
                a = 0.55 * (1 - k) * r * (0.6 + 0.4 * math.sin(t * 7 + i))
                ctx.set_source_rgba(0.85, 0.93, 0.96, a)
                rrect(ctx, xx - 12, -2 + 3 * math.sin(t * 5 + i), 24 - i * 0.8, 3, 1.5); ctx.fill()
                circle(ctx, xx + 6 * math.sin(i * 3.1 + t * 2), 6 + (i % 3) * 3, 1.6); ctx.fill()
            ctx.set_source_rgba(0.85, 0.93, 0.96, 0.6 * r)
            ctx.move_to(sx * 70, -1); ctx.curve_to(sx * 40, -10, -sx * 20, -10, -sx * 60, 0); ctx.set_line_width(3); ctx.stroke()
        # fin, clipped above the water
        ctx.save(); ctx.rectangle(-500, -2000, 1000, 2000 - 1); ctx.clip()
        ctx.translate(0, (1 - r) * h * 1.05 + bob * r)
        ctx.scale(sx, 1)
        ctx.move_to(-0.42 * h, 10); ctx.curve_to(-0.30 * h, -0.2 * h, -0.10 * h, -0.62 * h, 0.02 * h, -h)
        ctx.curve_to(0.06 * h, -1.01 * h, 0.09 * h, -0.98 * h, 0.08 * h, -0.9 * h)
        ctx.curve_to(0.06 * h, -0.6 * h, 0.10 * h, -0.2 * h, 0.24 * h, 10); ctx.close_path()
        set_col(ctx, '#05090C'); ctx.fill_preserve()
        ctx.set_source_rgba(0.45, 0.6, 0.7, 0.55); ctx.set_line_width(2.4); ctx.stroke()
        # moon rim light on the leading edge
        ctx.move_to(0.02 * h, -h + 6); ctx.curve_to(-0.10 * h, -0.62 * h, -0.30 * h, -0.2 * h, -0.40 * h, 4)
        ctx.set_source_rgba(0.75, 0.86, 0.92, 0.35); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        ctx.restore()


# ============================================================== POV ship's wheel + hands
class WheelPOV(Element):
    """First-person cockpit: wheel (rot deg K), two gloved hands on the rim, binnacle glow."""
    def __init__(self, wheel=0.0, R=330, **kw):
        super().__init__(**kw); self.wheel, self.R = wheel, R

    def _hand(self, ctx, ang, R, left):
        """Hand gripping the rim at angle ang (screen frame); forearm runs down and out of frame."""
        x, y = R * math.cos(ang), R * math.sin(ang)
        sx = -1 if left else 1
        ex, ey = x + sx * 260, R + 700          # elbow far below frame
        dx, dy = ex - x, ey - y; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
        w0, w1 = 40, 70
        ctx.move_to(x + nx * w0, y + ny * w0); ctx.line_to(ex + nx * w1, ey + ny * w1)
        ctx.line_to(ex - nx * w1, ey - ny * w1); ctx.line_to(x - nx * w0, y - ny * w0); ctx.close_path()
        set_col(ctx, '#1B3A52'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        cx, cy = x + dx / L * 52, y + dy / L * 52
        ctx.save(); ctx.translate(cx, cy); ctx.rotate(math.atan2(dy, dx) - math.pi / 2)
        rrect(ctx, -44, -14, 88, 28, 10); set_col(ctx, '#C8453A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.restore()
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang + math.pi / 2)
        rrect(ctx, -44, -36, 88, 72, 30); set_col(ctx, '#E2B58F'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        ctx.set_line_width(3)
        for i in range(3):
            xx = -24 + i * 22
            ctx.move_to(xx, -32); ctx.line_to(xx, -6); ctx.stroke()
        ctx.restore()

    def draw(self, ctx, t):
        R = self.R; a = math.radians(ev(self.wheel, t))
        # binnacle glow (warm instrument light from below)
        g = cairo.RadialGradient(0, 120, 0, 0, 120, 520)
        g.add_color_stop_rgba(0, 0.94, 0.65, 0.29, 0.35); g.add_color_stop_rgba(1, 0.94, 0.65, 0.29, 0)
        ctx.set_source(g); circle(ctx, 0, 120, 520); ctx.fill()
        ctx.save(); ctx.rotate(a)
        # spokes
        for i in range(8):
            ang = i * TAU / 8
            ctx.save(); ctx.rotate(ang)
            ctx.move_to(40, -9); ctx.line_to(R + 60, -7); ctx.line_to(R + 60, 7); ctx.line_to(40, 9); ctx.close_path()
            set_col(ctx, '#B9BEC0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
            ctx.restore()
        # rim
        ctx.arc(0, 0, R, 0, TAU); set_col(ctx, OUT); ctx.set_line_width(46); ctx.stroke()
        ctx.arc(0, 0, R, 0, TAU); set_col(ctx, '#8E9497'); ctx.set_line_width(36); ctx.stroke()
        ctx.arc(0, 0, R - 8, math.pi * 1.1, math.pi * 1.6); ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(6); ctx.stroke()
        ctx.arc(0, 0, R + 6, math.pi * 0.1, math.pi * 0.8); ctx.set_source_rgba(0.94, 0.65, 0.29, 0.45); ctx.set_line_width(6); ctx.stroke()
        # hub
        circle(ctx, 0, 0, 64); set_col(ctx, '#2A3238'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        circle(ctx, 0, 0, 26); set_col(ctx, '#8E9497'); ctx.fill_preserve(); ctx.stroke()
        # king spoke marker
        rrect(ctx, -10, -R - 30, 20, 40, 5); set_col(ctx, PAL.ORANGE); ctx.fill()
        ctx.restore()
        self._hand(ctx, math.radians(-150) + a, R, True)
        self._hand(ctx, math.radians(-30) + a, R, False)


class CockpitDeck(Element):
    """Foreground cockpit coaming + instrument display (dark, warm glow)."""
    def draw(self, ctx, t):
        ctx.move_to(-200, 860); ctx.curve_to(500, 820, 1400, 820, 2120, 860); ctx.line_to(2120, 1200); ctx.line_to(-200, 1200); ctx.close_path()
        set_col(ctx, '#0B141A'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-200, 872); ctx.curve_to(500, 832, 1400, 832, 2120, 872); ctx.set_source_rgba(0.94, 0.65, 0.29, 0.35); ctx.set_line_width(3); ctx.stroke()
        # instrument pod
        rrect(ctx, 1420, 880, 260, 150, 14); set_col(ctx, '#05090C'); ctx.fill_preserve(); set_col(ctx, '#2A3238'); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, 1440, 900, 220, 110, 8); set_col(ctx, '#1A1208'); ctx.fill()
        k = 0.8 + 0.2 * math.sin(t * 6)
        draw_text(ctx, 'HDG 087', 1550, 948, 'xb', 30, mix('#1A1208', PAL.ORANGE, k), 0.06, 'center', shadow=False)
        draw_text(ctx, f'{5.8 + 0.1 * math.sin(t * 1.3):.1f} KN', 1550, 990, 'bold', 22, mix('#1A1208', PAL.ORANGE, 0.7 * k), 0.12, 'center', shadow=False)


class SternRail(Element):
    """Foreground stern pulpit + backstay silhouette (looking back off the stern)."""
    def draw(self, ctx, t):
        set_col(ctx, '#020507')
        ctx.move_to(-200, 1000); ctx.curve_to(400, 940, 1500, 940, 2120, 1000); ctx.line_to(2120, 1300); ctx.line_to(-200, 1300); ctx.close_path(); ctx.fill()
        ctx.set_line_width(10)
        for x in (140, 520, 1400, 1780):
            ctx.move_to(x, 970); ctx.line_to(x + (x - 960) * 0.05, 760); ctx.stroke()
        ctx.move_to(100, 770); ctx.curve_to(600, 740, 1300, 740, 1820, 770); ctx.stroke()
        ctx.set_line_width(4)
        ctx.move_to(100, 860); ctx.curve_to(600, 840, 1300, 840, 1820, 860); ctx.stroke()
        ctx.set_source_rgba(0.6, 0.75, 0.82, 0.25); ctx.set_line_width(2)
        ctx.move_to(100, 764); ctx.curve_to(600, 734, 1300, 734, 1820, 764); ctx.stroke()
        # stern lamp
        g = cairo.RadialGradient(960, 950, 0, 960, 950, 90)
        g.add_color_stop_rgba(0, 1, 0.92, 0.7, 0.5); g.add_color_stop_rgba(1, 1, 0.92, 0.7, 0)
        ctx.set_source(g); circle(ctx, 960, 950, 90); ctx.fill()
        circle(ctx, 960, 950, 9); ctx.set_source_rgba(1, 0.95, 0.8, 1); ctx.fill()


# ============================================================== Strait of Gibraltar map card
SPAIN = [(-7.6, 37.25), (-7.0, 37.2), (-6.5, 36.95), (-6.43, 36.74), (-6.29, 36.53), (-6.18, 36.38), (-6.03, 36.25),
         (-5.92, 36.19), (-5.78, 36.08), (-5.60, 36.01), (-5.50, 36.05), (-5.45, 36.13), (-5.40, 36.17), (-5.35, 36.13),
         (-5.33, 36.16), (-5.25, 36.30), (-5.15, 36.42), (-4.88, 36.51), (-4.60, 36.57), (-4.42, 36.72), (-4.0, 36.73),
         (-3.6, 36.74), (-3.6, 38.2), (-7.6, 38.2)]
MOROCCO = [(-7.6, 34.2), (-6.9, 34.4), (-6.5, 34.9), (-6.15, 35.19), (-6.03, 35.47), (-5.95, 35.70), (-5.92, 35.79),
           (-5.80, 35.79), (-5.70, 35.81), (-5.55, 35.84), (-5.42, 35.90), (-5.31, 35.89), (-5.33, 35.80), (-5.32, 35.68),
           (-5.27, 35.62), (-5.10, 35.45), (-4.8, 35.25), (-4.4, 35.15), (-3.9, 35.2), (-3.6, 35.25), (-3.6, 34.0), (-7.6, 34.0)]

class StraitMap(Element):
    """Blueprint map of the Strait: coastlines, labels, dashed orange route + moving boat."""
    def __init__(self, box=(160, 120, 1760, 960), route=None, t_route=0.3, route_dur=2.2, **kw):
        super().__init__(**kw)
        self.box = box; self.t_route, self.route_dur = t_route, route_dur
        self.route = route or [(-7.2, 35.85), (-6.5, 35.92), (-5.95, 35.95), (-5.7, 35.97), (-5.55, 35.98)]
        self.lon = (-7.4, -3.9); self.lat = (34.9, 37.0)

    def xy(self, lon, lat):
        x0, y0, x1, y1 = self.box
        u = (lon - self.lon[0]) / (self.lon[1] - self.lon[0]); v = (lat - self.lat[0]) / (self.lat[1] - self.lat[0])
        return x0 + u * (x1 - x0), y1 - v * (y1 - y0)

    def _land(self, ctx, pts, name, lx, ly):
        sm = catmull([self.xy(*p) for p in pts[:-3]], 6)
        tail = [self.xy(*p) for p in pts[-3:]]
        ctx.move_to(*sm[0])
        for p in sm[1:]: ctx.line_to(*p)
        for p in tail: ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgba(0.11, 0.25, 0.30, 0.9); ctx.fill_preserve()
        set_col(ctx, PAL.CYAN, 0.9); ctx.set_line_width(2.6); ctx.stroke()
        draw_text(ctx, name, lx, ly, 'bold', 30, PAL.CYAN_HI, 0.3, 'center')

    def draw(self, ctx, t):
        x0, y0, x1, y1 = self.box
        ctx.save(); ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.clip()
        ctx.set_source_rgba(0.03, 0.10, 0.13, 0.7); ctx.paint()
        # bathymetry rings
        ctx.set_source_rgba(0.5, 0.75, 0.8, 0.10); ctx.set_line_width(1.5)
        for i in range(6):
            cx, cy = self.xy(-6.6, 35.95)
            ctx.save(); ctx.translate(cx, cy); ctx.scale(1.0, 0.35)
            circle(ctx, 0, 0, 120 + i * 90 + 6 * math.sin(t + i)); ctx.restore(); ctx.stroke()
        self._land(ctx, SPAIN, 'SPAIN', *self.xy(-5.2, 36.75))
        self._land(ctx, MOROCCO, 'MOROCCO', *self.xy(-5.6, 35.25))
        draw_text(ctx, 'ATLANTIC', *self.xy(-6.95, 35.6), 'bold', 22, PAL.GREY, 0.3, 'center')
        draw_text(ctx, 'MEDITERRANEAN', *self.xy(-4.4, 35.95), 'bold', 22, PAL.GREY, 0.3, 'center')
        ctx.restore()
        corner_box(ctx, self.box)
        # route
        lt = t - self.t_route
        if lt > 0:
            k = ease('eio', min(1, lt / self.route_dur))
            pts = catmull([self.xy(*p) for p in self.route], 12)
            L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
            cut = L[-1] * k
            n = int(np.searchsorted(L, cut))
            ctx.set_dash([18, 12], -t * 30)
            ctx.move_to(*pts[0])
            for p in pts[1:max(2, n)]: ctx.line_to(*p)
            set_col(ctx, PAL.ORANGE); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])
            bx, by = pts[min(n, len(pts) - 1)]
            # boat icon (moving)
            ctx.save(); ctx.translate(bx, by)
            circle(ctx, 0, 0, 26 + 4 * math.sin(t * 5)); ctx.set_source_rgba(0.94, 0.65, 0.29, 0.25); ctx.fill()
            ctx.move_to(-20, 4); ctx.line_to(20, 4); ctx.line_to(12, 14); ctx.line_to(-14, 14); ctx.close_path(); set_col(ctx, PAL.WHITE); ctx.fill()
            ctx.move_to(-2, 2); ctx.line_to(-2, -26); ctx.line_to(14, 0); ctx.close_path(); ctx.fill()
            ctx.restore()

def corner_box(ctx, box, arm=40, col=PAL.WHITE, a=0.9, w=2.4):
    x0, y0, x1, y1 = box
    set_col(ctx, col, a); ctx.set_line_width(w)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ctx.move_to(cx, cy + sy * arm); ctx.line_to(cx, cy); ctx.line_to(cx + sx * arm, cy)
    ctx.stroke()


# ============================================================== polaroid content: sailor at the wheel, night
def sailor_photo(ctx, t, w, h):
    g = cairo.LinearGradient(0, 0, 0, h)
    g.add_color_stop_rgba(0, *hexc('#0B2231')); g.add_color_stop_rgba(0.62, *hexc('#16384A')); g.add_color_stop_rgba(0.63, *hexc('#081A22'))
    g.add_color_stop_rgba(1, *hexc('#030B0F'))
    ctx.set_source(g); ctx.paint()
    circle(ctx, w * 0.78, h * 0.2, 20); set_col(ctx, '#E9EEEA'); ctx.fill()
    for i in range(10):
        ctx.set_source_rgba(0.85, 0.93, 0.96, 0.4 * (1 - i / 10)); rrect(ctx, w * 0.78 - 30 + 8 * math.sin(t * 2 + i), h * 0.64 + i * 8, 60 - i * 4, 2.5, 1); ctx.fill()
    # sailor silhouette at the wheel
    set_col(ctx, '#020507')
    cx, cy = w * 0.42, h * 0.58
    circle(ctx, cx, cy - 92, 24); ctx.fill()
    ctx.move_to(cx - 32, cy - 112); ctx.line_to(cx + 30, cy - 112); ctx.line_to(cx + 22, cy - 124); ctx.line_to(cx - 24, cy - 126); ctx.close_path(); ctx.fill()
    ctx.move_to(cx - 44, cy - 62); ctx.curve_to(cx - 50, cy, cx - 46, cy + 80, cx - 40, h); ctx.line_to(cx + 44, h); ctx.curve_to(cx + 48, cy + 60, cx + 52, cy, cx + 40, cy - 62); ctx.close_path(); ctx.fill()
    ang = 0.15 * math.sin(t * 1.4)
    ctx.save(); ctx.translate(cx + 96, cy - 10); ctx.rotate(ang)
    ctx.arc(0, 0, 70, 0, TAU); ctx.set_line_width(10); ctx.stroke()
    for i in range(6):
        a = i * TAU / 6; ctx.move_to(0, 0); ctx.line_to(92 * math.cos(a), 92 * math.sin(a)); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()
    ctx.move_to(cx + 30, cy - 50); ctx.line_to(cx + 60, cy - 30); ctx.set_line_width(14); ctx.stroke()
    # deck
    ctx.rectangle(0, h * 0.86, w, h); ctx.fill()


# ============================================================== tear-off calendar (sepia)
class Calendar(Element):
    """Tear-off calendar: pages 1..4 flip away, lands on 4 MAY 2023."""
    def __init__(self, t_flip=(0.15, 0.45, 0.75), **kw):
        super().__init__(**kw); self.t_flip = t_flip

    def _page(self, ctx, day, a=1.0):
        rrect(ctx, -230, -170, 460, 420, 10); set_col(ctx, '#F6F1E2', a); ctx.fill_preserve(); set_col(ctx, PAL.INK, a); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, str(day), 0, 170, 'black', 300, PAL.INK, 0.0, 'center', shadow=False, alpha=a)

    def draw(self, ctx, t):
        ctx.save(); ctx.translate(10, 16); rrect(ctx, -240, -280, 480, 540, 14); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.fill(); ctx.restore()
        rrect(ctx, -240, -280, 480, 540, 14); set_col(ctx, '#F6F1E2'); ctx.fill()
        rrect(ctx, -240, -280, 480, 120, 14); set_col(ctx, PAL.RED_DARK if hasattr(PAL, 'RED_DARK') else PAL.RED); ctx.fill()
        ctx.rectangle(-240, -200, 480, 40); ctx.fill()
        draw_text(ctx, 'MAY 2023', 0, -196, 'black', 64, PAL.WHITE, 0.08, 'center', shadow=False)
        for i in range(6):
            circle(ctx, -180 + i * 72, -280, 12); set_col(ctx, '#3A3530'); ctx.fill()
        nflip = sum(1 for tf in self.t_flip if t >= tf)
        self._page(ctx, 4)
        for j in range(len(self.t_flip) - 1, -1, -1):   # pages 1,2,3 on top, torn in order
            day = j + 1
            tf = self.t_flip[j]
            if t < tf:
                if j == nflip:   # top page
                    self._page(ctx, day)
                elif j > nflip:
                    pass
            else:
                lt = t - tf
                if lt < 0.6:
                    ctx.save(); ctx.translate(180 * lt + 400 * lt * lt, -260 * lt + 1400 * lt * lt); ctx.rotate(0.9 * lt * 3)
                    self._page(ctx, day, a=max(0, 1 - lt / 0.6)); ctx.restore()
        # draw remaining top page correctly (lowest untorn index on top)
        if nflip < len(self.t_flip):
            self._page(ctx, nflip + 1)


# ============================================================== helicopter + rescue
class Helicopter(Element):
    """Dark rescue helicopter silhouette with spinning rotor, blinking light, searchlight, winch line."""
    def __init__(self, line=0.0, beam=True, **kw):
        super().__init__(**kw); self.line, self.beam = line, beam

    def draw(self, ctx, t):
        if self.beam:
            g = cairo.LinearGradient(0, 40, 0, 700)
            g.add_color_stop_rgba(0, 1, 0.96, 0.85, 0.35); g.add_color_stop_rgba(1, 1, 0.96, 0.85, 0)
            ctx.move_to(-10, 40); ctx.line_to(-220, 700); ctx.line_to(180, 700); ctx.line_to(20, 40); ctx.close_path(); ctx.set_source(g); ctx.fill()
        L = ev(self.line, t)
        if L > 0:
            ctx.move_to(30, 40); ctx.line_to(30 + 6 * math.sin(t * 2), 40 + L); set_col(ctx, '#1A2026'); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, 30 + 6 * math.sin(t * 2), 50 + L, 14); set_col(ctx, '#E0A33A'); ctx.fill()
        set_col(ctx, '#2A3540')
        ctx.move_to(-120, -10); ctx.curve_to(-120, -60, -40, -70, 40, -60); ctx.curve_to(110, -50, 120, 20, 70, 40)
        ctx.line_to(-90, 40); ctx.curve_to(-120, 30, -125, 10, -120, -10); ctx.close_path(); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-110, -20); ctx.line_to(-330, -30); ctx.line_to(-330, -10); ctx.line_to(-100, 10); ctx.close_path(); set_col(ctx, '#2A3540'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        ctx.move_to(-330, -30); ctx.line_to(-350, -70); ctx.line_to(-320, -70); ctx.line_to(-310, -25); ctx.close_path(); set_col(ctx, '#2A3540'); ctx.fill()
        # red/white bands
        ctx.rectangle(-40, -30, 26, 70); set_col(ctx, '#C8453A'); ctx.fill()
        rrect(ctx, 40, -48, 60, 34, 10); set_col(ctx, '#7FC1CB', 0.7); ctx.fill()
        # skids
        set_col(ctx, OUT); ctx.set_line_width(5)
        ctx.move_to(-90, 70); ctx.line_to(80, 70); ctx.stroke()
        ctx.move_to(-50, 40); ctx.line_to(-60, 70); ctx.move_to(40, 40); ctx.line_to(50, 70); ctx.stroke()
        # rotor
        ctx.move_to(0, -62); ctx.line_to(0, -78); ctx.stroke()
        ph = (t * 14) % 1.0
        ctx.save(); ctx.translate(0, -80); ctx.scale(1, 0.12)
        for k in (0, 0.5):
            a = math.cos(TAU * (ph + k))
            ctx.move_to(-260 * a, 0); ctx.line_to(260 * a, 0)
        ctx.restore(); ctx.set_source_rgba(0.05, 0.07, 0.09, 0.8); ctx.set_line_width(7); ctx.stroke()
        ctx.save(); ctx.translate(0, -80); ctx.scale(1, 0.12); circle(ctx, 0, 0, 260); ctx.restore(); ctx.set_source_rgba(0.1, 0.12, 0.15, 0.18); ctx.fill()
        tr = (t * 20) % 1.0
        ctx.save(); ctx.translate(-335, -20); ctx.rotate(TAU * tr); ctx.move_to(-34, 0); ctx.line_to(34, 0); ctx.restore(); ctx.set_line_width(4); ctx.stroke()
        if (t % 1.0) < 0.15:
            circle(ctx, 0, 72, 6); ctx.set_source_rgba(1, 0.2, 0.2, 1); ctx.fill()
            g = cairo.RadialGradient(0, 72, 0, 0, 72, 40); g.add_color_stop_rgba(0, 1, 0.2, 0.2, 0.5); g.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
            ctx.set_source(g); circle(ctx, 0, 72, 40); ctx.fill()


class Beacon(Element):
    """Blinking light (rescue cruiser)."""
    def __init__(self, color=(0.4, 0.7, 1.0), period=0.8, r=6, **kw):
        super().__init__(**kw); self.c, self.period, self.r = color, period, r
    def draw(self, ctx, t):
        on = (t % self.period) < self.period * 0.4
        a = 1.0 if on else 0.25
        g = cairo.RadialGradient(0, 0, 0, 0, 0, self.r * 9)
        g.add_color_stop_rgba(0, *self.c, 0.6 * a); g.add_color_stop_rgba(1, *self.c, 0)
        ctx.set_source(g); circle(ctx, 0, 0, self.r * 9); ctx.fill()
        circle(ctx, 0, 0, self.r); ctx.set_source_rgba(*self.c, a); ctx.fill()


# ============================================================== aquarium poster + panda
class Poster(Element):
    """Retro aquarium poster: sunburst, headline, grinning cartoon orca jumping, starburst."""
    def __init__(self, w=760, h=980, **kw):
        super().__init__(**kw); self.w, self.h = w, h
        self.orca = Orca(pos=(0, 60), scale=0.62, facing='right', rot=-18, swim=0.6, jaw=6, period=2.4)

    def draw(self, ctx, t):
        w, h = self.w, self.h
        ctx.save(); ctx.translate(14, 18); rrect(ctx, -w / 2, -h / 2, w, h, 6); ctx.set_source_rgba(0, 0, 0, 0.28); ctx.fill(); ctx.restore()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, '#F3EAD2'); ctx.fill()
        ctx.save(); rrect(ctx, -w / 2 + 26, -h / 2 + 26, w - 52, h - 52, 4); ctx.clip()
        set_col(ctx, '#5FB3C4'); ctx.paint()
        ctx.save(); ctx.translate(0, 80); ctx.rotate(t * 0.12)
        for i in range(16):
            a0 = i * TAU / 16
            ctx.move_to(0, 0); ctx.arc(0, 0, 1200, a0, a0 + TAU / 32); ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 0.16); ctx.fill()
        ctx.restore()
        # waves at bottom
        set_col(ctx, '#2F7F96')
        ctx.move_to(-w, h / 2)
        for i in range(-12, 13):
            x = i * 60; ctx.curve_to(x - 30, 300 + 10 * math.sin(t * 2 + i), x - 10, 280, x + 30, 300 + 6 * math.sin(t * 2 + i))
        ctx.line_to(w, h / 2); ctx.close_path(); ctx.fill()
        bob = 12 * math.sin(t * 2.2)
        ctx.save(); ctx.translate(0, bob); self.orca.render(ctx, t); ctx.restore()
        # cartoon smile on the orca (drawn in orca space approx)
        ctx.save(); ctx.translate(0, 60 + bob); ctx.rotate(math.radians(-18)); ctx.scale(0.62, 0.62)
        ctx.move_to(310, 28); ctx.curve_to(350, 62, 420, 60, 470, 22)
        set_col(ctx, OUT); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()
        ctx.restore()
        rrect(ctx, -w / 2 + 26, -h / 2 + 26, w - 52, h - 52, 4); set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
        # headline band
        rrect(ctx, -w / 2 + 50, -h / 2 + 60, w - 100, 190, 8); set_col(ctx, '#F3EAD2'); ctx.fill_preserve(); set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, "MEET THE OCEAN'S", 0, -h / 2 + 142, 'black', 62, PAL.INK, 0.02, 'center', shadow=False)
        draw_text(ctx, 'BEST FRIEND!', 0, -h / 2 + 218, 'black', 72, PAL.RED, 0.02, 'center', shadow=False)
        draw_text(ctx, 'SEAWORLD-STYLE SPLASH SHOW • DAILY', 0, h / 2 - 62, 'bold', 22, PAL.INK, 0.22, 'center', shadow=False)
        # starburst
        ctx.save(); ctx.translate(w / 2 - 110, -h / 2 + 330); ctx.rotate(math.radians(12 + 3 * math.sin(t * 3)))
        n = 14
        for i in range(n * 2 + 1):
            r = 105 if i % 2 == 0 else 78; a = i * math.pi / n
            (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(a), r * math.sin(a))
        ctx.close_path(); set_col(ctx, '#F7D046'); ctx.fill_preserve(); set_col(ctx, PAL.INK); ctx.set_line_width(4); ctx.stroke()
        draw_text(ctx, 'SO', 0, -10, 'black', 40, PAL.INK, 0.02, 'center', shadow=False)
        draw_text(ctx, 'CUTE!', 0, 32, 'black', 40, PAL.INK, 0.02, 'center', shadow=False)
        ctx.restore()


class Panda(Element):
    """Flat panda face."""
    def draw(self, ctx, t):
        ctx.set_line_width(7); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for sx in (-1, 1):
            circle(ctx, sx * 150, -150, 70); set_col(ctx, '#15191C'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        ctx.save(); ctx.scale(1.08, 1.0); circle(ctx, 0, 0, 210); ctx.restore()
        set_col(ctx, '#F2F0EB'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        bl = 1.0 if (t % 3.3) > 0.12 else 0.15
        for sx in (-1, 1):
            ctx.save(); ctx.translate(sx * 82, -20); ctx.rotate(sx * -0.5); ctx.scale(1, 1.4); circle(ctx, 0, 0, 52); ctx.restore()
            set_col(ctx, '#15191C'); ctx.fill()
            ctx.save(); ctx.translate(sx * 86, -28); ctx.scale(1, bl); circle(ctx, 0, 0, 16); ctx.restore(); set_col(ctx, '#F2F0EB'); ctx.fill()
            circle(ctx, sx * 88, -28, 7 * bl); set_col(ctx, '#050607'); ctx.fill()
        ctx.save(); ctx.translate(0, 60); ctx.scale(1.3, 0.9); circle(ctx, 0, 0, 22); ctx.restore(); set_col(ctx, '#15191C'); ctx.fill()
        ctx.move_to(-50, 110); ctx.curve_to(-25, 140, 25, 140, 50, 110); set_col(ctx, OUT); ctx.set_line_width(7); ctx.stroke()


# ============================================================== liver highlight (x-ray inside shark)
class Liver(Element):
    """Glowing red liver blob inside a shark (pos in shark-local space via a Group)."""
    def draw(self, ctx, t):
        p = 0.75 + 0.25 * math.sin(t * 6)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 220)
        g.add_color_stop_rgba(0, 0.84, 0.25, 0.24, 0.55 * p); g.add_color_stop_rgba(1, 0.84, 0.25, 0.24, 0)
        ctx.set_source(g); circle(ctx, 0, 0, 220); ctx.fill()
        ctx.move_to(-170, -10); ctx.curve_to(-120, -60, 80, -70, 170, -20); ctx.curve_to(150, 30, 40, 60, -40, 50)
        ctx.curve_to(-120, 45, -170, 20, -170, -10); ctx.close_path()
        set_col(ctx, '#D73F3C'); ctx.fill_preserve(); set_col(ctx, '#FFB0A0', 0.9); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-120, 0); ctx.curve_to(-40, -30, 40, -30, 120, -10); ctx.set_source_rgba(1, 1, 1, 0.3); ctx.set_line_width(3); ctx.stroke()


# ============================================================== clipped panel (triptych)
class Panel(Element):
    """Bracketed panel: clips child elements to its box (local coords, box centred on pos).
    pops in (scale 0.9 -> 1) at t0. caption under the box."""
    def __init__(self, w=520, h=560, caption='', cap_color=PAL.WHITE, bg='#0E3140', ring=None, **kw):
        super().__init__(**kw); self.w, self.h, self.cap, self.cc, self.bg, self.ring = w, h, caption, cap_color, bg, ring

    def render(self, ctx, t):
        if not self.visible(t): return
        lt = t - self.t0
        pos, sc, rot, op = self.props(lt)
        k = min(1, lt / (4 / 30)); s = 0.9 + 0.1 * ease('eo', k)
        ctx.save(); ctx.translate(*pos); ctx.scale(s * sc, s * sc)
        w, h = self.w, self.h
        ctx.push_group()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, self.bg); ctx.fill()
        ctx.save(); rrect(ctx, -w / 2, -h / 2, w, h, 6); ctx.clip()
        for c in sorted(self.children, key=lambda c: c.z): c.render(ctx, lt)
        ctx.restore()
        rrect(ctx, -w / 2, -h / 2, w, h, 6); set_col(ctx, PAL.WHITE, 0.35); ctx.set_line_width(2); ctx.stroke()
        corner_box(ctx, (-w / 2 - 12, -h / 2 - 12, w / 2 + 12, h / 2 + 12), arm=36)
        if self.cap:
            draw_text(ctx, self.cap, 0, h / 2 + 64, 'xb', 36, self.cc, 0.06, 'center')
        if self.ring is not None and lt >= self.ring[2]:
            kk = ease('eo', min(1, (lt - self.ring[2]) / 0.25))
            ctx.arc(self.ring[0], self.ring[1], 70 * (0.6 + 0.4 * kk), 0, TAU * kk); set_col(ctx, PAL.RED); ctx.set_line_width(7); ctx.stroke()
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, op * (0.3 + k)))
        ctx.restore()


# ============================================================== misc
class FadeIn(Element):
    """Screen-space fade from black."""
    def __init__(self, dur=0.6, **kw):
        kw.setdefault('layer', 'overlay'); kw.setdefault('z', 99); super().__init__(**kw); self.d = dur
    def draw(self, ctx, t):
        a = 1 - min(1, t / self.d)
        if a > 0: ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(-50, -50, W + 100, H + 100); ctx.fill()


class Swell(Element):
    """Defocused dark swell crest passing along the bottom edge (foreground)."""
    def __init__(self, speed=40, **kw):
        super().__init__(**kw); self.speed = speed
    def draw(self, ctx, t):
        off = (t * self.speed) % 600
        ctx.move_to(-400, 120)
        for i in range(10):
            x = -400 + i * 300 - off
            ctx.curve_to(x + 80, -10, x + 220, -10, x + 300, 120 - 0)
        ctx.line_to(2600, 400); ctx.line_to(-400, 400); ctx.close_path()
        ctx.set_source_rgba(0.0, 0.03, 0.05, 0.85); ctx.fill()


class Ripples(Element):
    """Expanding flattened rings on the water surface."""
    def __init__(self, period=1.4, n=3, rmax=180, **kw):
        super().__init__(**kw); self.period, self.n, self.rmax = period, n, rmax
    def draw(self, ctx, t):
        for i in range(self.n):
            k = ((t / self.period) + i / self.n) % 1.0
            ctx.save(); ctx.scale(1, 0.18); circle(ctx, 0, 0, 20 + self.rmax * k); ctx.restore()
            ctx.set_source_rgba(0.85, 0.93, 0.96, 0.5 * (1 - k)); ctx.set_line_width(2.5); ctx.stroke()


class Blip(Element):
    """Sonar blip (green) fading in/out."""
    def __init__(self, r=10, **kw):
        super().__init__(**kw); self.r = r
    def draw(self, ctx, t):
        a = min(1, t / 0.15) * (0.6 + 0.4 * math.sin(t * 8))
        g = cairo.RadialGradient(0, 0, 0, 0, 0, self.r * 4)
        g.add_color_stop_rgba(0, 0.45, 1, 0.6, 0.7 * a); g.add_color_stop_rgba(1, 0.45, 1, 0.6, 0)
        ctx.set_source(g); circle(ctx, 0, 0, self.r * 4); ctx.fill()
        circle(ctx, 0, 0, self.r); ctx.set_source_rgba(0.6, 1, 0.7, a); ctx.fill()


class Underline(Element):
    """Orange underline wiping on (screen space)."""
    def __init__(self, w=900, dur=0.4, color=PAL.ORANGE, width=8, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw); self.w, self.d, self.c, self.lw = w, dur, color, width
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / self.d))
        ctx.move_to(-self.w / 2, 0); ctx.line_to(-self.w / 2 + self.w * k, 0)
        set_col(ctx, self.c); ctx.set_line_width(self.lw); ctx.set_line_cap(cairo.LINE_CAP_BUTT); ctx.stroke()


class WordReveal(Element):
    """Words of a line appear grey->white at given local times (centred at pos, baseline y=0)."""
    def __init__(self, text, times, size=64, font='xb', color=PAL.WHITE, track=0.02, **kw):
        kw.setdefault('layer', 'overlay'); super().__init__(**kw)
        self.words, self.times, self.size, self.font, self.c, self.track = text.split(), times, size, font, color, track
        self.text = text
    def draw(self, ctx, t):
        from engine.text import set_font
        tw = measure(ctx, self.text, self.font, self.size, self.track)[0]
        x = -tw / 2
        set_font(ctx, self.font, self.size); sp = ctx.text_extents(' ')[4]
        for wd, tt in zip(self.words, self.times):
            ww = measure(ctx, wd, self.font, self.size, self.track)[0]
            if t >= tt:
                k = min(1, (t - tt) / 0.15)
                draw_text(ctx, wd, x, 0, self.font, self.size, mix('#5E6466', self.c, k), self.track, 'left', alpha=min(1, 0.3 + k))
            x += ww + sp
