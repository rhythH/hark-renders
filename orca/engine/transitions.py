"""Transitions. Set on the INCOMING shot: shot.trans_in = ('dip', 0.7).

kinds (duration d straddles the cut, half before / half after, so timing of
the shots never changes):
  'cut'       hard cut (default, the majority)
  'dip'       dip to black (0.7 s topic break / before chapter cards)
  'dissolve'  cross-dissolve (0.8–1.6 s, continuity mid-sentence)
  'ink'       ink/smoke blooms through black (0.5–0.7 s)
  'lens'      foreground orca silhouette passes the lens, cut hidden behind it (0.6–1.0 s)
  'flash'     white flash at the head of the incoming shot (5–6 frames), not straddling
"""
import math
import cairocffi as cairo
from .core import W, H, TAU, rng, remap, ease

DEFAULTS = {'cut': 0.0, 'dip': 0.7, 'dissolve': 1.0, 'ink': 0.6, 'lens': 0.8, 'flash': 0.2}

def parse(tr):
    if tr is None: return 'cut', 0.0
    if isinstance(tr, str): return tr, DEFAULTS.get(tr, 0.5)
    return tr[0], float(tr[1])

def straddles(kind):
    return kind in ('dip', 'dissolve', 'ink', 'lens')

def flash(ctx, lt, d=0.2):
    """White frame fading out over ~d seconds (impacts / hard hits)."""
    a = 1.0 - lt / d
    if a > 0:
        ctx.save(); ctx.identity_matrix() if False else None
        ctx.set_source_rgba(1, 1, 1, min(1, a) ** 1.4); ctx.rectangle(-50, -50, W + 100, H + 100); ctx.fill()
        ctx.restore()

def draw(ctx, kind, d, A, B, tB, tA, u):
    """u = time relative to the cut (-d/2 .. +d/2). tA/tB = local times."""
    h = d / 2
    if kind == 'dip':
        if u < 0:
            A.render(ctx, tA); a = remap(u, -h, 0, 0, 1)
        else:
            B.render(ctx, tB); a = remap(u, 0, h, 1, 0)
        ctx.set_source_rgba(0, 0, 0, a); ctx.rectangle(-50, -50, W + 100, H + 100); ctx.fill()
    elif kind == 'dissolve':
        k = remap(u, -h, h, 0, 1, 'sine')
        A.render(ctx, tA)
        ctx.push_group(); B.render(ctx, tB); ctx.pop_group_to_source(); ctx.paint_with_alpha(k)
    elif kind == 'ink':
        if u < 0:
            A.render(ctx, tA); k = remap(u, -h, 0, 0, 1)
        else:
            B.render(ctx, tB); k = remap(u, 0, h, 1, 0)
        ink(ctx, k, seed=7)
    elif kind == 'lens':
        if u < 0: A.render(ctx, tA)
        else: B.render(ctx, tB)
        lens_silhouette(ctx, (u + h) / d)

def ink(ctx, k, seed=7):
    """Black ink/smoke blooms covering the frame as k goes 0->1."""
    if k <= 0: return
    r = rng(seed)
    blobs = [(r.uniform(-100, W + 100), r.uniform(-100, H + 100), r.uniform(0.0, 0.45), r.uniform(0.7, 1.3)) for _ in range(26)]
    for (x, y, delay, sz) in blobs:
        kk = max(0.0, (k - delay) / (1 - delay))
        if kk <= 0: continue
        R = ease('eo', kk) * 900 * sz
        g = cairo.RadialGradient(x, y, R * 0.55, x, y, R)
        g.add_color_stop_rgba(0, 0, 0, 0, 1); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.new_sub_path(); ctx.arc(x, y, R, 0, TAU); ctx.fill()
    if k > 0.85:
        ctx.set_source_rgba(0, 0, 0, (k - 0.85) / 0.15); ctx.rectangle(-50, -50, W + 100, H + 100); ctx.fill()

def lens_silhouette(ctx, p):
    """A huge defocused orca silhouette sweeps L->R across the lens. p 0..1;
    the frame is fully covered around p=0.5."""
    from .chars.orca import orca_silhouette_path
    x = remap(p, 0, 1, W + 1700, -1900)
    ctx.save()
    # draw at low res and upscale = cheap defocus
    s = ctx.get_matrix()[0]
    lw, lh = max(32, int(W * s / 10)), max(18, int(H * s / 10))
    small = cairo.ImageSurface(cairo.FORMAT_ARGB32, lw, lh)
    c = cairo.Context(small); c.scale(lw / W, lh / H)
    c.translate(x, H * 0.55); c.scale(5.2, 5.2); c.rotate(-0.05)
    orca_silhouette_path(c)
    c.set_source_rgba(0.01, 0.03, 0.045, 1); c.fill()
    ctx.scale(W / lw, H / lh)
    ctx.set_source_surface(small, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
