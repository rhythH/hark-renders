"""Boats for surface cross-sections.

Sailboat(pos, scale, facing='right', plate=<Surface> (auto-float on its waves),
         rudder=0 (deg or K), damage='ok'|'cracked'|'broken'|'missing', heel=0,
         sails=True, crew=1)
  .rudder_world(t) -> world (x,y) of the rudder blade centre (aim impacts there)
  .rudder_piece(t_break, ...) -> Element: the snapped blade tumbling down
Origin = hull centre at the waterline. Hull length ~620 units.
Speedboat(...) small white motorboat (as in the reference fishing scene).
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, set_col, hexc, circle, rrect, TAU, PAL, catmull, poly, remap
OUT = '#0A0D10'

def _float_props(el, t, plate, x):
    """y on the waves + tilt from the local wave slope."""
    if plate is None: return 0.0, 0.0
    y = plate.water_y(x, t)
    sl = (plate.water_y(x + 60, t) - plate.water_y(x - 60, t)) / 120
    return y - plate.wl, math.degrees(math.atan(sl)) * 0.9

class _Floating(Element):
    def __init__(self, plate=None, **kw):
        super().__init__(**kw); self.plate = plate
        self.proc(self._float)
    def _float(self, el, t):
        if self.plate is None: return {}
        x = ev(self.pos, t)[0]
        dy, rot = _float_props(self, t + self.t0, self.plate, x)
        return {'dpos': (0, dy), 'drot': rot + ev(getattr(self, 'heel', 0), t)}

class Sailboat(_Floating):
    def __init__(self, facing='right', rudder=0.0, damage='ok', heel=0.0, sails=True, crew=1,
                 hull='#F2F1EC', stripe='#1E3A4C', bottom='#7A2A2A', **kw):
        super().__init__(**kw)
        self.facing, self.rudder, self.damage, self.heel, self.sails, self.crew = facing, rudder, damage, heel, sails, crew
        self.hull_c, self.stripe_c, self.bottom_c = hull, stripe, bottom

    # geometry facing right (bow at +x)
    HULL = [(-300, -40), (-150, -46), (60, -46), (230, -40), (322, -58), (300, -10), (250, 30), (130, 52), (-120, 54), (-280, 40), (-310, 0)]
    RUDDER_PIVOT = (-262, 40)

    def rudder_local(self):
        return (-262 + (0 if self.facing == 'right' else 0), 120)

    def rudder_world(self, t):
        """Approximate world position of the rudder blade (for impacts)."""
        pos = ev(self.pos, t - self.t0); s = ev(self.scale, t - self.t0)
        s = s if not isinstance(s, tuple) else s[0]
        dx = -262 * (1 if self.facing == 'right' else -1)
        dy = 0
        if self.plate is not None: dy = self.plate.water_y(pos[0], t) - self.plate.wl
        return (pos[0] + dx * s, pos[1] + dy + 115 * s)

    def _rudder_path(self, ctx, broken=False):
        if broken:   # only the stub remains
            ctx.move_to(-270, 44); ctx.line_to(-252, 44); ctx.line_to(-250, 78); ctx.line_to(-258, 70)
            ctx.line_to(-266, 82); ctx.line_to(-272, 72); ctx.close_path(); return
        ctx.move_to(-272, 44); ctx.line_to(-250, 44); ctx.curve_to(-242, 90, -244, 140, -252, 178)
        ctx.curve_to(-262, 186, -278, 184, -284, 172); ctx.curve_to(-286, 130, -282, 86, -272, 44); ctx.close_path()

    def draw(self, ctx, t):
        ctx.push_group()
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ow = 4
        # keel
        ctx.move_to(-40, 50); ctx.line_to(60, 50); ctx.line_to(40, 190); ctx.curve_to(30, 205, -10, 205, -20, 190); ctx.close_path()
        set_col(ctx, '#20282E'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # rudder (rotates about its stock)
        ra = ev(self.rudder, t); dmg = ev(self.damage, t)
        if dmg != 'missing':
            ctx.save(); ctx.translate(-261, 44); ctx.rotate(math.radians(ra) * 0.25); ctx.scale(math.cos(math.radians(ra)) * 0.4 + 0.6, 1)
            ctx.translate(261, -44)
            self._rudder_path(ctx, broken=dmg == 'broken')
            set_col(ctx, '#2A3238'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
            if dmg == 'cracked':
                ctx.move_to(-276, 96); ctx.line_to(-262, 106); ctx.line_to(-270, 118); ctx.line_to(-254, 132)
                set_col(ctx, '#E8EEF0'); ctx.set_line_width(2.5); ctx.stroke()
            ctx.restore()
        # hull
        P = catmull(self.HULL, 8, closed=True)
        poly(ctx, P); set_col(ctx, self.hull_c); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        ctx.rectangle(-400, 14, 800, 80); set_col(ctx, self.bottom_c); ctx.fill()          # antifouling
        ctx.rectangle(-400, -6, 800, 10); set_col(ctx, self.stripe_c); ctx.fill()          # boot stripe
        g = cairo.LinearGradient(0, -50, 0, 50); g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0.1, 0.15, 0.18)
        ctx.set_source(g); ctx.paint()
        ctx.restore()
        poly(ctx, P); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        # portholes
        for x in (-60, 0, 60):
            circle(ctx, x, -24, 6); set_col(ctx, '#2B4A5C'); ctx.fill()
        # cabin
        ctx.move_to(-150, -46); ctx.line_to(-130, -86); ctx.line_to(70, -86); ctx.line_to(110, -46); ctx.close_path()
        set_col(ctx, '#E4E5E0'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()
        for x in (-110, -50, 10):
            rrect(ctx, x, -78, 44, 18, 5); set_col(ctx, '#2B4A5C'); ctx.fill()
        # crew
        for i in range(self.crew):
            cx = -210 + i * 50
            rrect(ctx, cx - 14, -96, 28, 50, 10); set_col(ctx, ['#C8453A', '#2F6FA0', '#E0A33A'][i % 3]); ctx.fill_preserve()
            set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, cx, -110, 13); set_col(ctx, '#E2B58F'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
            ctx.move_to(cx - 13, -114); ctx.curve_to(cx - 10, -128, cx + 10, -128, cx + 13, -114); ctx.close_path(); set_col(ctx, '#20282E'); ctx.fill()
        # mast + boom + sails
        if self.sails:
            ctx.move_to(-20, -86); ctx.line_to(-20, -640); set_col(ctx, '#C9CCCB'); ctx.set_line_width(9); ctx.stroke()
            ctx.move_to(-20, -640); ctx.line_to(-20, -86); set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()
            flutter = 6 * math.sin(t * 2.1)
            # main
            ctx.move_to(-26, -628); ctx.curve_to(-90 + flutter, -460, -170 + flutter, -280, -246, -124); ctx.line_to(-26, -124); ctx.close_path()
            set_col(ctx, '#F4EFE4'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3.5); ctx.stroke()
            ctx.set_source_rgba(0.55, 0.5, 0.42, 0.35); ctx.set_line_width(2)
            for y in (-500, -380, -260):
                ctx.move_to(-26, y); ctx.line_to(-26 - (y + 628) / 504 * 220, y + 10); ctx.stroke()
            # jib
            ctx.move_to(-12, -600); ctx.curve_to(70 + flutter, -420, 160, -250, 236, -70); ctx.line_to(-12, -96); ctx.close_path()
            set_col(ctx, '#ECE6D8'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3.5); ctx.stroke()
            ctx.move_to(-20, -124); ctx.line_to(-260, -120); set_col(ctx, '#3A4148'); ctx.set_line_width(7); ctx.stroke()
            ctx.move_to(-20, -640); ctx.line_to(318, -60); ctx.move_to(-20, -640); ctx.line_to(-300, -44)
            ctx.set_source_rgba(0.1, 0.12, 0.14, 0.6); ctx.set_line_width(1.5); ctx.stroke()
        ctx.restore()
        # submerged tint: water colour over the parts below the waterline (ATOP = only on boat pixels)
        ctx.set_operator(cairo.OPERATOR_ATOP)
        g = cairo.LinearGradient(0, 4, 0, 220)
        g.add_color_stop_rgba(0, 0.10, 0.36, 0.42, 0.25); g.add_color_stop_rgba(1, 0.05, 0.22, 0.28, 0.55)
        ctx.set_source(g); ctx.rectangle(-700, 4, 1400, 400); ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source(); ctx.paint()

def rudder_piece(boat, t_break, fall=1.6, spin=260, **kw):
    """The snapped rudder blade: starts at the boat's rudder and tumbles down."""
    sx = 1 if boat.facing == 'right' else -1
    class Piece(Element):
        def draw(self, ctx, lt):
            ctx.save(); ctx.scale(sx, 1)
            ctx.translate(262, -112)
            ctx.move_to(-266, 82); ctx.line_to(-250, 78); ctx.curve_to(-242, 110, -244, 140, -252, 178)
            ctx.curve_to(-262, 186, -278, 184, -284, 172); ctx.curve_to(-286, 130, -282, 100, -272, 72); ctx.close_path()
            set_col(ctx, '#2A3238'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
            ctx.restore()
    p0 = boat.rudder_world(t_break)
    sc = ev(boat.scale, 0); sc = sc if not isinstance(sc, tuple) else sc[0]
    def pos(lt):
        return (p0[0] - sx * 50 * lt, p0[1] + 20 * lt + 55 * lt * lt)
    return Piece(pos=pos, rot=lambda lt: -sx * spin * lt * 0.35, scale=sc, t0=t_break, **kw)

Sailboat.rudder_piece = lambda self, t_break, **kw: rudder_piece(self, t_break, **kw)

class Speedboat(_Floating):
    """Small white fishing/motor boat (reference fishing scene)."""
    def __init__(self, facing='right', crew=2, **kw):
        super().__init__(**kw); self.facing, self.crew = facing, crew
    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        P = catmull([(-250, -40), (240, -40), (330, -60), (260, 10), (180, 34), (-230, 34), (-250, 0)], 6, closed=True)
        rrect(ctx, -290, -66, 34, 74, 6); set_col(ctx, '#1E2328'); ctx.fill()
        poly(ctx, P); set_col(ctx, '#F2F1EC'); ctx.fill_preserve()
        ctx.save(); ctx.clip(); ctx.rectangle(-400, 4, 800, 60); set_col(ctx, '#1E3A4C'); ctx.fill(); ctx.restore()
        poly(ctx, P); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, 20, -110, 90, 70, 6); set_col(ctx, '#ECECE6'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        rrect(ctx, 36, -96, 58, 26, 4); set_col(ctx, '#2B4A5C'); ctx.fill()
        for i in range(self.crew):
            cx = -150 + i * 120
            rrect(ctx, cx - 16, -112, 32, 72, 10); set_col(ctx, ['#2F6FA0', '#C8453A'][i % 2]); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            circle(ctx, cx, -128, 15); set_col(ctx, '#E2B58F'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
            ctx.move_to(cx - 15, -131); ctx.curve_to(cx - 12, -148, cx + 12, -148, cx + 15, -131); ctx.close_path(); set_col(ctx, '#20282E'); ctx.fill()
        ctx.restore()
