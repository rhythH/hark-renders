"""Act G custom assets (chapter 6 THE REAL DANGER + outro). Only used by scenes/act_g.py.
Reused rigs adapted from the orca act F assets, plus croc-specific props. Pure code."""
import math
import numpy as np
import cairocffi as cairo
from engine.core import Element, ev, hexc, mix, set_col, rrect, circle, poly, catmull, W, H, PAL, ease, remap, rng, lerp
from engine.text import draw_text, measure, text_path, cap_height
from engine.ui import UI, icon, Globe, _ortho, _pop, _country, _land
from engine.plates import Surface, Underwater

TAU = math.pi * 2
INK = '#2A2F30'
PAPER = '#EDE6CF'
DUSK = dict(sky=('#1B1E3A', '#5A3A55', '#D9876A'), sun='#FFD7A8', sea=('#2A3F4A', '#142630', '#060F14'), far='#2A2A3A')


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



# ================================================================== croc act G props
class Grade(Element):
    """Full-frame colour wash (night / dusk grade) drawn in a world layer, oversized so camera moves never reveal edges."""
    def __init__(self, color='#030A14', alpha=0.6, **kw):
        kw.setdefault('layer', 'mid'); super().__init__(**kw); self.c, self.a = color, alpha

    def draw(self, ctx, t):
        ctx.rectangle(-600, -600, W + 1200, H + 1200); set_col(ctx, self.c, float(ev(self.a, t))); ctx.fill()


class MoonGlint(Element):
    """Moon disc + shimmering reflection dashes on the water (night river)."""
    def __init__(self, water_y=430, **kw):
        kw.setdefault('layer', 'mid'); super().__init__(**kw); self.wy = water_y

    def draw(self, ctx, t):
        for r, a in ((90, 0.08), (60, 0.12)):
            circle(ctx, 0, 0, r); set_col(ctx, '#DDE8EE', a); ctx.fill()
        circle(ctx, 0, 0, 38); set_col(ctx, '#E9F0F2', 0.95); ctx.fill()
        r = rng(4)
        for i in range(16):
            y = self.wy + 20 + i * 26
            w = 30 + 140 * r.random() * (0.6 + 0.4 * math.sin(t * 1.3 + i))
            x = 6 * math.sin(t * 0.9 + i * 1.7)
            rrect(ctx, x - w / 2, y, w, 5, 2.5); set_col(ctx, '#CFE0E6', 0.35 - i * 0.015); ctx.fill()


class PriceTag(Element):
    """Hanging price tag on a string (origin = string top); swings gently."""
    def __init__(self, text='$', w=210, string=200, color='#E9DFC4', ink='#7A1A1C', swing=6, **kw):
        super().__init__(**kw); self.text, self.w, self.sl, self.c, self.ink, self.sw = text, w, string, color, ink, swing

    def draw(self, ctx, t):
        ctx.rotate(math.radians(self.sw * math.sin(t * 1.4)))
        w = self.w; h = w * 0.55; L = self.sl
        ctx.move_to(0, 0); ctx.line_to(0, L); set_col(ctx, '#CFC6B0', 0.8); ctx.set_line_width(3); ctx.stroke()
        ctx.save(); ctx.translate(0, L)
        ctx.move_to(0, 0); ctx.line_to(h * 0.5, h * 0.42); ctx.line_to(h * 0.5, w); ctx.line_to(-h * 0.5, w); ctx.line_to(-h * 0.5, h * 0.42); ctx.close_path()
        ctx.save(); ctx.translate(5, 7); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.fill_preserve(); ctx.restore()
        set_col(ctx, self.c); ctx.fill_preserve(); set_col(ctx, '#3A2A22'); ctx.set_line_width(4); ctx.stroke()
        circle(ctx, 0, h * 0.34, 10); set_col(ctx, '#3A2A22'); ctx.fill()
        ctx.save(); ctx.translate(0, w * 0.68); ctx.rotate(math.radians(-90))
        draw_text(ctx, self.text, 0, h * 0.13, 'black', h * 0.42, self.ink, 0.02, 'center', shadow=False)
        ctx.restore(); ctx.restore()


def _scutes(ctx, x, y, w, h, col, a=0.5, cell=26):
    set_col(ctx, col, a); ctx.set_line_width(2)
    j = 0
    yy = y + cell * 0.5
    while yy < y + h:
        xx = x + (cell * 0.5 if j % 2 else 0)
        while xx < x + w:
            rrect(ctx, xx + 3, yy - cell * 0.35, cell - 6, cell * 0.7, 5); ctx.stroke()
            xx += cell
        yy += cell * 0.8; j += 1


class Handbag(Element):
    """Croc-skin handbag (origin bottom-centre) with scute pattern and handle."""
    def __init__(self, w=260, color='#6B4A2E', **kw):
        super().__init__(**kw); self.w, self.c = w, color

    def draw(self, ctx, t):
        w = self.w; h = w * 0.7
        ctx.set_line_width(14); set_col(ctx, '#2C1E14')
        ctx.arc(0, -h, w * 0.28, math.pi, 0); ctx.stroke()
        ctx.move_to(-w * 0.5, 0); ctx.line_to(-w * 0.42, -h); ctx.line_to(w * 0.42, -h); ctx.line_to(w * 0.5, 0); ctx.close_path()
        ctx.save(); ctx.translate(6, 8); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill_preserve(); ctx.restore()
        set_col(ctx, self.c); ctx.fill_preserve(); ctx.save(); ctx.clip()
        _scutes(ctx, -w / 2, -h, w, h, '#2C1E14', 0.45)
        ctx.restore()
        set_col(ctx, '#2C1E14'); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, -w * 0.42, -h, w * 0.84, h * 0.28, 8); set_col(ctx, mix(self.c, '#000000', 0.25)); ctx.fill()
        rrect(ctx, -18, -h * 0.82, 36, 22, 5); set_col(ctx, '#D9B45A'); ctx.fill()


class HideRoll(Element):
    """Rolled crocodile hide (origin centre)."""
    def __init__(self, w=300, color='#8A6A44', **kw):
        super().__init__(**kw); self.w, self.c = w, color

    def draw(self, ctx, t):
        w = self.w; h = w * 0.36
        rrect(ctx, -w / 2, -h / 2, w, h, h / 2)
        ctx.save(); ctx.translate(5, 7); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill_preserve(); ctx.restore()
        set_col(ctx, self.c); ctx.fill_preserve(); ctx.save(); ctx.clip()
        _scutes(ctx, -w / 2, -h / 2, w, h, '#3A2A1A', 0.4, 22); ctx.restore()
        set_col(ctx, '#3A2A1A'); ctx.set_line_width(4); ctx.stroke()
        ctx.save(); ctx.translate(w / 2 - h / 2, 0); ctx.scale(0.45, 1)
        for r in (h / 2, h / 3, h / 6):
            circle(ctx, 0, 0, r); set_col(ctx, '#3A2A1A', 0.8); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
        ctx.move_to(-w * 0.15, -h / 2); ctx.line_to(-w * 0.15, h / 2); ctx.move_to(w * 0.1, -h / 2); ctx.line_to(w * 0.1, h / 2)
        set_col(ctx, '#C9A86A'); ctx.set_line_width(7); ctx.stroke()


class FallGraph(UI):
    """Line graph that draws on: points list of (x 0..1, y 0..1); axis box w×h; colour; year labels."""
    def __init__(self, pts, w=1100, h=480, color=PAL.RED, dur=2.4, xlabels=(), **kw):
        kw.setdefault('pos', (410, 820)); super().__init__(**kw)
        self.pts, self.w, self.h, self.c, self.dur, self.xl = pts, w, h, color, dur, xlabels

    def draw(self, ctx, t):
        w, h = self.w, self.h
        set_col(ctx, PAL.WHITE, 0.7); ctx.set_line_width(3)
        ctx.move_to(0, -h); ctx.line_to(0, 0); ctx.line_to(w, 0); ctx.stroke()
        for i in range(1, 5):
            ctx.move_to(0, -h * i / 5); ctx.line_to(w, -h * i / 5)
        set_col(ctx, PAL.WHITE, 0.1); ctx.set_line_width(1.5); ctx.stroke()
        for x, s in self.xl:
            draw_text(ctx, s, x * w, 46, 'bold', 24, PAL.WHITE, 0.2, 'center', alpha=0.8)
        k = ease('eio', min(1, max(0, t / self.dur)))
        P = [(x * w, -y * h) for x, y in self.pts]
        segs = list(zip(P, P[1:])); tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs)
        rem = tot * k; ctx.move_to(*P[0]); head = P[0]
        for a, b in segs:
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            if rem <= 0: break
            u = min(1, rem / d); head = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u); ctx.line_to(*head); rem -= d
        set_col(ctx, self.c); ctx.set_line_width(9); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        circle(ctx, head[0], head[1], 13 + 3 * math.sin(t * 6)); set_col(ctx, self.c); ctx.fill()
        circle(ctx, head[0], head[1], 6); set_col(ctx, PAL.WHITE); ctx.fill()


class GreyGlobe(Globe):
    """Globe whose countries start orange and fade to grey (with EXTINCT tags) at given times.
    grey = {name: (t_grey, (dx, dy) tag offset)}."""
    def __init__(self, grey=None, **kw):
        super().__init__(**kw); self.grey = grey or {}

    def draw(self, ctx, t):
        super().draw(ctx, t)
        R = self.R
        lon0 = math.radians(self.c0[0] - self.spin * t); lat0 = math.radians(self.c0[1])
        ctx.save(); circle(ctx, 0, 0, R); ctx.clip()
        cents = {}
        for name, (tg, off) in self.grey.items():
            k = ease('eio', min(1, max(0, (t - tg) / 0.4)))
            col = mix(PAL.ORANGE, '#5E6A6E', k)
            for p in _country(name):
                x, y, c = _ortho(p, lon0, lat0, R)
                if (c > 0).sum() < 2: continue
                ctx.move_to(x[0], y[0])
                for xx, yy in zip(x[1:], y[1:]): ctx.line_to(xx, yy)
                ctx.close_path()
                ctx.set_source_rgba(*col); ctx.fill_preserve(); set_col(ctx, '#0B2530', 0.6); ctx.set_line_width(1.5); ctx.stroke()
                if name not in cents or len(p) > cents[name][2]:
                    cents[name] = (float(np.mean(x)), float(np.mean(y)), len(p))
        ctx.restore()
        for name, (tg, off) in self.grey.items():
            if name not in cents or t < tg: continue
            a, s = _pop(t - tg, 5, 0.9)
            cx, cy, _ = cents[name]
            tx, ty = cx + off[0], cy + off[1]
            ctx.move_to(cx, cy); ctx.line_to(tx, ty); set_col(ctx, PAL.WHITE, 0.7 * a); ctx.set_line_width(2.5); ctx.stroke()
            circle(ctx, cx, cy, 6); set_col(ctx, PAL.WHITE, a); ctx.fill()
            ctx.save(); ctx.translate(tx, ty); ctx.scale(s, s)
            nm = name.upper(); tw = measure(ctx, nm, 'xb', 30, 0.05)[0]
            bw = max(tw, 150) + 40
            rrect(ctx, -bw / 2, -62, bw, 96, 12); set_col(ctx, '#11181B', 0.92 * a); ctx.fill()
            draw_text(ctx, nm, 0, -24, 'xb', 30, PAL.WHITE, 0.05, 'center', shadow=False, alpha=a)
            draw_text(ctx, 'EXTINCT', 0, 18, 'bold', 22, '#9AA5A8', 0.24, 'center', shadow=False, alpha=a)
            ctx.restore()


def _mini_croc(ctx, col, a=1.0):
    """Tiny top-down croc glyph ~90 px long, facing left."""
    ctx.move_to(-46, 0); ctx.curve_to(-40, -6, -22, -9, -10, -10); ctx.curve_to(10, -11, 24, -6, 46, 0)
    ctx.curve_to(24, 6, 10, 11, -10, 10); ctx.curve_to(-22, 9, -40, 6, -46, 0); ctx.close_path()
    set_col(ctx, col, a); ctx.fill()
    for sx in (-14, 12):
        for sy in (-1, 1):
            ctx.move_to(sx, sy * 8); ctx.line_to(sx - 6, sy * 18)
    set_col(ctx, col, a); ctx.set_line_width(4); ctx.stroke()


class RamreeMap(Element):
    """Sepia 1945-style map of Ramree Island: coastline, mangrove hatch, croc glyphs that fade out at t_gone."""
    CROCS = [(-180, 40), (-60, 120), (80, 60), (200, 150), (-120, 220), (40, 250), (260, 20), (-240, 160), (130, 300)]

    def __init__(self, t_gone=2.0, **kw):
        kw.setdefault('layer', 'mid'); super().__init__(**kw); self.tg = t_gone

    def outline(self, ctx):
        r = rng(11); pts = []
        for i in range(28):
            a = TAU * i / 28
            rr = 1 + 0.12 * math.sin(a * 3 + 1) + 0.06 * r.uniform(-1, 1)
            pts.append((math.cos(a) * 470 * rr, math.sin(a) * 290 * rr + 60))
        ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]; ctx.close_path()

    def draw(self, ctx, t):
        self.outline(ctx); set_col(ctx, '#D8CBA4'); ctx.fill_preserve()
        set_col(ctx, INK); ctx.set_line_width(5); ctx.stroke()
        ctx.save(); self.outline(ctx); ctx.clip()
        # mangrove hatch (lower half)
        set_col(ctx, '#5C6B4A', 0.55); ctx.set_line_width(3)
        for i in range(-30, 30):
            x = i * 24
            ctx.move_to(x, 60); ctx.line_to(x + 120, 420)
        ctx.stroke()
        ctx.restore()
        # coast ripples
        for k in (1.08, 1.17):
            ctx.save(); ctx.scale(k, k); self.outline(ctx); ctx.restore()
            set_col(ctx, INK, 0.25); ctx.set_line_width(2); ctx.set_dash([10, 8]); ctx.stroke(); ctx.set_dash([])
        for i, (x, y) in enumerate(self.CROCS):
            tg = self.tg + i * 0.12
            a = 1 - min(1, max(0, (t - tg) / 0.5))
            if a <= 0:
                ctx.save(); ctx.translate(x, y); set_col(ctx, INK, 0.25); ctx.set_line_width(3)
                ctx.move_to(-12, -12); ctx.line_to(12, 12); ctx.move_to(12, -12); ctx.line_to(-12, 12); ctx.stroke(); ctx.restore()
                continue
            ctx.save(); ctx.translate(x + 4 * math.sin(t * 0.8 + i), y); ctx.rotate(math.radians(-20 + 40 * ((i * 37) % 5) / 5))
            _mini_croc(ctx, '#3E4A30', a); ctx.restore()


class RedactCard(UI):
    """Dossier card: 'FEARS:' with a black redaction bar that wipes off at t_rev revealing 'US' in red."""
    def __init__(self, t_rev=2.0, **kw):
        super().__init__(**kw); self.tr = t_rev

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.9); ctx.scale(s, s)
        w, h = 900, 380
        rrect(ctx, -w / 2 + 8, -h / 2 + 12, w, h, 10); ctx.set_source_rgba(0, 0, 0, 0.4 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 10); set_col(ctx, PAPER, a); ctx.fill()
        draw_text(ctx, 'SUBJECT: SALTWATER CROCODILE', -w / 2 + 50, -h / 2 + 70, 'bold', 26, INK, 0.2, shadow=False, alpha=a)
        ctx.move_to(-w / 2 + 50, -h / 2 + 95); ctx.line_to(w / 2 - 50, -h / 2 + 95); set_col(ctx, INK, 0.4 * a); ctx.set_line_width(2); ctx.stroke()
        draw_text(ctx, 'FEARS:', -w / 2 + 50, 70, 'black', 96, INK, 0.02, shadow=False, alpha=a)
        x0 = -w / 2 + 420
        if t >= self.tr:
            draw_text(ctx, 'US', x0 + 10, 70, 'black', 130, PAL.RED, 0.02, shadow=False, alpha=a)
        k = ease('eo', min(1, max(0, (t - self.tr) / 0.25)))
        bw = 360 * (1 - k)
        if bw > 1:
            rrect(ctx, x0 + 360 - bw, -30, bw, 120, 4); set_col(ctx, '#0D0D0D', a); ctx.fill()


class SenseCompare(UI):
    """Fingertip vs sensory dome comparison: two icons + bars growing at t_bars (croc bar longer)."""
    def __init__(self, t_bars=0.4, **kw):
        super().__init__(**kw); self.tb = t_bars

    def draw(self, ctx, t):
        a, s = _pop(t, 5, 0.9); ctx.scale(s, s)
        # fingertip icon
        ctx.save(); ctx.translate(-560, -110)
        rrect(ctx, -55, -80, 110, 220, 55); set_col(ctx, '#E2B497', a); ctx.fill_preserve(); set_col(ctx, PAL.OUTLINE, a); ctx.set_line_width(4); ctx.stroke()
        for r in (14, 26, 38):
            ctx.arc(0, -10, r, math.pi * 1.05, math.pi * 1.95); set_col(ctx, '#9A6A55', a); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        draw_text(ctx, 'YOUR FINGERTIP', -470, -110, 'bold', 28, PAL.WHITE, 0.2, alpha=a)
        # dome icon (jaw edge with dots)
        ctx.save(); ctx.translate(-560, 170)
        ctx.move_to(-90, 30); ctx.curve_to(-60, -40, 60, -40, 90, 30); ctx.close_path()
        set_col(ctx, '#5E6B3C', a); ctx.fill()
        for i in range(12):
            x = -60 + i * 11; y = 6 - 18 * math.sin(math.pi * (i / 11))
            glow = 0.5 + 0.5 * math.sin(t * 5 + i)
            circle(ctx, x, y, 4.5); set_col(ctx, mix('#2A2F20', PAL.CYAN_HI, glow), a); ctx.fill()
        ctx.restore()
        draw_text(ctx, 'CROC SENSORY DOME', -470, 170, 'bold', 28, PAL.CYAN, 0.2, alpha=a)
        k1 = ease('eo', min(1, max(0, (t - self.tb) / 0.63)))
        k2 = ease('eo', min(1, max(0, (t - self.tb - 0.25) / 0.8)))
        rrect(ctx, -470, -80, 520 * k1, 40, 20); set_col(ctx, PAL.WHITE, a); ctx.fill()
        rrect(ctx, -470, 200, 1000 * k2, 40, 20); set_col(ctx, PAL.CYAN, a); ctx.fill()


class Nest(Element):
    """Mound nest of leaves and mud (origin bottom-centre). call_t: sound arcs pulse after this.
    dig: 0..1|K flattens the mound and throws dirt; babies peek when dig > 0.5."""
    def __init__(self, w=360, call_t=None, dig=0.0, **kw):
        super().__init__(**kw); self.w, self.ct, self.dig = w, call_t, dig

    def draw(self, ctx, t):
        w = self.w; d = float(ev(self.dig, t)); h = w * 0.42 * (1 - 0.6 * d)
        ctx.move_to(-w / 2, 0); ctx.curve_to(-w * 0.35, -h * 1.1, w * 0.35, -h * 1.1, w / 2, 0); ctx.close_path()
        set_col(ctx, '#5A4628'); ctx.fill_preserve(); set_col(ctx, '#2E2414'); ctx.set_line_width(4); ctx.stroke()
        r = rng(3)
        for i in range(26):
            x = r.uniform(-0.4, 0.4) * w; yk = 1 - (2 * x / w) ** 2
            y = -r.uniform(0.1, 0.95) * h * yk
            ctx.save(); ctx.translate(x, y); ctx.rotate(r.uniform(0, TAU))
            ctx.scale(1, 0.4); circle(ctx, 0, 0, r.uniform(10, 18)); ctx.restore()
            set_col(ctx, ['#6E7A3A', '#8A6A30', '#4E5A2A'][i % 3]); ctx.fill()
        if d > 0.5:
            k = min(1, (d - 0.5) / 0.3)
            for j, x in enumerate((-60, 10, 70)):
                yy = -h * 0.8 - 18 * k + 4 * math.sin(t * 4 + j)
                ctx.save(); ctx.translate(x, yy)
                circle(ctx, 0, 0, 18); set_col(ctx, '#C9A845'); ctx.fill_preserve(); set_col(ctx, '#2E2414'); ctx.set_line_width(3); ctx.stroke()
                circle(ctx, -6, -4, 6); set_col(ctx, '#F4E7B0'); ctx.fill(); circle(ctx, -7, -4, 3); set_col(ctx, '#111111'); ctx.fill()
                ctx.restore()
        if 0.02 < d < 0.98:
            for i in range(10):
                ph = (t * 1.8 + i * 0.37) % 1
                x = -w * 0.2 + (i % 3) * 30 + ph * (180 + 30 * (i % 4)) * (1 if i % 2 else -0.6)
                y = -h - 40 * math.sin(math.pi * ph) * 2 + ph * 40
                circle(ctx, x, y, 6 + (i % 3) * 2); set_col(ctx, '#4A3820', 1 - ph); ctx.fill()
        if self.ct is not None and t >= self.ct:
            for i in range(3):
                ph = ((t - self.ct) * 0.9 + i / 3) % 1
                rr = 40 + 160 * ph
                for side in (-1, 1):
                    ctx.arc(0, -h * 0.5, rr, -math.pi / 2 - 0.5 + (0 if side > 0 else math.pi), -math.pi / 2 + 0.5 + (0 if side > 0 else math.pi))
                    set_col(ctx, PAL.WHITE, 0.8 * (1 - ph)); ctx.set_line_width(5); ctx.stroke()


from engine.chars.croc import CrocHead as _CrocHead


class DomeHead(_CrocHead):
    """CrocHead with working sensory domes: the engine's Croc.__init__ stores a list in self._domes,
    which shadows the _domes() draw method (TypeError when domes=True). Drop the instance attr."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.__dict__.pop('_domes', None)
