"""Act A — cold open (abs 0.0–92.1 s, beats B01–B12). Shot plan: scenes/plan_a.md. Assets: scenes/assets_a.py."""
import math
from engine import *
import cairocffi as cairo
from engine.core import PAL, Fn, Group, K, set_col, circle, rrect, hexc, ease
from engine.text import draw_text
from engine import plates as P
from scenes.assets_a import (CapeYorkMap, MaskPOV, JawClose, ThoughtBubble, Hands, ScaleEdge, TeethRing, Panel,
                             Postcard, MudBank, Zzz, BiteGauge, GapGauge, FadeIn, Ripples, Underline, Waterline,
                             WordReveal, TouristBoat)

CUTS = [0.0, 4.55, 6.65, 8.60, 11.55, 14.70, 17.80, 19.70, 24.17, 26.56, 29.58, 33.45, 38.95, 41.50, 45.22,
        46.55, 49.06, 51.56, 55.59, 61.73, 66.62, 70.31, 73.95, 76.40, 77.70, 80.64, 84.32, 89.21, 92.10]

SIL = '#05262B'      # croc silhouette on reef
REEF_W = '#2C8F94'


def _wpos(pos, sc, p):
    return (pos[0] + sc * p[0], pos[1] + sc * p[1])


def build(words=None):
    shots = []
    it = iter(range(len(CUTS) - 1))

    def new(plate, cam=None, name=''):
        i = next(it)
        a, b = CUTS[i], CUTS[i + 1]
        s = Shot(round(b - a, 4), plate=plate, camera=cam or Camera(push=0.8, drift=(6, -2)), name=name or f'a{i+1}')
        if i == 0: s.abs_start = 0.0
        shots.append(s)
        return s, (lambda t, a=a: t - a)

    def snorkel_group(s, sy, xs, sc=0.42, drift=20, dur=5.0, labels=None):
        out = []
        for k, x in enumerate(xs):
            el = s.add(Snorkeller(pos=K((0, (x, sy)), (dur, (x - drift, sy), 'linear')), scale=sc * (1 - 0.08 * (k % 2)),
                                  period=0.7 + 0.07 * k, suit=['#1F6F86', '#2F6FA0', '#7A4E8C', '#C2603E'][k % 4],
                                  rot=lambda t, k=k: 2 * math.sin(t * 2.1 + k)))
            out.append(el)
        return out

    # 1 — reef surface, four snorkellers 0.00–4.55
    s, L = new(Reef(surface_y=210), Camera(push=0.5, drift=(-4, 0)))
    snorkel_group(s, 210, [520, 860, 1180, 1500], sc=0.42, dur=4.6)
    s.add(Bubbles(pos=(960, 900), rate=2, spread=700, layer='fg'))
    s.add(FadeIn(dur=0.6))
    s.add(Pill('CAPE YORK, AUSTRALIA', 'dark', size=34, pos=(330, 320), t0=L(3.85)))

    # 2 — map: 40 km offshore 4.55–6.65
    s, L = new(P.Board(), Camera(push=0.8, drift=(0, 0), wander=2))
    m = CapeYorkMap(t_route=L(4.69) - 0.05, route_dur=1.2)
    s.add(m)
    s.add(Pill('40 KM OFFSHORE', 'orange', size=30, pos=(1500, 230), t0=L(5.89)))

    # 3 — crystal clear 6.65–8.60
    s, L = new(Reef(), Camera(push=1.0, drift=(-10, 0)))
    s.add(Snorkeller(pos=K((0, (1500, 120)), (2.0, (1300, 120), 'linear')), scale=0.5, layer='mid'))
    s.add(Fish(pos=K((0, (300, 640)), (2.0, (520, 630), 'linear')), scale=0.35, facing='right'))
    s.add(Bubbles(pos=(960, 1000), rate=3, spread=800, layer='fg'))
    s.add(Pill('CRYSTAL CLEAR', 'cyan', size=34, pos=(960, 880), t0=L(7.35)))

    # 4 — wife and friends + far croc 8.60–11.55
    s, L = new(Reef(surface_y=200), Camera(push=0.6, drift=(-3, 0)))
    sn = snorkel_group(s, 200, [420, 760, 1080, 1430], sc=0.40, dur=3.0)
    s.add(Croc(pos=K((0, (2200, 780)), (3.0, (1560, 760), 'linear')), scale=0.45, variant='silhouette', sil_color=SIL,
               opacity=0.55, layer='back'))
    s.add(Pill('WIFE', 'dark', size=30, pos=(760, 380), target=(760, 225), t0=L(8.79)))
    s.add(Pill('FRIENDS', 'dark', size=30, pos=(1250, 380), target=(1080, 225), t0=L(9.21)))
    s.add(Pill('YOU', 'orange', size=32, pos=(1430, 470), target=(1430, 225), t0=L(10.79)))

    # 5 — mask POV, hit from behind 11.55–14.70
    s, L = new(Reef(), Camera(push=0.6, drift=(0, 4), wander=5))
    th = L(11.99)
    s.add(Snorkeller(pos=K((0, (560, 420)), (3.2, (600, 400))), scale=0.8, rot=-12, layer='mid'))
    s.add(Bubbles(pos=(960, 700), rate=4, spread=500, layer='fg'))
    s.add(MaskPOV())
    s.camera.shake(th, amp=30, decay=0.6)
    s.camera.crash(th, dur=0.2, amount=1.12, target=(960, 600))
    s.add(Fn(lambda ctx, t, th=th: (ctx.set_source_rgba(1, 1, 1, max(0, 0.8 - (t - th) * 5)), ctx.paint()) if t >= th else None,
             layer='overlay', z=60))
    s.add(Label('HARD.', size=180, font='black', align='center', pos=(960, 600), t0=L(13.81), reveal=None,
                scale=lambda t: 1.0 + 0.25 * max(0, 1 - t / (5 / 30)), z=70, layer='overlay'))

    # 6 — jaws close round the view 14.70–17.80
    s, L = new(Reef(), Camera(push=1.4, drift=(0, 0), wander=5))
    tc = L(16.29)
    s.add(Bubbles(pos=(960, 640), rate=10, spread=300, layer='fg'))
    s.add(JawClose(close=K((0, 1.0), (tc - 0.9, 0.75, 'ei'), (tc, 0.15, 'eo'), (3.2, 0.08))))
    s.camera.shake(tc, amp=14, decay=0.5)
    s.add(Label('YOUR WHOLE HEAD', size=44, font='bold', track=0.2, align='center', pos=(960, 1010), t0=L(15.65), layer='overlay', z=5))
    s.add(Label('IS INSIDE SOMETHING', size=44, font='bold', track=0.2, color=PAL.RED, align='center', pos=(960, 140), t0=tc, layer='overlay', z=5))

    # 7 — shark? 17.80–19.70
    s, L = new(P.Abyss(), Camera(push=0.8, drift=(0, 0)))
    s.add(Bubbles(pos=(960, 900), rate=5, spread=600, layer='fg'))
    s.add(ThoughtBubble(pos=(1100, 460), r=230, t0=L(18.1)))
    s.add(Shark(pos=(1100, 460), scale=0.3, facing='left', t0=L(18.2), layer='overlay', z=3))
    s.add(Label('SHARK?', size=96, font='xb', align='center', pos=(1100, 860), t0=L(18.79), reveal='letters'))

    # 8 — hands reach up: not skin, scales 19.70–24.17
    s, L = new(P.Abyss(), Camera(push=0.9, drift=(0, 0), wander=5))
    tr, tf = L(20.03), L(20.95)
    s.add(ScaleEdge(reveal=K((0, 0.55), (tf, 0.75), (4.5, 0.85)), depth=330, layer='mid'))
    s.add(Hands(pos=K((0, (960, 1400)), (tr, (960, 1350)), (tf, (960, 640), 'eo'), (4.5, (960, 620))), gap=1000, scale=1.2, layer='mid', z=2))
    s.add(Bubbles(pos=(960, 900), rate=4, spread=600, layer='fg'))
    s.add(Label('NOT SKIN.', size=84, font='xb', align='center', pos=(960, 560), t0=L(21.96), t1=L(23.19), reveal='wipe', layer='overlay'))
    s.add(Punchline('…SCALES.', size=120, pos=(960, 580), t0=L(23.19)))
    s.camera.emphasis(L(23.19), L(24.0), 0.15, target=(960, 320))

    # 9 — teeth all the way round 24.17–26.56
    s, L = new(Reef(), Camera(push=1.5, drift=(0, 0), wander=6))
    s.add(Bubbles(pos=(960, 640), rate=12, spread=260, layer='fg'))
    s.add(TeethRing(n=30, rx=760, ry=420, dur=1.2, t0=L(24.29)))
    s.add(Label('ALL THE WAY ROUND', size=48, font='bold', track=0.22, align='center', pos=(960, 560), t0=L(24.79), layer='overlay', z=5))
    s.camera.shake(L(24.29), amp=6, decay=0.4)

    # 10 — not a shark, a crocodile 26.56–29.58
    s, L = new(P.Black(particles=True), Camera(push=0.5, drift=(0, 0)))
    s.add(Croc(pos=K((0, (2300, 760)), (3.1, (-500, 740), 'linear')), scale=1.0, facing='left', variant='silhouette',
               sil_color='#1A2B26', opacity=0.9, layer='back'))
    s.add(WordReveal("IT'S NOT A SHARK.", [L(x) for x in (26.66, 26.81, 26.99, 27.15)], size=72, pos=(960, 470)))
    s.add(Punchline("…IT'S A CROCODILE.", size=100, pos=(960, 650), t0=L(28.35)))
    s.camera.shake(L(28.35), amp=10, decay=0.4)

    # 11 — polaroid: Marcus McGowan 29.58–33.45
    s, L = new(P.Board(), Camera(push=1.0, drift=(3, 0)))

    def photo(ctx, t, w, h):
        g = cairo.LinearGradient(0, 0, 0, h)
        g.add_color_stop_rgba(0, *hexc('#7FC8C4')); g.add_color_stop_rgba(0.45, *hexc('#2FA7A0')); g.add_color_stop_rgba(1, *hexc('#0F4C55'))
        ctx.set_source(g); ctx.paint()
        ctx.rectangle(0, h * 0.45 + 4 * math.sin(t * 2), w, 3); ctx.set_source_rgba(1, 1, 1, 0.6); ctx.fill()
        cx, cy = w * 0.5, h * 0.62
        set_col(ctx, '#1F6F86'); rrect(ctx, cx - 110, cy - 20, 220, 260, 70); ctx.fill()        # shoulders
        set_col(ctx, '#D9A57E'); circle(ctx, cx, cy - 80, 80); ctx.fill()                          # head
        set_col(ctx, '#3A2E26'); ctx.arc(cx, cy - 92, 82, math.pi, 0); ctx.fill()                   # hair
        rrect(ctx, cx - 78, cy - 196, 156, 54, 20); set_col(ctx, '#0F1A1E'); ctx.fill()             # mask pushed up
        rrect(ctx, cx - 66, cy - 188, 60, 38, 14); rrect(ctx, cx + 6, cy - 188, 60, 38, 14); ctx.set_source_rgba(0.7, 0.9, 0.95, 0.8); ctx.fill()
        set_col(ctx, PAL.ORANGE); rrect(ctx, cx + 70, cy - 230, 14, 120, 6); ctx.fill()             # snorkel
        set_col(ctx, '#3A2E26'); circle(ctx, cx - 28, cy - 70, 7); ctx.fill(); circle(ctx, cx + 28, cy - 70, 7); ctx.fill()
        ctx.move_to(cx - 26, cy - 32); ctx.curve_to(cx - 10, cy - 22, cx + 10, cy - 22, cx + 26, cy - 32); ctx.set_line_width(5); ctx.stroke()
    s.add(Polaroid(content=photo, caption='DIVER', w=520, h=460, pos=(600, 520), angle=-4, t0=0.05, layer='overlay'))
    s.add(Pill('51-YEAR-OLD DIVER', 'orange', size=32, pos=(1260, 380), t0=L(30.13)))
    s.add(Typewriter('MARCUS McGOWAN, 51', size=64, pos=(980, 560), t0=L(32.21), cps=30))

    # 12 — date + place on the map 33.45–38.95
    s, L = new(P.Board(), Camera(push=0.7, drift=(0, 0), wander=2))
    m = CapeYorkMap(t_route=0.0, route_dur=0.01, ruler=False, pin=L(36.41))
    s.add(m)
    ix, iy = m.xy(143.56, -11.90)
    s.camera.emphasis(L(36.2), L(37.4), 0.22, target=(ix - 200, iy - 40))
    s.add(StatBox('27 MAY 2023', pos=(96, 90), size=56, t0=L(33.61)))
    s.add(Pill('CHARLES HARDY ISLANDS', 'red', size=30, pos=(ix - 120, iy - 250), target=(ix, iy - 100), t0=L(36.41)))
    cx_, cy_ = m.xy(142.3, -11.5)
    s.add(Pill('CAPE YORK', 'dark', size=30, pos=(cx_, cy_ + 120), target=(cx_, cy_ + 20), t0=L(37.83)))

    # 13 — something impossible 38.95–41.50
    s, L = new(Reef(surface_y=160), Camera(push=0.9, drift=(-4, 0)))
    cp, csc = (900, 560), 0.75
    c = s.add(Croc(pos=K((0, cp), (2.6, (cp[0] - 50, cp[1] - 10), 'linear')), scale=csc, facing='right', variant='silhouette',
                   sil_color=SIL, jaw=14, swim=0.6))
    jt = c.jaw_tip(0)
    s.add(Snorkeller(pos=K((0, (cp[0] + csc * jt[0] + 100, cp[1] + csc * jt[1] + 10)), (2.6, (cp[0] - 50 + csc * jt[0] + 100, cp[1] - 10 + csc * jt[1] + 10), 'linear')),
                     scale=0.6, style='silhouette', sil_color='#0A2F35', panic=0.6, rot=8, z=-1))
    s.add(Bubbles(pos=(cp[0] + 380, cp[1]), rate=10, spread=120, layer='fg'))
    s.add(Label('IMPOSSIBLE?', size=110, font='xb', color=PAL.ORANGE, align='center', pos=(960, 960), t0=L(40.19), reveal='letters'))

    # 14 — x-ray: levered the jaws open 41.50–45.22
    s, L = new(P.Board(), Camera(push=0.6, drift=(0, 0)))
    tj, tg, to = L(42.15), L(43.61), L(44.39)
    cp, csc = (1150, 600), 0.95
    c = Croc(pos=cp, scale=csc, facing='right', variant='xray', swim=0.3, jaw=K((0, 6), (tj - 0.2, 6), (tg, 30, 'eo'), (3.8, 31)))
    s.add(c)
    j0 = c.jaw_tip(0)
    hx, hy = cp[0] + csc * j0[0], cp[1] + csc * j0[1]
    s.add(Snorkeller(pos=K((0, (hx + 60, hy + 6)), (to, (hx + 60, hy + 6)), (to + 0.6, (hx + 460, hy + 40), 'eo')), scale=0.72,
                     style='outline', outline_color=PAL.ORANGE, facing='left', kick=K((0, 0.3), (to, 1.5)), panic=0.4), layer='mid')
    s.add(GapGauge(pos=(hx - 40, hy - 10), gap=K((0, 0.05), (tj - 0.2, 0.05), (tg, 1.0, 'eo')), full=220, t_label=tg, layer='mid'))
    box = Fn(lambda ctx, t: (rrect(ctx, -330, -50, 660, 92, 8), set_col(ctx, PAL.WHITE), ctx.set_line_width(3), ctx.stroke(),
                             draw_text(ctx, 'JAWS: LEVERED OPEN', 0, 18, 'xb', 48, PAL.WHITE, 0.04, 'center')),
             pos=(960, 150), t0=L(41.63), layer='overlay')
    s.add(box)
    s.camera.emphasis(tj, tg, 0.2, target=(hx, hy))
    s.add(Pill('HEAD OUT', 'green', size=30, tick=True, pos=(1500, 880), t0=to + 0.2))

    # 15 — it came back 45.22–46.55
    s, L = new(Reef(surface_y=200), Camera(push=1.0, drift=(0, 0)))
    s.add(Snorkeller(pos=(700, 200), scale=0.55, panic=0.8))
    s.add(Croc(pos=K((0, (1900, 560)), (1.35, (1050, 380), 'eo')), rot=K((0, 14), (1.35, 22)), scale=0.6, facing='left',
               variant='silhouette', sil_color=SIL, jaw=K((0, 5), (1.0, 30)), swim=1.4))
    s.add(Pill('IT CAME BACK', 'red', size=38, pos=(960, 900), t0=L(45.41)))

    # 16 — push away, bitten hand 46.55–49.06
    s, L = new(Reef(surface_y=180), Camera(push=0.7, drift=(0, 0)))
    tp, tb = L(46.71), L(47.87)
    sp = (760, 180)
    s.add(Snorkeller(pos=sp, scale=0.65, panic=1.0, arms='forward'))
    hit = (sp[0] + 40, sp[1] + 120)
    s.add(Croc(pos=K((0, (hit[0] + 520, hit[1] + 160)), (tp, (hit[0] + 330, hit[1] + 90), 'ei'), (tp + 0.35, (hit[0] + 560, hit[1] + 200), 'eo'),
                     (tb - 0.15, (hit[0] + 380, hit[1] + 120)), (tb, (hit[0] + 330, hit[1] + 100), 'ei'), (2.5, (hit[0] + 600, hit[1] + 230), 'eo')),
               rot=K((0, 22), (tp, 20), (2.5, 12)), scale=0.6, facing='left', variant='silhouette', sil_color=SIL,
               jaw=K((0, 10), (tb - 0.2, 26), (tb, 4), (tb + 0.4, 4))))
    impact(s, tp, hit, amp=16, scale=0.7, bubbles=12, gravity=60)
    s.add(Pill('PUSHED IT AWAY', 'dark', size=30, pos=(1350, 820), t0=tp))
    s.add(Fn(lambda ctx, t: (circle(ctx, 0, 0, 34 * min(1, t / 0.12)), set_col(ctx, PAL.RED), ctx.fill(),
                             draw_text(ctx, '!', 0, 16, 'black', 48, PAL.WHITE, 0, 'center', shadow=False)),
             pos=(hit[0] - 30, hit[1] - 60), t0=tb, layer='mid', z=5))
    s.add(Pill('BITTEN HAND', 'red', size=30, pos=(420, 520), target=(hit[0] - 30, hit[1] - 30), t0=tb))
    s.camera.shake(tb, amp=10, decay=0.35)

    # 17 — swims to the boat, survives 49.06–51.56
    pl = Surface('day', waterline=600, sun=(0.7, 0.2))
    s, L = new(pl, Camera(push=0.6, drift=(4, 0)))
    s.add(Speedboat(pos=(1400, 600), scale=0.7, plate=pl, facing='left', crew=2))
    s.add(Snorkeller(pos=K((0, (380, 600)), (2.5, (1020, 600), 'eo')), scale=0.5, facing='right', kick=1.8, period=0.45))
    s.add(Ripples(pos=K((0, (380, 610)), (2.5, (1020, 610), 'eo')), period=1.0, rmax=120, layer='mid'))
    s.add(Pill('SURVIVED', 'green', size=40, tick=True, pos=(960, 230), t0=L(50.51)))

    # 18 — quote 51.56–55.59
    s, L = new(P.Black(particles=True), Camera(push=0.4, drift=(0, 0)))
    q = '"I WAS SIMPLY IN THE WRONG PLACE, AT THE WRONG TIME."'
    wt = [51.66, 51.73, 51.83, 52.01, 52.27, 52.35, 52.49, 53.15, 53.31, 53.37, 53.55]
    s.add(QuoteReveal(q, kicker='MARCUS McGOWAN', attribution='STATEMENT VIA CAIRNS HEALTH SERVICE',
                      word_times=[L(x) for x in wt], t_attr=L(54.31), size=68, pos=(960, 540)))

    # 19 — name card: saltwater crocodile 2–3 m 55.59–61.73
    s, L = new(P.Board(), Camera(push=0.8, drift=(-3, 0)))
    s.add(Croc(pos=K((0, (1060, 520)), (6.2, (980, 520), 'linear')), scale=0.85, facing='left', gait=0.0, swim=0.6, blink=[1.5, 4.0],
               opacity=K((0, 0), (0.5, 1))))
    s.add(Fn(lambda ctx, t: (circle(ctx, 0, -12, 12), set_col(ctx, PAL.ORANGE), ctx.fill(),
                             draw_text(ctx, 'SALTWATER CROCODILE', 34, 0, 'xb', 64, PAL.WHITE, 0.03, 'left')),
             pos=(150, 170), t0=L(56.45), layer='overlay'))
    s.add(Pill("'JUST A YOUNG ONE'", 'orange', size=32, pos=(1450, 300), target=(1150, 470), t0=L(59.21)))
    t2 = L(60.19)
    s.add(Fn(lambda ctx, t: (lambda k: (
        ctx.move_to(660, 0), ctx.line_to(660 + 640 * k, 0), set_col(ctx, PAL.WHITE), ctx.set_line_width(4), ctx.stroke(),
        ctx.move_to(660, -18), ctx.line_to(660, 18), ctx.stroke(),
        ctx.move_to(660 + 640 * k, -18), ctx.line_to(660 + 640 * k, 18), ctx.stroke(),
        draw_text(ctx, '2 M' if t < 0.65 else '2–3 M', 660 + 640 * k / 2, 70, 'xb', 56, PAL.WHITE, 0.02, 'center')))(
        0.67 * ease('eo', min(1, t / 0.4)) + 0.33 * ease('eo', min(1, max(0, t - 0.65) / 0.4))),
        pos=(0, 800), t0=t2, layer='mid'))

    # 20 — postcard from the river 61.73–66.62
    s, L = new(P.Sepia(), Camera(push=0.9, drift=(0, 0)))
    pc = Postcard(pos=(960, 560), scale=1.0, rot=-2, flip=K((0, 1), (4.55, 1), (4.89, 0.02, 'ei')))
    pc.add(MudBank(pos=(0, 180)))
    pc.add(Croc(pos=(60, 220), scale=0.8, facing='left', swim=0.1, legs='sprawl', blink=None, jaw=K((0, 6), (2.0, 12), (4, 6)),
                rot=-3))
    pc.add(Zzz(pos=(-330, 110)))
    s.add(pc)
    s.add(Pill('LAZING', 'dark', size=32, pos=(1500, 930), t0=L(64.71)))

    # 21 — reef, 40 km out, behind you 66.62–70.31
    s, L = new(Reef(surface_y=170), Camera(push=0.8, drift=(0, 0)))
    s.add(Fn(lambda ctx, t: None))
    s.add(Snorkeller(pos=K((0, (760, 170)), (3.7, (700, 170), 'linear')), scale=0.38))
    tbh = L(69.15)
    s.add(Croc(pos=K((0, (1850, 470)), (tbh, (1180, 360), 'linear'), (3.7, (1060, 330), 'linear')), scale=0.55, facing='left',
               variant='silhouette', sil_color=SIL, opacity=0.85, swim=0.8))
    s.add(Pill('NOT A RIVERBANK', 'dark', size=30, pos=(330, 600), t0=L(66.72)))
    s.add(Pill('40 KM OUT TO SEA', 'orange', size=32, pos=(330, 680), t0=L(67.63)))
    s.add(Punchline('…BEHIND YOU.', size=110, pos=(960, 930), t0=tbh))
    s.camera.emphasis(tbh, tbh + 0.6, 0.2, target=(900, 300))

    # 22 — strongest bite 70.31–73.95
    s, L = new(P.Board(), Camera(push=0.7, drift=(0, 0)))
    tsb = L(71.95)
    hp = Panel(w=820, h=620, pos=(1380, 540), t0=0.0)
    hp.add(CrocHead(pos=(170, 40), scale=1.35, facing='right', jaw=K((0, 8), (tsb - 0.3, 34, 'eo'), (tsb, 0, 'ei'), (3.7, 2)), domes=False))
    s.add(hp, layer='mid')
    s.add(BiteGauge(pos=(560, 560), r=260, t_hit=tsb))
    s.add(Label('STRONGEST BITE', size=60, font='xb', align='center', pos=(560, 700), t0=tsb, reveal='wipe'))
    s.add(Label('EVER MEASURED', size=40, font='bold', track=0.22, color=PAL.ORANGE, align='center', pos=(560, 770), t0=L(73.13)))
    s.camera.shake(tsb, amp=12, decay=0.4)

    # 23 — waits underwater an hour 73.95–76.40
    s, L = new(MurkyWater(surface_y=200), Camera(push=0.8, drift=(0, 0)))
    s.add(Croc(pos=(900, 780), scale=0.65, facing='left', swim=0.15, blink=[0.8, 2.0]))
    s.add(Bubbles(pos=(560, 760), rate=0.6, spread=10, layer='mid'))
    s.add(Stopwatch(start=0, rate=45, r=70, pos=(1420, 400), t0=L(74.23), layer='overlay',
                    fmt=lambda v: f'{min(60, int(v)):d} MIN'))
    s.add(Label('1 HOUR UNDER', size=72, font='xb', color=PAL.ORANGE, align='center', pos=(960, 980), t0=L(75.63), reveal='wipe'))

    # 24 — killed a tiger 76.40–77.70
    s, L = new(P.Board(), Camera(push=1.2, drift=(0, 0)))
    s.add(Tiger(pos=(1240, 700), scale=1.0, pose='drink', style='outline', outline_color=PAL.CYAN_HI))
    tk = L(77.09)
    s.add(Croc(pos=K((0, (380, 700)), (tk - 0.1, (430, 690)), (tk, (640, 610), 'ei'), (1.3, (660, 610))), scale=0.8, facing='right',
               variant='xray', jaw=K((0, 10), (tk - 0.1, 34), (tk + 0.05, 6))))
    s.add(Label('KILLED A TIGER', size=80, font='xb', color=PAL.ORANGE, align='center', pos=(960, 200), t0=tk, reveal='letters'))
    s.camera.shake(tk, amp=12, decay=0.35)

    # 25 — four-panel recap, shark + tourists 77.70–80.64
    s, L = new(P.Board(), Camera(push=0.4, drift=(0, 0), wander=2))
    xs = [270, 730, 1190, 1650]
    caps = [('BITE', PAL.WHITE), ('1 HOUR', PAL.WHITE), ('TIGER', PAL.WHITE), ('SHARK', PAL.RED)]
    for k, x in enumerate(xs):
        pn = Panel(w=380, h=440, caption=caps[k][0], cap_color=caps[k][1], cap_size=40, pos=(x, 470),
                   t0=0.05 * k if k < 3 else L(78.21))
        if k == 0:
            pn.add(CrocHead(pos=(-40, 30), scale=0.7, jaw=lambda t: 18 + 14 * math.sin(t * 3), domes=False))
        elif k == 1:
            pn.add(Fn(lambda ctx, t: (ctx.rectangle(-200, -120, 400, 4), ctx.set_source_rgba(0.7, 0.9, 0.95, 0.6), ctx.fill())))
            pn.add(Stopwatch(start=0, rate=40, r=60, pos=(-90, 60), fmt=lambda v: f'{min(60, int(v))} MIN'))
        elif k == 2:
            pn.add(Tiger(pos=(10, 90), scale=0.55, style='outline', outline_color=PAL.CYAN_HI, pose='lying'))
        else:
            pn.add(TouristBoat(pos=(0, -110), scale=0.6))
            pn.add(Fn(lambda ctx, t: (ctx.rectangle(-200, -86, 400, 3), ctx.set_source_rgba(0.7, 0.9, 0.95, 0.6), ctx.fill())))
            pn.add(BullShark(pos=(-10, 90), scale=0.32, style='outline', outline_color=PAL.RED, thrash=1.0))
        s.add(pn, layer='mid')
    s.add(Stamp('IN FRONT OF TOURISTS', PAL.RED, 54, pos=(1320, 930), t0=L(79.57), angle=-5))

    # 26 — the uncomfortable part 80.64–84.32
    s, L = new(Mangrove(horizon=430), Camera(push=0.9, drift=(-4, 0)))
    s.add(CrocEyes(pos=K((0, (1400, 700)), (3.7, (1040, 700), 'linear')), scale=1.3, view='side'))
    s.add(Label('WHY IT\'S SO DANGEROUS', size=40, font='bold', track=0.22, align='center', pos=(960, 160), t0=L(80.87), layer='overlay'))
    s.add(Pill('THE UNCOMFORTABLE PART', 'red', size=40, pos=(960, 950), t0=L(82.75)))

    # 27 — same spot, MON/TUE/WED 84.32–89.21
    pl = Riverbank(560, mud=True, mangroves=True, bank_x=1250)
    s, L = new(pl, Camera(push=0.4, drift=(0, 0)))
    days = [(L(84.32), L(85.73), 'MON', 760), (L(85.73), L(86.96), 'TUE', 990), (L(86.96), 9.0, 'WED', 1170)]
    for (a, b, nm, ex) in days:
        s.add(Human(pos=(1360, pl.bank_y(1360)), scale=0.45, pose='crouch', facing='left', t0=a, t1=b))
        s.add(Bucket(pos=(1450, pl.bank_y(1450)), scale=0.8, t0=a, t1=b))
        s.add(CrocEyes(pos=K((0, (ex + 40, 562)), (b - a, (ex, 562), 'linear')), scale=0.9, view='side', t0=a, t1=b))
        s.add(Pill(nm, 'white', size=40, pos=(170, 120), t0=a, t1=b, layer='overlay'))
    s.add(Checklist([("DOESN'T CHASE", 'x', L(84.83) - L(84.45)), ('PATIENT', 'tick', L(85.91) - L(84.45))], t_items=[0, L(85.73) - L(84.45)],
                    size=44, gap=80, pos=(110, 820), t0=L(84.45)))
    s.add(Pill('…IT LEARNS.', 'orange', size=40, pos=(1000, 300), t0=L(87.13)))
    s.add(Pill('WHERE YOU STAND', 'dark', size=30, pos=(1360, 380), target=(1360, pl.bank_y(1360) - 10), t0=L(88.19)))

    # 28 — title 89.21–92.10
    s, L = new(P.Black(particles=True), Camera(push=0.6, drift=(0, 0)))
    s.add(FadeIn(dur=0.4))
    s.add(Waterline(pos=(960, 760), w=1500, layer='mid'))
    s.add(CrocEyes(pos=K((0, (1800, 760)), (2.9, (1250, 760), 'linear')), scale=0.6, view='side', ripples=True, body=False, water='#0A1414'))
    s.add(Label("WHY YOU'D NEVER WANT TO MEET", size=74, font='xb', align='center', pos=(960, 470), t0=L(89.97), reveal='letters', dur=0.6))
    s.add(Label('A SALTWATER CROCODILE', size=104, font='xb', align='center', pos=(960, 610), t0=L(91.05), reveal='letters', dur=0.35))
    s.add(Underline(w=1200, pos=(960, 650), t0=L(91.49)))
    s.camera.shake(L(91.49), amp=8, decay=0.35)
    s.add(Ring(pos=(960, 560), t0=L(91.49), r0=40, r1=700, dur=0.5, width=10, color='#FFFFFF', layer='fg'))
    return shots
