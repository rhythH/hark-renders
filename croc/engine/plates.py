"""Background plates. Each plate has draw_bg(ctx,t,cam) and draw_fg(ctx,t,cam).

Static pieces (gradients, rays, grids, vignettes, paper) are pre-rendered once
per output scale and cached; only cheap animated parts are drawn per frame.
"""
import math
import numpy as np
import cairocffi as cairo
from .core import W, H, TAU, hexc, mix, set_col, rng, circle, PAL, catmull, poly

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

def _dev_scale(ctx):
    return ctx.get_matrix()[0]

def _surf(s, margin=0.0):
    w = int(round(W * s * (1 + 2 * margin))); h = int(round(H * s * (1 + 2 * margin)))
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

def _blur_surface(surf, sigma):
    """Gaussian-blur an ARGB32 surface in place (premultiplied, so blur all 4 channels)."""
    if cv2 is None or sigma <= 0: return surf
    surf.flush()
    w, h, st = surf.get_width(), surf.get_height(), surf.get_stride()
    a = np.ndarray((h, st // 4, 4), np.uint8, buffer=surf.get_data())
    b = cv2.GaussianBlur(a[:, :w].copy(), (0, 0), sigma)
    a[:, :w] = b
    surf.mark_dirty()
    return surf

class Plate:
    parallax = 0.35
    margin = 0.08
    def __init__(self):
        self._cache = {}

    def cached(self, key, s, builder, margin=None):
        m = self.margin if margin is None else margin
        k = (key, round(s, 4))
        if k not in self._cache:
            surf = _surf(s, m)
            c = cairo.Context(surf)
            c.translate(W * s * m, H * s * m); c.scale(s, s)
            builder(c, s)
            self._cache[k] = (surf, m)
        return self._cache[k]

    def paint_cached(self, ctx, key, builder, cam=None, t=0, parallax=None, alpha=1.0, margin=None):
        """Paint a cached full-frame layer, moved by the camera at `parallax`."""
        s = _dev_scale(ctx)
        surf, m = self.cached(key, s, builder, margin)
        ctx.save()
        if cam is not None and (parallax if parallax is not None else self.parallax) > 0:
            cam.apply(ctx, t, self.parallax if parallax is None else parallax)
        ctx.translate(-W * m, -H * m)
        ctx.scale(1 / s, 1 / s)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
        if alpha >= 0.999: ctx.paint()
        else: ctx.paint_with_alpha(alpha)
        ctx.restore()

    def draw_bg(self, ctx, t, cam): pass
    def draw_fg(self, ctx, t, cam): pass

# --------------------------------------------------------------------------- shared pieces
def vignette_builder(strength=0.45, color='#000000', inner=0.35, outer=0.95, aspect=1.0):
    def b(c, s):
        cx, cy = W / 2, H / 2
        c.save(); c.translate(cx, cy); c.scale(1.0, (H / W) * aspect)
        R = W * 0.62
        g = cairo.RadialGradient(0, 0, R * inner, 0, 0, R * outer)
        col = hexc(color)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], 0)
        g.add_color_stop_rgba(0.55, col[0], col[1], col[2], strength * 0.35)
        g.add_color_stop_rgba(1, col[0], col[1], col[2], strength)
        c.set_source(g); c.rectangle(-W, -H * 2, W * 2, H * 4); c.fill(); c.restore()
    return b

class Particles:
    """Drifting specks + soft discs, three depth bins with camera parallax."""
    def __init__(self, n_specks=120, n_discs=18, seed=7, color='#BFE3EE', drift=(3, -4),
                 alpha=0.55, region=(0, 0, W, H), disc_alpha=0.10):
        r = rng(seed)
        x0, y0, x1, y1 = region
        self.region = region
        self.sp = [(r.uniform(x0 - 100, x1 + 100), r.uniform(y0 - 60, y1 + 60), r.uniform(1.2, 4.5) / 2,
                    r.choice([0.6, 1.0, 1.35]), r.uniform(0.25, 1.0), r.random() * TAU) for _ in range(n_specks)]
        self.ds = [(r.uniform(x0 - 100, x1 + 100), r.uniform(y0, y1), r.uniform(7, 13),
                    r.choice([0.6, 1.0, 1.35]), r.uniform(0.4, 1.0), r.random() * TAU) for _ in range(n_discs)]
        self.color, self.drift, self.alpha, self.disc_alpha = color, drift, alpha, disc_alpha

    def draw(self, ctx, t, cam):
        c = hexc(self.color)
        x0, y0, x1, y1 = self.region
        ww, hh = (x1 - x0) + 200, (y1 - y0) + 120
        for depth in (0.6, 1.0, 1.35):
            ctx.save()
            if cam is not None: cam.apply(ctx, t, depth)
            for (x, y, r, d, a, ph) in self.sp:
                if d != depth: continue
                px = x0 - 100 + ((x - x0 + 100) + self.drift[0] * d * t + 3 * math.sin(t * 0.5 + ph)) % ww
                py = y0 - 60 + ((y - y0 + 60) + self.drift[1] * d * t) % hh
                tw = 0.75 + 0.25 * math.sin(t * 1.3 + ph * 3)
                ctx.set_source_rgba(c[0], c[1], c[2], self.alpha * a * tw)
                circle(ctx, px, py, r * d); ctx.fill()
            for (x, y, r, d, a, ph) in self.ds:
                if d != depth: continue
                px = x0 - 100 + ((x - x0 + 100) + self.drift[0] * 0.7 * d * t + 6 * math.sin(t * 0.3 + ph)) % ww
                py = y0 + ((y - y0) + self.drift[1] * 0.6 * d * t) % (y1 - y0)
                rr = r * d
                g = cairo.RadialGradient(px, py, 0, px, py, rr)
                g.add_color_stop_rgba(0, c[0], c[1], c[2], self.disc_alpha * a)
                g.add_color_stop_rgba(0.6, c[0], c[1], c[2], self.disc_alpha * a * 0.5)
                g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
                ctx.set_source(g); circle(ctx, px, py, rr); ctx.fill()
            ctx.restore()

def rays_builder(kind='soft', seed=3, n=9, alpha=0.12, src=(W * 0.5, -900), spread=46, fade=0.75,
                 subset=0, color='#DFF4FA', region_h=H):
    """God rays. kind 'soft' = v2 fan from top centre (blurred);
    'hard' = v1 hard-edged wedges from top-left, 6–18° off vertical."""
    def b(c, s):
        r = rng(seed + subset * 101)
        col = hexc(color)
        c.save()
        for i in range(n):
            if kind == 'soft':
                ang = math.radians(-spread / 2 + spread * (i + r.uniform(-0.3, 0.3)) / max(1, n - 1))
                wdt = math.radians(r.uniform(1.2, 2.6))
                sx, sy = src[0] + r.uniform(-260, 260), src[1]
            else:
                ang = math.radians(r.uniform(6, 18)) * -1
                wdt = math.radians(r.uniform(1.4, 3.6))
                sx, sy = r.uniform(-300, W * 0.9), -60
            L = region_h * 2.6
            a = alpha * r.uniform(0.45, 1.0)
            p1 = (sx + math.sin(ang - wdt) * L, sy + math.cos(ang - wdt) * L)
            p2 = (sx + math.sin(ang + wdt) * L, sy + math.cos(ang + wdt) * L)
            g = cairo.LinearGradient(0, max(0, sy) if kind != 'soft' else 0, 0, region_h * fade)
            g.add_color_stop_rgba(0, col[0], col[1], col[2], a)
            g.add_color_stop_rgba(0.55, col[0], col[1], col[2], a * 0.5)
            g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
            c.set_source(g)
            c.move_to(sx, sy); c.line_to(*p1); c.line_to(*p2); c.close_path(); c.fill()
        c.restore()
        if kind == 'soft':
            _blur_surface(c.get_target(), 22 * s)
        else:
            _blur_surface(c.get_target(), 1.2 * s)
    return b

# --------------------------------------------------------------------------- underwater
class Underwater(Plate):
    """Open-water plate: gradient x oval vignette + god rays + particles.

    style 'v2' (humpback: soft fan, radial #166F85->#062F3D) or 'v1' (sperm:
    hard wedges, #4189A2->#1A566B->#021319). depth 0..1 darkens (0 shallow,
    1 abyss). surface=True draws the faint surface lines at the very top.
    """
    def __init__(self, style='v2', depth=0.3, rays=True, particles=True, surface=False,
                 vignette=0.42, seed=1, tint=None):
        super().__init__()
        self.style, self.depth, self.rays, self.surface, self.vig = style, depth, rays, surface, vignette
        if style == 'v1':
            top, mid, bot = '#4189A2', '#1A566B', '#021319'
        else:
            top, mid, bot = '#3C7590', '#164862', '#031A29'
        d = depth
        self.top = mix(top, '#03141B', d * 0.75); self.mid = mix(mid, '#020D12', d * 0.7)
        self.bot = mix(bot, '#000608', d * 0.6)
        if tint: self.top, self.mid, self.bot = [mix(c, tint, 0.35) for c in (self.top, self.mid, self.bot)]
        self.seed = seed
        self.parts = Particles(seed=seed + 5, alpha=0.5 * (1 - d * 0.5)) if particles else None

    def _base(self, c, s):
        g = cairo.LinearGradient(0, -H * 0.1, 0, H * 1.1)
        g.add_color_stop_rgba(0, *self.top); g.add_color_stop_rgba(0.5, *self.mid); g.add_color_stop_rgba(1, *self.bot)
        c.set_source(g); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        # light pool from the surface, top centre
        lc = mix(self.top, '#BFE7F2', 0.35)
        c.save(); c.translate(W * 0.5, -H * 0.15); c.scale(1.6, 1.0)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, H * 0.95)
        rg.add_color_stop_rgba(0, lc[0], lc[1], lc[2], 0.38 * (1 - self.depth))
        rg.add_color_stop_rgba(1, lc[0], lc[1], lc[2], 0)
        c.set_source(rg); c.rectangle(-W, -H, W * 2, H * 3); c.fill(); c.restore()
        if self.surface:
            r = rng(self.seed)
            for i in range(26):
                y = r.uniform(4, 60); x = r.uniform(-100, W)
                c.set_source_rgba(0.85, 0.95, 1, 0.10 + 0.08 * r.random()); c.set_line_width(1.6)
                c.move_to(x, y)
                c.curve_to(x + 60, y - 6, x + 120, y + 6, x + r.uniform(160, 340), y)
                c.stroke()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
        if self.rays:
            kind = 'hard' if self.style == 'v1' else 'soft'
            a1 = 0.6 + 0.4 * math.sin(t * 0.45)
            a2 = 0.6 + 0.4 * math.sin(t * 0.45 + 2.2)
            amp = (1 - self.depth * 0.8)
            for sub, a in ((0, a1), (1, a2)):
                ctx.save()
                sway = math.radians(0.5 * math.sin(t * 0.21 + sub))
                ctx.translate(W / 2, -200); ctx.rotate(sway); ctx.translate(-W / 2, 200)
                self.paint_cached(ctx, ('rays', kind, sub),
                                  rays_builder(kind, self.seed, n=7 if kind == 'soft' else 7, subset=sub,
                                               alpha=0.13 if kind == 'soft' else 0.11), cam, t, alpha=a * amp)
                ctx.restore()
        if self.parts: self.parts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#00070A'), None, t, parallax=0, margin=0)

class Abyss(Underwater):
    """Near-black deep water with sparse particles."""
    def __init__(self, **kw):
        kw.setdefault('depth', 0.95); kw.setdefault('rays', False)
        super().__init__(**kw)

# --------------------------------------------------------------------------- flat/graphic worlds
class Board(Plate):
    """Blueprint data board: #0B2530, grid ~49 px one shade lighter, white corner
    brackets (2 px, inset 18 px, arms 60 px). Optional tint variants: 'teal'
    (default), 'maroon', 'indigo', 'sepia'."""
    TINTS = {'teal': ('#0B2530', '#173E4B', '#071820'),
             'maroon': ('#2A0D10', '#3A171A', '#160507'),
             'indigo': ('#121a33', '#1c2647', '#090d1c'),
             'sepia': ('#1A140F', '#261E17', '#0C0905')}
    parallax = 0.15
    def __init__(self, tint='teal', grid=49, brackets=True, particles=False, vignette=0.35):
        super().__init__()
        self.base, self.line, self.dark = self.TINTS[tint]
        self.grid, self.brackets, self.vig = grid, brackets, vignette
        self.parts = Particles(n_specks=40, n_discs=6, alpha=0.25) if particles else None

    def _base(self, c, s):
        b = hexc(self.base); d = hexc(self.dark)
        rg = cairo.RadialGradient(W / 2, H * 0.45, 0, W / 2, H * 0.45, W * 0.75)
        lc = mix(self.base, '#ffffff', 0.025)
        rg.add_color_stop_rgba(0, *lc); rg.add_color_stop_rgba(0.6, *b); rg.add_color_stop_rgba(1, *d)
        c.set_source(rg); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        set_col(c, self.line, 1.0); c.set_line_width(1.0)
        g = self.grid
        x = W / 2 - g * 30
        while x < W * 1.2:
            c.move_to(x, -H * 0.2); c.line_to(x, H * 1.2); x += g
        y = H / 2 - g * 20
        while y < H * 1.2:
            c.move_to(-W * 0.2, y); c.line_to(W * 1.2, y); y += g
        c.stroke()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
        if self.parts: self.parts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#000000'), None, t, parallax=0, margin=0)
        if self.brackets: corner_brackets(ctx)

def corner_brackets(ctx, inset=18, arm=60, width=2.0, alpha=0.85, color='#F2F0EB', box=(0, 0, W, H)):
    x0, y0, x1, y1 = box
    set_col(ctx, color, alpha); ctx.set_line_width(width); ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
    i, a = inset, arm
    for (cx, cy, sx, sy) in ((x0 + i, y0 + i, 1, 1), (x1 - i, y0 + i, -1, 1), (x0 + i, y1 - i, 1, -1), (x1 - i, y1 - i, -1, -1)):
        ctx.move_to(cx, cy + sy * a); ctx.line_to(cx, cy); ctx.line_to(cx + sx * a, cy)
    ctx.stroke()

class Black(Plate):
    parallax = 0.0
    def __init__(self, color='#000203', particles=False, vignette=0.6):
        super().__init__(); self.color = color; self.vig = vignette
        self.parts = Particles(n_specks=50, n_discs=8, alpha=0.18, color='#7FA9B5') if particles else None
    def draw_bg(self, ctx, t, cam):
        set_col(ctx, self.color); ctx.paint()
        if self.parts: self.parts.draw(ctx, t, cam)
    def draw_fg(self, ctx, t, cam):
        if self.vig: self.paint_cached(ctx, 'vig', vignette_builder(self.vig), None, t, parallax=0, margin=0)

class Danger(Plate):
    """Deep red/maroon danger plate (optional grid)."""
    def __init__(self, grid=False, vignette=0.55):
        super().__init__(); self.grid = grid; self.vig = vignette
        self.parts = Particles(n_specks=50, n_discs=8, alpha=0.22, color='#F0A0A0')
    def _base(self, c, s):
        rg = cairo.RadialGradient(W / 2, H * 0.42, 0, W / 2, H * 0.42, W * 0.7)
        rg.add_color_stop_rgba(0, *hexc('#5A1418')); rg.add_color_stop_rgba(0.6, *hexc('#2E0A0D'))
        rg.add_color_stop_rgba(1, *hexc('#120305'))
        c.set_source(rg); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        if self.grid:
            c.set_source_rgba(1, 0.5, 0.5, 0.06); c.set_line_width(1)
            for x in range(-200, W + 200, 49): c.move_to(x, -200); c.line_to(x, H + 200)
            for y in range(-200, H + 200, 49): c.move_to(-200, y); c.line_to(W + 200, y)
            c.stroke()
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t); self.parts.draw(ctx, t, cam)
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig), None, t, parallax=0, margin=0)

class Sepia(Plate):
    """Sepia paper (history, maps): cream paper with painted speckle + fibres,
    warm vignette. dark=True gives the dark sepia grid world instead."""
    parallax = 0.2
    def __init__(self, dark=False, grid=False):
        super().__init__(); self.dark = dark; self.grid = grid
    def _base(self, c, s):
        if self.dark:
            Board('sepia')._base(c, s); return
        rg = cairo.RadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.7)
        rg.add_color_stop_rgba(0, *hexc('#F1E8D0')); rg.add_color_stop_rgba(0.7, *hexc('#E3D5B3'))
        rg.add_color_stop_rgba(1, *hexc('#B99E70'))
        c.set_source(rg); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        r = rng(11)
        for _ in range(2600):   # speckle
            x, y = r.uniform(-150, W + 150), r.uniform(-100, H + 100)
            c.set_source_rgba(0.35, 0.25, 0.12, r.uniform(0.03, 0.10)); circle(c, x, y, r.uniform(0.5, 1.8)); c.fill()
        c.set_line_width(0.8)
        for _ in range(260):    # fibres
            x, y = r.uniform(-150, W + 150), r.uniform(-100, H + 100); a = r.uniform(0, TAU); L = r.uniform(8, 30)
            c.set_source_rgba(0.45, 0.33, 0.18, 0.07)
            c.move_to(x, y); c.curve_to(x + math.cos(a) * L * 0.3, y + math.sin(a) * L * 0.6, x + math.cos(a + 0.4) * L * 0.6,
                                        y + math.sin(a + 0.3) * L * 0.6, x + math.cos(a) * L, y + math.sin(a) * L); c.stroke()
        if self.grid:
            c.set_source_rgba(0.3, 0.22, 0.1, 0.10); c.set_line_width(1)
            for x in range(-200, W + 200, 49): c.move_to(x, -200); c.line_to(x, H + 200)
            for y in range(-200, H + 200, 49): c.move_to(-200, y); c.line_to(W + 200, y)
            c.stroke()
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(0.35, '#3A2410'), None, t, parallax=0, margin=0)

# --------------------------------------------------------------------------- surface cross-section
class Surface(Plate):
    """Surface cross-section: sky gradient + sun glow + horizon, animated
    waterline (thin white wave), water below with soft rays and particles.

    preset: 'day' (pale blue sky), 'haze' (misty grey), 'dawn' (peach),
            'storm' (dark grey).  waterline: y of mean water level.
    The plate is drawn at parallax 1.0 so props on 'mid' stay locked to it.
    Use water_y(x, t) to sit boats on the waves.
    """
    parallax = 1.0
    margin = 0.12
    PRESETS = {
        'day':   dict(sky=('#8FB8D4', '#C5DCE4', '#DCE6E0'), sun='#FFF3D6', sea=('#3E8C99', '#1F5E6E', '#0A2A33'), far='#5C8F98'),
        'haze':  dict(sky=('#AEBFC0', '#C9D4CF', '#D7DCD4'), sun='#FBF4DF', sea=('#457473', '#1D4A4F', '#0A252A'), far='#6E8B88'),
        'dawn':  dict(sky=('#E7A68A', '#F2C6A4', '#F7E1C5'), sun='#FFF0D0', sea=('#4D6F78', '#22424D', '#0B1E26'), far='#8C7F7E'),
        'storm': dict(sky=('#4A555C', '#66717A', '#7D878C'), sun='#B9C2C4', sea=('#2D4F57', '#173138', '#071418'), far='#3D4E53'),
    }
    def __init__(self, preset='day', waterline=620, sun=(0.62, 0.18), wave_amp=5, rays=True,
                 mountains=False, particles=True, vignette=0.28, seed=2):
        super().__init__()
        self.p = self.PRESETS[preset]; self.wl = waterline; self.sun = sun
        self.wave_amp, self.rays, self.mountains, self.vig, self.seed = wave_amp, rays, mountains, vignette, seed
        self.parts = Particles(n_specks=70, n_discs=10, alpha=0.4, region=(0, waterline + 20, W, H)) if particles else None

    def water_y(self, x, t):
        a = self.wave_amp
        return self.wl + a * math.sin(x * 0.006 + t * 1.3) + a * 0.5 * math.sin(x * 0.017 - t * 1.9 + 1.0)

    def _sky(self, c, s):
        p = self.p; wl = self.wl
        g = cairo.LinearGradient(0, -H * 0.15, 0, wl)
        g.add_color_stop_rgba(0, *hexc(p['sky'][0])); g.add_color_stop_rgba(0.6, *hexc(p['sky'][1]))
        g.add_color_stop_rgba(1, *hexc(p['sky'][2]))
        c.set_source(g); c.rectangle(-W, -H, W * 3, wl + H + 40); c.fill()
        sx, sy = self.sun[0] * W, self.sun[1] * H
        sc = hexc(p['sun'])
        rg = cairo.RadialGradient(sx, sy, 0, sx, sy, H * 0.55)
        rg.add_color_stop_rgba(0, sc[0], sc[1], sc[2], 0.85); rg.add_color_stop_rgba(0.25, sc[0], sc[1], sc[2], 0.35)
        rg.add_color_stop_rgba(1, sc[0], sc[1], sc[2], 0)
        c.set_source(rg); c.rectangle(-W, -H, W * 3, wl + H); c.fill()
        if self.mountains:
            r = rng(self.seed)
            for layer, (col, base, amp) in enumerate((('#8A9C9C', wl - 6, 90), ('#6F8483', wl - 2, 55))):
                pts = [(-300, wl + 5)]
                x = -300
                while x < W + 300:
                    pts.append((x, base - amp * (0.3 + 0.7 * r.random()))); x += r.uniform(90, 220)
                pts.append((W + 300, wl + 5))
                sm = catmull(pts[1:-1], 8)
                c.move_to(-300, wl + 5)
                for px, py in sm: c.line_to(px, py)
                c.line_to(W + 300, wl + 5); c.close_path()
                set_col(c, mix(col, p['sky'][2], 0.25 - layer * 0.15)); c.fill()
        # distant sea band just under horizon
        set_col(c, p['far']); c.rectangle(-W, wl - 14, W * 3, 30); c.fill()
        # water body
        g = cairo.LinearGradient(0, wl, 0, H * 1.1)
        g.add_color_stop_rgba(0, *hexc(p['sea'][0])); g.add_color_stop_rgba(0.45, *hexc(p['sea'][1]))
        g.add_color_stop_rgba(1, *hexc(p['sea'][2]))
        c.set_source(g); c.rectangle(-W, wl + 2, W * 3, H * 2); c.fill()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'sky', self._sky, cam, t)
        if self.rays:
            ctx.save(); m0 = ctx.get_matrix(); cam.apply(ctx, t, 1.0)
            ctx.rectangle(-W, self.wl, W * 3, H * 2); ctx.clip()
            ctx.set_matrix(m0)
            self.paint_cached(ctx, 'urays', rays_builder('soft', self.seed, n=6, alpha=0.10,
                                                         src=(self.sun[0] * W, self.wl - 1300), spread=36),
                              cam, t, alpha=0.7 + 0.3 * math.sin(t * 0.5))
            ctx.restore()
        if self.parts: self.parts.draw(ctx, t, cam)

    def draw_waterline(self, ctx, t, cam, x0=-400, x1=W + 400):
        """Front water surface: re-fills the sea above the rays seam + white wave line."""
        pass

    def draw_fg(self, ctx, t, cam):
        # waterline drawn on the world (parallax 1) so it matches boats
        ctx.save(); cam.apply(ctx, t, 1.0)
        xs = np.arange(-500, W + 520, 24)
        ys = [self.water_y(x, t) for x in xs]
        ctx.move_to(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]): ctx.line_to(float(x), y)
        ctx.set_source_rgba(1, 1, 1, 0.92); ctx.set_line_width(3.0); ctx.stroke()
        ctx.restore()
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#03141A'), None, t, parallax=0, margin=0)

class TopDown(Plate):
    """Top-down ocean (teal, faint wavy-line texture drifting)."""
    parallax = 1.0
    def __init__(self, seed=4, vignette=0.4, color=('#1A7389', '#0F4E60', '#0A2C3A')):
        super().__init__(); self.seed = seed; self.vig = vignette; self.col = color
        r = rng(seed)
        self.waves = [(r.uniform(-300, W + 300), r.uniform(-100, H + 100), r.uniform(80, 260), r.uniform(0.04, 0.12),
                       r.random() * TAU) for _ in range(70)]
    def _base(self, c, s):
        rg = cairo.RadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.75)
        for k, col in zip((0, 0.6, 1), self.col): rg.add_color_stop_rgba(k, *hexc(col))
        c.set_source(rg); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t, parallax=0.4)
        ctx.save(); cam.apply(ctx, t, 1.0)
        ctx.set_line_width(2.2); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, y, L, a, ph) in self.waves:
            xx = x + 8 * t; yy = y + 3 * math.sin(t * 0.6 + ph)
            ctx.set_source_rgba(0.85, 0.96, 1.0, a * (0.7 + 0.3 * math.sin(t + ph)))
            ctx.move_to(xx, yy)
            ctx.curve_to(xx + L * 0.25, yy - 9, xx + L * 0.5, yy + 9, xx + L * 0.75, yy)
            ctx.curve_to(xx + L * 0.85, yy - 4, xx + L * 0.95, yy - 2, xx + L, yy)
            ctx.stroke()
        ctx.restore()
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig), None, t, parallax=0, margin=0)

class Sonar(Plate):
    """Black sonar screen (#000503): faint green polar grid + sweep beam (1.2 s loop)."""
    parallax = 0.0
    def __init__(self, origin=(80, 600), sweep=True):
        super().__init__(); self.o = origin; self.sweep = sweep
    def _base(self, c, s):
        set_col(c, PAL.SONAR_BG); c.paint()
        ox, oy = self.o
        c.set_source_rgba(0.09, 0.65, 0.2, 0.22); c.set_line_width(1.2)
        for r in range(220, 2400, 220):
            c.new_sub_path(); c.arc(ox, oy, r, -0.7, 0.7); c.stroke()
        for a in np.linspace(-0.7, 0.7, 9):
            c.move_to(ox, oy); c.line_to(ox + math.cos(a) * 2400, oy + math.sin(a) * 2400); c.stroke()
    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, None, t, parallax=0, margin=0)
        if self.sweep:
            ox, oy = self.o
            a = -0.7 + 1.4 * ((t / 1.2) % 1.0)
            ctx.set_source_rgba(0.12, 0.8, 0.3, 0.6); ctx.set_line_width(2.5)
            ctx.move_to(ox, oy); ctx.line_to(ox + math.cos(a) * 2600, oy + math.sin(a) * 2600); ctx.stroke()
    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(0.5), None, t, parallax=0, margin=0)


# =========================================================================== CROC KIT plates
# Flat Depth Theory river / swamp / reef worlds for the saltwater-crocodile video.
RIVER = dict(sky=('#AFB49C', '#C9C2A2', '#D9D1B2'), sun='#F6EDCF', far='#3C4E40', tree='#0E1F1B',
             mud='#6B5A3E', mud_hi='#8A7552', mud_dk='#4A3E2B', water_s='#1E3A34', water=('#2E4F42', '#24443A', '#0A1714'),
             silt='#A8B48C', root='#1A2A20')

def _mangrove_tree(c, x, base_y, h, col, seed=0, roots_to=None, canopy=True):
    """Flat mangrove silhouette: arched prop roots fanning down from a short trunk + lumpy canopy.
    roots_to = y the prop roots reach (default base_y)."""
    r = rng(seed)
    ry = base_y if roots_to is None else roots_to
    hub = (x, base_y - h * 0.32)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    set_col(c, col)
    for i in range(7):
        fx = x + (i - 3) * h * 0.11 + r.uniform(-8, 8)
        c.set_line_width(max(3, h * 0.022))
        c.move_to(hub[0] + (i - 3) * 3, hub[1])
        c.curve_to(hub[0] + (i - 3) * h * 0.05, hub[1] - h * 0.04, fx, hub[1] + (ry - hub[1]) * 0.15, fx, ry + 6)
        c.stroke()
    # trunk
    c.set_line_width(max(6, h * 0.05))
    c.move_to(hub[0], hub[1]); c.curve_to(x + h * 0.03, base_y - h * 0.55, x - h * 0.02, base_y - h * 0.7, x, base_y - h * 0.78)
    c.stroke()
    if canopy:
        for k in range(9):
            cx = x + r.uniform(-h * 0.32, h * 0.32); cy = base_y - h * (0.78 + r.uniform(-0.06, 0.16))
            c.save(); c.translate(cx, cy); c.scale(1, 0.62); circle(c, 0, 0, h * r.uniform(0.13, 0.22)); c.restore(); c.fill()

def _treeline(c, y, x0, x1, amp, col, seed, step=(30, 80)):
    r = rng(seed)
    pts = []; x = x0
    while x < x1:
        pts.append((x, y - amp * (0.55 + 0.45 * r.random()))); x += r.uniform(*step)
    pts.append((x1, y - amp * 0.7))
    sm = catmull(pts, 6)
    c.move_to(x0, y + 4)
    for px, py in sm: c.line_to(px, py)
    c.line_to(x1, y + 4); c.close_path(); set_col(c, col); c.fill()
    # lumpy canopy crowns along the top so it reads as forest, not hills
    for (px, py) in pts:
        for k in range(3):
            rr = amp * r.uniform(0.16, 0.3)
            c.save(); c.translate(px + r.uniform(-25, 25), py + rr * 0.5 + r.uniform(-6, 6)); c.scale(1.25, 0.8)
            circle(c, 0, 0, rr); c.restore(); c.fill()

class _Roots:
    """Hanging aerial roots (mangrove) that sway gently. Drawn per frame on the world."""
    def __init__(self, n, x0, x1, y0, ymin, ymax, seed=31, color=RIVER['root'], alpha=0.9, width=(3, 9)):
        r = rng(seed)
        self.items = [(r.uniform(x0, x1), y0 + r.uniform(-10, 10), r.uniform(ymin, ymax), r.uniform(*width),
                       r.random() * TAU, r.uniform(-30, 30)) for _ in range(n)]
        self.col, self.alpha = color, alpha
    def draw(self, ctx, t):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, y, L, w, ph, curl) in self.items:
            sw = 7 * math.sin(t * 0.7 + ph) * (L / 300)
            set_col(ctx, self.col, self.alpha); ctx.set_line_width(w)
            ctx.move_to(x, y)
            ctx.curve_to(x + curl * 0.3, y + L * 0.35, x + curl + sw * 0.6, y + L * 0.7, x + curl * 0.6 + sw, y + L)
            ctx.stroke()
            ctx.set_line_width(w * 0.45)       # little fork near the tip
            ctx.move_to(x + curl * 0.8 + sw * 0.8, y + L * 0.82)
            ctx.line_to(x + curl * 0.8 + sw + w * 2.2, y + L * 0.96); ctx.stroke()


class Riverbank(Plate):
    """Split river cross-section: hazy sky, far mangrove treeline, muddy bank (right) with
    mangroves, and below the waterline the murky olive river with silt and hanging roots.

    Riverbank(waterline_y=560, mud=True, mangroves=True, bank_x=1250 (where the mud meets the water),
              wave_amp=3, roots=True, particles=True, vignette=0.3, seed=5)
    Drawn at parallax 1 (props on 'mid' stay locked). water_y(x, t) = animated surface;
    bank_y(x) = top of the mud at x (stand people / buckets on it).
    Animation: waterline wave, drifting ripple dashes, hanging roots sway, silt drift, canopy breathes.
    """
    parallax = 1.0
    margin = 0.12
    def __init__(self, waterline_y=560, mud=True, mangroves=True, bank_x=1250, wave_amp=3, roots=True,
                 particles=True, vignette=0.3, seed=5):
        super().__init__()
        self.wl, self.mud, self.mang, self.bank_x, self.wave_amp = waterline_y, mud, mangroves, bank_x, wave_amp
        self.vig, self.seed = vignette, seed
        wl = waterline_y
        self.parts = Particles(n_specks=110, n_discs=14, alpha=0.38, color=RIVER['silt'], drift=(5, 1.5),
                               region=(0, wl + 30, W, H), disc_alpha=0.12, seed=seed + 3) if particles else None
        self.roots = _Roots(14, -100, 330, wl - 4, 60, 230, seed=seed + 7) \
            if (roots and mangroves) else None
        r = rng(seed + 1)
        self.rip = [(r.uniform(-200, W + 200), r.uniform(4, 40), r.uniform(30, 110), r.random() * TAU) for _ in range(26)]

    # geometry
    def water_y(self, x, t):
        a = self.wave_amp
        return self.wl + a * math.sin(x * 0.007 + t * 1.1) + a * 0.5 * math.sin(x * 0.019 - t * 1.6 + 1.0)

    def bank_y(self, x):
        """Top of the mud bank at x (above water right of bank_x, rising to the right)."""
        if not self.mud: return self.wl
        k = max(0.0, (x - self.bank_x) / 520.0)
        return self.wl - 150 * (1 - math.exp(-k * 1.6)) - 6 * k

    def _static(self, c, s):
        P = RIVER; wl = self.wl
        g = cairo.LinearGradient(0, -H * 0.15, 0, wl)
        for k, col in zip((0, 0.6, 1), P['sky']): g.add_color_stop_rgba(k, *hexc(col))
        c.set_source(g); c.rectangle(-W, -H, W * 3, wl + H + 20); c.fill()
        sc = hexc(P['sun']); sx, sy = W * 0.34, H * 0.16
        rg = cairo.RadialGradient(sx, sy, 0, sx, sy, H * 0.6)
        rg.add_color_stop_rgba(0, sc[0], sc[1], sc[2], 0.8); rg.add_color_stop_rgba(0.3, sc[0], sc[1], sc[2], 0.3)
        rg.add_color_stop_rgba(1, sc[0], sc[1], sc[2], 0)
        c.set_source(rg); c.rectangle(-W, -H, W * 3, wl + H); c.fill()
        # far bank treeline (two hazy layers)
        if self.mang:
            _treeline(c, wl - 2, -400, W + 400, 70, mix(P['far'], P['sky'][2], 0.55), self.seed, (40, 110))
            _treeline(c, wl + 1, -400, W + 400, 42, mix(P['tree'], P['sky'][2], 0.38), self.seed + 9, (30, 80))
        else:
            set_col(c, mix(P['far'], P['sky'][2], 0.5)); c.rectangle(-W, wl - 10, W * 3, 12); c.fill()
        # water body (below the line)
        g = cairo.LinearGradient(0, wl, 0, H * 1.12)
        for k, col in zip((0, 0.35, 1), P['water']): g.add_color_stop_rgba(k, *hexc(col))
        c.set_source(g); c.rectangle(-W, wl, W * 3, H * 2); c.fill()
        # light pool just under the surface
        c.save(); c.translate(W * 0.4, wl); c.scale(2.4, 0.5)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, H * 0.6)
        rg.add_color_stop_rgba(0, 0.75, 0.8, 0.6, 0.16); rg.add_color_stop_rgba(1, 0.75, 0.8, 0.6, 0)
        c.set_source(rg); c.rectangle(-W, 0, W * 2, H); c.fill(); c.restore()
        # river bed
        r = rng(self.seed + 4)
        pts = [(-400, H - 40)]
        x = -400
        while x < W + 400:
            pts.append((x, H - 50 - 30 * r.random())); x += r.uniform(120, 260)
        sm = catmull(pts, 6)
        c.move_to(-400, H + 300)
        for px, py in sm: c.line_to(px, py)
        c.line_to(W + 400, H + 300); c.close_path(); set_col(c, mix(P['mud_dk'], P['water'][2], 0.55)); c.fill()
        if self.mud:
            bx = self.bank_x
            xs = np.linspace(bx - 40, W + 420, 60)
            top = [self.bank_y(x) for x in xs]
            # underwater part of the bank: slope continues down, tinted by the water
            c.move_to(bx - 40, wl)
            c.curve_to(bx - 90, wl + 140, bx - 210, H - 160, bx - 330, H + 40)
            c.line_to(W + 420, H + 40); c.line_to(W + 420, wl); c.close_path()
            g = cairo.LinearGradient(0, wl, 0, H)
            g.add_color_stop_rgba(0, *mix(P['mud_dk'], P['water'][1], 0.45)); g.add_color_stop_rgba(1, *mix(P['mud_dk'], P['water'][2], 0.7))
            c.set_source(g); c.fill()
            # dry mud above the water
            c.move_to(bx - 40, wl + 2)
            for x, y in zip(xs, top): c.line_to(float(x), y)
            c.line_to(W + 420, wl + 2); c.close_path()
            g = cairo.LinearGradient(0, wl - 160, 0, wl)
            g.add_color_stop_rgba(0, *hexc(P['mud_hi'])); g.add_color_stop_rgba(1, *hexc(P['mud']))
            c.set_source(g); c.fill()
            # wet band at the water's edge + cracked-mud ticks + crest highlight
            c.move_to(bx - 40, wl + 2)
            for x, y in zip(xs, top): c.line_to(float(x), max(y, wl - 16))
            c.line_to(W + 420, wl + 2); c.close_path(); set_col(c, P['mud_dk'], 0.55); c.fill()
            c.move_to(float(xs[0]), top[0])
            for x, y in zip(xs[1:], top[1:]): c.line_to(float(x), y)
            set_col(c, '#A89068', 0.8); c.set_line_width(3); c.stroke()
            c.set_line_width(1.6)
            for _ in range(46):
                x = r.uniform(bx + 60, W + 300); yt = self.bank_y(x)
                y = r.uniform(yt + 8, wl - 18)
                if y <= yt + 6: continue
                L = r.uniform(10, 26)
                set_col(c, P['mud_dk'], 0.5); c.move_to(x, y); c.line_to(x + L, y + r.uniform(-3, 3)); c.stroke()
        if self.mang:
            # near-bank mangroves (left edge, roots into the water) and on the mud bank
            for i, (x, h) in enumerate(((-60, 420), (150, 330))):
                _mangrove_tree(c, x, wl, h, P['tree'], self.seed + 20 + i, roots_to=wl + 40)
            if self.mud:
                for i, (x, h) in enumerate(((self.bank_x + 380, 360), (self.bank_x + 610, 470))):
                    by = self.bank_y(x)
                    _mangrove_tree(c, x, by, h, P['tree'], self.seed + 30 + i, roots_to=by + 6)

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'static', self._static, cam, t)
        ctx.save(); cam.apply(ctx, t, 1.0)
        if self.roots: self.roots.draw(ctx, t)
        ctx.restore()
        if self.parts: self.parts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        ctx.save(); cam.apply(ctx, t, 1.0)
        x_end = (self.bank_x - 20) if self.mud else W + 500
        xs = np.arange(-500, x_end, 20)
        ys = [self.water_y(x, t) for x in xs]
        # thin surface film + bright line
        ctx.move_to(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]): ctx.line_to(float(x), y)
        ctx.set_source_rgba(0.88, 0.92, 0.82, 0.85); ctx.set_line_width(2.6); ctx.stroke()
        # drifting ripple dashes just under the line
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, dy, L, ph) in self.rip:
            xx = (x + 14 * t + 200) % (W + 400) - 200
            if xx > x_end - L: continue
            a = 0.22 * (0.6 + 0.4 * math.sin(t * 1.4 + ph))
            ctx.set_source_rgba(0.85, 0.9, 0.78, a); ctx.set_line_width(2)
            yy = self.water_y(xx, t) + dy
            ctx.move_to(xx, yy); ctx.line_to(xx + L, yy); ctx.stroke()
        ctx.restore()
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#0A1410'), None, t, parallax=0, margin=0)


class Mangrove(Plate):
    """Mangrove swamp at water level: hazy sky, layered mangrove forest on both sides and behind,
    still olive-teal water (#1E3A34) with flat ripple lines and soft tree reflections.

    Mangrove(horizon=430, density=1.0, haze=0.5, particles=True, vignette=0.4, seed=8)
    Put CrocEyes / Croc(submerged=…) on the water (y > horizon). Drawn at parallax 1.
    water_y(x, t) returns the horizon line (the far water edge) for reference.
    Animation: ripple lines drift and pulse, reflections shimmer, leaves/specks drift, roots sway.
    """
    parallax = 1.0
    margin = 0.12
    def __init__(self, horizon=430, density=1.0, haze=0.5, particles=True, vignette=0.4, seed=8):
        super().__init__()
        self.hz, self.dens, self.haze, self.vig, self.seed = horizon, density, haze, vignette, seed
        r = rng(seed + 2)
        self.rips = []
        for i in range(48):
            y = horizon + 14 + (H - horizon) * (r.random() ** 1.6)
            k = (y - horizon) / (H - horizon)
            self.rips.append((r.uniform(-200, W + 200), y, 40 + 260 * k * r.uniform(0.5, 1.1), 1.0 + 2.6 * k, r.random() * TAU))
        self.leaves = [(r.uniform(0, W), r.uniform(horizon + 30, H), r.uniform(5, 11), r.random() * TAU) for _ in range(14)]
        self.parts = Particles(n_specks=40, n_discs=4, alpha=0.25, color='#E8E2C2', drift=(4, -2),
                               region=(0, 0, W, horizon), seed=seed + 1) if particles else None
        self.roots = _Roots(12, -120, 330, 0, 90, 260, seed=seed + 5, alpha=0.95, width=(3, 7))

    def water_y(self, x, t):
        return self.hz

    def _static(self, c, s):
        P = RIVER; hz = self.hz
        g = cairo.LinearGradient(0, -H * 0.2, 0, hz)
        for k, col in zip((0, 0.6, 1), P['sky']): g.add_color_stop_rgba(k, *hexc(col))
        c.set_source(g); c.rectangle(-W, -H, W * 3, hz + H + 10); c.fill()
        sk = P['sky'][2]
        # forest layers, far -> near (far ones hazier)
        layers = [(hz, 120, 0.7, (50, 120)), (hz + 2, 80, 0.45, (40, 90))]
        for i, (y, amp, hzk, st) in enumerate(layers):
            _treeline(c, y, -400, W + 400, amp * self.dens, mix(P['tree'], sk, hzk * self.haze * 1.4), self.seed + i, st)
        # water
        g = cairo.LinearGradient(0, hz, 0, H * 1.1)
        g.add_color_stop_rgba(0, *mix(P['water_s'], sk, 0.35)); g.add_color_stop_rgba(0.25, *hexc(P['water_s']))
        g.add_color_stop_rgba(1, *hexc('#0C1C18'))
        c.set_source(g); c.rectangle(-W, hz, W * 3, H * 2); c.fill()
        # soft reflection of the treeline
        c.save(); c.translate(0, 2 * hz); c.scale(1, -1)
        c.push_group()
        _treeline(c, hz + 2, -400, W + 400, 80 * self.dens, P['tree'], self.seed + 1, (40, 90))
        c.pop_group_to_source(); c.paint_with_alpha(0.32); c.restore()
        # side stands of mangroves (both banks), roots into the water
        trees = [(-80, 560), (110, 470), (300, 380)] + [(W - 260, 400), (W - 70, 540), (W + 90, 600)]
        if self.dens < 0.8: trees = trees[::2]
        for i, (x, h) in enumerate(trees):
            col = mix(P['tree'], sk, 0.18 * self.haze * (1 if 200 < x < W - 200 else 0))
            base = hz + 60 + (h - 380) * 0.35
            _mangrove_tree(c, x, base, h, col, self.seed + 40 + i, roots_to=base + 8)
            # reflection
            c.save(); c.translate(0, 2 * (base + 8)); c.scale(1, -1); c.push_group()
            _mangrove_tree(c, x, base, h, P['tree'], self.seed + 40 + i, roots_to=base + 8, canopy=False)
            c.pop_group_to_source(); c.paint_with_alpha(0.22); c.restore()
        # overhanging canopy at the top corners
        set_col(c, P['tree'])
        r = rng(self.seed + 60)
        for k in range(20):
            cx = r.choice([r.uniform(-150, 420), r.uniform(W - 420, W + 150)]); cy = r.uniform(-80, 60)
            c.save(); c.translate(cx, cy); c.scale(1, 0.6); circle(c, 0, 0, r.uniform(70, 130)); c.restore(); c.fill()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'static', self._static, cam, t)
        if self.parts: self.parts.draw(ctx, t, cam)
        ctx.save(); cam.apply(ctx, t, 1.0)
        self.roots.draw(ctx, t)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, y, L, w, ph) in self.rips:
            xx = (x + 6 * t * (1 + (y - self.hz) / 300) + 200) % (W + 400) - 200
            a = 0.16 + 0.12 * math.sin(t * 0.9 + ph)
            ctx.set_source_rgba(0.82, 0.88, 0.78, a); ctx.set_line_width(w)
            yy = y + 1.5 * math.sin(t * 0.8 + ph)
            ctx.move_to(xx, yy); ctx.line_to(xx + L, yy); ctx.stroke()
        for (x, y, r_, ph) in self.leaves:
            xx = (x + 9 * t + 50) % (W + 100) - 50; yy = y + 2 * math.sin(t + ph)
            ctx.save(); ctx.translate(xx, yy); ctx.rotate(ph + 0.2 * math.sin(t * 0.7 + ph)); ctx.scale(1, 0.45)
            circle(ctx, 0, 0, r_); ctx.restore()
            ctx.set_source_rgba(0.55, 0.52, 0.3, 0.7); ctx.fill()
        ctx.restore()

    def draw_fg(self, ctx, t, cam):
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#06100D'), None, t, parallax=0, margin=0)


def _coral_layer(c, y_base, col, seed, scale=1.0, n=14, x0=-300, x1=W + 300):
    """Flat coral silhouettes: branching staghorn, round brain/boulder, fan, and tube clusters."""
    r = rng(seed)
    set_col(c, col); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    x = x0
    while x < x1:
        kind = r.choice(['stag', 'boulder', 'fan', 'tube', 'boulder', 'stag'])
        s = scale * r.uniform(0.7, 1.3)
        if kind == 'boulder':
            c.save(); c.translate(x, y_base); c.scale(1, 0.7); circle(c, 0, 0, 70 * s); c.restore(); c.fill()
        elif kind == 'stag':
            def br(px, py, ang, L, w, d):
                ex, ey = px + math.sin(ang) * L, py - math.cos(ang) * L
                c.set_line_width(w); c.move_to(px, py); c.line_to(ex, ey); c.stroke()
                if d > 0:
                    br(ex, ey, ang - r.uniform(0.3, 0.6), L * 0.72, w * 0.75, d - 1)
                    br(ex, ey, ang + r.uniform(0.3, 0.6), L * 0.72, w * 0.75, d - 1)
            br(x, y_base + 10, r.uniform(-0.15, 0.15), 60 * s, 18 * s, 3)
        elif kind == 'fan':
            c.move_to(x, y_base + 6)
            c.curve_to(x - 110 * s, y_base - 60 * s, x - 90 * s, y_base - 190 * s, x, y_base - 200 * s)
            c.curve_to(x + 90 * s, y_base - 190 * s, x + 110 * s, y_base - 60 * s, x, y_base + 6); c.fill()
        else:
            for k in range(4):
                h = r.uniform(50, 120) * s; xx = x + (k - 1.5) * 22 * s
                c.set_line_width(18 * s); c.move_to(xx, y_base + 10); c.line_to(xx + r.uniform(-8, 8), y_base - h); c.stroke()
        x += r.uniform(90, 200) * scale

class Reef(Plate):
    """Clear turquoise shallow reef, underwater: bright gradient (#2C8F94 -> #0F4C55), god-ray fan,
    pale sand floor, two layers of flat coral silhouettes (far teal, near coral/cyan), swaying soft
    corals, particles. surface_y=None | y draws the bright underside of the surface at y (snorkellers).

    Reef(surface_y=None, floor=True, rays=True, particles=True, vignette=0.32, seed=12)
    Animation: rays shimmer/sway, sea-fan + weed sway, particles drift, surface ripples.
    """
    parallax = 0.35
    def __init__(self, surface_y=None, floor=True, rays=True, particles=True, vignette=0.32, seed=12):
        super().__init__()
        self.sy, self.floor, self.rays, self.vig, self.seed = surface_y, floor, rays, vignette, seed
        self.parts = Particles(seed=seed + 5, alpha=0.55, color='#E6FBFA') if particles else None
        r = rng(seed + 3)
        self.weeds = [(r.uniform(-100, W + 100), H - r.uniform(40, 120), r.uniform(60, 150), r.random() * TAU,
                       r.choice(['#E08A6B', '#F0A54A', '#7FC1CB', '#D9665A'])) for _ in range(16)]

    def _base(self, c, s):
        g = cairo.LinearGradient(0, -H * 0.1, 0, H * 1.05)
        g.add_color_stop_rgba(0, *hexc('#4DB3AE')); g.add_color_stop_rgba(0.35, *hexc('#2C8F94'))
        g.add_color_stop_rgba(1, *hexc('#0F4C55'))
        c.set_source(g); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        c.save(); c.translate(W * 0.5, -H * 0.1); c.scale(1.7, 1.0)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, H * 0.9)
        rg.add_color_stop_rgba(0, 0.85, 1, 0.95, 0.35); rg.add_color_stop_rgba(1, 0.85, 1, 0.95, 0)
        c.set_source(rg); c.rectangle(-W, -H, W * 2, H * 3); c.fill(); c.restore()
        if self.floor:
            # far coral band (hazy teal), sand, near corals
            _coral_layer(c, H - 150, mix('#2C8F94', '#0F4C55', 0.35), self.seed, 0.6, x0=-300)
            r = rng(self.seed + 1)
            pts = [(-400, H - 120)]; x = -400
            while x < W + 400:
                pts.append((x, H - 110 - 26 * r.random())); x += r.uniform(160, 300)
            sm = catmull(pts, 6)
            c.move_to(-400, H + 300)
            for px, py in sm: c.line_to(px, py)
            c.line_to(W + 400, H + 300); c.close_path()
            g = cairo.LinearGradient(0, H - 140, 0, H)
            g.add_color_stop_rgba(0, *mix('#E7D9B0', '#2C8F94', 0.45)); g.add_color_stop_rgba(1, *mix('#E7D9B0', '#2C8F94', 0.25))
            c.set_source(g); c.fill()
            # sand ripples
            c.set_line_width(2)
            for i in range(40):
                x = r.uniform(-300, W + 300); y = r.uniform(H - 95, H - 10)
                c.set_source_rgba(1, 1, 0.92, 0.12); c.move_to(x, y); c.curve_to(x + 20, y - 4, x + 40, y + 4, x + 60, y); c.stroke()
            _coral_layer(c, H - 60, mix('#E08A6B', '#2C8F94', 0.25), self.seed + 2, 1.0, x0=-250, x1=W * 0.42)
            _coral_layer(c, H - 50, mix('#7FC1CB', '#2C8F94', 0.3), self.seed + 3, 0.9, x0=W * 0.45, x1=W * 0.75)
            _coral_layer(c, H - 55, mix('#E08A6B', '#2C8F94', 0.3), self.seed + 4, 1.1, x0=W * 0.78, x1=W + 250)

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
        if self.rays:
            for sub in (0, 1):
                a = 0.65 + 0.35 * math.sin(t * 0.5 + sub * 2.1)
                ctx.save(); sway = math.radians(0.6 * math.sin(t * 0.23 + sub))
                ctx.translate(W / 2, -200); ctx.rotate(sway); ctx.translate(-W / 2, 200)
                self.paint_cached(ctx, ('rays', sub), rays_builder('soft', self.seed, n=8, subset=sub, alpha=0.2,
                                                                   color='#F2FFF8', fade=0.85), cam, t, alpha=a)
                ctx.restore()
        if self.floor:
            ctx.save(); cam.apply(ctx, t, 0.7)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for (x, y, L, ph, col) in self.weeds:
                sw = 14 * math.sin(t * 0.9 + ph)
                for k in (-1, 0, 1):
                    ctx.move_to(x + k * 10, y)
                    ctx.curve_to(x + k * 14 + sw * 0.3, y - L * 0.4, x + k * 18 + sw * 0.8, y - L * 0.75, x + k * 20 + sw, y - L * (1 - 0.1 * abs(k)))
                set_col(ctx, mix(col, '#2C8F94', 0.25)); ctx.set_line_width(9); ctx.stroke()
            ctx.restore()
        if self.parts: self.parts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        if self.sy is not None:
            ctx.save(); cam.apply(ctx, t, 1.0)
            sy = self.sy
            g = cairo.LinearGradient(0, sy - 40, 0, sy + 60)
            g.add_color_stop_rgba(0, 0.95, 1, 0.98, 0.0); g.add_color_stop_rgba(0.4, 0.95, 1, 0.98, 0.25)
            g.add_color_stop_rgba(1, 0.95, 1, 0.98, 0)
            ctx.set_source(g); ctx.rectangle(-W, sy - 40, W * 3, 100); ctx.fill()
            xs = np.arange(-500, W + 520, 20)
            ctx.move_to(-500, sy)
            for x in xs: ctx.line_to(float(x), sy + 4 * math.sin(x * 0.008 + t * 1.4) + 2 * math.sin(x * 0.021 - t * 2))
            ctx.set_source_rgba(1, 1, 1, 0.85); ctx.set_line_width(3); ctx.stroke()
            ctx.restore()
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#03262B'), None, t, parallax=0, margin=0)


class MurkyWater(Plate):
    """Low-visibility tidal-river water: green-brown gradient (#24443A -> #0A1714), drifting silt
    (dense specks + soft clouds), haze banks that swallow anything a few metres away, hanging
    mangrove roots from the top edge, optional surface line.

    MurkyWater(surface_y=238 | None, roots=True, silt=1.0 (density), haze=0.6, vignette=0.6, seed=21)
    Put Croc(..., tint='#24443A') or lower opacity on far animals to sell the murk.
    Animation: silt drift, haze clouds drift, roots sway, surface shimmer.
    """
    parallax = 0.35
    def __init__(self, surface_y=238, roots=True, silt=1.0, haze=0.6, vignette=0.6, seed=21):
        super().__init__()
        self.sy, self.haze, self.vig, self.seed = surface_y, haze, vignette, seed
        top = 0 if surface_y is None else surface_y
        self.parts = Particles(n_specks=int(220 * silt), n_discs=int(30 * silt), alpha=0.42, color='#B5B48A',
                               drift=(7, 2), region=(0, top, W, H), disc_alpha=0.16, seed=seed + 2)
        self.roots = _Roots(22, -100, W + 100, top - 6, 80, 300, seed=seed + 4, color='#0B1712', alpha=0.85) if roots else None
        r = rng(seed + 6)
        self.clouds = [(r.uniform(-300, W + 300), r.uniform(top + 60, H), r.uniform(200, 420), r.random() * TAU,
                        r.uniform(0.5, 1.0)) for _ in range(9)]

    def _base(self, c, s):
        top = -H * 0.1 if self.sy is None else self.sy
        g = cairo.LinearGradient(0, top, 0, H * 1.08)
        g.add_color_stop_rgba(0, *hexc('#3B5A44')); g.add_color_stop_rgba(0.25, *hexc('#24443A'))
        g.add_color_stop_rgba(1, *hexc('#0A1714'))
        c.set_source(g); c.rectangle(-W, -H, W * 3, H * 3); c.fill()
        if self.sy is not None:
            # dim above-water band (seen through the surface), no detail
            g = cairo.LinearGradient(0, self.sy - 260, 0, self.sy)
            g.add_color_stop_rgba(0, *hexc('#6F7458')); g.add_color_stop_rgba(1, *hexc('#8C8C68'))
            c.set_source(g); c.rectangle(-W, -H, W * 3, self.sy + H); c.fill()
        # brownish light pool under the surface
        c.save(); c.translate(W * 0.5, (self.sy or 0)); c.scale(2.0, 0.7)
        rg = cairo.RadialGradient(0, 0, 0, 0, 0, H * 0.7)
        rg.add_color_stop_rgba(0, 0.6, 0.62, 0.42, 0.22); rg.add_color_stop_rgba(1, 0.6, 0.62, 0.42, 0)
        c.set_source(rg); c.rectangle(-W, 0, W * 2, H * 2); c.fill(); c.restore()

    def draw_bg(self, ctx, t, cam):
        self.paint_cached(ctx, 'base', self._base, cam, t)
        ctx.save(); cam.apply(ctx, t, 0.6)
        for (x, y, R, ph, a) in self.clouds:
            xx = (x + 10 * t + 400) % (W + 800) - 400; yy = y + 12 * math.sin(t * 0.2 + ph)
            ctx.save(); ctx.translate(xx, yy); ctx.scale(1.8, 0.7)
            rg = cairo.RadialGradient(0, 0, 0, 0, 0, R)
            rg.add_color_stop_rgba(0, 0.42, 0.45, 0.32, 0.22 * a * self.haze); rg.add_color_stop_rgba(1, 0.42, 0.45, 0.32, 0)
            ctx.set_source(rg); circle(ctx, 0, 0, R); ctx.fill(); ctx.restore()
        ctx.restore()
        self.parts.draw(ctx, t, cam)

    def draw_fg(self, ctx, t, cam):
        ctx.save(); cam.apply(ctx, t, 1.0)
        if self.roots: self.roots.draw(ctx, t)
        if self.sy is not None:
            sy = self.sy
            ctx.move_to(-500, sy)
            for x in np.arange(-500, W + 520, 20):
                ctx.line_to(float(x), sy + 3 * math.sin(x * 0.009 + t * 1.2) + 1.5 * math.sin(x * 0.023 - t * 1.7))
            ctx.set_source_rgba(0.86, 0.88, 0.72, 0.7); ctx.set_line_width(2.6); ctx.stroke()
        ctx.restore()
        # murk: a flat haze over everything (fg) + heavy vignette
        ctx.set_source_rgba(0.14, 0.22, 0.17, 0.12 * self.haze); ctx.paint()
        self.paint_cached(ctx, 'vig', vignette_builder(self.vig, '#030A07'), None, t, parallax=0, margin=0)
