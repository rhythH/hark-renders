"""Crocodile-video cast: Tiger, BullShark, Buffalo, Pig, Hyena, Snorkeller, Fisherman (+ Esky, Bucket props).

All side views, flat fills + dark outline + painted shading, always moving (breathing, tail, ears, kick).
Every animal takes facing='left'|'right' and style='color'|'silhouette'|'outline' (outline = line-art
for evidence boards; outline_color/outline_dash available). Origin = ground under the body centre
unless the class says otherwise.
"""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, set_col, hexc, mix, circle, rrect, TAU, PAL, catmull, rng
from .orca import Deform, rot_pts, _path, _teeth
OUT = PAL.OUTLINE


def _sm(pts, n=8, closed=True):
    return catmull(pts, n, closed=closed)


class _Animal(Element):
    def __init__(self, facing='left', style='color', sil_color='#061722', outline_color=PAL.CYAN, dash=None,
                 outline=6.0, **kw):
        super().__init__(**kw)
        self.facing, self.style, self.sil_color, self.oc, self.dash, self.ow = facing, style, sil_color, outline_color, dash, outline

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.paint(ctx, t)
        ctx.restore()

    # shape helper: fill (or silhouette / outline) a closed polygon
    def shape(self, ctx, P, col, ow=None, shade=None):
        ow = self.ow if ow is None else ow
        _path(ctx, P)
        if self.style == 'silhouette':
            set_col(ctx, self.sil_color); ctx.fill(); return
        if self.style == 'outline':
            ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(3.0)
            if self.dash: ctx.set_dash(self.dash)
            ctx.stroke(); ctx.set_dash([]); return
        set_col(ctx, col); ctx.fill_preserve()
        if shade:
            ctx.save(); ctx.clip(); shade(); ctx.restore(); _path(ctx, P)
        set_col(ctx, OUT); ctx.set_line_width(ow); ctx.stroke()

    @property
    def colored(self):
        return self.style == 'color'


def _limb(a, b, c, wa, wb, wc, n=4):
    """Tapered limb polygon through joints a-b-c with widths."""
    a, b, c = map(np.asarray, (a, b, c))
    def nrm(p, q):
        v = q - p; m = np.array([-v[1], v[0]]); return m / (np.linalg.norm(m) + 1e-9)
    n0, n2 = nrm(a, b), nrm(b, c); n1 = n0 + n2; n1 /= (np.linalg.norm(n1) + 1e-9)
    L = [a + n0 * wa / 2, b + n1 * wb / 2, c + n2 * wc / 2]
    R = [a - n0 * wa / 2, b - n1 * wb / 2, c - n2 * wc / 2]
    return np.vstack([catmull(L, n), catmull(R[::-1], n)])


# ============================================================================ TIGER
class Tiger(_Animal):
    """Bengal tiger, side view facing LEFT, ~620 units nose->rump (+tail), shoulder ~250 high.
    Tiger(pose='stand'|'drink'|'dragged'|'lying', walk=0..1 (leg cycle), missing_leg=False (near hind leg
    dashed / absent, for the evidence board), style, facing). Origin = ground under the chest/rump middle."""
    def __init__(self, pose='stand', walk=0.0, missing_leg=False, **kw):
        super().__init__(**kw); self.pose, self.walk, self.missing_leg = pose, walk, missing_leg

    def paint(self, ctx, t):
        pose = ev(self.pose, t)
        br = 2.5 * math.sin(TAU * t / 3.0)
        ORANGE, DARK, WHITE = '#E58B35', '#1B1410', '#F4EBDC'
        wk = ev(self.walk, t); wp = TAU * t / 1.2
        tilt = 0.0; by = 0.0
        if pose == 'lying': by = 120
        if pose == 'dragged': tilt = 9 + 3 * math.sin(t * 7)
        ctx.save()
        ctx.translate(0, by)
        if tilt: ctx.translate(-100, -60); ctx.rotate(math.radians(tilt)); ctx.translate(100, 60)
        # body landmarks
        body = _sm([(-200, -205 + br * 0.3), (-150, -248 + br), (-40, -238), (80, -236), (180, -250), (228, -214),
                    (230, -150), (190, -118), (90, -112), (-40, -112 + br * 0.5), (-150, -118), (-205, -150)], 8)
        # head / neck
        if pose == 'drink':
            hx, hy, ha = -255, -44, 38
        elif pose == 'lying':
            hx, hy, ha = -255, -190, -4 + 3 * math.sin(t * 0.8)
        elif pose == 'dragged':
            hx, hy, ha = -270, -250, -18
        else:
            hx, hy, ha = -262, -246 + br, 0
        # tail
        sw = math.sin(TAU * t / 2.2)
        tail = catmull([(222, -228), (280, -222 + 6 * sw), (330, -180 + 14 * sw), (360, -120 + 20 * sw), (352, -70 + 26 * sw)], 6)
        tl = tail + np.array([[0, -9]]) * np.linspace(1, 0.8, len(tail))[:, None]
        tr = tail + np.array([[0, 9]]) * np.linspace(1, 0.8, len(tail))[:, None]
        def tshade():
            for i in range(1, len(tail) - 1, 3):
                p = tail[i]; ctx.move_to(p[0] - 6, p[1] - 14); ctx.line_to(p[0] + 4, p[1] + 14)
            set_col(ctx, DARK); ctx.set_line_width(7); ctx.stroke()
        self.shape(ctx, np.vstack([tl, tr[::-1]]), ORANGE, shade=tshade if self.colored else None)
        # legs (far pair first)
        def leg(x0, y0, kind, far, ph):
            sw_ = wk * math.sin(wp + ph)
            if pose == 'lying':
                a, b, c = (x0, y0 + 10), (x0 - 50, y0 + 70), (x0 - 120, y0 + 100)
                if kind == 'h': a, b, c = (x0, y0 + 10), (x0 + 10, y0 + 70), (x0 - 70, y0 + 102)
            elif kind == 'f':
                fx = x0 - 6 + 34 * sw_ - (20 if pose == 'drink' else 0)
                a, b, c = (x0, y0), (x0 + 6 + 20 * sw_, y0 + 70), (fx, -10 + 10 * max(0, math.cos(wp + ph)) * wk)
            else:
                a, b, c = (x0, y0), (x0 + 34 + 20 * sw_, y0 + 62), (x0 + 10 + 34 * sw_, -10 + 10 * max(0, math.cos(wp + ph)) * wk)
                if pose == 'dragged' and not far:
                    a, b, c = (x0, y0), (x0 + 70, y0 + 60), (x0 + 150, y0 + 95)
            col = mix(ORANGE, '#000000', 0.3) if far else hexc(ORANGE)
            P = _limb(a, b, c, 58 if kind == 'h' else 50, 36, 30)
            if not far and kind == 'h' and self.missing_leg:
                _path(ctx, P); ctx.set_dash([10, 8]); ctx.set_source_rgba(*hexc(PAL.RED if self.style != 'outline' else self.oc))
                ctx.set_line_width(3); ctx.stroke(); ctx.set_dash([]); return
            def sh():
                for k in range(3):
                    p = np.asarray(a) * (0.75 - k * 0.2) + np.asarray(b) * (0.25 + k * 0.2)
                    ctx.move_to(p[0] - 22, p[1] - 4); ctx.line_to(p[0] + 4, p[1] + 2)
                set_col(ctx, DARK); ctx.set_line_width(5); ctx.stroke()
            self.shape(ctx, P, col, shade=sh if self.colored else None)
            ctx.save(); ctx.translate(c[0] - 8, c[1] + 2); ctx.scale(1.25, 0.6); circle(ctx, 0, 0, 24); ctx.restore()
            if self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
            elif self.style == 'outline': ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(3); ctx.stroke()
            else: set_col(ctx, col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        leg(-140, -150, 'f', True, PI_)
        leg(150, -160, 'h', True, 0)
        # body
        def bshade():
            # white belly
            ctx.move_to(-210, -150); ctx.curve_to(-120, -130, 60, -128, 210, -140); ctx.line_to(210, -90); ctx.line_to(-210, -90); ctx.close_path()
            set_col(ctx, WHITE); ctx.fill()
            # stripes
            r = rng(3)
            for i, x in enumerate(np.linspace(-150, 210, 15)):
                w = r.uniform(7, 13); y0 = -250; L = r.uniform(70, 120)
                ctx.move_to(x - w, y0); ctx.curve_to(x - w + 8, y0 + L * 0.4, x - 8, y0 + L * 0.7, x - 2 + r.uniform(-10, 10), y0 + L)
                ctx.curve_to(x + 3, y0 + L * 0.7, x + w, y0 + L * 0.4, x + w, y0); ctx.close_path()
                set_col(ctx, DARK); ctx.fill()
            g = cairo.LinearGradient(0, -250, 0, -110); g.add_color_stop_rgba(0, 1, 0.85, 0.6, 0.18); g.add_color_stop_rgba(1, 0, 0, 0, 0.18)
            ctx.set_source(g); ctx.paint()
        self.shape(ctx, body, ORANGE, shade=bshade if self.colored else None)
        # neck + head
        # neck drawn in world space between head and shoulders
        if pose == 'drink':
            npoly = _sm([(-175, -230), (-230, -140), (-250, -70), (-215, -40), (-180, -110), (-130, -150)], 6)
        elif pose == 'lying':
            npoly = _sm([(-170, -235), (-215, -225), (-235, -175), (-190, -150), (-150, -150)], 6)
        else:
            npoly = _sm([(-160, -245), (-220, -260 + br), (-240, -215 + br), (-200, -170), (-150, -160)], 6)
        self.shape(ctx, npoly, ORANGE, shade=(lambda: (set_col(ctx, DARK), ctx.set_line_width(6),
                                                       [ (ctx.move_to(*(npoly[i] + np.array([0, 4]))), ctx.line_to(*(npoly[i] + np.array([12, 30]))), ctx.stroke()) for i in range(2, len(npoly) // 2, 2)])) if self.colored else None)
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(math.radians(ha))
        self._head(ctx, t, ORANGE, DARK, WHITE)
        ctx.restore()
        leg(-110, -150, 'f', False, 0)
        leg(170, -165, 'h', False, PI_)
        ctx.restore()

    def _head(self, ctx, t, ORANGE, DARK, WHITE):
        ear = 3 * math.sin(t * 2.3) if (t % 3.1) < 0.4 else 0
        for ex in (22, 2):
            ctx.save(); ctx.translate(ex, -52); ctx.rotate(math.radians(-10 + ear))
            P = _sm([(-16, 6), (-14, -14), (0, -26), (14, -16), (16, 6)], 5)
            self.shape(ctx, P, ORANGE if ex == 22 else mix(ORANGE, '#000000', 0.3), ow=4.5)
            ctx.restore()
        head = _sm([(-62, 6), (-58, -20), (-30, -46), (10, -56), (46, -44), (62, -10), (52, 26), (20, 44), (-30, 40), (-58, 26)], 7)
        def hs():
            ctx.move_to(-66, 8); ctx.curve_to(-40, 16, -10, 18, 10, 46); ctx.line_to(-66, 46); ctx.close_path(); set_col(ctx, WHITE); ctx.fill()
            ctx.move_to(-4, 2); ctx.curve_to(10, -12, 30, -6, 50, 20); ctx.curve_to(36, 30, 16, 26, -4, 2); ctx.close_path(); set_col(ctx, WHITE); ctx.fill()
            for x, y, a in ((18, -50, 0.3), (32, -42, 0.5), (46, -30, 0.8), (40, 6, 0.2), (30, 22, 0.1)):
                ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.scale(1, 0.35); circle(ctx, 0, 0, 12); ctx.restore()
                set_col(ctx, DARK); ctx.fill()
        self.shape(ctx, head, ORANGE, ow=5, shade=hs if self.colored else None)
        if not self.colored: return
        # eye, nose, mouth
        ctx.save(); ctx.translate(-26, -20); ctx.scale(1, 0.75); circle(ctx, 0, 0, 6.5); set_col(ctx, '#E9C23C'); ctx.fill()
        circle(ctx, 0, 0, 3); set_col(ctx, '#111111'); ctx.fill(); ctx.restore()
        ctx.move_to(-38, -26); ctx.line_to(-16, -28); set_col(ctx, DARK); ctx.set_line_width(3); ctx.stroke()
        ctx.move_to(-66, 0); ctx.line_to(-56, -6); ctx.line_to(-56, 6); ctx.close_path(); set_col(ctx, '#C9726A'); ctx.fill()
        ctx.move_to(-58, 10); ctx.curve_to(-50, 22, -36, 22, -30, 16); set_col(ctx, DARK); ctx.set_line_width(2.5); ctx.stroke()
        ctx.set_line_width(1.2); ctx.set_source_rgba(1, 1, 1, 0.8)
        for k in (-1, 0, 1):
            ctx.move_to(-48, 10); ctx.line_to(-86, 6 + k * 7); ctx.stroke()

PI_ = math.pi


# ============================================================================ BULL SHARK
B_TOP = [(-500, 22), (-494, -6), (-470, -40), (-420, -78), (-330, -112), (-200, -132), (-60, -134), (80, -118),
         (200, -86), (300, -52), (380, -26), (420, -16)]
B_BOT = [(420, 14), (370, 24), (280, 46), (160, 82), (40, 108), (-80, 118), (-200, 112), (-310, 94), (-400, 70),
         (-460, 50), (-492, 36), (-500, 24)]
B_TAIL = [(420, -16), (450, -44), (494, -128), (530, -196), (540, -186), (524, -100), (510, -18), (518, 22),
          (546, 86), (538, 98), (492, 56), (448, 26), (420, 14)]
B_D1 = [(-130, -132), (-104, -196), (-70, -262), (-52, -276), (-42, -262), (-30, -190), (10, -132), (30, -126)]
B_D2 = [(230, -76), (246, -104), (262, -112), (268, -100), (276, -64)]
B_PEC = [(0, 0), (40, 24), (130, 100), (200, 166), (180, 172), (90, 130), (20, 64), (-12, 20)]


class BullShark(_Animal):
    """Bull shark: stocky grey body, blunt short snout, tall first dorsal, white belly. Facing LEFT,
    1000 units long. BullShark(swim=1, period=2.0, jaw=deg, thrash=0..1|K (violent bending + roll-ish
    wobble, for 'in the croc's jaws'), style, facing)."""
    def __init__(self, swim=1.0, period=2.0, jaw=0.0, thrash=0.0, **kw):
        super().__init__(**kw)
        self.swim, self.period, self.jaw, self.thrash = swim, period, jaw, thrash
        self.top = catmull(B_TOP, 8); self.bot = catmull(B_BOT, 8); self.tail = catmull(B_TAIL, 6)
        self.d1 = catmull(B_D1, 6); self.d2 = catmull(B_D2, 5); self.pec = catmull(B_PEC, 6, closed=True)

    def paint(self, ctx, t):
        th = float(ev(self.thrash, t))
        if th > 0:
            ctx.rotate(math.radians(th * (14 * math.sin(t * 13) + 6 * math.sin(t * 21))))
        per = self.period / (1 + 3.5 * th)
        D = Deform(t, 30 * ev(self.swim, t) + 70 * th, per, bend=th * 40 * math.sin(t * 9))
        top, bot, tail, d1, d2 = D(self.top), D(self.bot), D(self.tail, fluke=True), D(self.d1), D(self.d2)
        jaw = ev(self.jaw, t)
        GREY, GREY_D, BELLY = '#7E8B93', '#66737B', '#EEF0EC'
        if jaw > 0:
            hinge = np.array([-400.0, 50.0]); a = -math.radians(jaw)
            m = bot[:, 0] < -380
            bot = bot.copy(); bot[m] = rot_pts(bot[m], hinge, a)
        body = np.vstack([top, tail[1:], bot[1:]])
        for fin in (d2,):
            P = np.vstack([fin, [fin[0] + np.array([30, 20])]])
            self.shape(ctx, P, GREY_D, ow=self.ow * 0.8)
        P = np.vstack([d1, [d1[0] + np.array([60, 30])]])
        self.shape(ctx, P, GREY_D)
        def sh():
            xs = np.linspace(-520, 440, 40)
            edge = 30 + 10 * np.sin(xs * 0.02) + np.where(xs < -350, (xs + 350) * -0.15, 0) + np.where(xs > 200, (xs - 200) * -0.12, 0)
            pts = D(np.column_stack([xs, edge]))
            ctx.move_to(-560, 300)
            for x, y in pts: ctx.line_to(float(x), float(y))
            ctx.line_to(560, 300); ctx.close_path(); set_col(ctx, BELLY); ctx.fill()
            g = cairo.LinearGradient(0, -140, 0, 20)
            g.add_color_stop_rgba(0, 0.25, 0.3, 0.35, 0.45); g.add_color_stop_rgba(1, 0.25, 0.3, 0.35, 0)
            ctx.set_source(g); ctx.rectangle(-600, -200, 1200, 220); ctx.fill()
            ctx.save(); ctx.translate(-200, -90); ctx.scale(1, 0.3)
            rg = cairo.RadialGradient(0, 0, 0, 0, 0, 300); rg.add_color_stop_rgba(0, 0.8, 0.86, 0.9, 0.25); rg.add_color_stop_rgba(1, 0.8, 0.86, 0.9, 0)
            ctx.set_source(rg); circle(ctx, 0, 0, 300); ctx.fill(); ctx.restore()
        if jaw > 0 and self.colored:
            lip_u = catmull([(-488, 40), (-450, 46), (-410, 50)], 5)
            lip_l = rot_pts(lip_u + np.array([0, 6]), np.array([-400.0, 50.0]), -math.radians(jaw))
            _path(ctx, np.vstack([lip_u, lip_l[::-1]])); set_col(ctx, '#5A1A1E'); ctx.fill()
            _teeth(ctx, lip_u, 7, 16, up=False, offset=0); _teeth(ctx, lip_l, 7, 14, up=True, offset=0.5)
        self.shape(ctx, body, GREY, shade=sh if self.colored else None)
        if not self.colored:
            pc = D(self.pec + np.array([-280.0, 70])); self.shape(ctx, pc, GREY_D); return
        ctx.set_line_width(3); set_col(ctx, '#3B444A')
        for i in range(5):
            x = -330 + i * 20
            g0 = D(np.array([[x, -40.0], [x + 6, 4], [x, 46]]))
            ctx.move_to(*g0[0]); ctx.curve_to(*g0[1], *g0[1], *g0[2]); ctx.stroke()
        e = D(np.array([[-430.0, -18]]))[0]
        circle(ctx, e[0], e[1], 7); set_col(ctx, '#050607'); ctx.fill()
        circle(ctx, e[0] - 2, e[1] - 2.5, 2); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.fill()
        if jaw <= 0:
            lu = D(catmull([(-486, 40), (-450, 46), (-410, 50)], 5)); _path(ctx, lu, False); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        pc = D(self.pec + np.array([-280.0, 70]))
        self.shape(ctx, pc, GREY_D)


# ============================================================================ WATER BUFFALO
class Buffalo(_Animal):
    """Water buffalo, side view facing LEFT (~560 units body, ~300 high at the shoulder), big swept-back
    crescent horns. Buffalo(pose='stand'|'drink', walk=0..1, style, facing). Origin = ground mid-body."""
    def __init__(self, pose='stand', walk=0.0, **kw):
        super().__init__(**kw); self.pose, self.walk = pose, walk

    def paint(self, ctx, t):
        pose = ev(self.pose, t); wk = ev(self.walk, t); wp = TAU * t / 1.6
        br = 2.5 * math.sin(TAU * t / 3.3)
        BODY, DARK, HORN = '#3F4447', '#2B2F31', '#B9AE94'
        # tail swish
        sw = math.sin(TAU * t / 1.9)
        tail = catmull([(250, -240), (276, -190 + 4 * sw), (284 + 10 * sw, -130), (282 + 22 * sw, -90)], 6)
        ctx.move_to(*tail[0])
        for p in tail[1:]: ctx.line_to(*p)
        set_col(ctx, OUT if self.style != 'silhouette' else self.sil_color); ctx.set_line_width(10); ctx.stroke()
        if self.style == 'color':
            ctx.move_to(*tail[0])
            for p in tail[1:]: ctx.line_to(*p)
            set_col(ctx, BODY); ctx.set_line_width(5); ctx.stroke()
        tip = tail[-1]; ctx.save(); ctx.translate(*tip); ctx.scale(0.6, 1); circle(ctx, 0, 6, 14); ctx.restore()
        set_col(ctx, DARK if self.colored else self.sil_color); ctx.fill()
        def leg(x0, far, ph, front):
            s_ = wk * math.sin(wp + ph)
            a = (x0, -150); b = (x0 + (6 if front else 22) + 18 * s_, -80); c = (x0 + 26 * s_, -14 + 10 * max(0, math.cos(wp + ph)) * wk)
            if pose == 'drink' and front: b = (x0 - 16, -80); c = (x0 - 34, -14)
            col = mix(BODY, '#000000', 0.35) if far else hexc(BODY)
            self.shape(ctx, _limb(a, b, c, 58 if not front else 52, 32, 26), col)
            ctx.move_to(c[0] - 18, c[1] + 2); ctx.line_to(c[0] + 16, c[1] + 2); ctx.line_to(c[0] + 12, c[1] + 16); ctx.line_to(c[0] - 20, c[1] + 16); ctx.close_path()
            if self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
            elif self.style == 'outline': ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(3); ctx.stroke()
            else: set_col(ctx, '#1E2123'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        leg(-150, True, math.pi, True); leg(180, True, 0, False)
        body = _sm([(-230, -230), (-190, -298 + br), (-80, -296 + br), (60, -280), (200, -282), (262, -250), (268, -170),
                    (230, -128), (100, -120), (-60, -112 + br * 0.5), (-180, -122), (-236, -160)], 8)
        def bs():
            g = cairo.LinearGradient(0, -300, 0, -110); g.add_color_stop_rgba(0, 0.7, 0.74, 0.76, 0.22); g.add_color_stop_rgba(1, 0, 0, 0, 0.3)
            ctx.set_source(g); ctx.paint()
            ctx.move_to(-200, -180); ctx.curve_to(-120, -170, -40, -160, 40, -168); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.set_line_width(3); ctx.stroke()
            ctx.move_to(120, -270); ctx.curve_to(160, -220, 170, -180, 150, -140); ctx.stroke()
        self.shape(ctx, body, BODY, shade=bs if self.colored else None)
        # head
        if pose == 'drink':
            hx, hy, ha = -270, -70, 62
            neck = _sm([(-190, -280), (-250, -220), (-290, -120), (-250, -80), (-200, -150), (-160, -190)], 6)
        else:
            hx, hy, ha = -286, -250 + br, 12
            neck = _sm([(-180, -290 + br), (-250, -290 + br), (-290, -250 + br), (-260, -200), (-200, -170), (-170, -200)], 6)
        self.shape(ctx, neck, BODY)
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(math.radians(ha))
        ear = 6 * math.sin(t * 3) if (t % 2.7) < 0.35 else 0
        ctx.save(); ctx.translate(30, -22); ctx.rotate(math.radians(20 + ear))
        self.shape(ctx, _sm([(0, -8), (40, -16), (54, -4), (40, 8), (0, 8)], 5), DARK, ow=4); ctx.restore()
        head = _sm([(-70, 30), (-74, 0), (-60, -30), (-20, -44), (30, -40), (52, -10), (40, 30), (0, 46), (-50, 46)], 7)
        self.shape(ctx, head, BODY, ow=5, shade=(lambda: (ctx.move_to(-80, 20), ctx.line_to(-30, 20), ctx.line_to(-30, 60), ctx.line_to(-80, 60), ctx.close_path(), ctx.set_source_rgba(0.55, 0.57, 0.58, 0.5), ctx.fill())) if self.colored else None)
        # horns: big crescent sweeping back
        horn = _sm([(-10, -40), (20, -78), (80, -96), (150, -82), (186, -50), (176, -46), (140, -66), (80, -72), (30, -56), (10, -34)], 6)
        self.shape(ctx, horn, HORN, ow=4.5, shade=(lambda: [(ctx.move_to(x, -60 - (x - 60) * 0.1 - 18), ctx.line_to(x + 4, -60 - (x - 60) * 0.1 + 6)) for x in range(30, 170, 16)] and (ctx.set_source_rgba(0.3, 0.27, 0.2, 0.45), ctx.set_line_width(2), ctx.stroke())) if self.colored else None)
        if self.colored:
            circle(ctx, -30, -12, 5.5); set_col(ctx, '#0A0A0A'); ctx.fill(); circle(ctx, -32, -14, 1.6); ctx.set_source_rgba(1, 1, 1, .8); ctx.fill()
            ctx.save(); ctx.translate(-66, 22); ctx.scale(1, 0.6); circle(ctx, 0, 0, 5); set_col(ctx, '#0A0A0A'); ctx.fill(); ctx.restore()
        ctx.restore()
        leg(-110, False, 0, True); leg(220, False, math.pi, False)


# ============================================================================ PIG
class Pig(_Animal):
    """Feral pig (dark bristly boar), side view facing LEFT, ~300 units long. Pig(pose='stand'|'root',
    walk=0..1, style, facing). Origin = ground mid-body."""
    def __init__(self, pose='stand', walk=0.0, **kw):
        super().__init__(**kw); self.pose, self.walk = pose, walk

    def paint(self, ctx, t):
        pose = ev(self.pose, t); wk = ev(self.walk, t); wp = TAU * t / 0.9
        BODY, DARK, SNOUT = '#4E4039', '#342923', '#9C7468'
        br = 1.5 * math.sin(TAU * t / 2.4)
        sw = math.sin(TAU * t / 0.7)
        ctx.move_to(140, -96); ctx.curve_to(156, -96 + 4 * sw, 160, -80, 156 + 4 * sw, -62)
        set_col(ctx, OUT if self.style != 'silhouette' else self.sil_color); ctx.set_line_width(6); ctx.stroke()
        def leg(x0, far, ph):
            s_ = wk * math.sin(wp + ph)
            a, b, c = (x0, -60), (x0 + 4 + 8 * s_, -30), (x0 + 12 * s_, -4 + 6 * max(0, math.cos(wp + ph)) * wk)
            self.shape(ctx, _limb(a, b, c, 30, 18, 14), mix(BODY, '#000000', 0.35) if far else BODY, ow=4)
        leg(-80, True, math.pi); leg(100, True, 0)
        hd = 40 if pose == 'root' else 0
        body = _sm([(-120, -86), (-80, -134 + br), (20, -140 + br), (110, -126), (150, -94), (140, -58), (60, -46), (-60, -46), (-120, -60)], 8)
        def bs():
            ctx.set_source_rgba(0.1, 0.07, 0.05, 0.4); ctx.set_line_width(2)
            r = rng(2)
            for _ in range(36):
                x = r.uniform(-110, 140); y = r.uniform(-136, -60)
                ctx.move_to(x, y); ctx.line_to(x + 6, y - 7); ctx.stroke()
            ctx.move_to(-110, -126); ctx.curve_to(-40, -150, 40, -150, 120, -126); ctx.set_source_rgba(0.08, 0.06, 0.05, 0.6); ctx.set_line_width(8); ctx.stroke()
        self.shape(ctx, body, BODY, ow=5, shade=bs if self.colored else None)
        ctx.save(); ctx.translate(-118, -96 + hd); ctx.rotate(math.radians(28 if pose == 'root' else 4 * math.sin(t * 1.3)))
        head = _sm([(30, -40), (-20, -36), (-62, -14), (-82, 6), (-80, 22), (-40, 30), (20, 26), (40, 0)], 6)
        self.shape(ctx, head, BODY, ow=5)
        ctx.save(); ctx.translate(-82, 14); ctx.scale(0.45, 1); circle(ctx, 0, 0, 14); ctx.restore()
        if self.colored: set_col(ctx, SNOUT); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3.5); ctx.stroke()
        elif self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
        else: ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(2.5); ctx.stroke()
        ear = 8 * math.sin(t * 4) if (t % 2.3) < 0.3 else 0
        ctx.save(); ctx.translate(6, -36); ctx.rotate(math.radians(-30 + ear))
        self.shape(ctx, _sm([(-10, 4), (-6, -26), (10, -16), (10, 4)], 4), DARK, ow=3.5); ctx.restore()
        if self.colored:
            circle(ctx, -36, -10, 3.6); set_col(ctx, '#0A0A0A'); ctx.fill()
            ctx.move_to(-62, 18); ctx.curve_to(-60, 6, -52, 2, -46, 4); ctx.set_source_rgba(0.95, 0.92, 0.82, 1); ctx.set_line_width(3.5); ctx.stroke()
        ctx.restore()
        leg(-58, False, 0); leg(120, False, math.pi)


# ============================================================================ HYENA
class Hyena(_Animal):
    """Spotted hyena: high shoulders, sloping back, round ears, spots. Facing LEFT, ~420 long,
    shoulder ~230. Hyena(jaw=0..1 (bite), walk=0..1, style='color'|'silhouette'|'outline')."""
    def __init__(self, jaw=0.0, walk=0.0, **kw):
        super().__init__(**kw); self.jaw, self.walk = jaw, walk

    def paint(self, ctx, t):
        wk = ev(self.walk, t); wp = TAU * t / 1.0; jaw = ev(self.jaw, t)
        BODY, DARK = '#B59B6B', '#4B3A26'
        br = 2 * math.sin(TAU * t / 2.6)
        sw = math.sin(TAU * t / 1.8)
        tail = catmull([(170, -160), (196, -140 + 3 * sw), (206 + 6 * sw, -110), (210 + 10 * sw, -86)], 5)
        ctx.move_to(*tail[0])
        for p in tail[1:]: ctx.line_to(*p)
        set_col(ctx, OUT if self.style != 'silhouette' else self.sil_color); ctx.set_line_width(12); ctx.stroke()
        if self.colored:
            ctx.move_to(*tail[0])
            for p in tail[1:]: ctx.line_to(*p)
            set_col(ctx, DARK); ctx.set_line_width(7); ctx.stroke()
        def leg(x0, y0, far, ph, front):
            s_ = wk * math.sin(wp + ph)
            a, b, c = (x0, y0), (x0 + (4 if front else 26) + 14 * s_, (y0 - 10) / 2), (x0 + 20 * s_, -8 + 8 * max(0, math.cos(wp + ph)) * wk)
            self.shape(ctx, _limb(a, b, c, 40 if front else 46, 24, 18), mix(BODY, '#000000', 0.35) if far else BODY, ow=4.5)
        leg(-120, -150, True, math.pi, True); leg(130, -120, True, 0, False)
        body = _sm([(-170, -180), (-120, -238 + br), (-20, -228), (90, -190), (170, -168), (186, -130), (150, -100),
                    (40, -104), (-80, -116 + br * 0.5), (-160, -130)], 8)
        def bs():
            r = rng(5)
            for _ in range(28):
                x = r.uniform(-150, 180); y = r.uniform(-220, -110)
                circle(ctx, x, y, r.uniform(5, 9)); set_col(ctx, DARK, 0.85); ctx.fill()
            ctx.move_to(-150, -230); ctx.curve_to(-80, -248, 0, -230, 100, -194); set_col(ctx, DARK); ctx.set_line_width(10); ctx.stroke()
        self.shape(ctx, body, BODY, shade=bs if self.colored else None)
        neck = _sm([(-140, -230 + br), (-200, -234 + br), (-232, -200), (-200, -160), (-150, -150)], 6)
        self.shape(ctx, neck, BODY)
        ctx.save(); ctx.translate(-236, -200 + br)
        for ex in (24, 10):
            ctx.save(); ctx.translate(ex, -34); circle(ctx, 0, -12, 14); ctx.restore()
            if self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
            elif self.style == 'outline': ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(3); ctx.stroke()
            else: set_col(ctx, BODY if ex == 24 else mix(BODY, '#000000', 0.3)); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        a = math.radians(26 * jaw)
        lower = rot_pts(np.array(_sm([(-70, 10), (-60, 22), (-10, 26), (20, 14), (10, 4)], 5)), np.array([10.0, 8.0]), a)
        self.shape(ctx, lower, mix(BODY, '#000000', 0.2), ow=4)
        head = _sm([(-74, 6), (-70, -14), (-40, -34), (10, -42), (40, -24), (36, 10), (0, 18), (-50, 14)], 6)
        self.shape(ctx, head, BODY, ow=5, shade=(lambda: (ctx.move_to(-80, -10), ctx.line_to(-44, -10), ctx.line_to(-44, 20), ctx.line_to(-80, 20), ctx.close_path(), set_col(ctx, '#2A2118'), ctx.fill())) if self.colored else None)
        if self.colored:
            circle(ctx, -24, -14, 4); set_col(ctx, '#0A0A0A'); ctx.fill()
        ctx.restore()
        leg(-96, -150, False, 0, True); leg(150, -120, False, math.pi, False)


# ============================================================================ SNORKELLER
class Snorkeller(_Animal):
    """Snorkeller lying face-down AT the surface (local y=0 = waterline), head LEFT, ~360 units long.
    Back of the head, snorkel and back break the surface; arms forward or at sides, flutter-kicking fins.
    Snorkeller(kick=1, period=0.7, panic=0..1|K (head up, arms thrash, splashes), suit='#1F6F86',
    fins='#E8B32A', snorkel=PAL.ORANGE, arms='side'|'forward', style, facing)."""
    def __init__(self, kick=1.0, period=0.7, panic=0.0, suit='#1F6F86', fins=PAL.YELLOW, snorkel=PAL.ORANGE,
                 arms='side', **kw):
        super().__init__(**kw)
        self.kick, self.period, self.panic, self.suit, self.fins, self.snork, self.arms = kick, period, panic, suit, fins, snorkel, arms

    def paint(self, ctx, t):
        pn = float(np.clip(ev(self.panic, t), 0, 1)); kk = ev(self.kick, t)
        per = self.period / (1 + 1.2 * pn)
        ph = TAU * t / per
        SKIN = '#E2B58F'
        bob = 3 * math.sin(TAU * t / 3.0)
        ctx.translate(0, bob)
        tilt = -24 * pn          # panic: head comes up out of the water
        ctx.save(); ctx.translate(-80, 0); ctx.rotate(math.radians(-tilt * -1 * 0 + tilt)); ctx.translate(80, 0)
        # legs + fins (below the surface, kicking)
        for side, off in ((1, 0.0), (-1, math.pi)):
            k = kk * math.sin(ph + off)
            hip = np.array([70.0, 14]); knee = hip + np.array([70, 8 + 16 * k]); ank = knee + np.array([64, 4 + 30 * k])
            col = mix(self.suit, '#000000', 0.35) if side < 0 else hexc(self.suit)
            self.shape(ctx, _limb(hip, knee, ank, 30, 24, 16), col, ow=4)
            ang = math.atan2(ank[1] - knee[1], ank[0] - knee[0]) + 0.25 * k
            ctx.save(); ctx.translate(*ank); ctx.rotate(ang)
            fin = _sm([(0, -9), (40, -12), (92, -16 - 6 * k), (96, 8 + 4 * k), (40, 10), (0, 8)], 5)
            self.shape(ctx, fin, mix(self.fins, '#000000', 0.3) if side < 0 else self.fins, ow=4,
                       shade=(lambda: [(ctx.move_to(30, -4 + i * 4), ctx.line_to(92, -10 + i * 8)) for i in range(3)] and (ctx.set_source_rgba(0, 0, 0, 0.25), ctx.set_line_width(2), ctx.stroke())) if self.colored else None)
            ctx.restore()
        # torso (mostly submerged, back at the surface)
        torso = _sm([(-60, -10), (0, -14), (60, -10), (88, 4), (70, 28), (0, 32), (-60, 28), (-80, 10)], 6)
        self.shape(ctx, torso, self.suit, ow=5, shade=(lambda: (ctx.rectangle(-90, -20, 190, 14), ctx.set_source_rgba(1, 1, 1, 0.12), ctx.fill())) if self.colored else None)
        # arms
        for side in (-1, 1):
            if pn > 0.05:
                a = math.sin(ph * 1.3 + side) * 70 * pn
                sh = np.array([-50.0, 4]); el = sh + 48 * np.array([-math.cos(math.radians(60 + a)), -math.sin(math.radians(60 + a))])
                hd = el + 44 * np.array([-math.cos(math.radians(30 + a * 1.4)), -math.sin(math.radians(30 + a * 1.4))])
            elif self.arms == 'forward':
                sw_ = 6 * math.sin(ph * 0.5 + side)
                sh = np.array([-50.0, 6]); el = sh + np.array([-50, 10 + sw_]); hd = el + np.array([-46, 6])
            else:
                sh = np.array([-50.0, 8]); el = sh + np.array([30, 22]); hd = el + np.array([40, 6])
            col = mix(self.suit, '#000000', 0.35) if side < 0 else hexc(self.suit)
            self.shape(ctx, _limb(sh, el, hd, 24, 18, 14), col, ow=4)
            circle(ctx, hd[0], hd[1], 9)
            if self.colored: set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
            elif self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
            else: ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(2.5); ctx.stroke()
        # head (face down), mask, snorkel
        hx, hy = -104, -2
        circle(ctx, hx, hy, 30)
        if self.colored: set_col(ctx, SKIN); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4.5); ctx.stroke()
        elif self.style == 'silhouette': set_col(ctx, self.sil_color); ctx.fill()
        else: ctx.set_source_rgba(*hexc(self.oc)); ctx.set_line_width(3); ctx.stroke()
        if self.colored:
            ctx.move_to(hx - 31, hy - 4); ctx.curve_to(hx - 30, hy - 36, hx + 26, hy - 40, hx + 31, hy - 4)
            ctx.curve_to(hx + 10, hy - 16, hx - 10, hy - 16, hx - 31, hy - 4); set_col(ctx, '#3A2A20'); ctx.fill()
            # mask (front/bottom of the face) + strap
            ctx.save(); ctx.translate(hx - 18, hy + 18); ctx.rotate(0.5)
            rrect(ctx, -16, -12, 32, 26, 8); ctx.set_source_rgba(0.6, 0.85, 0.95, 0.85); ctx.fill_preserve()
            set_col(ctx, '#111111'); ctx.set_line_width(5); ctx.stroke(); ctx.restore()
            ctx.move_to(hx - 4, hy + 4); ctx.curve_to(hx + 10, hy - 4, hx + 22, hy - 6, hx + 30, hy - 10)
            set_col(ctx, '#111111'); ctx.set_line_width(5); ctx.stroke()
        # snorkel tube sticking up out of the water
        sx, sy = hx - 10, hy - 26
        ctx.move_to(hx - 22, hy + 22); ctx.curve_to(hx - 30, hy, sx - 2, sy + 6, sx, sy - 40)
        set_col(ctx, OUT if self.style != 'silhouette' else self.sil_color); ctx.set_line_width(12); ctx.stroke()
        if self.colored:
            ctx.move_to(hx - 22, hy + 22); ctx.curve_to(hx - 30, hy, sx - 2, sy + 6, sx, sy - 40)
            set_col(ctx, self.snork); ctx.set_line_width(7); ctx.stroke()
        ctx.restore()
        # splashes when panicking
        if pn > 0.05 and self.colored:
            r = rng(int(t * 8))
            for _ in range(int(8 * pn)):
                x = r.uniform(-170, 40); h = r.uniform(10, 40) * pn
                ctx.move_to(x, 0); ctx.line_to(x + r.uniform(-12, 12), -h)
                ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(3); ctx.stroke()
            for k in range(2):
                p = ((t * 2 + k * 0.5) % 1.0)
                ctx.save(); ctx.translate(-60, 0); ctx.scale(1, 0.18); circle(ctx, 0, 0, 60 + 160 * p); ctx.restore()
                ctx.set_source_rgba(1, 1, 1, 0.6 * (1 - p) * pn); ctx.set_line_width(2.5); ctx.stroke()


# ============================================================================ FISHERMAN
class Fisherman(_Animal):
    """Person standing on a bank with a rod, line running down to the water. Built on Human
    (origin at the feet, ~300 tall). Fisherman(line_to=(dx, dy) offset of the float from the feet,
    bite=0..1|K (rod tip jerks), cap=True, coat='#6E7F4B', facing='left'|'right' (faces the water),
    style). Rod held in front, angled up toward the water side."""
    def __init__(self, line_to=(-330, 150), bite=0.0, cap=True, coat='#6E7F4B', pants='#3A3530', **kw):
        kw.setdefault('facing', 'left')
        super().__init__(**kw)
        self.line_to, self.bite, self.cap, self.coat, self.pants = line_to, bite, cap, coat, pants
        from .human import Human
        self.h = Human(coat=coat, pose=(8, 0, 58, 38), hat=None, pants=pants, facing='right')

    def paint(self, ctx, t):
        # (we are already mirrored for facing='left' by _Animal: draw facing +x = toward the water at -x? )
        # Human faces +x in its own frame; flip so the person faces the water (to local -x).
        ctx.save(); ctx.scale(-1, 1)
        if self.style == 'color':
            self.h.draw(ctx, t)
        else:
            ctx.push_group(); self.h.draw(ctx, t); pat = ctx.pop_group()
            set_col(ctx, self.sil_color if self.style == 'silhouette' else self.oc); ctx.mask(pat)
        breathe = 1.5 * math.sin(TAU * t / 3.2)
        # hand position (replicates Human.arm for the right arm)
        sh = np.array([30, -205 + breathe]); r1 = math.radians(58); r2 = math.radians(58 + 38)
        el = sh + 52 * np.array([math.sin(r1), math.cos(r1)]); hd = el + 50 * np.array([math.sin(r2), math.cos(r2)])
        if self.cap:
            hy = -262 + breathe
            ctx.move_to(-33, hy - 6); ctx.curve_to(-30, hy - 44, 30, hy - 44, 33, hy - 6); ctx.line_to(62, hy - 4); ctx.line_to(60, hy + 4); ctx.line_to(-33, hy)
            ctx.close_path(); set_col(ctx, '#C8742F' if self.colored else self.sil_color); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.restore()
        bite = float(ev(self.bite, t))
        jerk = bite * (12 * math.sin(t * 17))
        hx, hy = -hd[0], hd[1]
        tip = np.array([hx - 250, hy - 170 + jerk + 3 * math.sin(t * 1.7)])
        mid = np.array([hx - 130, hy - 110 + jerk * 0.3])
        ctx.move_to(hx + 26, hy + 20); ctx.curve_to(*mid, *(mid * 0.4 + tip * 0.6), *tip)
        set_col(ctx, '#2A2622' if self.style != 'silhouette' else self.sil_color); ctx.set_line_width(5); ctx.stroke()
        # line to the float
        fx, fy = self.line_to
        fy2 = fy + 3 * math.sin(t * 2.1) + bite * 10 * max(0, math.sin(t * 9))
        ctx.move_to(*tip); ctx.curve_to(tip[0] - 20, tip[1] + 80, fx + 30, fy2 - 60, fx, fy2)
        ctx.set_source_rgba(0.95, 0.95, 0.9, 0.75); ctx.set_line_width(1.6); ctx.stroke()
        circle(ctx, fx, fy2 - 3, 6); set_col(ctx, PAL.RED); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(2); ctx.stroke()


class Esky(Element):
    """Cooler box (white/blue) — a prop to keep between you and the water. ~110 units wide, origin bottom-centre."""
    def __init__(self, color='#2F6FA0', **kw):
        super().__init__(**kw); self.col = color
    def draw(self, ctx, t):
        rrect(ctx, -55, -70, 110, 70, 8); set_col(ctx, '#EEF0EC'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, -60, -84, 120, 22, 6); set_col(ctx, self.col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
        rrect(ctx, -20, -96, 40, 12, 4); set_col(ctx, '#D8DCD8'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()


class Bucket(Element):
    """Metal/plastic bucket with a swinging handle. ~60 units wide, origin bottom-centre."""
    def __init__(self, color='#9AA4A8', **kw):
        super().__init__(**kw); self.col = color
    def draw(self, ctx, t):
        a = 0.2 * math.sin(t * 2.5)
        ctx.save(); ctx.translate(0, -66); ctx.rotate(a)
        ctx.arc_negative(0, 0, 32, 0, math.pi); set_col(ctx, OUT); ctx.set_line_width(3); ctx.stroke(); ctx.restore()
        ctx.move_to(-32, -66); ctx.line_to(32, -66); ctx.line_to(24, 0); ctx.line_to(-24, 0); ctx.close_path()
        set_col(ctx, self.col); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-30, -50); ctx.line_to(30, -50); ctx.set_source_rgba(0, 0, 0, 0.2); ctx.set_line_width(3); ctx.stroke()
