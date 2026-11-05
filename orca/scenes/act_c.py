"""Act C — chapter 3/6 SHARKS (abs 224.5 – 302.2)."""
import math
from engine import *
from engine.timing import Words
from engine.core import Fn, set_col, circle, rrect, W as FW, H as FH
from engine.text import draw_text
from scenes.assets_c import *

T_START, T_END = 224.5, 302.2
CUTS = [224.5, 228.44, 230.48, 233.06, 234.79, 238.01, 242.12, 245.38, 250.38, 254.82, 259.39, 264.28,
        269.07, 274.12, 276.19, 278.65, 281.35, 284.44, 288.58, 293.34, 295.73, 298.05, 302.2]
LABELS = ['SIZE', 'MENU', 'SHARKS', 'BOATS', 'YOUR MOVE', 'REAL DANGER']


def build(words=None):
    Wd = Words(words) if words else None

    def wt(phrase, after, fallback):
        if Wd is None: return fallback
        try:
            v = Wd.find(phrase, after=after - 0.5)
            return v if abs(v - fallback) < 3.0 else fallback
        except KeyError:
            return fallback

    shots = []
    idx = [0]

    def new(plate, camera=None, name=''):
        i = idx[0]; idx[0] += 1
        s = Shot(CUTS[i + 1] - CUTS[i], plate=plate, camera=camera or Camera(), name=name)
        s.c0 = CUTS[i]
        if i == 0: s.abs_start = T_START
        shots.append(s)
        return s

    L = lambda s, t_abs: t_abs - s.c0

    # 1 chapter card ------------------------------------------------------------
    s = new(MaroonPlate(), Camera(push=0.6, drift=(6, 0)), 'ch3')
    s.add(SharkSil(pos=K((0, (1500, 250)), (s.dur, (700, 230), 'linear')), scale=0.62, color='#050203', layer='back'))
    s.add(Orca(pos=K((0, (900, 1350)), (s.dur, (1150, 720), 'eo')), scale=0.62, rot=-28, facing='left',
               variant='silhouette', sil_color='#8E1E1C', layer='mid'))
    s.add(Bubbles(pos=(1200, 1000), rate=4, spread=200, layer='fg'))
    s.add(ChapterTitle('SHARKS', 'WHAT THE GREAT WHITE FEARS', 3, 6, labels=LABELS, t0=0.3))
    s.add(FadeIn(0.45))

    # 2 globe South Africa ------------------------------------------------------
    s = new(Board(), Camera(push=0.8, drift=(3, 0), wander=3), 'globe')
    s.add(Globe(center=(22, -28), radius=340, spin=1.5, highlight=['South Africa'], pins=[(19.35, -34.6)],
                pos=(1180, 560), t0=0))
    s.add(StatBox('GANSBAAI, SOUTH AFRICA', sub='2017', t0=L(s, 228.72), t_sub=0.5, size=46))
    s.add(SharkSil(pos=K((0, (2100, 930)), (s.dur, (-200, 900), 'linear')), scale=0.3, color='#061A22', layer='fg'))

    # 3 cage diver --------------------------------------------------------------
    s = new(Underwater(depth=0.3), Camera(push=0.9, drift=(-6, 0)), 'cage')
    s.add(Shark(pos=K((0, (2200, 380)), (s.dur, (-300, 330), 'linear')), scale=0.45, layer='back'))
    s.add(Cage(pos=(960, 560), w=420, h=380, layer='mid', z=1))
    s.add(Diver(pos=(920, 580), scale=0.36, facing='right', kick=0.6, layer='mid', z=0))
    s.add(Shark(pos=K((0, (-500, 760)), (s.dur, (1500, 790), 'linear')), scale=0.62, facing='right', jaw=8, layer='fg'))
    s.add(Pill('BEST PLACE ON EARTH TO SEE THEM', 'orange', size=34, pos=(960, 150), t0=L(s, wt('best places', 231.5, 231.5))))

    # 4 beach carcasses ---------------------------------------------------------
    s = new(Beach(horizon=360, shore=600), Camera(push=1.0, drift=(-5, 0), wander=2), 'beach')
    t5 = L(s, wt('five in', 233.16, 233.16))
    spots = [(380, 790), (760, 880), (1120, 760), (1470, 870), (1760, 760)]
    for k, (x, y) in enumerate(spots):
        s.add(Shark(pos=(x, y), scale=0.26, rot=180 + (k % 2) * 8 - 4, swim=0.04, period=3, layer='mid', t0=t5 + 0.15 * k))
    s.add(Counter(1, 5, dur=0.66, suffix=' DEAD', size=92, pos=(960, 200), t0=t5, unit='great white sharks'))
    s.add(Pill('5 IN 5 MONTHS', 'red', size=34, pos=(960, 300), t0=t5 + 0.75))

    # 5 x-ray shark -------------------------------------------------------------
    s = new(Board(), Camera(push=0.8, drift=(0, 0), wander=3), 'xray')
    tg, tgo = L(s, 236.02), L(s, 237.14)
    s.add(XRayShark(pos=(900, 640), scale=1.05, liver_glow=K((0, 0), (tg, 0), (tg + 0.3, 1, 'eo')),
                    liver_gone=K((0, 0), (tgo, 0), (tgo + 0.25, 1, 'eo')), layer='mid'))
    s.add(Label('4 OF 5', size=110, font='black', align='center', pos=(960, 170), t0=L(s, 234.89)))
    s.add(Pill('THE LIVER', 'red', size=32, pos=(560, 880), target=(800, 670), t0=tg))
    s.add(Stamp('LIVER: MISSING', PAL.RED, 66, pos=(1320, 900), t0=tgo))
    s.camera.emphasis(tg - 0.2, tg + 0.6, 0.12, target=(800, 660))

    # 6 surgical tray -----------------------------------------------------------
    s = new(Black(particles=True), Camera(push=1.0, drift=(0, -2)), 'surg')
    s.add(SurgTray(pos=(960, 760), scale=1.2, layer='mid'))
    s.add(QuoteReveal('\u201CALMOST SURGICAL PRECISION\u201D', kicker='RESEARCHERS', size=70,
                      word_times=[L(s, 239.78), L(s, 240.22), L(s, 240.70)], pos=(960, 330), t0=0))

    # 7 line-up -----------------------------------------------------------------
    s = new(Board(tint='indigo'), Camera(push=0.7, drift=(0, 0), wander=3), 'lineup')
    def lineup(ctx, t):
        for i in range(8):
            y = 860 - i * 90
            ctx.move_to(120, y); ctx.line_to(1800, y); set_col(ctx, '#FFFFFF', 0.12 if i % 2 else 0.25); ctx.set_line_width(3); ctx.stroke()
            draw_text(ctx, f'{i}M' if i % 2 == 0 else '', 70, y + 10, 'bold', 22, '#FFFFFF', 0.1, shadow=False, alpha=0.5)
    s.add(Fn(lineup, layer='back'))
    s.add(floppy_orca('back', pos=(560, 620), scale=0.5, facing='right', swim=0.5, layer='mid'))
    s.add(floppy_orca('front', pos=(1360, 620), scale=0.5, facing='left', swim=0.5, phase=1.2, layer='mid'))
    s.add(Stamp('SUSPECTS', PAL.RED, 80, pos=(960, 170), t0=L(s, 242.28)))
    s.add(Pill('PORT', 'red', size=44, pos=(560, 920), t0=L(s, 244.10)))
    s.add(Pill('STARBOARD', 'green', size=44, pos=(1360, 920), t0=L(s, 244.60)))

    # 8 rear fins ---------------------------------------------------------------
    pl = Surface('haze', waterline=640, sun=(0.5, 0.2))
    s = new(pl, Camera(push=0.6, drift=(0, 0), wander=3), 'fins')
    tl, tr = L(s, 247.92), L(s, 249.10)
    s.add(RearFin(pos=(620, 650), height=240, bend=K((0, 0), (tl - 0.1, 0), (tl + 0.5, -42, 'eo')), layer='mid'))
    s.add(RearFin(pos=(1300, 650), height=240, bend=K((0, 0), (tr - 0.1, 0), (tr + 0.5, 42, 'eo')), layer='mid'))
    s.add(NavLight('#E5332E', pos=(620, 150), t0=0.3))
    s.add(NavLight('#3CC45A', pos=(1300, 150), t0=0.6))
    s.add(Label('PORT', size=50, align='center', pos=(620, 285), t0=0.3))
    s.add(Label('STARBOARD', size=50, align='center', pos=(1300, 285), t0=0.6))
    s.add(Pill('BENT LEFT', 'red', size=34, pos=(620, 900), t0=tl))
    s.add(Pill('BENT RIGHT', 'green', size=34, pos=(1300, 900), t0=tr))

    # 9 sharks leave ------------------------------------------------------------
    s = new(Underwater(depth=0.35), Camera(push=0.5, drift=(4, 0)), 'leave')
    tx = L(s, wt('they left', 253.68, 253.68))
    for k, (y0, sc, ts) in enumerate([(420, 0.42, 1.0), (640, 0.5, 1.3), (840, 0.36, 1.6)]):
        x0 = 400 + k * 330
        pos = K((0, (x0, y0)), (tx, (x0 + 220, y0), 'linear'), (s.dur, (x0 + 2200, y0 - 30), 'ei'))
        s.add(Shark(pos=pos, scale=sc, facing='right', layer='mid', z=k))
        s.add(Suitcase(pos=(lambda p: (lambda t: (p(t)[0] - 10, p(t)[1] + 95)))(pos), scale=0.9 * sc / 0.42,
                       layer='mid', z=k + 0.5, t0=ts))
    s.add(Punchline('THEY LEFT.', size=96, pos=(960, 200), t0=tx))
    s.add(SightingsGraph(pos=(1380, 760), t_draw=0.2, t_drop=tx, layer='overlay'))
    s.add(SpeedLines(pos=(700, 600), angle=0, t0=tx, layer='fg'))

    # 10 reef for sale ----------------------------------------------------------
    s = new(Underwater(depth=0.4), Camera(push=0.7, drift=(-3, 0)), 'sale')
    tsold = L(s, 258.04)
    s.add(Reef(pos=(960, 900), layer='back'))
    s.add(SaleSign(pos=(1350, 960), t_sold=tsold, layer='mid', z=2))
    s.add(Orca(pos=K((0, (-500, 430)), (s.dur, (900, 470), 'eo')), scale=0.42, facing='right', layer='mid'))
    s.add(Orca(pos=K((0, (-800, 650)), (s.dur, (560, 640), 'eo')), scale=0.38, facing='right', phase=1.0, layer='mid'))
    s.add(Punchline('\u2026TWO DOLPHINS MOVED IN.', size=78, pos=(960, 170), t0=L(s, 257.42)))
    s.add(Bubbles(pos=(400, 980), rate=3, spread=300, layer='fg'))

    # 11 drone, Mossel Bay ------------------------------------------------------
    pl = Surface('day', waterline=560, sun=(0.7, 0.16))
    s = new(pl, Camera(push=0.6, drift=(-4, 0)), 'drone')
    fin = K((0, (1500, 570)), (s.dur, (800, 570), 'linear'))
    s.add(RearFin(pos=fin, bend=40, height=220, scale=0.7, layer='mid'))
    s.add(Shark(pos=K((0, (300, 820)), (s.dur, (700, 810), 'linear')), scale=0.32, facing='right', layer='mid'))
    s.add(Drone(pos=(1450, 200), scale=1.2, layer='mid'))
    s.add(StatBox('MOSSEL BAY, 2023', t0=L(s, 260.92), size=48))
    s.add(Pill('STARBOARD', 'green', size=34, pos=(1250, 420), target=lambda t: (fin(t)[0] + 40, 470), t0=L(s, 261.84)))
    s.add(Stamp('ALONE', PAL.RED, 90, pos=(960, 330), t0=L(s, 263.42)))

    # 12 REC top-down grab ------------------------------------------------------
    s = new(TopDown(), Camera(push=0.4, drift=(0, 0), wander=2), 'rec')
    tgrab, ttc, tfz = L(s, 264.44), L(s, 267.10), L(s, 268.26)
    thr = lambda t: 18 * math.sin(t * 7) * (1 if t < tfz else 0) + (0 if t < tfz else 18 * math.sin(tfz * 7))
    s.add(SharkTop(pos=(900, 560), scale=0.55, rot=lambda t: 20 + thr(t), beat=1.4, period=0.5, layer='mid', z=0))
    s.add(OrcaTop(pos=(1050, 380), scale=0.6, rot=lambda t: 120 - thr(t) * 0.7, layer='mid', z=1))
    for k, tt in enumerate([tgrab, tgrab + 0.9, tgrab + 1.9, tgrab + 2.8]):
        s.add(TopSplash(pos=(960 + 80 * (k % 2) - 40, 470 + 40 * (k % 3)), r=260, dur=1.1, seed=k + 2, t0=tt, layer='fg'))
    s.add(RecFreeze(tc_start=0.0, jumps=[(ttc, 112.0)], t_freeze=tfz))
    s.camera.handheld(amp=2.6, freq=1.0, t0=0)
    s.add(Pill('< 2 MIN', 'red', size=44, pos=(960, 960), t0=ttc))
    s.add(Fn(lambda ctx, t: (ctx.set_source_rgba(1, 1, 1, max(0, 1 - t / 0.2)), ctx.paint()), t0=tfz, layer='overlay'))

    # 13 dive boat + tourists ---------------------------------------------------
    pl = Surface('day', waterline=520, sun=(0.3, 0.15))
    s = new(pl, Camera(push=0.6, drift=(3, 0)), 'diveboat')
    s.add(Speedboat(pos=(980, 520), scale=0.9, plate=pl, crew=0, layer='mid', z=1))
    for k, x in enumerate([800, 920, 1040, 1160]):
        s.add(PhoneHuman(raise_=K((0, 0), (2.4 + 0.25 * k, 0), (2.9 + 0.25 * k, 1)), pos=(x, 486), scale=0.55,
                         coat=['#C8453A', '#2F6FA0', '#E0A040', '#4DB271'][k], facing='left' if k % 2 else 'right',
                         hat='hair', layer='mid', z=2))
    opos = K((0, (2000, 820)), (s.dur, (-300, 800), 'linear'))
    s.add(Orca(pos=opos, scale=0.45, facing='left', jaw=6, layer='mid', z=3))
    s.add(Liver(pos=lambda t, opos=opos: (opos(t)[0] - 215, opos(t)[1] + 10), scale=0.55, layer='mid', z=4))
    s.add(Pill('SHARK-DIVING BOAT', 'dark', size=30, pos=(980, 200), t0=0.3))

    # 14 close: showing off? ----------------------------------------------------
    s = new(Underwater(depth=0.3), Camera(push=1.2, drift=(-6, 0)), 'close')
    opos = K((0, (1250, 560)), (s.dur, (980, 560), 'linear'))
    s.add(Orca(pos=opos, scale=1.0, facing='left', jaw=8, layer='mid'))
    s.add(Liver(pos=lambda t, opos=opos: (opos(t)[0] - 470, opos(t)[1] + 30), scale=1.1, layer='mid', z=2))
    s.add(Badge('question', 'SHOWING OFF?', pos=(1500, 230), r=70, t0=0.4))

    # 15 wide: just swimming past ----------------------------------------------
    pl = Surface('day', waterline=380, sun=(0.7, 0.12))
    s = new(pl, Camera(push=0.3, drift=(0, 0)), 'past')
    tpush = L(s, 277.82)
    s.add(Speedboat(pos=(960, 380), scale=0.6, plate=pl, crew=3, layer='mid'))
    opos = K((0, (1500, 720)), (s.dur, (420, 700), 'linear'))
    s.add(Orca(pos=opos, scale=0.3, facing='left', jaw=6, layer='mid', z=2))
    s.add(Liver(pos=lambda t, opos=opos: (opos(t)[0] - 143, opos(t)[1] + 6), scale=0.33, layer='mid', z=3))
    s.add(Label('JUST SWIMMING PAST.', size=64, align='center', pos=(960, 1000), t0=0.4))
    s.camera.emphasis(tpush, s.dur, 0.25, target=(960, 640))

    # 16 menu -------------------------------------------------------------------
    s = new(Sepia(), Camera(push=0.9, drift=(0, 0)), 'menu')
    s.add(MenuCard(pos=(960, 560), scale=0.95, t_items=(0.15, 0.45), t_circle=0.9, t_big=1.7, layer='mid'))

    # 17 Australia globe --------------------------------------------------------
    s = new(Board(), Camera(push=0.8, drift=(-3, 0), wander=3), 'oz')
    s.add(Globe(center=(128, -28), radius=340, spin=1.5, highlight=['Australia'], pins=[(119.4, -34.4)],
                pos=(1180, 560), t0=0))
    s.add(StatBox('MARCH 2019', sub='OFF WESTERN AUSTRALIA', t0=L(s, wt('march', 281.4, 281.6)), t_sub=0.9, size=56))

    # 18 blue whale swarmed -----------------------------------------------------
    s = new(Underwater(depth=0.45), Camera(push=0.9, drift=(-4, 0)), 'swarm')
    tdz = L(s, wt('dozen', 285.4, 285.76))
    s.add(BlueWhale(pos=K((0, (1060, 560)), (s.dur, (940, 570), 'linear')), scale=1.25, layer='mid', z=0))
    for k in range(12):
        a0 = k / 12 * math.tau; rx, ry = 680 + 40 * (k % 3), 230 + 30 * (k % 2)
        def p(t, a0=a0, rx=rx, ry=ry):
            a = a0 + 0.5 * t
            return (980 + rx * math.cos(a), 560 + ry * math.sin(a))
        fac = 'left' if math.sin(a0) > 0 else 'right'
        s.add(Orca(pos=p, scale=0.17, facing=fac, phase=k * 0.4, layer='mid', z=1 if math.sin(a0) > 0 else -1))
    s.add(IconRow('orca', times=[tdz + 0.05 * i for i in range(12)], r=26, gap=70, pos=(960, 130)))
    s.add(Label('ABOUT A DOZEN ORCAS', size=44, align='center', pos=(960, 230), t0=tdz + 0.4))

    # 19 scale board ------------------------------------------------------------
    s = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'scale')
    t20, tor = L(s, wt('20', 288.6, 288.92)), L(s, wt('twice', 289.8, 290.54))
    s.add(BlueWhale(pos=(960, 320), scale=1.4, swim=0.4, layer='mid'))
    s.add(DimensionLine((260, 470), (1660, 470), label='~20 M', sub='ADULT BLUE WHALE', t0=t20))
    s.add(Orca(pos=(610, 780), scale=0.7, facing='left', swim=0.4, layer='mid', t0=tor))
    s.add(DimensionLine((260, 960), (960, 960), label='BIGGEST ORCA EVER MEASURED', size=30, t0=tor + 0.3))
    s.add(Stamp('2\u00D7', PAL.ORANGE, 120, pos=(1400, 820), t0=tor + 0.9))

    # 20 clock ------------------------------------------------------------------
    s = new(Abyss(), Camera(push=0.6, drift=(0, 0)), 'clock')
    s.add(BlueWhale(pos=K((0, (760, 420)), (s.dur, (720, 640), 'linear')), rot=K((0, 3), (s.dur, 14, 'linear')),
                    scale=1.1, swim=0.15, silhouette=True, sil_color='#2B4B5E', layer='mid'))
    s.add(Clock(pos=(1500, 420), r=200, t_a=0.2, t_b=1.8, minutes=60, layer='overlay'))
    s.add(Label('ABOUT AN HOUR', size=54, align='center', pos=(1500, 720), t0=0.3))

    # 21 field report -----------------------------------------------------------
    s = new(Sepia(), Camera(push=0.8, drift=(0, 0)), 'report')
    def fig(ctx, t, w, h):
        BlueWhale(pos=(w / 2, h / 2), scale=0.28, swim=0.6).render(ctx, t)
        for k in range(5):
            Orca(pos=(w / 2 - 120 + 60 * k, h / 2 + 70 - 140 * (k % 2)), scale=0.06, facing='left').render(ctx, t)
    s.add(FieldReport(figure=fig, pos=(960, 560), layer='mid'))
    s.add(Stamp('FIRST EVER RECORDED', PAL.RED, 70, pos=(1180, 860), t0=L(s, 296.17)))

    # 22 survival plan ----------------------------------------------------------
    s = new(Board(tint='teal'), Camera(push=0.7, drift=(0, 0)), 'plan')
    def fig2(ctx, t, w, h):
        BlueWhale(pos=(w / 2 + 20 * math.sin(t), h / 2), scale=0.38, swim=0.8).render(ctx, t)
    tst = L(s, 301.01)
    s.add(Clipboard(t_strike=tst, figure=fig2, pos=(680, 560), scale=1.0, layer='mid'))
    s.add(Punchline('\u2026NOT A PLAN.', size=86, pos=(1420, 580), t0=L(s, 301.44)))
    s.camera.shake(L(s, 301.44), amp=10, decay=0.4)

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-6
    return shots
