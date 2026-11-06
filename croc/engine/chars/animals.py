"""Other animals: great white shark, seal, ice floe, fish / herring school, blue whale."""
import math
import numpy as np
import cairocffi as cairo
from ..core import Element, ev, set_col, hexc, mix, circle, rrect, TAU, PAL, catmull, poly, rng
from .orca import Deform, rot_pts, _path, _teeth
OUT = PAL.OUTLINE

# ------------------------------------------------------------------ great white
S_TOP = [(-500, 30), (-492, 4), (-460, -26), (-400, -56), (-300, -84), (-180, -100), (-60, -104), (60, -96),
         (180, -76), (290, -48), (370, -24), (420, -14)]
S_BOT = [(420, 12), (370, 20), (280, 36), (160, 62), (40, 82), (-80, 90), (-200, 84), (-300, 70), (-380, 56),
         (-440, 46), (-480, 40), (-500, 32)]
S_TAIL = [(420, -14), (450, -40), (500, -130), (540, -200), (548, -190), (530, -100), (512, -20), (520, 20),
          (552, 90), (544, 104), (500, 60), (450, 24), (420, 12)]
S_DORSAL = [(-90, -100), (-60, -170), (-24, -240), (0, -262), (12, -250), (20, -170), (60, -112), (80, -96)]
S_PEC = [(0, 0), (40, 20), (120, 90), (190, 150), (176, 160), (90, 120), (20, 60), (-10, 20)]
S_LIP = [(-470, 40), (-420, 36), (-380, 32), (-350, 30)]

class Shark(Element):
    """Great white, side view facing LEFT. jaw (deg) opens the mouth with teeth."""
    def __init__(self, facing='left', swim=1.0, period=2.2, jaw=0.0, outline=7.0, **kw):
        super().__init__(**kw)
        self.facing, self.swim, self.period, self.jaw, self.ow = facing, swim, period, jaw, outline
        self.top = catmull(S_TOP, 8); self.bot = catmull(S_BOT, 8); self.tail = catmull(S_TAIL, 6)
        self.dorsal = catmull(S_DORSAL, 6); self.pec = catmull(S_PEC, 6, closed=True)

    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        D = Deform(t, 30 * ev(self.swim, t), self.period)
        top, bot, tail, dor = D(self.top), D(self.bot), D(self.tail, fluke=True), D(self.dorsal)
        jaw = ev(self.jaw, t)
        # lower jaw: rotate the front of the bottom contour
        if jaw > 0:
            hinge = np.array([-350.0, 30.0]); a = -math.radians(jaw)
            m = bot[:, 0] < -330
            bot = bot.copy(); bot[m] = rot_pts(bot[m], hinge, a)
            lip_l = rot_pts(np.array(catmull(S_LIP, 5)), hinge, a)
            lip_u = catmull(S_LIP, 5) - np.array([0, 2])
            mi = np.vstack([lip_u, lip_l[::-1]])
            _path(ctx, mi); set_col(ctx, '#5A1A1E'); ctx.fill()
            _teeth(ctx, lip_u, 8, 22, up=False, offset=0)
            _teeth(ctx, lip_l, 8, 20, up=True, offset=0.5)
        body = np.vstack([top, tail[1:], bot[1:]])
        _path(ctx, dor, close=False); ctx.line_to(float(dor[0, 0]) + 60, float(dor[0, 1]) + 30); ctx.close_path()
        set_col(ctx, '#5F6E79'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        _path(ctx, body); set_col(ctx, '#6E7E8A'); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        # countershading: white belly with a ragged edge
        xs = np.linspace(-520, 440, 40)
        edge = 22 + 18 * np.sin(xs * 0.03) * 0.4 + np.where(xs < -300, (xs + 300) * -0.08, 0) + np.where(xs > 200, (xs - 200) * -0.12, 0)
        pts = np.column_stack([xs, edge]); pts = D(pts)
        ctx.move_to(-560, 300)
        for x, y in pts: ctx.line_to(float(x), float(y))
        ctx.line_to(560, 300); ctx.close_path(); set_col(ctx, '#ECEFEE'); ctx.fill()
        g = cairo.LinearGradient(0, -110, 0, 10)
        g.add_color_stop_rgba(0, 0.25, 0.3, 0.35, 0.6); g.add_color_stop_rgba(1, 0.25, 0.3, 0.35, 0)
        ctx.set_source(g); ctx.rectangle(-600, -200, 1200, 220); ctx.fill()
        ctx.restore()
        _path(ctx, body); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        # gills
        ctx.set_line_width(3); set_col(ctx, '#2B3339')
        for i in range(5):
            x = -300 + i * 22
            g0 = D(np.array([[x, -30.0], [x + 6, 10], [x, 44]]))
            ctx.move_to(*g0[0]); ctx.curve_to(*g0[1], *g0[1], *g0[2]); ctx.stroke()
        # eye
        e = D(np.array([[-400.0, -22]]))[0]
        circle(ctx, e[0], e[1], 9); set_col(ctx, '#050607'); ctx.fill()
        circle(ctx, e[0] - 2.5, e[1] - 3, 2.4); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.fill()
        if jaw <= 0:
            lu = D(catmull(S_LIP, 5)); _path(ctx, lu, False); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        # pectoral
        pc = D(self.pec + np.array([-250.0, 50]))
        _path(ctx, pc); set_col(ctx, '#64737E'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        ctx.restore()

# ------------------------------------------------------------------ seal + ice floe
class Seal(Element):
    """Harbour/Weddell-type seal lying on its belly, facing LEFT. look: head lift."""
    def __init__(self, facing='left', look=0.0, color='#8C969C', **kw):
        super().__init__(**kw); self.facing, self.look, self.color = facing, look, color
    def draw(self, ctx, t):
        ctx.save()
        if self.facing == 'right': ctx.scale(-1, 1)
        lk = ev(self.look, t)
        br = 2.5 * math.sin(TAU * t / 2.6)
        body = catmull([(-150, -20 - lk * 20), (-110, -50 - lk * 10 + br), (-20, -62 + br), (90, -50), (170, -24), (230, -8),
                        (250, 0), (170, 6), (40, 8), (-100, 8), (-150, 0)], 8, closed=True)
        _path(ctx, body); set_col(ctx, self.color); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        g = cairo.LinearGradient(0, -60, 0, 10); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.9, 0.93, 0.95, 0.45)
        ctx.set_source(g); ctx.paint()
        r = rng(3)
        for _ in range(16):
            circle(ctx, r.uniform(-120, 200), r.uniform(-50, -10), r.uniform(3, 7)); ctx.set_source_rgba(0.25, 0.3, 0.33, 0.45); ctx.fill()
        ctx.restore()
        _path(ctx, body); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        # rear flippers
        ctx.move_to(240, -4); ctx.line_to(296, -26); ctx.line_to(290, 10); ctx.close_path(); set_col(ctx, '#6F7980'); ctx.fill_preserve()
        set_col(ctx, OUT); ctx.stroke()
        # head
        hy = -40 - lk * 26
        circle(ctx, -150, hy, 44); set_col(ctx, self.color); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(5); ctx.stroke()
        ctx.move_to(-196, hy + 10); ctx.curve_to(-200, hy - 8, -186, hy - 18, -168, hy - 10); ctx.line_to(-172, hy + 22); ctx.close_path()
        set_col(ctx, self.color); ctx.fill()
        circle(ctx, -168, hy - 12, 6.5); set_col(ctx, '#050607'); ctx.fill()
        circle(ctx, -170, hy - 14, 2); ctx.set_source_rgba(1, 1, 1, 0.9); ctx.fill()
        circle(ctx, -194, hy + 4, 4); set_col(ctx, '#2A2F33'); ctx.fill()
        ctx.set_line_width(1.6); ctx.set_source_rgba(0.95, 0.95, 0.95, 0.8)
        for k in (-1, 0, 1):
            ctx.move_to(-188, hy + 10); ctx.line_to(-222, hy + 6 + k * 8); ctx.stroke()
        # fore flipper
        ctx.move_to(-90, 0); ctx.curve_to(-80, 10, -60, 14, -46, 10); ctx.set_line_width(5); set_col(ctx, OUT); ctx.stroke()
        ctx.restore()

class IceFloe(Element):
    """Ice floe in cross-section: snowy top, cyan side, submerged mass below
    the waterline (local y=0). width in units. Bobs when plate given.
    tilt: degrees (wave-washing / tipping gag)."""
    def __init__(self, width=520, plate=None, tilt=0.0, seed=2, **kw):
        super().__init__(**kw); self.w, self.plate, self.tilt, self.seed = width, plate, tilt, seed
        r = rng(seed); w = width / 2
        self.top = [(-w, -30), (-w * 0.6, -44), (-w * 0.1, -40), (w * 0.4, -46), (w, -32)]
        self.under = catmull([(w, -32), (w * 0.95, 30), (w * 0.7, 120), (w * 0.2, 150), (-w * 0.4, 140), (-w * 0.85, 90), (-w, -30)], 6)
        self.proc(self._bob)
    def _bob(self, el, t):
        d = {'drot': ev(self.tilt, t) + 1.2 * math.sin(t * 1.1)}
        if self.plate is not None:
            x = ev(self.pos, t)[0]; d['dpos'] = (0, self.plate.water_y(x, t + self.t0) - self.plate.wl)
        return d
    def draw(self, ctx, t):
        w = self.w / 2
        # submerged part
        _path(ctx, self.under, close=False); ctx.close_path()
        g = cairo.LinearGradient(0, 0, 0, 150); g.add_color_stop_rgba(0, 0.70, 0.88, 0.92, 0.75); g.add_color_stop_rgba(1, 0.4, 0.65, 0.72, 0.35)
        ctx.set_source(g); ctx.fill_preserve(); ctx.set_source_rgba(0.85, 0.95, 1, 0.6); ctx.set_line_width(3); ctx.stroke()
        # side face above water
        ctx.move_to(-w, -30); ctx.line_to(w, -32); ctx.line_to(w * 0.97, 4); ctx.line_to(-w * 0.98, 4); ctx.close_path()
        set_col(ctx, '#BFE3EC'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        # snowy top
        P = catmull(self.top, 6)
        ctx.move_to(*P[0])
        for p in P[1:]: ctx.line_to(*p)
        ctx.line_to(w, -30); ctx.line_to(-w, -30); ctx.close_path()
        set_col(ctx, '#F7FBFC'); ctx.fill_preserve(); set_col(ctx, OUT); ctx.set_line_width(4); ctx.stroke()

# ------------------------------------------------------------------ fish + schools
def fish_path(ctx, L=40):
    h = L * 0.28
    ctx.move_to(L * 0.5, 0)
    ctx.curve_to(L * 0.35, -h, -L * 0.15, -h, -L * 0.32, -h * 0.25)
    ctx.line_to(-L * 0.55, -h * 0.75); ctx.line_to(-L * 0.48, 0); ctx.line_to(-L * 0.55, h * 0.75)
    ctx.line_to(-L * 0.32, h * 0.25)
    ctx.curve_to(-L * 0.15, h, L * 0.35, h, L * 0.5, 0); ctx.close_path()

class Fish(Element):
    def __init__(self, length=60, color='#C9D6DC', back='#5E7B8A', **kw):
        super().__init__(**kw); self.L, self.c, self.b = length, color, back
    def draw(self, ctx, t):
        fish_path(ctx, self.L); set_col(ctx, self.c); ctx.fill_preserve()
        ctx.save(); ctx.clip(); ctx.rectangle(-self.L, -self.L, 2 * self.L, self.L * 0.98); set_col(ctx, self.b); ctx.fill(); ctx.restore()
        circle(ctx, self.L * 0.3, -self.L * 0.04, self.L * 0.05); set_col(ctx, '#050607'); ctx.fill()

class FishSchool(Element):
    """Herring/fish school. mode 'ball' (bait ball, swirling), 'stream'
    (school moving along +x with a sine), 'scatter' (k 0..1 bursts outward).
    n fish, radius in units. colour/back for the fish; orange=True gives the
    reference's orange krill/fish look; tighten (0..1, keyframable) shrinks the ball."""
    def __init__(self, n=160, radius=260, mode='ball', fish_len=34, seed=4, color='#CFDCE2', back='#56717F',
                 speed=0.5, tighten=0.0, scatter=0.0, **kw):
        super().__init__(**kw)
        r = rng(seed)
        self.f = [(r.random() ** 0.6, r.uniform(0, TAU), r.uniform(0.75, 1.25), r.uniform(-1, 1), r.uniform(0.8, 1.2), r.random() * TAU)
                  for _ in range(n)]
        self.R, self.mode, self.L, self.c, self.b = radius, mode, fish_len, color, back
        self.speed, self.tighten, self.scatter = speed, tighten, scatter

    def draw(self, ctx, t):
        R = self.R * (1 - 0.45 * ev(self.tighten, t)); sc = ev(self.scatter, t)
        c, b = hexc(self.c), hexc(self.b)
        for (rr, a0, sp, z, ls, ph) in self.f:
            if self.mode == 'stream':
                x = (rr - 0.5) * R * 2.4 + 30 * math.sin(t * 1.4 + ph); y = math.sin(a0) * R * 0.45 + 12 * math.sin(t * 1.1 + ph)
                ang = 0.12 * math.cos(t * 1.4 + ph)
            else:
                w = self.speed * sp * (1.4 - rr * 0.6)
                a = a0 + w * t
                rad = R * rr * (1 + 0.06 * math.sin(t * 2 + ph))
                x = math.cos(a) * rad; y = math.sin(a) * rad * 0.62 + z * R * 0.12
                ang = a + math.pi / 2 + 0.15 * math.sin(t * 3 + ph)
                if sc > 0:
                    out = 1 + sc * 2.5 * sp
                    x *= out; y *= out
                    ang = ang * (1 - sc) + math.atan2(y, x) * sc
            L = self.L * ls * (0.85 + 0.15 * (z + 1) / 2)
            ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
            fish_path(ctx, L)
            sh = 0.75 + 0.25 * math.sin(ang * 2 + ph)   # silver flash
            ctx.set_source_rgba(c[0] * sh + 0.1 * (1 - sh), c[1] * sh + 0.1 * (1 - sh), c[2] * sh + 0.12 * (1 - sh), 0.95)
            ctx.fill()
            ctx.move_to(L * 0.45, -L * 0.05); ctx.line_to(-L * 0.45, -L * 0.05)
            ctx.set_source_rgba(b[0], b[1], b[2], 0.9); ctx.set_line_width(L * 0.12); ctx.stroke()
            ctx.restore()

# ------------------------------------------------------------------ blue whale
class BlueWhale(Element):
    """Blue whale side view, facing LEFT. Length 1000 units (scale to taste for
    size comparisons: a 30 m blue vs 8 m orca = 3.75x). silhouette=True for flat navy."""
    def __init__(self, silhouette=False, color='#4E6B7E', sil_color='#061722', swim=1.0, period=5.0, outline=6, **kw):
        super().__init__(**kw)
        self.sil, self.col, self.sc, self.swim, self.period, self.ow = silhouette, color, sil_color, swim, period, outline
        self.top = catmull([(-500, 10), (-480, -14), (-420, -40), (-300, -58), (-150, -64), (0, -62), (150, -54), (290, -40),
                            (330, -48), (346, -40), (370, -26), (430, -10), (450, -8)], 8)
        self.tail = catmull([(450, -8), (480, -30), (520, -48), (514, -20), (500, 0), (514, 20), (520, 46), (480, 30), (450, 8)], 5)
        self.bot = catmull([(450, 8), (380, 14), (250, 30), (100, 50), (-60, 60), (-200, 58), (-330, 48), (-430, 34), (-490, 20), (-500, 10)], 8)
        self.pec = catmull([(0, 0), (30, 14), (80, 46), (120, 70), (106, 76), (50, 50), (6, 22)], 5, closed=True)

    def draw(self, ctx, t):
        D = Deform(t, 14 * ev(self.swim, t), self.period)
        body = np.vstack([D(self.top), D(self.tail, fluke=True)[1:], D(self.bot)[1:]])
        pec = D(self.pec + np.array([-330.0, 40]))
        if self.sil:
            _path(ctx, body); _path(ctx, pec); set_col(ctx, self.sc); ctx.fill(); return
        _path(ctx, body); set_col(ctx, self.col); ctx.fill_preserve()
        ctx.save(); ctx.clip()
        r = rng(9)
        for _ in range(40):
            circle(ctx, r.uniform(-450, 420), r.uniform(-60, 30), r.uniform(4, 12)); ctx.set_source_rgba(0.75, 0.85, 0.9, 0.12); ctx.fill()
        ctx.set_source_rgba(0.85, 0.9, 0.92, 0.35); ctx.set_line_width(2)
        for i in range(9):   # ventral grooves
            y = 26 + i * 4
            g = D(np.array([[-470.0, y - 8], [-200, y + 8], [0, y + 6]]))
            ctx.move_to(*g[0]); ctx.curve_to(*g[1], *g[1], *g[2]); ctx.stroke()
        ctx.restore()
        _path(ctx, body); set_col(ctx, OUT); ctx.set_line_width(self.ow); ctx.stroke()
        e = D(np.array([[-380.0, 8]]))[0]
        circle(ctx, e[0], e[1], 5); set_col(ctx, '#050607'); ctx.fill()
        _path(ctx, pec); set_col(ctx, mix(self.col, '#000000', 0.15)); ctx.fill_preserve(); set_col(ctx, OUT); ctx.stroke()
