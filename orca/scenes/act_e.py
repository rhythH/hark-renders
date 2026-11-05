"""Act E — chapter 5/6 YOUR MOVE. Absolute range [379.6, 453.8). Plan: scenes/plan_e.md."""
import math
from engine import *
from engine.core import StaticCamera
from scenes.assets_e import (MovesMenu, OptionCard, RaceBars, BreathTank, DepthRuler, TopBoat, PushArrow, Zzz,
                             WaveWash, Clipping, surfer_photo, Fist, Leg, fade_from_black)

T_START, T_END = 379.6, 453.8
CUTS = [379.6, 383.95, 387.37, 393.46, 396.26, 400.87, 402.18, 405.16, 407.30, 409.25, 410.91, 414.13,
        418.28, 420.55, 422.37, 425.07, 428.29, 434.00, 436.72, 441.07, 444.01, 447.31, 450.61, T_END]
ITEMS = ['Swim', 'Dive', 'Stay still', 'Fight']
NAV = ['SIZE', 'MENU', 'SHARKS', 'BOATS', 'YOUR MOVE', 'DANGER']


def build(words=None):
    shots = []
    idx = [0]

    def new(plate, camera=None, name=''):
        i = idx[0]; idx[0] += 1
        t0, t1 = CUTS[i], CUTS[i + 1]
        s = Shot(round(t1 - t0, 4), plate=plate, camera=camera or Camera(push=0.8, drift=(6, -2)), name=name)
        if i == 0: s.abs_start = T_START
        shots.append(s)
        return s, (lambda T: T - t0)

    # ---------------------------------------------------------------- 1 chapter card 5/6
    s, L = new(Underwater(depth=0.55, seed=5), Camera(push=0.9, drift=(4, -2)), 'card5')
    s.add(Orca(pos=K((0, (1500, 1350)), (4.35, (1180, 760), 'eo')), rot=-28, scale=0.55, facing='left',
               variant='silhouette', layer='back', period=2.2))
    s.add(Diver(pos=K((0, (980, 300)), (4.35, (1000, 285), 'linear')), scale=0.22, facing='left', kick=0.5, layer='mid'))
    s.add(Bubbles(pos=(1500, 1000), rate=3, spread=60, layer='fg'))
    s.add(ChapterTitle('YOUR MOVE', 'WHAT WOULD YOU ACTUALLY DO?', 5, 6, labels=NAV, t0=0.4))
    s.camera.emphasis(1.5, 4.3, 0.12, target=(1000, 400))
    s.post.append(fade_from_black(0.5))

    # ---------------------------------------------------------------- 2 menu appears
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'menu1')
    s.add(Orca(pos=K((0, (2300, 820)), (3.42, (-400, 790), 'linear')), scale=0.35, facing='left', variant='xray',
               layer='back', opacity=0.35))
    s.add(MovesMenu(ITEMS, t_items=[L(384.2) + 0.22 * i for i in range(4)], sel=[(L(386.10), 0)], pos=(960, 230)))

    # ---------------------------------------------------------------- 3 option 1 SWIM
    s, L = new(Underwater(depth=0.2, surface=True, seed=8), Camera(push=0.6, drift=(-20, 0)), 'swim')
    dpos = K((0, (700, 560)), (6.09, (1000, 560), 'linear'))
    s.add(Diver(pos=dpos, scale=0.45, facing='right', kick=1.6, period=0.42, panic=0.6, layer='mid'))
    s.add(SpeedLines(pos=(500, 560), n=10, length=260, angle=180, spread=300, layer='fg', opacity=0.5))
    s.add(Bubbles(pos=lambda t: (dpos(t)[0] - 180, 600), rate=8, spread=30, layer='fg'))
    s.add(OptionCard(1, 'SWIM', t0=0.05))
    s.add(DimensionLine((360, 820), (1560, 820), label='50 M', sub='FASTEST EVER SWUM', t0=L(387.86), layer='mid'))
    s.add(Stopwatch(pos=(1700, 170), rate=1.0, t0=L(388.6)))
    s.add(Label('UNDER 9 KM/H', size=96, font='black', color=PAL.ORANGE, align='center', pos=(960, 330), t0=L(391.20)))
    s.camera.emphasis(L(391.0), L(393.4), 0.12, target=(900, 500))

    # ---------------------------------------------------------------- 4 race bars
    def orca_rider(ctx, t):
        icon(ctx, 'orca', 40, PAL.WHITE)
    def person_rider(ctx, t):
        icon(ctx, 'person', 34, PAL.WHITE)
    rows_h = dict(label='Fastest human swimmer', value=9, vtext='< 9', color=PAL.WHITE, rider=person_rider)
    s, L = new(Board(), Camera(push=0.6, drift=(4, 0), wander=2), 'race')
    s.add(Label('TOP SPEED IN WATER', size=40, font='bold', track=0.22, pos=(220, 170), t0=0.0))
    s.add(RaceBars([dict(rows_h, t=0.1), dict(label='Orca (burst)', value=45, vtext='~45', color=PAL.RED, t=L(395.00), rider=orca_rider)],
                   pos=(220, 380), length=1250, vmax=50, gap=230))
    s.camera.shake(L(395.3), amp=8)

    # ---------------------------------------------------------------- 5 Usain Bolt ... on land
    s, L = new(Board(), Camera(push=0.8, drift=(3, 0), wander=2), 'bolt')
    s.add(Label('TOP SPEED', size=40, font='bold', track=0.22, pos=(220, 150)))
    s.add(RaceBars([dict(rows_h, t=-2), dict(label='Orca (burst)', value=45, vtext='~45', color=PAL.RED, t=-2, rider=orca_rider),
                    dict(label='Usain Bolt', value=44.7, vtext='ABOUT THE SAME', color=PAL.ORANGE, t=L(397.44), rider=person_rider)],
                   pos=(220, 330), length=1250, vmax=50, gap=200, opacity=K((0, 1), (L(399.5), 1), (L(399.8), 0.35))))
    s.add(Punchline('…ON LAND.', size=120, pos=(960, 1000), t0=L(399.66)))
    s.camera.emphasis(L(399.5), L(400.8), 0.1, target=(960, 700))

    # ---------------------------------------------------------------- 6 menu: swim struck, dive
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'menu2')
    s.add(MovesMenu(ITEMS, sel=[(-1, 0), (L(401.26), 1)], strikes={0: 0.12}, stamps={0: ('TOO SLOW', 0.3)}, pos=(960, 230)))

    # ---------------------------------------------------------------- 7 option 2 DIVE
    s, L = new(Underwater(depth=0.65, seed=11), Camera(push=0.6, drift=(0, 14)), 'dive')
    s.add(Diver(pos=K((0, (620, 260)), (2.98, (700, 640), 'linear')), rot=62, scale=0.38, facing='right', kick=1.3, period=0.5, layer='mid'))
    s.add(Bubbles(pos=K((0, (560, 220)), (2.98, (640, 600), 'linear')), rate=6, spread=20, layer='fg'))
    s.add(DepthRuler(speed=200, x=1820))
    s.add(OptionCard(2, 'DIVE', t0=0.05))
    s.add(BreathTank(lambda t: 1 - t / 1.8, 'YOU', PAL.CYAN, w=130, h=420, pos=(1240, 860), t0=0.5))
    s.add(BreathTank(lambda t: 1.0 - 0.02 * t, 'ORCA', PAL.ORANGE, w=130, h=420, pos=(1520, 860), t0=L(404.0)))
    s.add(Label('10+ MIN', size=84, font='black', color=PAL.ORANGE, align='center', pos=(1520, 380), t0=L(404.20)))

    # ---------------------------------------------------------------- 8 hunts seals for a living
    s, L = new(Underwater(depth=0.4, seed=4), Camera(push=0.9, drift=(-30, 0)), 'chase')
    sp = K((0, (700, 520)), (2.14, (250, 470), 'linear'))
    s.add(Seal(pos=sp, rot=K((0, -4), (1, 4), (2.14, -3)), scale=0.75, layer='mid', z=2))
    s.add(Orca(pos=K((0, (1750, 560)), (2.14, (1050, 520), 'linear')), scale=0.62, facing='left', jaw=K((0, 0), (1.2, 18), (2, 8)),
               period=1.6, layer='mid', z=1))
    s.add(Bubbles(pos=lambda t: (sp(t)[0] + 260, 520), rate=6, spread=20, layer='fg'))
    s.add(Pill('HUNTS SEALS FOR A LIVING', 'red', size=40, pos=(960, 200), t0=L(405.44)))

    # ---------------------------------------------------------------- 9 seal rating
    s, L = new(Board(), Camera(push=0.6, drift=(2, 0), wander=2), 'rating')
    s.add(Seal(pos=(560, 620), scale=1.0, look=K((0, 0), (1.95, 0.6)), layer='mid'))
    s.add(Diver(pos=(1360, 640), scale=0.62, facing='left', kick=0.6, panic=0.3, layer='mid'))
    s.add(Pill('SEAL', 'dark', size=30, pos=(560, 400), target=(560, 560), t0=0.1))
    s.add(Pill('YOU', 'dark', size=30, pos=(1360, 400), target=(1360, 590), t0=0.25))
    s.add(Stamp('SEAL RATING: C-', PAL.RED, 80, angle=-6, pos=(1360, 850), t0=L(408.20)))
    s.camera.shake(L(408.25), amp=10)

    # ---------------------------------------------------------------- 10 menu: dive struck, stay still
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'menu3')
    s.add(MovesMenu(ITEMS, sel=[(-1, 1), (L(409.47), 2)], strikes={0: -1, 1: 0.1}, stamps={0: ('TOO SLOW', -1), 1: ('OUTCLASSED', 0.12)},
                    pos=(960, 230)))

    # ---------------------------------------------------------------- 11 option 3 STAY STILL
    s, L = new(Underwater(depth=0.35, seed=6), Camera(push=0.7, drift=(0, -2)), 'still')
    s.add(Orca(pos=K((0, (-500, 860)), (3.22, (2300, 830), 'linear')), scale=0.4, facing='right', variant='silhouette', layer='back'))
    s.add(Diver(pos=lambda t: (960, 520 + 8 * math.sin(t * 1.4)), scale=0.48, facing='left', kick=0.0, layer='mid'))
    s.add(Bubbles(pos=(900, 450), rate=2, spread=10, layer='fg'))
    s.add(OptionCard(3, 'STAY STILL', t0=0.05))
    s.add(Pill('BEST OPTION', 'green', size=40, tick=True, pos=(960, 820), t0=L(411.91)))

    # ---------------------------------------------------------------- 12 seal on the ice, perfectly still
    sf = Surface('haze', waterline=600, sun=(0.3, 0.2))
    s, L = new(sf, Camera(push=0.6, drift=(2, 0), wander=2), 'floe')
    s.add(IceFloe(pos=(1000, 600), width=620, plate=sf, layer='mid', z=1))
    s.add(Seal(pos=(1000, 560), scale=0.6, layer='mid', z=2))
    for j in range(3):
        s.add(Orca(pos=K((0, (-150 - 120 * j, 760 + 70 * j)), (4.15, (380 - 90 * j, 760 + 70 * j), 'linear')), scale=0.32,
                   facing='right', layer='mid', z=0, period=2.4 + 0.2 * j))
    s.add(Pill('PERFECTLY STILL', 'green', size=36, tick=True, pos=(1000, 300), target=(1000, 500), t0=L(416.27)))

    # ---------------------------------------------------------------- 13 the wave
    sf2 = Surface('haze', waterline=600, sun=(0.3, 0.2))
    s, L = new(sf2, Camera(push=0.8, drift=(0, 0), wander=2), 'wave')
    th = L(419.61)
    s.add(IceFloe(pos=(1000, 600), width=620, plate=sf2, tilt=K((0, 0), (th, 0), (th + 0.3, 8, 'eo'), (2.27, 3)), layer='mid', z=1))
    s.add(Seal(pos=K((0, (1000, 560)), (th, (1000, 560)), (th + 0.7, (1750, 700), 'ei')), rot=K((0, 0), (th, 0), (th + 0.7, 70)),
               scale=0.6, layer='mid', z=4))
    for j in range(3):
        s.add(Orca(pos=K((0, (380 - 90 * j, 760 + 70 * j)), (2.27, (760 - 90 * j, 760 + 70 * j), 'linear')), scale=0.32,
                   facing='right', layer='mid', z=0))
    s.add(WaveWash((lambda t: -300 + (1050 + 300) * min(t / th, 1) + max(0, t - th) * 800), sf2, layer='mid', z=3))
    s.add(Punchline('…THEY JUST MADE A WAVE.', size=84, style='v1', pos=(960, 200), t0=th + 0.05))
    s.camera.shake(th, amp=16)

    # ---------------------------------------------------------------- 14 menu: still struck, fight
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'menu4')
    s.add(MovesMenu(ITEMS, sel=[(-1, 2), (L(421.23), 3)], strikes={0: -1, 1: -1, 2: 0.1},
                    stamps={0: ('TOO SLOW', -1), 1: ('OUTCLASSED', -1), 2: ('SEE: SEALS', 0.12)}, pos=(960, 230)))

    # ---------------------------------------------------------------- 15 option 4 FIGHT, 1972 clipping
    s, L = new(Sepia(), Camera(push=0.8, drift=(4, 0), wander=2), 'clip')
    s.add(Clipping('SEPT 1972', 'SURFER BITTEN', photo=surfer_photo, pos=(1000, 560), w=900, h=560, t0=0.1))
    s.add(OptionCard(4, 'FIGHT', t0=0.05))
    s.add(Pill('ONE PERSON', 'orange', size=40, pos=(1500, 230), t0=L(423.43)))

    # ---------------------------------------------------------------- 16 Hans Kretschmer punch
    s, L = new(Sepia(), Camera(push=0.7, drift=(0, 0), wander=2), 'punch')
    tp = L(425.69)
    s.add(Polaroid(content=lambda ctx, t, w, h: surfer_photo(ctx, t, w, h, sepia=False), caption='HANS KRETSCHMER',
                   w=760, h=520, angle=-3, pos=(900, 500), layer='mid', world=False, t0=0.0))
    s.add(Fist(pos=K((0, (-300, 560)), (tp - 0.18, (-300, 560)), (tp, (1050, 520), 'ei'), (tp + 0.4, (980, 540), 'eo'),
                     (3.22, (960, 545))), streak=K((0, 0), (tp - 0.18, 1), (tp, 1), (tp + 0.3, 0)), scale=0.9, layer='overlay', t0=0))
    impact(s, tp, (1150, 520), amp=18)
    s.add(Pill('IT LET GO', 'green', size=40, tick=True, pos=(1450, 900), t0=L(427.23)))

    # ---------------------------------------------------------------- 17 the punch? or not a sea lion?
    s, L = new(Board(), StaticCamera(), 'balance')
    ta, tb, tc = L(429.13), L(431.57), L(432.61)
    tilt = K((0, 0), (ta, 0), (ta + 0.5, 12, 'eo'), (tb, 10), (tb + 0.5, -12, 'eo'), (tc, -10), (tc + 0.6, 0, 'eo'), (5.71, 0))
    bpos = (960, 300); half = 450
    s.add(Balance(tilt=tilt, width=900, pos=bpos, scale=1.0, layer='overlay'))
    def pan(side):
        def f(t):
            a = math.radians(ev(tilt, t))
            return (bpos[0] + side * half * math.cos(a), bpos[1] + side * half * math.sin(a) + 230)
        return f
    s.add(Pill('THE PUNCH?', 'orange', size=36, pos=pan(-1), t0=ta, world=False))
    s.add(Pill('NOT A SEA LION?', 'cyan', size=36, pos=pan(1), t0=tb, world=False))
    s.add(Stamp('NOBODY CAN SAY', PAL.RED, 84, angle=-5, pos=(960, 880), t0=tc))

    # ---------------------------------------------------------------- 18 still needed 100 stitches
    s, L = new(Danger(), Camera(push=0.8, drift=(3, 0), wander=2), 'stitches')
    t_full = L(435.67)
    s.add(Leg(lambda t: 100 * min(1, max(0, (t - 0.15) / (t_full - 0.15))), total=100, pos=(900, 620), scale=1.0, layer='mid'))
    s.add(Counter(0, 100, dur=t_full - 0.15, suffix=' STITCHES', size=96, pos=(960, 230), t0=0.15))
    s.add(Label('STILL:', size=48, font='black', color=PAL.ORANGE, align='center', pos=(960, 120), t0=0.05))

    # ---------------------------------------------------------------- 19 menu: fight struck, 5. stay out of their way
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'menu5')
    s.add(MovesMenu(ITEMS, sel=[(-1, 3)], strikes={0: -1, 1: -1, 2: -1, 3: 0.15},
                    stamps={0: ('TOO SLOW', -1), 1: ('OUTCLASSED', -1), 2: ('SEE: SEALS', -1), 3: ('STILL BITTEN', 0.2)},
                    dim=(L(438.37), 0.35), extra=('Stay out of their way', L(439.56)), pos=(960, 170)))

    # ---------------------------------------------------------------- 20 top-down: 2022 study of boat encounters
    s, L = new(TopDown(), Camera(push=0.6, drift=(0, 0), wander=2), 'study')
    s.add(TopBoat(heading=0, sails=1, speed=0.8, pos=(1080, 540), scale=1.25, layer='mid', z=1))
    for j, (y, ph) in enumerate([(495, 0), (590, 0.6)]):
        s.add(OrcaTop(pos=(lambda y=y, ph=ph: (lambda t: (690 + 20 * math.sin(t * 1.3 + ph), y + 12 * math.sin(t * 0.9 + ph))))(),
                      rot=180, scale=0.2, layer='mid', z=0))
    s.add(StatBox('2022 STUDY', sub='BOAT ENCOUNTERS', t0=L(441.37), t_sub=L(442.97) - L(441.37)))

    # ---------------------------------------------------------------- 21 crew fights the wheel -> orcas push harder
    s, L = new(TopDown(), Camera(push=1.0, drift=(0, 0), wander=3), 'fight')
    ta = L(446.19)
    s.add(TopBoat(heading=lambda t: 10 * math.sin(t * 2.6), sails=1, speed=0.6, fight=1.0, pos=(1080, 540), scale=1.25, layer='mid', z=1))
    for j, (y, ph) in enumerate([(495, 0), (590, 0.6)]):
        s.add(OrcaTop(pos=(lambda y=y, ph=ph: (lambda t: (650 + 40 * math.sin(t * 2.2 + ph) + (60 if t > ta else 0), y)))(),
                      rot=180, scale=0.2, layer='mid', z=0))
        s.add(PushArrow(size=K((0, 0), (ta, 0), (ta + 0.3, 0.8, 'back'), (3.3, 1.0)), pos=(800, y), layer='mid', z=2))
    s.add(Pill('CREW FIGHTS THE WHEEL', 'dark', size=34, pos=(1050, 300), target=(900, 540), t0=0.2))
    s.add(Pill('ORCAS PUSH HARDER', 'red', size=44, pos=(960, 900), t0=L(446.39)))
    s.camera.shake(ta + 0.1, amp=10)

    # ---------------------------------------------------------------- 22 crew stops -> orcas lose interest
    s, L = new(TopDown(), Camera(push=0.4, drift=(0, 0), wander=2), 'stop')
    s.add(TopBoat(heading=0, sails=K((0, 1), (0.8, 0, 'eo')), speed=K((0, 0.4), (1.0, 0)), fight=0, pos=(1080, 540), scale=1.25, layer='mid', z=1))
    tl = L(449.19)
    for j, (y, ph, dy) in enumerate([(495, 0, -1), (590, 0.6, 1)]):
        s.add(OrcaTop(pos=(lambda y=y, ph=ph, dy=dy: (lambda t: (690 - 60 * max(0, t - 1.2), y + dy * 50 * max(0, t - 1.2))))(),
                      rot=lambda t, dy=dy: 180 + dy * 12 * min(1, max(0, t - 1.2)), scale=0.2, layer='mid', z=0))
    s.add(Zzz(pos=(640, 420), t0=1.2, layer='overlay'))
    s.add(Pill('CREW STOPS', 'dark', size=34, pos=(1050, 300), target=(900, 540), t0=0.2))
    s.add(Pill('ORCAS USUALLY LOSE INTEREST', 'green', size=44, tick=True, pos=(960, 900), t0=tl))

    # ---------------------------------------------------------------- 23 be boring
    sf3 = Surface('day', waterline=600, sun=(0.7, 0.18), wave_amp=3)
    s, L = new(sf3, Camera(push=0.7, drift=(0, 0), wander=2), 'boring')
    s.add(Sailboat(pos=(900, 600), scale=0.55, facing='right', plate=sf3, sails=False, crew=1, layer='mid', z=1))
    for j in range(2):
        s.add(Orca(pos=K((0, (1900 + 200 * j, 860 + 60 * j)), (3.19, (500 + 200 * j, 840 + 60 * j), 'linear')), scale=0.3,
                   facing='left', layer='mid', z=2, period=3.2))
    s.add(Punchline('BE BORING.', size=130, pos=(960, 250), t0=L(453.09)))
    return shots
