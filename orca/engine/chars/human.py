"""Simple flat human figure (reference fishermen / scientist style): round head,
beanie or hair, coloured jacket or lab coat, outline.

Human(pos, scale, coat='#2F6FA0' | 'lab', pose='stand'|'point'|'shrug'|'clipboard'|'wave'|'panic',
      glasses=False, hat='beanie'|'hair'|None, facing='right')
Origin at the feet; height ~300 units.
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, set_col, circle, rrect, TAU, PAL
OUT = PAL.OUTLINE
SKIN = '#E2B58F'

POSES = {   # (left shoulder deg, left elbow deg, right shoulder, right elbow) 0 = down, + = forward/up
    'stand': (8, 0, -8, 0), 'point': (6, 0, 95, 0), 'shrug': (30, 80, 30, 80),
    'clipboard': (8, 0, 60, 70), 'wave': (6, 0, 150, 30), 'panic': (150, 20, -150, -20),
}

class Human(Element):
    def __init__(self, coat='#2F6FA0', pose='stand', glasses=False, hat='beanie', facing='right',
                 pants='#2A2F35', hair='#3A2A20', **kw):
        super().__init__(**kw)
        self.coat, self.pose_, self.glasses, self.hat, self.facing = coat, pose, glasses, hat, facing
        self.pants, self.hair = pants, hair

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'left': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        pose = ev(self.pose_, t)
        ang = POSES[pose] if isinstance(pose, str) else pose
        if pose == 'panic':
            ang = (ang[0] + 15 * math.sin(t * 14), ang[1], ang[2] + 15 * math.sin(t * 14 + 1), ang[3])
        breathe = 1.5 * math.sin(TAU * t / 3.2)
        lab = self.coat == 'lab'
        coat = '#F1F1EC' if lab else self.coat
        # legs
        for x in (-16, 16):
            ctx.move_to(x, -110); ctx.line_to(x * 1.1, 0); set_col(ctx, self.pants); ctx.set_line_width(24); ctx.stroke()
        for x in (-16, 16):
            rrect(ctx, x * 1.1 - 14, -10, 34, 12, 5); set_col(ctx, '#1A1E22'); ctx.fill()
        # arms helper
        def arm(sx, a1, a2, front):
            sh = np.array([sx, -205 + breathe])
            r1 = math.radians(a1); r2 = math.radians(a1 + a2)
            el = sh + 52 * np.array([math.sin(r1), math.cos(r1)])
            hd = el + 50 * np.array([math.sin(r2), math.cos(r2)])
            ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*hd)
            set_col(ctx, OUT); ctx.set_line_width(22); ctx.stroke()
            ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*hd)
            set_col(ctx, coat); ctx.set_line_width(16); ctx.stroke()
            circle(ctx, hd[0], hd[1], 9); set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            return hd
        arm(-30, -ang[0], -ang[1], False)
        # torso
        rrect(ctx, -38, -226 + breathe, 76, 130 if lab else 120, 18); set_col(ctx, coat); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        if lab:
            ctx.move_to(0, -222 + breathe); ctx.line_to(0, -100); set_col(ctx, '#C9CCC8'); ctx.set_line_width(2.5); ctx.stroke()
            ctx.move_to(-14, -224 + breathe); ctx.line_to(0, -196 + breathe); ctx.line_to(14, -224 + breathe)
            set_col(ctx, '#5A86A8'); ctx.set_line_width(6); ctx.stroke()
        hd = arm(30, ang[2], ang[3], True)
        if pose == 'clipboard':
            ctx.save(); ctx.translate(hd[0] + 6, hd[1] - 20); ctx.rotate(-0.2)
            rrect(ctx, -18, -26, 40, 52, 4); set_col(ctx, '#B9875A'); ctx.fill(); rrect(ctx, -14, -20, 32, 42, 2); set_col(ctx, '#F5F3EE'); ctx.fill()
            ctx.restore()
        # head
        hy = -262 + breathe
        circle(ctx, 0, hy, 32); set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        if self.hat == 'beanie':
            ctx.move_to(-33, hy - 4); ctx.curve_to(-30, hy - 46, 30, hy - 46, 33, hy - 4); ctx.close_path()
            set_col(ctx, '#20282E'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        elif self.hat == 'hair':
            ctx.move_to(-33, hy); ctx.curve_to(-34, hy - 44, 30, hy - 48, 34, hy - 8); ctx.curve_to(10, hy - 20, -10, hy - 18, -33, hy)
            set_col(ctx, self.hair); ctx.fill()
        circle(ctx, 14, hy + 2, 3.5); set_col(ctx, '#1A1E22'); ctx.fill()
        if self.glasses:
            circle(ctx, 14, hy + 2, 10); set_col(ctx, '#1A1E22'); ctx.set_line_width(3); ctx.stroke()
            ctx.move_to(4, hy); ctx.line_to(-20, hy - 4); ctx.stroke()
        ctx.move_to(10, hy + 16); ctx.line_to(22, hy + 15); set_col(ctx, '#7A4A3A'); ctx.set_line_width(2.5); ctx.stroke()
        ctx.restore()
