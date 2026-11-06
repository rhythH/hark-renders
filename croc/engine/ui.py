"""Overlay / UI kit (v2 Depth Theory look). All elements default to layer='overlay'
(screen space, no camera) and appear ON their t0 with short pops; they never
animate out (text leaves with the cut). Positions are 1920x1080 design px.
"""
import math, json, os
import numpy as np
import cairocffi as cairo
from .core import (to_screen, Element, Fn, ev, hexc, mix, set_col, rrect, circle, poly, catmull, TAU, W, H, PAL,
                   remap, ease, rng, lerp, stroke_glow)
from .text import draw_text, draw_text_reveal, measure, set_font, text_path, wrap, cap_height

FPS = 30
def _pop(t, frames=3, s0=0.9):
    """(opacity, scale) for a quick pop-in over `frames` frames."""
    k = min(1.0, max(0.0, t / (frames / FPS)))
    return k, s0 + (1 - s0) * ease('eo', k)

class UI(Element):
    """Overlay element. world=True: pos (and Pill targets) are WORLD coords that
    follow the camera (push/drift/shake) while the graphic stays crisp/unscaled."""
    def __init__(self, world=False, **kw):
        kw.setdefault('layer', 'overlay')
        super().__init__(**kw)
        self.world = world

    def render(self, ctx, t):
        if not (self.world and self.layer == 'overlay') or not self.visible(t):
            return super().render(ctx, t)
        orig = self.pos
        p = ev(orig, t - self.t0)
        self.pos = to_screen(p)
        try: super().render(ctx, t)
        finally: self.pos = orig

# ------------------------------------------------------------------ pills + leaders
PILL_KINDS = {
    # kind: (fill, text colour, outline)
    'dark':    (PAL.PILL, PAL.WHITE, None),
    'red':     (hexc(PAL.RED_DARK, 0.95), PAL.WHITE, None),
    'orange':  (hexc(PAL.ORANGE, 0.97), '#1A1410', None),
    'cyan':    (PAL.PILL, PAL.CYAN_HI, (PAL.CYAN, 2.0)),
    'green':   (hexc('#2F8F57', 0.95), PAL.WHITE, None),
    'outline': ((0.03, 0.04, 0.05, 0.88), PAL.WHITE, (PAL.WHITE, 2.2)),
    'white':   (hexc(PAL.WHITE, 0.96), '#111518', None),
    'grey':    ((0.12, 0.14, 0.16, 0.6), '#8E9496', None),
}

def tick_path(ctx, x, y, s, k=1.0):
    """Check mark stroke, drawn-on fraction k."""
    pts = [(x, y), (x + s * 0.35, y + s * 0.35), (x + s, y - s * 0.45)]
    L1 = math.hypot(s * 0.35, s * 0.35); L2 = math.hypot(s * 0.65, s * 0.8); L = (L1 + L2) * k
    ctx.move_to(*pts[0])
    if L <= L1:
        f = L / L1; ctx.line_to(x + s * 0.35 * f, y + s * 0.35 * f)
    else:
        ctx.line_to(*pts[1]); f = (L - L1) / L2
        ctx.line_to(pts[1][0] + (pts[2][0] - pts[1][0]) * f, pts[1][1] + (pts[2][1] - pts[1][1]) * f)

def x_path(ctx, x, y, s, k=1.0):
    k1 = min(1, k * 2); k2 = max(0, k * 2 - 1)
    ctx.move_to(x - s / 2, y - s / 2); ctx.line_to(x - s / 2 + s * k1, y - s / 2 + s * k1)
    if k2 > 0:
        ctx.move_to(x + s / 2, y - s / 2); ctx.line_to(x + s / 2 - s * k2, y - s / 2 + s * k2)

class Pill(UI):
    """Label pill. kind: dark|red|orange|cyan|green|outline|white|grey.
    pos = pill centre. target=(x,y) draws a thin white leader line from the
    pill to the target with a dot (orange dot for 'dark'). tick=True adds a
    drawn-on check (green 'false reassurance'). ghost=t: starts grey, goes solid at t."""
    def __init__(self, text, kind='dark', size=32, target=None, tick=False, ghost=None, font='xb',
                 track=0.02, dot=None, pad=(20, 12), world=None, **kw):
        super().__init__(world=(target is not None) if world is None else world, **kw)
        self.text, self.kind, self.size, self.target, self.tick, self.ghost = text, kind, size, target, tick, ghost
        self.font, self.track, self.dot, self.pad = font, track, dot, pad

    def draw(self, ctx, t):
        a, s = _pop(t)
        kind = self.kind
        if self.ghost is not None and t < self.ghost: kind = 'grey'
        fill, tc, outl = PILL_KINDS[kind]
        tw, asc, desc = measure(ctx, self.text, self.font, self.size, self.track)
        ch = cap_height(ctx, self.font, self.size)
        px, py = self.pad
        extra = self.size * 1.1 if self.tick else 0
        w = tw + 2 * px + extra; h = ch + 2 * py
        # leader (drawn first, under the pill)
        if self.target is not None:
            pos = ev(self.pos, t)
            tg = self.target(t + self.t0) if callable(self.target) else self.target
            if self.world: tg = to_screen(tg)
            tx, ty = tg[0] - pos[0], tg[1] - pos[1]
            k = ease('eo', min(1, t / 0.18))
            sx = 0; sy = h / 2 if ty > 0 else -h / 2
            if abs(tx) > abs(ty) * 2.5: sx, sy = (w / 2 if tx > 0 else -w / 2), 0
            ex, ey = sx + (tx - sx) * k, sy + (ty - sy) * k
            ctx.move_to(sx, sy); ctx.line_to(ex, ey)
            ctx.set_source_rgba(0, 0, 0, 0.35 * a); ctx.set_line_width(4); ctx.stroke()
            ctx.move_to(sx, sy); ctx.line_to(ex, ey)
            set_col(ctx, PAL.WHITE, a); ctx.set_line_width(2.2); ctx.stroke()
            if k >= 1:
                circle(ctx, tx, ty, 5.5); set_col(ctx, self.dot or (PAL.WHITE if kind != 'dark' else PAL.WHITE), a); ctx.fill()
        ctx.save(); ctx.scale(s, s)
        # soft shadow
        rrect(ctx, -w / 2 + 2, -h / 2 + 4, w, h, 7); ctx.set_source_rgba(0, 0, 0, 0.28 * a); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, 7)
        c = hexc(fill); ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a); ctx.fill_preserve()
        if outl:
            set_col(ctx, outl[0], a); ctx.set_line_width(outl[1]); ctx.stroke()
        ctx.new_path()
        draw_text(ctx, self.text, -w / 2 + px, ch / 2, self.font, self.size, tc, self.track, shadow=False, alpha=a)
        if self.tick:
            kk = min(1, max(0, (t - 0.12) / 0.3))
            tick_path(ctx, w / 2 - px - extra * 0.85, 0, self.size * 0.7, ease('eo', kk))
            set_col(ctx, PAL.WHITE, a); ctx.set_line_width(self.size * 0.14); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()

class Label(UI):
    """Plain text with the tight hard shadow. align left|center|right.
    reveal: None | 'fade' (3–9 frames) | 'wipe' (0.12 s mask) | 'letters' | 'type' (30 cps)."""
    def __init__(self, text, size=48, font='xb', color=PAL.WHITE, track=0.04, align='left', reveal='fade',
                 dur=None, shadow=True, **kw):
        super().__init__(**kw)
        self.text, self.size, self.font, self.c, self.track, self.align = text, size, font, color, track, align
        self.reveal, self.dur, self.shadow = reveal, dur, shadow

    def draw(self, ctx, t):
        r = self.reveal
        if r == 'fade':
            a = min(1, t / ((self.dur or 0.15)))
            draw_text(ctx, self.text, 0, 0, self.font, self.size, self.c, self.track, self.align, self.shadow, alpha=a)
        elif r == 'wipe':
            draw_text_reveal(ctx, self.text, 0, 0, min(1, t / (self.dur or 0.12)), self.font, self.size, self.c, self.track, self.align, 'wipe', self.shadow)
        elif r == 'letters':
            draw_text_reveal(ctx, self.text, 0, 0, min(1, t / (self.dur or 0.2)), self.font, self.size, self.c, self.track, self.align, 'letters', self.shadow)
        elif r == 'type':
            n = int(t * 30)
            draw_text(ctx, self.text[:n], 0, 0, self.font, self.size, self.c, self.track, self.align, self.shadow)
        else:
            draw_text(ctx, self.text, 0, 0, self.font, self.size, self.c, self.track, self.align, self.shadow)

class Typewriter(UI):
    """Typewriter text at cps chars/s (30 = house), optional blinking cursor."""
    def __init__(self, text, size=44, font='xb', color=PAL.WHITE, cps=30, cursor=True, track=0.03, **kw):
        super().__init__(**kw); self.text, self.size, self.font, self.c, self.cps, self.cursor, self.track = text, size, font, color, cps, cursor, track
    def draw(self, ctx, t):
        n = min(len(self.text), int(t * self.cps))
        s = self.text[:n]
        w = draw_text(ctx, s, 0, 0, self.font, self.size, self.c, self.track) if s else 0
        if self.cursor and (n < len(self.text) or int(t * 2) % 2 == 0):
            ch = cap_height(ctx, self.font, self.size)
            ctx.rectangle(w + 6, -ch, self.size * 0.08, ch); set_col(ctx, PAL.ORANGE); ctx.fill()

class StatBox(UI):
    """Top-left stat/date box: big text in a dark box with a thin white outline,
    optional sub-pill under it ('3 KM OFFSHORE') popping at t_sub."""
    def __init__(self, text, sub=None, t_sub=0.4, size=52, pos=(96, 100), **kw):
        super().__init__(pos=pos, **kw); self.text, self.sub, self.t_sub, self.size = text, sub, t_sub, size
    def draw(self, ctx, t):
        a, s = _pop(t)
        tw, _, _ = measure(ctx, self.text, 'xb', self.size, 0.02); ch = cap_height(ctx, 'xb', self.size)
        w, h = tw + 36, ch + 30
        ctx.save(); ctx.scale(s, s)
        rrect(ctx, 0, 0, w, h, 8); ctx.set_source_rgba(0.04, 0.05, 0.06, 0.9 * a); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, a * 0.9); ctx.set_line_width(2.4); ctx.stroke()
        draw_text(ctx, self.text, 18, 15 + ch, 'xb', self.size, PAL.WHITE, 0.02, shadow=False, alpha=a)
        ctx.restore()
        if self.sub and t >= self.t_sub:
            a2, s2 = _pop(t - self.t_sub)
            size = self.size * 0.6
            tw2, _, _ = measure(ctx, self.sub, 'xb', size, 0.02); ch2 = cap_height(ctx, 'xb', size)
            ctx.save(); ctx.translate(6, h + 26)
            rrect(ctx, 0, 0, tw2 + 26, ch2 + 20, 6); ctx.set_source_rgba(0.03, 0.035, 0.04, 0.92 * a2); ctx.fill()
            draw_text(ctx, self.sub, 13, 10 + ch2, 'xb', size, PAL.WHITE, 0.02, shadow=False, alpha=a2)
            ctx.restore()

class CalloutCard(UI):
    """Dark navy card with orange left bar, tiny orange tracked kicker, white
    body; leader line from card to target ending in an orange dot."""
    def __init__(self, kicker, body, width=520, target=None, size=26, **kw):
        super().__init__(**kw); self.k, self.b, self.w, self.target, self.size = kicker, body, width, target, size
    def draw(self, ctx, t):
        a, s = _pop(t, 4)
        lines = wrap(ctx, self.b, self.w - 50, 'semi', self.size)
        lh = self.size * 1.32
        h = 64 + lh * len(lines)
        if self.target is not None:
            pos = ev(self.pos, t); tx, ty = self.target[0] - pos[0], self.target[1] - pos[1]
            k = ease('eo', min(1, t / 0.2))
            ctx.move_to(0, h * 0.3); ctx.line_to(tx * k, h * 0.3 + (ty - h * 0.3) * k)
            set_col(ctx, PAL.WHITE, a * 0.9); ctx.set_line_width(2); ctx.stroke()
            circle(ctx, tx * k, h * 0.3 + (ty - h * 0.3) * k, 6); set_col(ctx, PAL.ORANGE, a); ctx.fill()
        ctx.save(); ctx.scale(s, s)
        rrect(ctx, 0, 0, self.w, h, 6); ctx.set_source_rgba(0.035, 0.07, 0.09, 0.9 * a); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.15 * a); ctx.set_line_width(1.2); ctx.stroke()
        ctx.rectangle(0, 0, 5, h); set_col(ctx, PAL.ORANGE, a); ctx.fill()
        draw_text(ctx, self.k.upper(), 24, 36, 'bold', 18, PAL.ORANGE, 0.22, shadow=False, alpha=a)
        for i, ln in enumerate(lines):
            draw_text(ctx, ln, 24, 36 + 18 + lh * (i + 1) - 8, 'semi', self.size, PAL.WHITE, 0, shadow=False, alpha=a)
        ctx.restore()

# ------------------------------------------------------------------ punchline, stamp, counter
class Punchline(UI):
    """Red underlined punchline (often starting with '…'). style 'v1' uses
    Archivo Black (sperm-video look), 'v2' Raleway Black. The underline strokes
    on over 10 frames. pos = left baseline (align='center' to centre)."""
    def __init__(self, text, size=74, style='v2', color=PAL.RED, align='center', underline=True, **kw):
        super().__init__(**kw); self.text, self.size, self.style, self.c, self.align, self.ul = text, size, style, color, align, underline
    def draw(self, ctx, t):
        font = 'archivo' if self.style == 'v1' else 'black'
        a = min(1, t / 0.1)
        w = measure(ctx, self.text, font, self.size, 0.0 if self.style == 'v1' else 0.03)[0]
        x0 = -w / 2 if self.align == 'center' else 0
        # soft dark halo (v1) / tight hard shadow (v2)
        if self.style == 'v1':
            for r_, al in ((10, 0.10), (6, 0.15), (3, 0.2)):
                ctx.new_path(); text_path(ctx, self.text, x0, 0, font, self.size, 0)
                ctx.set_source_rgba(0, 0, 0, al * a); ctx.set_line_width(r_ * 2); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        draw_text(ctx, self.text, x0, 0, font, self.size, self.c, 0.0 if self.style == 'v1' else 0.03, shadow=self.style != 'v1', alpha=a)
        if self.ul:
            k = ease('eo', min(1, max(0, (t - 0.05) / (10 / FPS))))
            y = self.size * 0.2
            ctx.move_to(x0, y + 2); ctx.line_to(x0 + w * k, y + 2)
            ctx.set_source_rgba(0, 0, 0, 0.45 * a); ctx.set_line_width(self.size * 0.085); ctx.stroke()
            ctx.move_to(x0, y); ctx.line_to(x0 + w * k, y)
            set_col(ctx, self.c, a); ctx.set_line_width(self.size * 0.075); ctx.set_line_cap(cairo.LINE_CAP_BUTT); ctx.stroke()

class Stamp(UI):
    """Rubber stamp: outlined rounded box + heavy caps, tilted −5..−8°, slams
    from 130% to 100% in 5 frames, distressed (ink speckle knocked out).
    color: PAL.RED (coral danger), PAL.ORANGE, PAL.CYAN, PAL.GREEN."""
    def __init__(self, text, color=PAL.RED, size=64, angle=-6, fill=True, seed=3, shake=True, **kw):
        kw.setdefault('rot', angle)
        super().__init__(**kw); self.text, self.c, self.size, self.fill, self.seed = text, color, size, fill, seed
        r = rng(seed)
        self.specks = [(r.random(), r.random(), r.uniform(0.8, 2.4)) for _ in range(40)]
    def draw(self, ctx, t):
        k = min(1, t / (5 / FPS))
        s = 1.3 - 0.3 * ease('ei2', k)
        a = min(1, 0.4 + k)
        tw, _, _ = measure(ctx, self.text, 'black', self.size, 0.03); ch = cap_height(ctx, 'black', self.size)
        w, h = tw + self.size * 0.7, ch + self.size * 0.62
        ctx.save(); ctx.scale(s, s)
        ctx.push_group()
        if self.fill:
            rrect(ctx, -w / 2, -h / 2, w, h, self.size * 0.14); ctx.set_source_rgba(0.03, 0.05, 0.06, self.fill if isinstance(self.fill, float) else 0.16); ctx.fill()
        rrect(ctx, -w / 2, -h / 2, w, h, self.size * 0.14); set_col(ctx, self.c); ctx.set_line_width(self.size * 0.07); ctx.stroke()
        draw_text(ctx, self.text, 0, ch / 2, 'black', self.size, self.c, 0.03, 'center', shadow=False)
        # distress: knock out specks
        ctx.set_operator(cairo.OPERATOR_DEST_OUT)
        for (u, v, r) in self.specks:
            circle(ctx, -w / 2 + u * w, -h / 2 + v * h, r); ctx.set_source_rgba(0, 0, 0, 0.55); ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
        ctx.restore()

class Counter(UI):
    """Number easing from v0 to v1 over dur (ease-out). fmt e.g. '{:,.0f}'.
    prefix/suffix strings ('~', ' TONNES'). size, align, colour; optional
    unit line below in tiny wide-tracked caps."""
    def __init__(self, v0, v1, dur=1.2, fmt='{:,.0f}', prefix='', suffix='', size=96, color=PAL.WHITE,
                 align='center', unit=None, e='eo', font='xb', **kw):
        super().__init__(**kw)
        self.v0, self.v1, self.d, self.fmt, self.pre, self.suf = v0, v1, dur, fmt, prefix, suffix
        self.size, self.c, self.align, self.unit, self.e, self.font = size, color, align, unit, e, font
    def value(self, t):
        return self.v0 + (self.v1 - self.v0) * ease(self.e, t / self.d if self.d else 1)
    def draw(self, ctx, t):
        a = min(1, t / 0.1)
        s = self.pre + self.fmt.format(self.value(t)) + self.suf
        draw_text(ctx, s, 0, 0, self.font, self.size, self.c, 0.02, self.align, alpha=a)
        if self.unit:
            draw_text(ctx, self.unit.upper(), 0, self.size * 0.55, 'bold', self.size * 0.24, PAL.GREY, 0.24, self.align, alpha=a)

class QuoteReveal(UI):
    """Quote on black: tiny kicker, words reveal grey->white one by one
    (word_times list in shot-local seconds, or wps words/second), then the
    attribution fades in. pos = centre of the block."""
    def __init__(self, text, kicker=None, attribution=None, word_times=None, wps=2.8, size=54, width=1300,
                 t_attr=None, **kw):
        super().__init__(**kw)
        self.text, self.kicker, self.attr, self.size, self.width = text, kicker, attribution, size, width
        n = len(text.split())
        self.wt = word_times or [i / wps for i in range(n)]
        self.t_attr = t_attr if t_attr is not None else self.wt[-1] + 0.5
    def draw(self, ctx, t):
        words = self.text.split()
        lines = wrap(ctx, self.text, self.width, 'xb', self.size)
        lh = self.size * 1.3
        y0 = -lh * (len(lines) - 1) / 2
        if self.kicker:
            draw_text(ctx, self.kicker.upper(), 0, y0 - lh * 1.1, 'bold', 20, PAL.ORANGE, 0.24, 'center')
        wi = 0
        for li, ln in enumerate(lines):
            lw = measure(ctx, ln, 'xb', self.size, 0.0)[0]
            x = -lw / 2
            set_font(ctx, 'xb', self.size)
            space = ctx.text_extents(' ')[4]
            for wd in ln.split():
                tw = self.wt[wi] if wi < len(self.wt) else 1e9
                k = min(1, max(0, (t - tw) / 0.15))
                if t >= tw - 0.0:
                    col = mix('#5E6466', PAL.WHITE, k)
                    draw_text(ctx, wd, x, y0 + li * lh, 'xb', self.size, col, 0, alpha=min(1, 0.25 + k))
                set_font(ctx, 'xb', self.size)
                x += ctx.text_extents(wd)[4] + space
                wi += 1
        if self.attr and t >= self.t_attr:
            a = min(1, (t - self.t_attr) / 0.3)
            draw_text(ctx, '— ' + self.attr.upper(), 0, y0 + len(lines) * lh + 20, 'bold', 22, PAL.GREY, 0.22, 'center', alpha=a)

# ------------------------------------------------------------------ icons
def icon(ctx, name, r=20, color=PAL.WHITE, lw=None):
    """Simple line icons centred at 0,0 inside radius r (navigator, grids, badges)."""
    lw = lw or max(1.5, r * 0.12)
    set_col(ctx, color); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    s = r
    if name == 'orca':
        ctx.move_to(-s * 0.85, 0.05 * s); ctx.curve_to(-s * 0.6, -s * 0.45, s * 0.3, -s * 0.4, s * 0.7, -s * 0.05)
        ctx.line_to(s * 0.95, -s * 0.3); ctx.line_to(s * 0.9, s * 0.25); ctx.line_to(s * 0.7, s * 0.05)
        ctx.curve_to(s * 0.3, s * 0.35, -s * 0.5, s * 0.4, -s * 0.85, 0.05 * s); ctx.close_path(); ctx.fill()
        ctx.move_to(-s * 0.1, -s * 0.32); ctx.line_to(0, -s * 0.85); ctx.line_to(s * 0.18, -s * 0.3); ctx.close_path(); ctx.fill()
    elif name == 'fin':
        ctx.move_to(-s * 0.8, s * 0.4); ctx.curve_to(-s * 0.3, s * 0.2, -s * 0.1, -s * 0.5, s * 0.1, -s * 0.8)
        ctx.curve_to(s * 0.15, -s * 0.3, s * 0.4, s * 0.2, s * 0.8, s * 0.4); ctx.stroke()
        ctx.move_to(-s * 0.9, s * 0.55); ctx.line_to(s * 0.9, s * 0.55); ctx.stroke()
    elif name == 'tooth':
        ctx.move_to(-s * 0.4, -s * 0.6); ctx.curve_to(-s * 0.45, 0, -s * 0.2, s * 0.6, 0, s * 0.8)
        ctx.curve_to(s * 0.2, s * 0.6, s * 0.45, 0, s * 0.4, -s * 0.6); ctx.close_path(); ctx.stroke()
    elif name == 'wave':
        for dy in (-0.35, 0.05, 0.45):
            ctx.move_to(-s * 0.75, s * dy)
            ctx.curve_to(-s * 0.4, s * (dy - 0.25), -s * 0.2, s * (dy + 0.25), 0, s * dy)
            ctx.curve_to(s * 0.2, s * (dy - 0.25), s * 0.4, s * (dy + 0.25), s * 0.75, s * dy); ctx.stroke()
    elif name == 'eye':
        ctx.move_to(-s * 0.8, 0); ctx.curve_to(-s * 0.4, -s * 0.55, s * 0.4, -s * 0.55, s * 0.8, 0)
        ctx.curve_to(s * 0.4, s * 0.55, -s * 0.4, s * 0.55, -s * 0.8, 0); ctx.stroke()
        circle(ctx, 0, 0, s * 0.22); ctx.fill()
    elif name == 'brain':
        circle(ctx, -s * 0.25, -s * 0.1, s * 0.42); ctx.stroke(); circle(ctx, s * 0.25, -s * 0.1, s * 0.42); ctx.stroke()
        ctx.move_to(0, -s * 0.5); ctx.line_to(0, s * 0.4); ctx.stroke()
    elif name == 'globe':
        circle(ctx, 0, 0, s * 0.75); ctx.stroke()
        ctx.save(); ctx.scale(0.4, 1); circle(ctx, 0, 0, s * 0.75); ctx.restore(); ctx.stroke()
        ctx.move_to(-s * 0.75, 0); ctx.line_to(s * 0.75, 0); ctx.stroke()
    elif name == 'question':
        set_font(ctx, 'black', s * 1.4); e = ctx.text_extents('?')
        ctx.move_to(-e[2] / 2 - e[0], -e[1] / 2 - e[3] / 2 + e[3]); ctx.text_path('?'); ctx.fill()
    elif name == 'boat':
        ctx.move_to(-s * 0.8, s * 0.1); ctx.line_to(s * 0.8, s * 0.1); ctx.line_to(s * 0.55, s * 0.45); ctx.line_to(-s * 0.6, s * 0.45); ctx.close_path(); ctx.stroke()
        ctx.move_to(0, s * 0.1); ctx.line_to(0, -s * 0.8); ctx.line_to(s * 0.55, s * 0.0); ctx.close_path(); ctx.stroke()
    elif name == 'fish':
        ctx.move_to(s * 0.7, 0); ctx.curve_to(s * 0.3, -s * 0.45, -s * 0.3, -s * 0.35, -s * 0.45, 0)
        ctx.curve_to(-s * 0.3, s * 0.35, s * 0.3, s * 0.45, s * 0.7, 0); ctx.stroke()
        ctx.move_to(-s * 0.45, 0); ctx.line_to(-s * 0.8, -s * 0.3); ctx.line_to(-s * 0.8, s * 0.3); ctx.close_path(); ctx.stroke()
    elif name == 'sonar':
        circle(ctx, -s * 0.5, 0, s * 0.1); ctx.fill()
        for rr in (0.4, 0.75, 1.1):
            ctx.new_sub_path(); ctx.arc(-s * 0.5, 0, s * rr, -0.8, 0.8); ctx.stroke()
    elif name == 'skull':
        circle(ctx, 0, -s * 0.15, s * 0.55); ctx.stroke()
        circle(ctx, -s * 0.2, -s * 0.15, s * 0.12); ctx.fill(); circle(ctx, s * 0.2, -s * 0.15, s * 0.12); ctx.fill()
        ctx.move_to(-s * 0.25, s * 0.4); ctx.line_to(-s * 0.25, s * 0.7); ctx.line_to(s * 0.25, s * 0.7); ctx.line_to(s * 0.25, s * 0.4); ctx.stroke()
    elif name == 'seal':
        ctx.move_to(-s * 0.8, s * 0.3); ctx.curve_to(-s * 0.5, -s * 0.3, s * 0.4, -s * 0.2, s * 0.8, s * 0.3); ctx.close_path(); ctx.stroke()
        circle(ctx, -s * 0.55, -s * 0.05, s * 0.25); ctx.stroke()
    elif name == 'heart':
        ctx.move_to(0, s * 0.7); ctx.curve_to(-s * 1.1, -s * 0.1, -s * 0.4, -s * 0.9, 0, -s * 0.3)
        ctx.curve_to(s * 0.4, -s * 0.9, s * 1.1, -s * 0.1, 0, s * 0.7); ctx.fill()
    elif name == 'person':
        circle(ctx, 0, -s * 0.5, s * 0.25); ctx.fill()
        ctx.move_to(-s * 0.45, s * 0.75); ctx.curve_to(-s * 0.45, -s * 0.1, s * 0.45, -s * 0.1, s * 0.45, s * 0.75); ctx.close_path(); ctx.fill()
    else:
        circle(ctx, 0, 0, s * 0.4); ctx.fill()

# ------------------------------------------------------------------ chapter card
class ChapterTitle(UI):
    """Chapter card overlay (v2). Title bottom-left (x≈5%, y≈70%) letter-reveal
    0.2 s; wide-tracked subtitle fades in 0.5 s later; navigator row of `total`
    outlined icon circles, current filled orange, 'n / 6' and the current
    chapter's tiny label under its circle."""
    def __init__(self, title, subtitle, n, total=6, icons=None, labels=None, size=128, **kw):
        kw.setdefault('pos', (96, 756))
        super().__init__(**kw)
        self.title, self.sub, self.n, self.total, self.size = title.upper(), subtitle.upper(), n, total, size
        self.icons = icons or ['orca', 'tooth', 'wave', 'fin', 'eye', 'question'][:total]
        self.labels = labels
    def draw(self, ctx, t):
        draw_text_reveal(ctx, self.title, 0, 0, min(1, t / 0.2), 'xb', self.size, PAL.WHITE, 0.04, 'left', 'letters')
        ts = t - 0.5
        if ts > 0:
            a = min(1, ts / 0.3)
            draw_text(ctx, self.sub, 6, 72, 'bold', 28, PAL.WHITE, 0.24, alpha=a)
        tn = t - 0.75
        if tn > 0:
            a = min(1, tn / 0.3)
            r = 21; gap = 64; y = 150
            for i in range(self.total):
                cx = 6 + r + i * gap
                if i > 0:
                    ctx.move_to(cx - gap + r + 4, y); ctx.line_to(cx - r - 4, y); set_col(ctx, PAL.WHITE, 0.5 * a); ctx.set_line_width(2); ctx.stroke()
                cur = (i + 1) == self.n
                circle(ctx, cx, y, r)
                if cur:
                    set_col(ctx, PAL.ORANGE, a); ctx.fill_preserve()
                set_col(ctx, PAL.WHITE if not cur else PAL.ORANGE, a); ctx.set_line_width(2.4); ctx.stroke()
                ctx.save(); ctx.translate(cx, y)
                icon(ctx, self.icons[i % len(self.icons)], r * 0.62, '#1A1410' if cur else PAL.WHITE)
                ctx.restore()
            draw_text(ctx, f'{self.n} / {self.total}', 6 + self.total * gap + 6, y + 15, 'xb', 44, PAL.WHITE, 0.02, alpha=a)
            lab = (self.labels[self.n - 1] if self.labels else self.title).upper()
            draw_text(ctx, lab, 6 + r + (self.n - 1) * gap, y + r + 36, 'bold', 20, PAL.WHITE, 0.2, 'center', alpha=a)

# ------------------------------------------------------------------ REC viewfinder
class RecOverlay(UI):
    """Phone/camcorder viewfinder: 4 white L brackets, red ● + 'REC' top-left,
    running timecode top-right (HH:MM:SS:FF from tc_start seconds). Pair with
    shot.camera.handheld() for the wobble (rec_shot() helper does both).
    jumps: list of (t, new_tc_seconds) for camcorder pause jump-cuts."""
    def __init__(self, tc_start=13.0, jumps=None, **kw):
        super().__init__(**kw); self.tc0, self.jumps = tc_start, sorted(jumps or [])
    def tc(self, t):
        base, t_ref = self.tc0, 0.0
        for (tj, v) in self.jumps:
            if t >= tj: base, t_ref = v, tj
        s = base + (t - t_ref)
        fr = int((s % 1) * 30); ss = int(s) % 60; mm = int(s // 60) % 60; hh = int(s // 3600)
        return f'{hh:02d}:{mm:02d}:{ss:02d}:{fr:02d}'
    def draw(self, ctx, t):
        from .plates import corner_brackets
        corner_brackets(ctx, inset=58, arm=78, width=3.4, alpha=0.95)
        if int(t * 1.6) % 2 == 0 or True:
            blink = 1.0 if (t % 1.0) < 0.62 else 0.25
            circle(ctx, 116, 106, 14); set_col(ctx, '#E5332E', blink); ctx.fill()
        draw_text(ctx, 'REC', 142, 119, 'xb', 38, PAL.WHITE, 0.04, shadow=True)
        draw_text(ctx, self.tc(t), W - 112, 119, 'xb', 34, PAL.WHITE, 0.06, 'right', shadow=True)

def rec_shot(shot, t0=0.0, tc_start=13.0, jumps=None, amp=2.6):
    """Turn a shot into a REC recreation: overlay + constant handheld wobble."""
    shot.add(RecOverlay(t0=t0, tc_start=tc_start, jumps=jumps))
    shot.camera.handheld(amp=amp, freq=1.0, t0=t0)
    return shot

class Letterbox(UI):
    def __init__(self, h=110, dur=0.4, **kw):
        super().__init__(**kw); self.h, self.d = h, dur
    def draw(self, ctx, t):
        hh = self.h * ease('eo', min(1, t / self.d))
        ctx.set_source_rgb(0, 0, 0); ctx.rectangle(0, 0, W, hh); ctx.rectangle(0, H - hh, W, hh); ctx.fill()

class Stopwatch(UI):
    """Stopwatch icon (white face, red hand) with readout, pops in with a tiny overshoot."""
    def __init__(self, start=0.0, rate=1.0, r=46, fmt=None, **kw):
        super().__init__(**kw); self.s0, self.rate, self.r, self.fmt = start, rate, r, fmt
    def draw(self, ctx, t):
        k = min(1, t / 0.2); s = ease('back', k)
        v = self.s0 + t * self.rate
        ctx.save(); ctx.scale(s, s)
        r = self.r
        rrect(ctx, -8, -r - 16, 16, 12, 3); set_col(ctx, PAL.WHITE); ctx.fill()
        circle(ctx, 0, 0, r); set_col(ctx, '#F4F2EC'); ctx.fill_preserve(); set_col(ctx, '#1A1E22'); ctx.set_line_width(4); ctx.stroke()
        a = (v % 60) / 60 * TAU - math.pi / 2
        ctx.move_to(0, 0); ctx.arc(0, 0, r * 0.8, -math.pi / 2, a); ctx.close_path(); set_col(ctx, PAL.RED, 0.35); ctx.fill()
        ctx.move_to(0, 0); ctx.line_to(math.cos(a) * r * 0.8, math.sin(a) * r * 0.8); set_col(ctx, PAL.RED); ctx.set_line_width(4); ctx.stroke()
        ctx.restore()
        txt = self.fmt(v) if self.fmt else f'{int(v // 60)}:{int(v % 60):02d}'
        draw_text(ctx, txt, r + 22, 14, 'xb', 40, PAL.WHITE, 0.04)

# ------------------------------------------------------------------ lists, menus
class Checklist(UI):
    """Checklist: items = [(text, state, t_state)], state 'tick'|'x'|'strike'|None.
    Items appear at t_items[i] (default 0.35 s apart). Ticks green, X red,
    strike-through red drawn over 10 frames (ease-out)."""
    def __init__(self, items, t_items=None, size=40, gap=74, title=None, **kw):
        super().__init__(**kw); self.items, self.size, self.gap, self.title = items, size, gap, title
        self.ti = t_items or [i * 0.35 for i in range(len(items))]
    def draw(self, ctx, t):
        y = 0
        if self.title:
            draw_text(ctx, self.title.upper(), 0, -self.gap * 0.9, 'bold', 22, PAL.ORANGE, 0.24)
        for i, (txt, state, ts) in enumerate(self.items):
            if t < self.ti[i]: continue
            a = min(1, (t - self.ti[i]) / 0.12)
            yy = i * self.gap
            rrect(ctx, 0, yy - self.size * 0.8, self.size * 0.9, self.size * 0.9, 6)
            set_col(ctx, PAL.WHITE, a * 0.9); ctx.set_line_width(2.5); ctx.stroke()
            done = state is not None and t >= ts
            col = PAL.WHITE if not (done and state in ('x', 'strike')) else '#9AA0A2'
            w = draw_text(ctx, txt, self.size * 1.4, yy, 'xb', self.size, col, 0.03, alpha=a)
            if done:
                k = ease('eo', min(1, (t - ts) / (10 / FPS)))
                cx, cy = self.size * 0.45, yy - self.size * 0.35
                if state == 'tick':
                    tick_path(ctx, cx - self.size * 0.35, cy, self.size * 0.75, k)
                    set_col(ctx, PAL.GREEN); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
                else:
                    x_path(ctx, cx, cy, self.size * 0.6, k)
                    set_col(ctx, PAL.RED); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
                    x0 = self.size * 1.3; ym = yy - self.size * 0.34
                    ctx.move_to(x0, ym); ctx.line_to(x0 + (w + 20) * k, ym)
                    set_col(ctx, PAL.RED); ctx.set_line_width(6); ctx.stroke()

class OptionsMenu(UI):
    """'YOUR OPTIONS' gauntlet (sperm-video menu): centred title, numbered
    options; strike(i, t) crosses one out (red line, 10 frames), select(i, t)
    draws the red outlined highlight box. pos = centre of the title."""
    def __init__(self, options, title='YOUR OPTIONS', size=44, gap=96, strikes=None, selects=None, t_items=None, **kw):
        super().__init__(**kw); self.opts, self.title, self.size, self.gap = options, title, size, gap
        self.strikes = dict(strikes or {}); self.selects = dict(selects or {})
        self.ti = t_items or [0.2 + 0.25 * i for i in range(len(options))]
    def strike(self, i, t): self.strikes[i] = t; return self
    def select(self, i, t): self.selects[i] = t; return self
    def draw(self, ctx, t):
        draw_text(ctx, self.title, 0, 0, 'black', self.size * 1.05, PAL.WHITE, 0.05, 'center')
        lw = max(measure(ctx, f'{i + 1}. {o.upper()}', 'black', self.size, 0.04)[0] for i, o in enumerate(self.opts))
        x0 = -lw / 2 - 20
        for i, o in enumerate(self.opts):
            if t < self.ti[i]: continue
            a = min(1, (t - self.ti[i]) / 0.12)
            y = (i + 1) * self.gap + 20
            s = f'{i + 1}. {o.upper()}'
            st = self.strikes.get(i); sel = self.selects.get(i)
            struck = st is not None and t >= st
            if sel is not None and t >= sel:
                k = min(1, (t - sel) / 0.1)
                ch = cap_height(ctx, 'black', self.size)
                rrect(ctx, x0 - 40, y - ch - 26, lw + 120, ch + 52, 10)
                ctx.set_source_rgba(0.28, 0.07, 0.07, 0.55 * k); ctx.fill_preserve(); set_col(ctx, PAL.RED, k); ctx.set_line_width(3.5); ctx.stroke()
            w = draw_text(ctx, s, x0, y, 'black', self.size, '#B9BCBC' if struck else PAL.WHITE, 0.04, alpha=a * (0.75 if struck else 1))
            if struck:
                k = ease('eo', min(1, (t - st) / (10 / FPS)))
                ym = y - cap_height(ctx, 'black', self.size) * 0.45
                ctx.move_to(x0 - 10, ym); ctx.line_to(x0 - 10 + (w + 20) * k, ym)
                set_col(ctx, PAL.RED); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()

# ------------------------------------------------------------------ charts
class BarChart(UI):
    """Vertical bars growing (ease-out 0.63 s, stagger) from a baseline at pos.
    values, labels, colors (default white / last orange), max_h px, bar_w, gap.
    value_fmt shows a number label above each bar."""
    def __init__(self, values, labels, colors=None, max_h=420, bar_w=120, gap=70, value_fmt='{:,.0f}', stagger=0.18,
                 unit='', vmax=None, **kw):
        super().__init__(**kw)
        self.v, self.l, self.max_h, self.bw, self.gap, self.fmt, self.stg, self.unit = values, labels, max_h, bar_w, gap, value_fmt, stagger, unit
        self.cols = colors or [PAL.WHITE] * (len(values) - 1) + [PAL.ORANGE]
        self.vmax = vmax or max(values)
    def draw(self, ctx, t):
        n = len(self.v); tw = n * self.bw + (n - 1) * self.gap
        x0 = -tw / 2
        ctx.move_to(x0 - 30, 0); ctx.line_to(x0 + tw + 30, 0); set_col(ctx, PAL.WHITE, 0.6); ctx.set_line_width(2); ctx.stroke()
        for i, (v, lab) in enumerate(zip(self.v, self.l)):
            k = ease('eo', min(1, max(0, (t - i * self.stg) / 0.63)))
            if t < i * self.stg: continue
            h = self.max_h * v / self.vmax * k
            x = x0 + i * (self.bw + self.gap)
            rrect(ctx, x, -h, self.bw, h + 0.01, 4); set_col(ctx, self.cols[i]); ctx.fill()
            draw_text(ctx, lab.upper(), x + self.bw / 2, 44, 'bold', 22, PAL.WHITE, 0.2, 'center')
            if self.fmt:
                draw_text(ctx, self.fmt.format(v * k) + self.unit, x + self.bw / 2, -h - 18, 'xb', 40, self.cols[i], 0.02, 'center')

class IconGrid(UI):
    """Population/icon grid: n icons in cols columns; from index `lost_from`
    on, icons fade to dim red outlines at t_lost (staggered) — 'shrinking'."""
    def __init__(self, n=50, cols=10, icon_name='orca', cell=70, color=PAL.WHITE, lost_from=None, t_lost=0.5,
                 lost_color='#5A2A2A', stagger=0.03, t_in=0.015, **kw):
        super().__init__(**kw)
        self.n, self.cols, self.icon, self.cell, self.c = n, cols, icon_name, cell, color
        self.lf, self.tl, self.lc, self.stg, self.tin = lost_from, t_lost, lost_color, stagger, t_in
    def draw(self, ctx, t):
        rows = math.ceil(self.n / self.cols)
        x0 = -(self.cols - 1) * self.cell / 2; y0 = -(rows - 1) * self.cell / 2
        for i in range(self.n):
            ti = i * self.tin
            if t < ti: continue
            a = min(1, (t - ti) / 0.1)
            col = self.c
            if self.lf is not None and i >= self.lf:
                tk = self.tl + (i - self.lf) * self.stg
                if t >= tk:
                    k = min(1, (t - tk) / 0.15); col = mix(self.c, self.lc, k)
            ctx.save(); ctx.translate(x0 + (i % self.cols) * self.cell, y0 + (i // self.cols) * self.cell)
            ctx.push_group(); icon(ctx, self.icon, self.cell * 0.42, col); ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
            ctx.restore()

class DimensionLine(UI):
    """Measuring line with end ticks that draws on from p0 to p1 (ease-out
    0.3 s) with a bold caps label above (and optional small sub-label).
    from_centre=True draws outward from the middle (house variant)."""
    def __init__(self, p0, p1, label='', sub=None, dur=0.3, from_centre=True, color=PAL.WHITE, size=40, tick=18, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw)
        self.p0, self.p1, self.label, self.sub, self.d, self.fc, self.c, self.size, self.tick = p0, p1, label, sub, dur, from_centre, color, size, tick
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / self.d))
        (x0, y0), (x1, y1) = self.p0, self.p1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if self.fc:
            a0 = (mx + (x0 - mx) * k, my + (y0 - my) * k); a1 = (mx + (x1 - mx) * k, my + (y1 - my) * k)
        else:
            a0 = (x0, y0); a1 = (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
        ang = math.atan2(y1 - y0, x1 - x0); nx, ny = -math.sin(ang), math.cos(ang)
        for (p, q) in ((a0, a1),):
            ctx.move_to(*p); ctx.line_to(*q)
        ctx.set_source_rgba(0, 0, 0, 0.35); ctx.set_line_width(5); ctx.stroke_preserve() if False else None
        ctx.move_to(*a0); ctx.line_to(*a1); set_col(ctx, self.c); ctx.set_line_width(3); ctx.stroke()
        for p in (a0, a1):
            ctx.move_to(p[0] + nx * self.tick, p[1] + ny * self.tick); ctx.line_to(p[0] - nx * self.tick, p[1] - ny * self.tick)
        ctx.stroke()
        if self.label and k > 0.6:
            a = min(1, (k - 0.6) / 0.4)
            ctx.save(); ctx.translate(mx, my); ctx.rotate(ang if abs(ang) < math.pi / 2 else ang + math.pi)
            draw_text(ctx, self.label.upper(), 0, -22, 'xb', self.size, self.c, 0.04, 'center', alpha=a)
            if self.sub: draw_text(ctx, self.sub.upper(), 0, 40, 'bold', self.size * 0.48, PAL.GREY, 0.22, 'center', alpha=a)
            ctx.restore()

class Balance(UI):
    """Balance scale: tilt (deg, keyframable; + = right side down). left/right:
    callables f(ctx) drawing the pan contents, or text labels."""
    def __init__(self, tilt=0.0, left=None, right=None, width=640, color=PAL.WHITE, **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw); self.tilt, self.left, self.right, self.w, self.c = tilt, left, right, width, color
    def draw(self, ctx, t):
        a = math.radians(ev(self.tilt, t)); w = self.w / 2
        set_col(ctx, self.c); ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(0, 0); ctx.line_to(0, 330); ctx.stroke()
        ctx.move_to(-90, 330); ctx.line_to(90, 330); ctx.stroke()
        ctx.move_to(-28, 0); ctx.line_to(0, -40); ctx.line_to(28, 0); ctx.close_path(); ctx.fill()
        ends = [(-w * math.cos(a), -w * math.sin(a)), (w * math.cos(a), w * math.sin(a))]
        ctx.move_to(*ends[0]); ctx.line_to(*ends[1]); ctx.stroke()
        for (ex, ey), content in zip(ends, (self.left, self.right)):
            ctx.set_line_width(2.5)
            ctx.move_to(ex, ey); ctx.line_to(ex - 90, ey + 160); ctx.move_to(ex, ey); ctx.line_to(ex + 90, ey + 160); ctx.stroke()
            ctx.move_to(ex - 120, ey + 160); ctx.curve_to(ex - 80, ey + 200, ex + 80, ey + 200, ex + 120, ey + 160); ctx.close_path()
            set_col(ctx, self.c); ctx.fill()
            if content is not None:
                ctx.save(); ctx.translate(ex, ey + 150)
                if callable(content): content(ctx)
                else: draw_text(ctx, str(content).upper(), 0, -20, 'xb', 34, PAL.WHITE, 0.04, 'center')
                ctx.restore()
                set_col(ctx, self.c); ctx.set_line_width(6)

class Badge(UI):
    """Medallion: navy circle, thin white ring, icon; small black caption pill
    below. Pops with a small overshoot (0.25 s)."""
    def __init__(self, icon_name='question', caption=None, r=70, fill='#0E2A38', **kw):
        super().__init__(**kw); self.ic, self.cap, self.r, self.fill = icon_name, caption, r, fill
    def draw(self, ctx, t):
        s = ease('back', min(1, t / 0.25)); a = min(1, t / 0.08)
        ctx.save(); ctx.scale(s, s)
        circle(ctx, 0, 0, self.r); set_col(ctx, self.fill, a); ctx.fill_preserve(); set_col(ctx, PAL.WHITE, a); ctx.set_line_width(3); ctx.stroke()
        icon(ctx, self.ic, self.r * 0.55, PAL.WHITE)
        ctx.restore()
        if self.cap and t > 0.1:
            Pill(self.cap, 'dark', size=26, pos=(0, self.r + 36)).render(ctx, t - 0.1)

class ProgressBar(UI):
    """'TRANSLATING ORCA…' style progress bar filling to `to` over dur, optional CANCEL at t_cancel."""
    def __init__(self, label, to=0.97, dur=2.5, width=760, t_cancel=None, **kw):
        super().__init__(**kw); self.label, self.to, self.d, self.w, self.tc = label, to, dur, width, t_cancel
    def draw(self, ctx, t):
        draw_text(ctx, self.label.upper(), -self.w / 2, -30, 'bold', 24, PAL.WHITE, 0.22)
        rrect(ctx, -self.w / 2, 0, self.w, 34, 6); set_col(ctx, PAL.WHITE, 0.9); ctx.set_line_width(2.5); ctx.stroke()
        k = self.to * ease('eo', min(1, t / self.d))
        rrect(ctx, -self.w / 2 + 6, 6, (self.w - 12) * k, 22, 3); set_col(ctx, PAL.ORANGE); ctx.fill()
        draw_text(ctx, f'{int(k * 100)}%', self.w / 2, -30, 'xb', 26, PAL.WHITE, 0.02, 'right')
        if self.tc is not None and t >= self.tc:
            Stamp('CANCELLED', PAL.RED, 56, pos=(0, 17)).render(ctx, t - self.tc)

# ------------------------------------------------------------------ globe
_LAND = None
def _land():
    global _LAND
    if _LAND is None:
        p = os.path.join(os.path.dirname(__file__), 'data', 'land110.geojson')
        g = json.load(open(p)); polys = []
        for f in g['features']:
            geom = f['geometry']
            cs = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
            for poly_ in cs: polys.append(np.radians(np.array(poly_[0], float)))
        _LAND = polys
    return _LAND

_COUNTRIES = None
def _country(name):
    global _COUNTRIES
    if _COUNTRIES is None:
        p = os.path.join(os.path.dirname(__file__), 'data', 'countries110.geojson')
        _COUNTRIES = {}
        for f in json.load(open(p))['features']:
            geom = f['geometry']; cs = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
            ps = [np.radians(np.array(pp[0], float)) for pp in cs]
            for key in ('NAME', 'NAME_LONG', 'ADMIN', 'ISO_A3'):
                if f['properties'].get(key): _COUNTRIES[f['properties'][key].lower()] = ps
    return _COUNTRIES.get(name.lower(), [])

def _ortho(lonlat, lon0, lat0, R):
    lon, lat = lonlat[:, 0], lonlat[:, 1]
    cosc = math.sin(lat0) * np.sin(lat) + math.cos(lat0) * np.cos(lat) * np.cos(lon - lon0)
    x = R * np.cos(lat) * np.sin(lon - lon0)
    y = -R * (math.cos(lat0) * np.sin(lat) - math.sin(lat0) * np.cos(lat) * np.cos(lon - lon0))
    return x, y, cosc

def _gc(a, b, n=64):
    """Great-circle points between (lon,lat) degrees."""
    a, b = np.radians(a), np.radians(b)
    def v(p): return np.array([math.cos(p[1]) * math.cos(p[0]), math.cos(p[1]) * math.sin(p[0]), math.sin(p[1])])
    va, vb = v(a), v(b); om = math.acos(max(-1, min(1, va @ vb)))
    out = []
    for k in np.linspace(0, 1, n):
        if om < 1e-6: p = va
        else: p = (math.sin((1 - k) * om) * va + math.sin(k * om) * vb) / math.sin(om)
        out.append((math.atan2(p[1], p[0]), math.asin(p[2])))
    return np.array(out)

class Globe(UI):
    """Globe inset: ocean disc + land (Natural Earth 110m), highlighted countries
    in orange, red pins, dashed great-circle routes drawing on, white ring,
    tracked caption below. Rotates slowly (spin deg/s).
    center=(lon,lat) deg the view looks at; pins=[(lon,lat)]; routes=[[(lon,lat),...]]."""
    def __init__(self, center=(0, 20), radius=260, spin=2.0, highlight=None, pins=None, routes=None, caption=None,
                 t_route=0.3, route_dur=1.2, land='#4A8590', ocean=('#15435A', '#06202E'), **kw):
        kw.setdefault('layer', 'mid')
        super().__init__(**kw)
        self.c0, self.R, self.spin, self.hl = center, radius, spin, highlight or []
        self.pins, self.routes, self.cap, self.tr, self.rd = pins or [], routes or [], caption, t_route, route_dur
        self.land_c, self.ocean = land, ocean
    def draw(self, ctx, t):
        R = self.R
        lon0 = math.radians(self.c0[0] - self.spin * t); lat0 = math.radians(self.c0[1])
        rg = cairo.RadialGradient(-R * 0.3, -R * 0.35, R * 0.1, 0, 0, R)
        rg.add_color_stop_rgba(0, *hexc(self.ocean[0])); rg.add_color_stop_rgba(1, *hexc(self.ocean[1]))
        circle(ctx, 0, 0, R); ctx.set_source(rg); ctx.fill()
        ctx.save(); circle(ctx, 0, 0, R); ctx.clip()
        def draw_polys(polys, col):
            for p in polys:
                x, y, c = _ortho(p, lon0, lat0, R)
                if (c > 0).sum() < 2: continue
                # clamp back-facing points to the limb for a clean edge
                m = c <= 0
                if m.any():
                    nrm = np.hypot(x, y) + 1e-9
                    x = np.where(m, x / nrm * R, x); y = np.where(m, y / nrm * R, y)
                ctx.move_to(x[0], y[0])
                for xx, yy in zip(x[1:], y[1:]): ctx.line_to(xx, yy)
                ctx.close_path()
            set_col(ctx, col); ctx.fill()
        draw_polys(_land(), self.land_c)
        for name in self.hl: draw_polys(_country(name), PAL.ORANGE)
        # graticule
        ctx.set_source_rgba(1, 1, 1, 0.06); ctx.set_line_width(1.2)
        for lo in range(-180, 180, 30):
            pts = np.radians(np.array([(lo, la) for la in range(-90, 91, 5)], float)); x, y, c = _ortho(pts, lon0, lat0, R)
            first = True
            for xx, yy, cc in zip(x, y, c):
                if cc > 0:
                    (ctx.move_to if first else ctx.line_to)(xx, yy); first = False
                else: first = True
            ctx.stroke()
        # shading
        rg = cairo.RadialGradient(-R * 0.35, -R * 0.4, 0, 0, 0, R * 1.05)
        rg.add_color_stop_rgba(0, 1, 1, 1, 0.10); rg.add_color_stop_rgba(0.6, 0, 0, 0, 0); rg.add_color_stop_rgba(1, 0, 0, 0, 0.45)
        ctx.set_source(rg); ctx.paint()
        ctx.restore()
        # routes
        for ri, route in enumerate(self.routes):
            pts = np.vstack([_gc(route[i], route[i + 1]) for i in range(len(route) - 1)])
            k = ease('eo', min(1, max(0, (t - self.tr - ri * 0.3) / self.rd)))
            n = max(2, int(len(pts) * k))
            x, y, c = _ortho(pts[:n], lon0, lat0, R)
            ctx.set_dash([10, 8])
            first = True
            for xx, yy, cc in zip(x, y, c):
                if cc > 0: (ctx.move_to if first else ctx.line_to)(xx, yy); first = False
                else: first = True
            set_col(ctx, PAL.WHITE); ctx.set_line_width(3.2); ctx.stroke(); ctx.set_dash([])
            if k > 0 and c[-1] > 0:
                circle(ctx, x[-1], y[-1], 7); set_col(ctx, PAL.WHITE); ctx.fill()
        # pins
        for (lo, la) in self.pins:
            x, y, c = _ortho(np.radians(np.array([[lo, la]], float)), lon0, lat0, R)
            if c[0] <= 0: continue
            pulse = (t % 1.2) / 1.2
            circle(ctx, x[0], y[0], 10 + 26 * pulse); set_col(ctx, PAL.RED, 0.6 * (1 - pulse)); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, x[0], y[0], 11); set_col(ctx, PAL.RED); ctx.fill_preserve(); set_col(ctx, PAL.WHITE); ctx.set_line_width(3); ctx.stroke()
        circle(ctx, 0, 0, R); set_col(ctx, PAL.WHITE, 0.9); ctx.set_line_width(3); ctx.stroke()
        if self.cap:
            draw_text(ctx, self.cap.upper(), 0, R + 64, 'bold', 28, PAL.WHITE, 0.24, 'center')

# ------------------------------------------------------------------ polaroid
class Polaroid(UI):
    """Polaroid/photo card: white frame with thick bottom strip, content drawn by
    `content(ctx, t, w, h)` (or an Element rendered inside), marker caption,
    translucent tape strip, soft shadow. Slides in from `from_off` (0.35 s ease-out)."""
    def __init__(self, content=None, caption='', w=420, h=360, tape=True, from_off=(260, 220), angle=5,
                 bg='#1E5566', **kw):
        kw.setdefault('rot', angle)
        super().__init__(**kw)
        self.content, self.cap, self.w, self.h, self.tape, self.off, self.bg = content, caption, w, h, tape, from_off, bg
    def draw(self, ctx, t):
        k = ease('eo', min(1, t / 0.35))
        ctx.save(); ctx.translate(self.off[0] * (1 - k), self.off[1] * (1 - k))
        w, h = self.w, self.h; m = 22; bot = 92
        W_, H_ = w + 2 * m, h + m + bot
        rrect(ctx, -W_ / 2 + 8, -H_ / 2 + 14, W_, H_, 4); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.fill()
        rrect(ctx, -W_ / 2, -H_ / 2, W_, H_, 4); set_col(ctx, '#F6F4EE'); ctx.fill()
        x0, y0 = -w / 2, -H_ / 2 + m
        ctx.save(); ctx.rectangle(x0, y0, w, h); ctx.clip()
        set_col(ctx, self.bg); ctx.paint()
        if self.content is not None:
            ctx.translate(x0, y0)
            if isinstance(self.content, Element): self.content.render(ctx, t)
            else: self.content(ctx, t, w, h)
        ctx.restore()
        ctx.rectangle(x0, y0, w, h); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.set_line_width(2); ctx.stroke()
        if self.cap:
            draw_text(ctx, self.cap.upper(), 0, H_ / 2 - bot / 2 + 16, 'marker', 40, '#2A2F30', 0.0, 'center', shadow=False)
        if self.tape:
            ctx.save(); ctx.translate(0, -H_ / 2); ctx.rotate(-0.08)
            rrect(ctx, -70, -20, 140, 40, 2); ctx.set_source_rgba(0.93, 0.89, 0.76, 0.75); ctx.fill()
            ctx.restore()
        ctx.restore()

# ------------------------------------------------------------------ misc helpers
class Dim(UI):
    """Full-frame darkening (focus pull for overlays)."""
    def __init__(self, alpha=0.45, dur=0.2, **kw):
        super().__init__(**kw); self.a, self.d = alpha, dur
    def draw(self, ctx, t):
        ctx.set_source_rgba(0, 0, 0, self.a * min(1, t / self.d)); ctx.rectangle(0, 0, W, H); ctx.fill()
