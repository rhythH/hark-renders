"""Effects: impact, bubbles, sonar rings, splash crown, flash, speed lines.

impact(shot, t, pos, amp=14) adds the full house impact in one call:
  white frame fading over 5–6 frames (overlay) + expanding ring + debris and
  bubbles (world, 'fg') + decaying camera shake ±amp px over 0.4 s.
"""
import math
from .core import Element, Fn, ev, set_col, hexc, circle, TAU, W, H, rng, remap, ease

class Ring(Element):
    """Expanding ring: radius r0->r1 over dur, fading."""
    def __init__(self, r0=10, r1=260, dur=0.45, width=10, color='#FFFFFF', squash=1.0, **kw):
        super().__init__(**kw); self.r0, self.r1, self.d, self.wd, self.c, self.sq = r0, r1, dur, width, color, squash
    def draw(self, ctx, t):
        if t > self.d: return
        k = ease('eo', t / self.d)
        r = self.r0 + (self.r1 - self.r0) * k
        ctx.save(); ctx.scale(1, self.sq); circle(ctx, 0, 0, r); ctx.restore()
        set_col(ctx, self.c, (1 - k) ** 1.2); ctx.set_line_width(self.wd * (1 - k * 0.7)); ctx.stroke()

class Debris(Element):
    """Burst of shards + bubbles flying out with drag and gravity (underwater: low gravity, bubbles rise)."""
    def __init__(self, n=26, speed=520, dur=1.4, color='#E9EEF0', bubbles=14, gravity=320, seed=3, shards=True, **kw):
        super().__init__(**kw)
        r = rng(seed)
        self.p = [(r.uniform(0, TAU), r.uniform(0.35, 1.0) * speed, r.uniform(4, 12), r.uniform(-8, 8)) for _ in range(n if shards else 0)]
        self.b = [(r.uniform(-2.6, -0.5), r.uniform(0.3, 1.0) * speed * 0.7, r.uniform(4, 14), r.random()) for _ in range(bubbles)]
        self.d, self.c, self.g = dur, color, gravity
    def draw(self, ctx, t):
        if t > self.d: return
        f = 1 - t / self.d
        drag = (1 - math.exp(-3.0 * t)) / 3.0
        for (a, v, s, spin) in self.p:
            x = math.cos(a) * v * drag; y = math.sin(a) * v * drag + 0.5 * self.g * t * t
            ctx.save(); ctx.translate(x, y); ctx.rotate(spin * t)
            ctx.move_to(-s, -s * 0.4); ctx.line_to(s, -s * 0.2); ctx.line_to(s * 0.2, s * 0.6); ctx.close_path()
            set_col(ctx, self.c, f); ctx.fill(); ctx.restore()
        for (a, v, s, ph) in self.b:
            x = math.cos(a) * v * drag + 6 * math.sin(t * 9 + ph * 6); y = math.sin(a) * v * drag - 90 * t * t
            circle(ctx, x, y, s * (0.7 + 0.3 * t))
            ctx.set_source_rgba(0.88, 0.96, 1, 0.85 * f); ctx.set_line_width(2.2); ctx.stroke()

class Bubbles(Element):
    """Continuous rising bubbles from a source (width = spread). rate per second."""
    def __init__(self, rate=6, spread=40, rise=150, life=2.5, size=(3, 10), seed=1, color=(0.88, 0.96, 1.0), **kw):
        super().__init__(**kw); self.rate, self.spread, self.rise, self.life, self.size, self.seed, self.col = rate, spread, rise, life, size, seed, color
    def draw(self, ctx, t):
        n0 = int((t - self.life) * self.rate) - 1; n1 = int(t * self.rate) + 1
        for i in range(max(0, n0), n1):
            t_b = i / self.rate
            age = t - t_b
            if age < 0 or age > self.life: continue
            r = rng(self.seed * 1000 + i)
            x = r.uniform(-self.spread, self.spread) + 8 * math.sin(age * 5 + r.random() * 6)
            y = -age * self.rise * r.uniform(0.7, 1.2)
            s = r.uniform(*self.size)
            a = min(1, age * 4) * (1 - age / self.life)
            circle(ctx, x, y, s); ctx.set_source_rgba(*self.col, 0.75 * a); ctx.set_line_width(2); ctx.stroke()
            circle(ctx, x - s * 0.35, y - s * 0.35, s * 0.22); ctx.set_source_rgba(*self.col, 0.6 * a); ctx.fill()

class SonarRings(Element):
    """Echolocation rings from a point: loop period (1.2 s), n rings, max radius.
    direction: None = full circles, or angle (deg) for a forward cone of arcs."""
    def __init__(self, period=1.2, n=3, rmax=420, color='#B6E8F3', width=4, direction=None, spread=50, **kw):
        super().__init__(**kw); self.p, self.n, self.rm, self.c, self.wd, self.dir, self.sp = period, n, rmax, color, width, direction, spread
    def draw(self, ctx, t):
        for i in range(self.n):
            k = ((t / self.p) + i / self.n) % 1.0
            r = 20 + k * self.rm
            if self.dir is None:
                circle(ctx, 0, 0, r)
            else:
                a = math.radians(self.dir); s = math.radians(self.sp / 2)
                ctx.new_sub_path(); ctx.arc(0, 0, r, a - s, a + s)
            set_col(ctx, self.c, (1 - k) ** 1.3 * 0.9); ctx.set_line_width(self.wd); ctx.stroke()

class Splash(Element):
    """Surface splash crown (white blobs + droplets) erupting at t=0; size in units."""
    def __init__(self, size=300, dur=1.6, seed=2, **kw):
        super().__init__(**kw); self.s, self.d = size, dur
        r = rng(seed)
        self.drops = [(r.uniform(-1, 1), r.uniform(0.5, 1.2), r.uniform(5, 14)) for _ in range(40)]
        self.spikes = [(r.uniform(-1, 1), r.uniform(0.5, 1.0), r.uniform(0.08, 0.18)) for _ in range(12)]
    def draw(self, ctx, t):
        if t > self.d or t < 0: return
        s = self.s; k = t / self.d
        rise = math.sin(min(1, k * 1.6) * math.pi) * s
        for (x, h, w) in self.spikes:
            hh = rise * h
            if hh <= 1: continue
            cx = x * s * 0.8
            ctx.move_to(cx - w * s, 0); ctx.curve_to(cx - w * s * 0.4, -hh * 0.5, cx - w * s * 0.1, -hh * 0.9, cx, -hh)
            ctx.curve_to(cx + w * s * 0.1, -hh * 0.9, cx + w * s * 0.4, -hh * 0.5, cx + w * s, 0); ctx.close_path()
            ctx.set_source_rgba(0.96, 0.98, 1, 0.85 * (1 - k)); ctx.fill()
        ctx.save(); ctx.scale(1, 0.22); circle(ctx, 0, 0, s * (0.6 + 0.6 * k)); ctx.restore()
        ctx.set_source_rgba(0.96, 0.98, 1, 0.6 * (1 - k)); ctx.fill()
        for (vx, vy, r) in self.drops:
            x = vx * s * 1.4 * k * 1.6; y = -vy * s * 2.2 * t + 0.5 * 1800 * t * t
            if y > 10: continue
            circle(ctx, x, y, r * (1 - k * 0.5)); ctx.set_source_rgba(0.96, 0.98, 1, 0.9 * (1 - k)); ctx.fill()

class SpeedLines(Element):
    def __init__(self, n=14, length=300, angle=0, spread=500, color='#FFFFFF', **kw):
        super().__init__(**kw); self.n, self.L, self.a, self.sp, self.c = n, length, angle, spread, color
    def draw(self, ctx, t):
        r = rng(4)
        ca, sa = math.cos(math.radians(self.a)), math.sin(math.radians(self.a))
        for i in range(self.n):
            off = r.uniform(-self.sp, self.sp); ph = r.random()
            k = (t * 3 + ph) % 1
            x0 = -self.L * 2 + k * self.L * 4
            ctx.move_to(ca * x0 - sa * off, sa * x0 + ca * off)
            ctx.line_to(ca * (x0 + self.L) - sa * off, sa * (x0 + self.L) + ca * off)
            set_col(ctx, self.c, 0.35 * math.sin(k * math.pi)); ctx.set_line_width(3); ctx.stroke()

def white_flash(t_hit, frames=6, fps=30, alpha=1.0):
    """Overlay element: one white frame fading out over `frames` frames."""
    d = frames / fps
    def fn(ctx, lt):
        k = 1 - lt / d
        if k > 0:
            ctx.set_source_rgba(1, 1, 1, alpha * k ** 1.3); ctx.rectangle(-60, -60, W + 120, H + 120); ctx.fill()
    return Fn(fn, t0=t_hit, t1=t_hit + d, layer='overlay', z=50)

def impact(shot, t, pos, amp=14, ring=True, debris=True, flash=True, color='#FFFFFF', bubbles=14, gravity=320, scale=1.0):
    """House impact: flash (5–6 frames) + ring + debris/bubbles + decaying shake."""
    els = []
    if flash: els.append(shot.add(white_flash(t, 6, alpha=0.9)))
    if ring:
        els.append(shot.add(Ring(pos=pos, t0=t, r0=20 * scale, r1=300 * scale, dur=0.45, width=12 * scale, color=color, layer='fg')))
        els.append(shot.add(Ring(pos=pos, t0=t + 0.06, r0=10 * scale, r1=180 * scale, dur=0.4, width=6 * scale, color=color, layer='fg')))
    if debris: els.append(shot.add(Debris(pos=pos, t0=t, bubbles=bubbles, gravity=gravity, scale=scale, layer='fg')))
    shot.camera.shake(t, amp=amp, decay=0.4)
    return els
