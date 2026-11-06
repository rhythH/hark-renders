"""DIVER (Depth Theory style): black suit, yellow fins, white tank, teal BCD
accent, white-framed mask. Side view facing RIGHT by default.

Diver(pos, scale=0.5, facing='right', kick=1.0 (amplitude), period=0.78,
      torch=False, bubbles=True, panic=0 (0..1 flail), xray=False (orange outline only))
Local size: ~540 units fins-to-hands; origin at the torso centre.
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, set_col, hexc, circle, rrect, TAU, PAL, rng

SUIT = '#1D2328'; SUIT_HI = '#343D45'; FIN = '#E8B32A'; FIN_DK = '#B9861B'
TANK = '#E6E9E8'; TANK_SH = '#B4BCBE'; TEAL = '#2E9DB0'; OUT = '#0A0D10'

def _limb(ctx, pts, w0, w1, col, out=True, ow=3.0):
    """Tapered limb through points (polyline), width w0->w1."""
    pts = np.asarray(pts, float)
    n = len(pts)
    left, right = [], []
    for i in range(n):
        if i == 0: d = pts[1] - pts[0]
        elif i == n - 1: d = pts[-1] - pts[-2]
        else: d = pts[i + 1] - pts[i - 1]
        d = d / max(1e-6, np.hypot(*d)); nrm = np.array([-d[1], d[0]])
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append(pts[i] + nrm * w); right.append(pts[i] - nrm * w)
    ctx.move_to(*left[0])
    for p in left[1:]: ctx.line_to(*p)
    # round end
    e = pts[-1]; ctx.arc(e[0], e[1], w1 / 2, math.atan2(*(left[-1] - e)[::-1]), math.atan2(*(left[-1] - e)[::-1]) + math.pi)
    for p in right[::-1]: ctx.line_to(*p)
    s0 = pts[0]; ctx.arc(s0[0], s0[1], w0 / 2, math.atan2(*(right[0] - s0)[::-1]), math.atan2(*(right[0] - s0)[::-1]) + math.pi)
    ctx.close_path()
    set_col(ctx, col)
    if out:
        ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
    else:
        ctx.fill()

class Diver(Element):
    def __init__(self, facing='right', kick=1.0, period=0.78, torch=False, bubbles=True, panic=0.0,
                 xray=False, outline=3.0, phase=0.0, **kw):
        super().__init__(**kw)
        self.facing, self.kick, self.period, self.torch, self.bubbles = facing, kick, period, torch, bubbles
        self.panic, self.xray, self.ow, self.phase = panic, xray, outline, phase

    def _leg(self, ctx, t, far, kick, col_suit, col_fin):
        ph = TAU * t / self.period + self.phase + (math.pi if far else 0)
        hip = np.array([-118.0, 4.0 + (4 if far else 0)])
        a_hip = math.radians(180 + 9 * kick * math.sin(ph))
        a_knee = a_hip + math.radians(-6 * kick * math.sin(ph - 0.9) - 4)
        knee = hip + 100 * np.array([math.cos(a_hip), math.sin(a_hip)])
        ankle = knee + 98 * np.array([math.cos(a_knee), math.sin(a_knee)])
        _limb(ctx, [hip, (hip + knee) / 2, knee], 40, 32, col_suit, ow=self.ow)
        _limb(ctx, [knee, (knee + ankle) / 2, ankle], 32, 24, col_suit, ow=self.ow)
        # fin: lags the shin
        a_fin = a_knee + math.radians(-14 * kick * math.sin(ph - 1.8))
        d = np.array([math.cos(a_fin), math.sin(a_fin)]); nrm = np.array([-d[1], d[0]])
        L = 190
        base = ankle - d * 10
        p = [base + nrm * 13, base + d * L + nrm * 34, base + d * (L + 8) + nrm * 6, base + d * (L + 4) - nrm * 30, base - nrm * 13]
        ctx.move_to(*p[0]); ctx.line_to(*p[1])
        ctx.curve_to(*(p[1] + d * 8), *(p[2] + d * 6), *p[3]); ctx.line_to(*p[4]); ctx.close_path()
        set_col(ctx, col_fin); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        # rib lines on fin
        ctx.set_line_width(2.4); set_col(ctx, FIN_DK if not self.xray else PAL.ORANGE, 0.9)
        for k in (0.33, 0.66):
            q0 = base + d * 30 + nrm * (13 - 26 * k); q1 = base + d * (L - 10) + nrm * (34 - 64 * k)
            ctx.move_to(*q0); ctx.line_to(*q1)
        ctx.stroke()
        # foot pocket
        ctx.move_to(*(ankle + nrm * 13 - d * 6)); ctx.line_to(*(ankle + d * 40 + nrm * 15)); ctx.line_to(*(ankle + d * 40 - nrm * 15))
        ctx.line_to(*(ankle - nrm * 13 - d * 6)); ctx.close_path(); set_col(ctx, '#2A2F33'); ctx.fill()

    def _arm(self, ctx, t, far, panic):
        ph = TAU * t / 0.5
        sh = np.array([58.0, -14.0 + (3 if far else 0)])
        a1 = math.radians(28 + (6 if far else 0) + panic * 50 * math.sin(ph + (2 if far else 0)))
        a2 = a1 + math.radians(-28 + panic * 40 * math.sin(ph * 1.3 + 1))
        el = sh + 70 * np.array([math.cos(a1), math.sin(a1)])
        hd = el + 64 * np.array([math.cos(a2), math.sin(a2)])
        col = SUIT if not far else '#15191D'
        _limb(ctx, [sh, el], 26, 22, col, ow=self.ow)
        _limb(ctx, [el, hd], 22, 18, col, ow=self.ow)
        circle(ctx, hd[0], hd[1], 10); set_col(ctx, '#2A2F33'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        return hd

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        kick = ev(self.kick, t); panic = ev(self.panic, t)
        if self.xray:
            self._xray_outline(ctx, t, kick, panic); ctx.restore(); return
        bob = 3 * math.sin(TAU * t / (self.period * 2))
        ctx.translate(0, bob)
        self._leg(ctx, t, True, kick, '#15191D', '#C9971F')
        self._arm(ctx, t, True, panic)
        # torso capsule
        rrect(ctx, -150, -34, 230, 64, 32); set_col(ctx, SUIT); ctx.fill_preserve()
        ctx.save(); ctx.clip(); rrect(ctx, -150, -34, 230, 18, 9); set_col(ctx, SUIT_HI, 0.8); ctx.fill(); ctx.restore()
        rrect(ctx, -150, -34, 230, 64, 32); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        # BCD band
        ctx.move_to(-70, -24); ctx.line_to(30, -24); ctx.set_line_width(5); set_col(ctx, TEAL); ctx.stroke()
        rrect(ctx, -60, -10, 70, 20, 6); set_col(ctx, '#0F1316'); ctx.fill()
        # tank on the back
        rrect(ctx, -132, -74, 186, 44, 22); set_col(ctx, TANK); ctx.fill_preserve()
        ctx.save(); ctx.clip(); ctx.rectangle(-140, -46, 200, 20); set_col(ctx, TANK_SH); ctx.fill()
        ctx.rectangle(-140, -70, 200, 7); ctx.set_source_rgba(1, 1, 1, 0.7); ctx.fill(); ctx.restore()
        rrect(ctx, -132, -74, 186, 44, 22); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        rrect(ctx, 52, -62, 22, 18, 4); set_col(ctx, '#3B4248'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        # hose
        ctx.move_to(70, -52); ctx.curve_to(98, -60, 118, -30, 118, 8); ctx.set_line_width(5); set_col(ctx, '#2A2F33'); ctx.stroke()
        self._leg(ctx, t, False, kick, SUIT, FIN)
        # head + hood
        circle(ctx, 104, -12, 32); set_col(ctx, SUIT); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        # mask
        rrect(ctx, 108, -32, 38, 24, 7); set_col(ctx, '#EEF1F0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(2.5); ctx.stroke()
        rrect(ctx, 114, -28, 26, 15, 5); set_col(ctx, '#86CFE0'); ctx.fill()
        ctx.move_to(118, -25); ctx.line_to(124, -17); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(2); ctx.stroke()
        # regulator
        circle(ctx, 128, 8, 9); set_col(ctx, '#596168'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(2.5); ctx.stroke()
        hd = self._arm(ctx, t, False, panic)
        if self.torch:
            ctx.save(); ctx.translate(hd[0], hd[1]); ctx.rotate(-0.08)
            rrect(ctx, -6, -9, 44, 18, 4); set_col(ctx, '#2A2F33'); ctx.fill()
            rrect(ctx, 32, -10, 12, 20, 3); set_col(ctx, '#E9ECEC'); ctx.fill()
            g = cairo.LinearGradient(44, 0, 420, 0)
            g.add_color_stop_rgba(0, 1, 0.98, 0.9, 0.35); g.add_color_stop_rgba(1, 1, 0.98, 0.9, 0)
            ctx.move_to(44, -8); ctx.line_to(420, -110); ctx.line_to(420, 110); ctx.line_to(44, 8); ctx.close_path()
            ctx.set_source(g); ctx.fill(); ctx.restore()
        ctx.restore()
        if self.bubbles: self._bubbles(ctx, t)

    def _xray_outline(self, ctx, t, kick, panic):
        o = PAL.ORANGE
        ctx.set_line_width(3); set_col(ctx, o)
        rrect(ctx, -150, -34, 230, 64, 32); ctx.stroke()
        rrect(ctx, -132, -74, 186, 44, 22); ctx.stroke()
        circle(ctx, 104, -12, 32); ctx.stroke()
        rrect(ctx, 108, -32, 38, 24, 7); ctx.stroke()
        for far in (True, False):
            ph = TAU * t / self.period + self.phase + (math.pi if far else 0)
            hip = np.array([-118.0, 4.0]); a = math.radians(180 + 9 * kick * math.sin(ph))
            knee = hip + 100 * np.array([math.cos(a), math.sin(a)]); a2 = a + math.radians(-6 * kick * math.sin(ph - 0.9) - 4)
            ank = knee + 98 * np.array([math.cos(a2), math.sin(a2)])
            ctx.move_to(*hip); ctx.line_to(*knee); ctx.line_to(*ank)
            d = np.array([math.cos(a2), math.sin(a2)]); n = np.array([-d[1], d[0]])
            ctx.move_to(*(ank + n * 12)); ctx.line_to(*(ank + d * 190 + n * 32)); ctx.line_to(*(ank + d * 190 - n * 28)); ctx.line_to(*(ank - n * 12))
            ctx.stroke()
        ctx.move_to(58, -14); ctx.line_to(118, 20); ctx.line_to(176, 14); ctx.stroke()

    def _bubbles(self, ctx, t):
        """Bubble puffs from the regulator every ~2.4 s, rising and wobbling."""
        sx = 132 if self.facing == 'right' else -132
        r = rng(5)
        for k in range(3):
            cyc = (t + k * 0.8) % 2.4
            base = int((t + k * 0.8) // 2.4)
            for j in range(4):
                rr = rng(base * 13 + j + k * 7)
                age = cyc - j * 0.12
                if age < 0 or age > 2.0: continue
                y = -age * 120 - j * 6
                x = sx + rr.uniform(-6, 14) + 6 * math.sin(age * 6 + j)
                rad = 3 + rr.uniform(0, 6) + age * 1.5
                circle(ctx, x, y - 10, rad)
                ctx.set_source_rgba(0.85, 0.95, 1, 0.75 * (1 - age / 2.0)); ctx.set_line_width(2); ctx.stroke()
