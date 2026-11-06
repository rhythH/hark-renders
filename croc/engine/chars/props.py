"""Flat comparison silhouettes for size scales (bus, elephant, car, person),
drawn to real proportions: pass `height` in units (= px at scale 1).

Real heights used for scaling: bus 3.0 m (12 m long), elephant 3.2 m (6 m long),
car 1.5 m (4.5 m long), person 1.8 m, croc 6.17 m long (0.85 m feet->crest), orca male 8 m long / dorsal 1.8 m.
"""
import math
from ..core import Element, set_col, rrect, circle, PAL
REAL = {'bus': (12.0, 3.0), 'elephant': (6.0, 3.2), 'car': (4.5, 1.5), 'person': (0.5, 1.8), 'croc': (6.17, 0.85)}

class _Sil(Element):
    kind = 'bus'
    def __init__(self, height=200, color='#DDE3E3', outline=None, **kw):
        super().__init__(**kw); self.h, self.col, self.outline = height, color, outline
    def finish(self, ctx):
        set_col(ctx, self.col)
        if self.outline:
            ctx.fill_preserve(); set_col(ctx, self.outline[0]); ctx.set_line_width(self.outline[1]); ctx.stroke()
        else:
            ctx.fill()

class Bus(_Sil):
    """Origin bottom-left. Length 4x height."""
    def draw(self, ctx, t):
        h = self.h; L = h * 4
        rrect(ctx, 0, -h, L, h * 0.86, h * 0.08)
        ctx.new_sub_path(); ctx.arc(L * 0.18, -h * 0.14, h * 0.14, 0, math.tau)
        ctx.new_sub_path(); ctx.arc(L * 0.8, -h * 0.14, h * 0.14, 0, math.tau)
        self.finish(ctx)
        ctx.set_source_rgba(0, 0, 0, 0.35)
        for i in range(7):
            rrect(ctx, L * 0.06 + i * L * 0.13, -h * 0.88, L * 0.1, h * 0.3, 4); ctx.fill()

class Car(_Sil):
    def draw(self, ctx, t):
        h = self.h; L = h * 3
        ctx.move_to(0, -h * 0.25); ctx.line_to(0, -h * 0.55); ctx.line_to(L * 0.22, -h * 0.6); ctx.line_to(L * 0.34, -h)
        ctx.line_to(L * 0.72, -h); ctx.line_to(L * 0.84, -h * 0.6); ctx.line_to(L, -h * 0.52); ctx.line_to(L, -h * 0.25); ctx.close_path()
        ctx.new_sub_path(); ctx.arc(L * 0.2, -h * 0.2, h * 0.2, 0, math.tau)
        ctx.new_sub_path(); ctx.arc(L * 0.8, -h * 0.2, h * 0.2, 0, math.tau)
        self.finish(ctx)

class Elephant(_Sil):
    def draw(self, ctx, t):
        h = self.h; s = h / 320.0
        ctx.save(); ctx.scale(s, s)
        pts = [(58, 0), (54, -150), (62, -230), (120, -290), (250, -306), (370, -300), (430, -268), (462, -210),
               (474, -120), (478, -50), (494, -22), (514, -28), (518, -14), (492, -2), (462, -30), (452, -120),
               (432, -168), (412, -158), (410, 0), (366, 0), (362, -100), (336, -100), (332, 0), (290, 0), (292, -122),
               (172, -126), (166, 0), (124, 0), (120, -100), (100, -100), (96, 0)]
        ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.close_path()
        self.finish(ctx)
        ctx.move_to(372, -270); ctx.curve_to(330, -262, 318, -190, 344, -150)
        ctx.set_source_rgba(0, 0, 0, 0.18); ctx.set_line_width(6); ctx.stroke()
        ctx.restore()

class Person(_Sil):
    def draw(self, ctx, t):
        h = self.h
        ctx.new_sub_path(); ctx.arc(0, -h * 0.9, h * 0.1, 0, math.tau)
        rrect(ctx, -h * 0.13, -h * 0.78, h * 0.26, h * 0.42, h * 0.08)
        rrect(ctx, -h * 0.11, -h * 0.42, h * 0.09, h * 0.42, h * 0.04)
        rrect(ctx, h * 0.02, -h * 0.42, h * 0.09, h * 0.42, h * 0.04)
        self.finish(ctx)

FEET = 118.0   # croc rig: walking feet at local y≈+118
BELLY = 86.0   # lowest belly point (legs=False: lying on the ground)

class CrocSil(_Sil):
    """Flat saltwater-croc silhouette (record 6.17 m, Lolong), built on the Croc rig
    (variant='silhouette', legs=False lying flat by default; legs=True stands it on its feet). `height` here = overall height (feet to crest);
    length = height * 6.17 / 0.85. Origin bottom-left (tail tip at the right). `gait` 0..1, `jaw` deg."""
    kind = 'croc'
    def __init__(self, height=100, color='#DDE3E3', outline=None, gait=0.0, jaw=0.0, facing='left', legs=False, **kw):
        super().__init__(height=height, color=color, outline=outline, **kw)
        from .croc import Croc
        self.length = height * REAL['croc'][0] / REAL['croc'][1]
        self._c = Croc(variant='silhouette', sil_color=color, swim=0.0, gait=gait, jaw=jaw, blink=None, facing=facing, legs=legs)
        self.feet = FEET if legs else BELLY
    def draw(self, ctx, t):
        s = self.length / 1000.0
        ctx.save(); ctx.translate(self.length / 2, -self.feet * s); ctx.scale(s, s)
        self._c.draw(ctx, t); ctx.restore()


def comparison_silhouette(kind, metres_per_unit, **kw):
    """Build a silhouette at true scale: metres_per_unit e.g. 8 m orca drawn
    600 px long -> 8/600."""
    L, Hm = REAL[kind]
    h = Hm / metres_per_unit
    return {'bus': Bus, 'car': Car, 'elephant': Elephant, 'person': Person, 'croc': CrocSil}[kind](height=h, **kw)
