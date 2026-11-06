"""Act F — chapter 5/6 YOUR MOVE (croc). Absolute range [402.0, 491.4). Plan: scenes/plan_f.md."""
import math
from engine import *
from engine.core import StaticCamera, Fn, set_col
from scenes.assets_f import (MovesMenu, OptionCard, HBars, TopBank, PathDraw, ZoneBand, TopPerson, Helicopter,
                             Railing, Reticle, NightWash, CurlArrow, InstructionHeader, Hands, SpotMap,
                             fade_from_black)

T_START, T_END = 402.0, 491.4
CUTS = [402.0, 406.29, 409.27, 411.33, 416.53, 419.07, 423.48, 427.89, 429.38, 432.87, 435.80, 437.61,
        440.34, 445.55, 447.05, 453.90, 456.82, 463.19, 465.95, 469.81, 473.52, 475.99, 479.55, 480.71,
        483.03, 488.31, T_END]
ITEMS = ['Run', 'Swim', 'Hold its mouth', 'Fight']
NAV = ['SIZE', 'BITE', 'RIVALS', 'PEOPLE', 'YOUR MOVE', 'REAL DANGER']
NAV_ICONS = ['eye', 'tooth', 'fin', 'person', 'person', 'skull']
RIVER = '#24443A'


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

    def menu_shot(name, **mk):
        s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), name)
        s.add(Croc(variant='xray', pos=K((0, (2300, 900)), (s.dur, (2300 - 260 * s.dur, 900), 'linear')),
                   scale=0.5, gait=1.0, layer='back', opacity=0.3))
        mk = {k: (v(L) if callable(v) else v) for k, v in mk.items()}
        s.add(MovesMenu(ITEMS, pos=(960, 230), **mk))
        return s, L

    def walker(t, xs, ts, ys):
        return (remap(t, ts[0], ts[1], xs[0], xs[1], 'eio'), ys)

    # 1 ---------------------------------------------------------- chapter card 5/6
    pl = Riverbank(600, bank_x=1150)
    s, L = new(pl, Camera(push=0.7, drift=(4, -1)), 'card5')
    s.add(Human(pos=(1300, pl.bank_y(1300)), scale=0.34, pose='stand', facing='left', layer='mid'))
    s.add(CrocEyes(pos=K((0, (250, 600)), (s.dur, (780, 600), 'linear')), scale=0.9, view='side', water=RIVER,
                   layer='mid'))
    s.add(PathDraw([(x, pl.bank_y(x) + 14) for x in range(1170, 1700, 40)], color=PAL.WHITE, width=5,
                   dash=[18, 14], arrow=False, dur=0.8, t0=0.9))
    s.add(Label('5 M', size=34, font='xb', align='center', pos=(1560, pl.bank_y(1560) + 64), t0=1.5, layer='mid'))
    s.add(ChapterTitle('YOUR MOVE', 'WHAT WOULD YOU ACTUALLY DO?', 5, 6, labels=NAV, icons=NAV_ICONS, t0=0.4))
    s.camera.emphasis(1.4, s.dur, 0.08, target=(1000, 560))
    s.post.append(fade_from_black(0.5))

    # 2 ---------------------------------------------------------- the menu
    menu_shot('menu1', t_items=lambda L: [L(406.39) + 0.22 * i for i in range(4)], sel=lambda L: [(L(408.40), 0)])

    # 3 ---------------------------------------------------------- RUN: on land, that works
    pl = Riverbank(660, bank_x=420, roots=False)
    s, L = new(pl, Camera(push=0.6, drift=(30, -4)), 'run')
    hx = K((0, (900, 0)), (s.dur, (1560, 0), 'linear'))
    s.add(Human(pos=lambda t, pl=pl, hx=hx: (hx(t)[0], pl.bank_y(hx(t)[0]) - 6 * abs(math.sin(t * 9))), scale=0.5,
                pose=lambda t: (40 * math.sin(t * 9), 60, -40 * math.sin(t * 9), 60), facing='right',
                rot=lambda t: 8, layer='mid', z=2))
    cx = K((0, (330, 0)), (s.dur, (640, 0), 'linear'))
    s.add(Croc(pos=lambda t, pl=pl, cx=cx: (cx(t)[0], pl.bank_y(cx(t)[0]) - 40), facing='right', scale=0.38, gait=1.0,
               walk_period=0.7, jaw=K((0, 0), (0.6, 20), (1.2, 8), (2, 0)), rot=lambda t: -7, layer='mid', z=1))
    s.add(SpeedLines(pos=(700, 520), n=8, length=200, angle=180, spread=220, layer='fg', opacity=0.4))
    s.add(OptionCard(1, 'RUN', t0=0.05))
    s.add(Pill('ON LAND, THAT ACTUALLY WORKS', 'green', size=40, tick=True, pos=(960, 900), t0=L(410.40)))

    # 4 ---------------------------------------------------------- 12–14 km/h bars
    tb = 412.83

    def croc_rider(ctx, t):
        pass
    s, L = new(Board(), Camera(push=0.5, drift=(3, 0), wander=2), 'bars1')
    s.add(Label('TOP SPEED ON LAND', size=40, font='bold', track=0.22, pos=(260, 200)))
    rows_c = dict(label='Crocodile', frac=0.45, lo=0.386, text='12–14 KM/H', color=PAL.RED, t=L(tb))
    s.add(HBars([rows_c], pos=(260, 430), length=1200))
    s.add(Croc(pos=lambda t: (260 + 540 * ease('eo', min(1, max(0, (t - L(tb)) / 0.7))) - 120, 330), scale=0.2,
               facing='right', gait=1.0, walk_period=0.6, layer='mid'))
    s.add(Pill('SHORT BURSTS', 'orange', size=36, pos=(1090, 610), t0=L(415.33)))

    # 5 ---------------------------------------------------------- a fit person outruns one
    s, L = new(Board(), Camera(push=0.6, drift=(3, 0), wander=2), 'bars2')
    s.add(Label('TOP SPEED ON LAND', size=40, font='bold', track=0.22, pos=(260, 200)))
    s.add(HBars([dict(rows_c, t=-2), dict(label='Fit person', frac=0.66, text='FASTER', color=PAL.GREEN_LT,
                                           t=L(417.37))], pos=(260, 430), length=1200))
    s.add(Croc(pos=(680, 330), scale=0.2, facing='right', gait=1.0, walk_period=0.6, layer='mid'))
    s.add(Human(pos=lambda t: (980 * min(1, 0.03 + ease('eo', min(1, max(0, (t - L(417.37)) / 0.7)))) + 120, 620 - 4 * abs(math.sin(t * 9))),
                scale=0.3, pose=lambda t: (40 * math.sin(t * 9), 60, -40 * math.sin(t * 9), 60), facing='right',
                rot=8, layer='mid', t0=L(417.37)))
    s.add(Pill('A FIT PERSON CAN OUTRUN ONE', 'green', size=40, tick=True, pos=(960, 930), t0=L(418.07)))

    # 6 ---------------------------------------------------------- top-down: charge zone 5–7 m
    tbk = TopBank(edge=620)
    s, L = new(Black(), Camera(push=0.5, drift=(2, 0), wander=3), 'charge')
    s.add(tbk)
    tl = L(420.53)
    s.add(CrocTop(pos=K((0, (330, 560)), (tl, (380, 560), 'linear'), (tl + 0.6, (900, 560), 'eo')), facing='right',
                  scale=0.45, layer='mid', z=2))
    s.add(ZoneBand(620, 560, t0=L(420.87)))
    s.add(Pill('CHARGE ZONE: 5–7 M', 'red', size=40, pos=(900, 170), t0=L(420.87)))
    s.add(TopPerson(pos=(1500, 560), heading=180, run=0.0, scale=1.3, layer='mid', z=3))
    s.add(Label('ONE RESEARCHER:', size=30, font='bold', track=0.22, color=PAL.CYAN, pos=(1240, 960), t0=L(419.37)))
    s.camera.shake(tl + 0.5, amp=8)

    # 7 ---------------------------------------------------------- zig-zag myth, run straight
    s, L = new(Black(), Camera(push=0.4, drift=(2, 0), wander=3), 'zigzag')
    s.add(TopBank(edge=620))
    s.add(ZoneBand(620, 560, t0=-1))
    s.add(CrocTop(pos=(820, 560), facing='right', scale=0.45, swim=0.3, layer='mid', z=2))
    zz = [(1220, 540), (1330, 330), (1450, 740), (1570, 330), (1690, 740), (1800, 420)]
    s.add(PathDraw(zz, color=PAL.RED, width=9, dash=[22, 14], dur=1.3, t0=L(423.81),
                   opacity=K((0, 1), (L(426.4) - L(423.81), 1), (L(426.7) - L(423.81), 0.25))))
    s.add(Stamp('ZIG-ZAG = MYTH', PAL.RED, 74, angle=-6, pos=(1480, 200), t0=L(425.65)))
    s.add(PathDraw([(1220, 560), (1820, 560)], color=PAL.GREEN_LT, width=12, dur=0.5, t0=L(426.53)))
    ts = L(426.63)
    s.add(TopPerson(pos=K((0, (1180, 560)), (ts, (1180, 560), 'hold'), (s.dur, (1560, 560), 'linear')),
                    heading=0, scale=1.3, layer='mid', z=3))
    s.add(Pill('RUN STRAIGHT', 'green', size=48, tick=True, pos=(1480, 900), t0=ts))

    # 8 ---------------------------------------------------------- menu: run ticked, swim
    menu_shot('menu2', ticks={0: 0.05}, sel=lambda L: [(-1, 0), (L(428.12), 1)])

    # 9 ---------------------------------------------------------- SWIM: please don't
    pl = Riverbank(330, bank_x=1750, mangroves=True)
    s, L = new(pl, Camera(push=1.0, drift=(0, 0), focus=(960, 420)), 'swim')
    s.add(Snorkeller(pos=lambda t, pl=pl: (980 - 12 * t, pl.water_y(980, t)), scale=0.55, panic=K((0, 0.2), (1.2, 0.8)),
                     layer='mid', z=2))
    s.add(Croc(pos=K((0, (1350, 1200)), (s.dur, (1180, 700), 'eo')), rot=24, scale=0.55, facing='left',
               swim=1.0, period=2.0, tint='#173029', opacity=0.85, layer='mid', z=1))
    s.add(OptionCard(2, 'SWIM', t0=0.05))
    s.add(Pill("PLEASE DON'T.", 'red', size=56, pos=(960, 170), t0=L(429.48)))
    s.add(Pill('DEEP WATER', 'dark', size=34, pos=(420, 900), t0=L(430.75)))

    # 10 --------------------------------------------------------- ~100 % fatal
    s, L = new(Danger(grid=True), Camera(push=0.8, drift=(0, 0), wander=3), 'fatal')
    s.add(Croc(variant='silhouette', sil_color='#2A0C0E', pos=K((0, (2200, 820)), (s.dur, (1400, 820), 'linear')),
               scale=0.7, facing='left', layer='back'))
    s.add(Label('DEEP WATER — FATALITY RATE', size=40, font='bold', track=0.22, align='center', pos=(960, 300),
                t0=L(432.97)))
    s.add(Label('CLOSE TO', size=60, font='xb', align='center', color=PAL.WHITE, pos=(960, 420), t0=L(433.65)))
    s.add(Counter(0, 100, dur=L(434.23) - L(433.0), suffix=' %', size=260, color=PAL.RED, pos=(960, 680),
                  t0=L(433.0)))
    s.camera.shake(L(434.25), amp=12)

    # 11 --------------------------------------------------------- menu: swim struck, hold its mouth
    menu_shot('menu3', ticks={0: -1}, strikes={1: 0.1}, stamps={1: ("PLEASE DON'T", 0.25)},
              sel=lambda L: [(-1, 1), (L(436.05), 2)])

    # 12 --------------------------------------------------------- x-ray: weak opening muscles
    s, L = new(Board(), Camera(push=0.8, drift=(-3, 0), wander=2, focus=(800, 560)), 'xray')
    tj = L(438.0)
    s.add(Croc(variant='xray', pos=(1100, 620), scale=1.0, facing='left', swim=0.25, layer='mid',
               jaw=K((0, 0), (tj, 0), (tj + 0.6, 14), (tj + 1.2, 6), (tj + 1.8, 15), (tj + 2.4, 4))))
    s.add(CurlArrow(r=80, a0=-2.6, a1=-1.4, color=PAL.CYAN, width=6, pos=(560, 600), layer='mid', t0=tj))
    s.add(Pill('OPENING MUSCLES: WEAK', 'red', size=40, pos=(700, 300), target=(560, 600), t0=L(438.83)))
    s.add(Pill('REMEMBER?', 'cyan', size=32, pos=(1450, 260), t0=L(439.33)))
    s.add(OptionCard(3, 'HOLD ITS MOUTH', t0=0.05))

    # 13 --------------------------------------------------------- instruction card gag, pull back
    cam = Camera(push=0.0, drift=(0, 0), wander=2, zoom=1.75, focus=(640, 470))
    s, L = new(Sepia(), cam, 'steps')
    tp = L(442.0)
    s.camera.emphasis(tp, tp + 1.1, -0.36, target=(960, 480))
    s.add(Croc(variant='silhouette', sil_color=PAL.INK, pos=(1060, 640), scale=0.8, facing='left', swim=0.3,
               layer='mid'))
    s.add(Hands(pos=(720, 610), scale=0.65, layer='mid', z=2, t0=0.3))
    s.add(InstructionHeader('STEP 1: HOLD JAWS SHUT', size=46, pos=(760, 450), t0=0.15))
    s.add(InstructionHeader('STEP 0: GET ON TOP OF A CROCODILE', color=PAL.RED_DARK, size=60, pos=(960, 180),
                            t0=tp + 0.4))
    s.add(Human(pos=(1150, 575), rot=-90, scale=0.6, pose='panic', facing='right', layer='mid', z=3,
                t0=L(443.13)))
    s.camera.shake(L(444.71), amp=10)

    # 14 --------------------------------------------------------- menu: hold struck, fight
    menu_shot('menu4', ticks={0: -1}, strikes={1: -1, 2: 0.1},
              stamps={1: ("PLEASE DON'T", -1), 2: ('STEP 0', 0.25)}, sel=lambda L: [(-1, 2), (L(446.12), 3)])

    # 15 --------------------------------------------------------- most attacks 2.5–3 m, adult chance
    s, L = new(Board(), Camera(push=0.5, drift=(2, 0), wander=2), 'scale')
    s.add(OptionCard(4, 'FIGHT', t0=0.05))
    s.add(Croc(pos=K((0, (720, 720)), (s.dur, (660, 720), 'linear')), scale=0.75, facing='left', gait=1.0,
               walk_period=2.2, layer='mid'))
    s.add(Label('MOST ATTACKS INVOLVE', size=36, font='bold', track=0.22, align='center', pos=(700, 260),
                t0=L(447.29)))
    s.add(DimensionLine((290, 900), (1040, 900), label='2.5–3 M', sub='CROCODILES', t0=L(448.91)))
    s.add(Human(pos=(1480, 860), scale=1.85, pose='stand', facing='left', layer='mid'))
    s.add(Pill('ADULT: DECENT CHANCE', 'green', size=40, tick=True, pos=(1480, 230), target=(1480, 380),
               t0=L(451.79)))

    # 16 --------------------------------------------------------- go for the eyes
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'eyes')
    s.add(CrocHead(pos=(1000, 600), scale=2.4, domes=False, jaw=K((0, 4), (1.2, 10), (2.4, 3)), layer='mid', facing='left'))
    eye = (935, 490)
    s.add(Reticle(r=60, label='EYES', pos=eye, t0=L(454.49)))
    s.add(Pill('REPORTEDLY', 'cyan', size=36, pos=(1350, 820), t0=L(455.25)))
    s.camera.emphasis(L(454.4), s.dur, 0.12, target=eye)

    # 17 --------------------------------------------------------- "they seem to let go"
    s, L = new(Reef(surface_y=190), Camera(push=0.5, drift=(-6, 0)), 'quote')
    s.add(Snorkeller(pos=(1300, 190), scale=0.5, layer='back'))
    s.add(Croc(pos=K((0, (-300, 760)), (s.dur, (700, 740), 'linear')), scale=0.4, facing='right', tint='#2C8F94',
               opacity=0.5, layer='back'))
    s.add(Dim(0.45, dur=0.4, t0=L(458.4)))
    s.add(Pill('REPTILE EXPERT', 'dark', size=34, pos=(960, 380), t0=L(457.27)))
    s.add(Pill('ON MARCUS MCGOWAN', 'orange', size=34, pos=(960, 450), t0=L(458.61), opacity=1))
    wt = [L(461.09), L(461.73), L(462.11), L(462.29), L(462.47)]
    s.add(QuoteReveal('"CROCODILES SEEM TO LET GO."', kicker='when people fight back', word_times=[w - L(459.45) for w in wt],
                      attribution='— REPTILE EXPERT', size=72, width=1500, pos=(960, 640), t0=L(459.45)))

    # 18 --------------------------------------------------------- still needed a helicopter
    s, L = new(Surface(preset='day', waterline=780), Camera(push=0.4, drift=(40, 0)), 'heli')
    s.add(Helicopter(pos=K((0, (180, 340)), (s.dur, (1600, 300), 'linear')), scale=0.75, layer='mid'))
    s.add(Pill('…HE STILL NEEDED A HELICOPTER.', 'orange', size=48, pos=(1000, 880), t0=L(464.71)))

    # 19 --------------------------------------------------------- the boring answer: don't be there
    pl = Riverbank(600, bank_x=1100)
    s, L = new(pl, Camera(push=0.8, drift=(3, 0)), 'boring')
    s.add(CrocEyes(pos=K((0, (520, 600)), (s.dur, (720, 600), 'linear')), scale=0.8, view='side', water=RIVER,
                   layer='mid'))
    s.add(Label('THE REAL ANSWER', size=64, align='center', reveal='letters', pos=(960, 200), t0=L(466.39)))
    s.add(Label('IS THE BORING ONE', size=36, font='bold', track=0.22, align='center', color=PAL.CYAN,
                pos=(960, 260), t0=L(467.51)))
    s.add(Stamp("DON'T BE THERE.", PAL.RED, 88, angle=-6, pos=(1220, 470), t0=L(468.65)))
    s.camera.shake(L(468.68), amp=10)

    # 20 --------------------------------------------------------- Queensland's advice
    s, L = new(Board(), Camera(push=0.5, drift=(2, 0), wander=2), 'qld')
    s.add(Globe(center=(140, -22), radius=270, highlight=['Australia'], pins=[(145.0, -18.0)], caption='QUEENSLAND',
                pos=(520, 520), t0=0.1))
    s.add(Label("QUEENSLAND'S ADVICE", size=60, reveal='letters', pos=(900, 330), t0=L(469.91)))
    s.add(Pill('SIMPLE', 'orange', size=34, pos=(1010, 420), t0=L(471.15)))
    s.add(Checklist([('KEEP OUT OF THE WATER', 'tick', L(472.69))], t_items=[L(472.10)], size=48, pos=(900, 600)))

    # 21 --------------------------------------------------------- stay more than 5 m from the edge
    pl = Riverbank(640, bank_x=560, roots=False)
    s, L = new(pl, Camera(push=0.5, drift=(4, 0)), 'stay5')
    t5 = L(473.62)
    hxs = K((0, (650, 0)), (t5, (650, 0), 'hold'), (t5 + 1.0, (1450, 0), 'eio'))
    s.add(Human(pos=lambda t, pl=pl, hxs=hxs, t5=t5: (hxs(t)[0], pl.bank_y(hxs(t)[0]) - (5 * abs(math.sin(t * 7)) if t5 < t < t5 + 1 else 0)),
                scale=0.5, pose='stand', facing='left', layer='mid', z=2))
    s.add(CrocEyes(pos=(380, 640), scale=0.8, view='side', water=RIVER, layer='mid'))
    yl = pl.bank_y(1450) + 60
    s.add(DimensionLine((600, pl.bank_y(600) + 40), (1450, pl.bank_y(1450) + 40), label='5 M+', size=52, from_centre=False, dur=0.6, t0=L(474.15)))
    s.add(Pill('MORE THAN 5 M FROM THE EDGE', 'green', size=42, tick=True, pos=(960, 160), t0=L(475.19)))

    # 22 --------------------------------------------------------- something sturdy between you and the water
    pl = Riverbank(620, bank_x=640, roots=False)
    s, L = new(pl, Camera(push=0.6, drift=(3, 0)), 'sturdy')
    s.add(Railing(pos=(800, pl.bank_y(800) + 4), scale=1.0, layer='mid', z=3))
    s.add(Fisherman(pos=(990, pl.bank_y(990)), scale=0.5, facing='left', line_to=(-700, 300), layer='mid', z=2))
    s.add(CrocEyes(pos=K((0, (200, 620)), (s.dur, (330, 620), 'linear')), scale=0.45, view='side', water=RIVER,
                   layer='mid'))
    s.add(Label('IF YOU HAVE TO GET CLOSER', size=36, font='bold', track=0.22, align='center', pos=(960, 160),
                t0=L(476.09)))
    s.add(Pill('SOMETHING STURDY', 'green', size=42, tick=True, pos=(1260, 330), target=(860, pl.bank_y(800) - 120),
               t0=L(477.77)))

    # 23 --------------------------------------------------------- don't crouch
    pl = Riverbank(620, bank_x=640, roots=False)
    s, L = new(pl, Camera(push=1.2, drift=(0, 0), focus=(760, 560)), 'crouch')
    s.add(Human(pos=(720, pl.bank_y(720)), scale=0.55, pose='crouch', facing='left', layer='mid', z=2))
    s.add(CrocEyes(pos=K((0, (380, 620)), (s.dur, (470, 620), 'linear')), scale=0.8, view='side', water=RIVER,
                   layer='mid'))
    s.add(Stamp("DON'T CROUCH", PAL.RED, 84, angle=-6, pos=(1280, 300), t0=L(479.99)))

    # 24 --------------------------------------------------------- never the same spot twice (top-down)
    s, L = new(Black(), Camera(push=0.6, drift=(0, 0), wander=3), 'spots')
    s.add(TopBank(edge=620, seed=5))
    s.add(SpotMap([(760, 240, 'MON', L(480.81)), (800, 820, 'TUE', L(481.29)), (720, 520, 'WED', L(481.73))]))
    s.add(CrocTop(pos=K((0, (300, 360)), (s.dur, (330, 330), 'linear')), facing='right', scale=0.38,
                  submerged=0.6, water='#1E3A34', layer='mid', opacity=0.8))
    s.add(Pill('NEVER THE SAME SPOT TWICE', 'green', size=42, tick=True, pos=(1360, 540), t0=L(482.13)))

    # 25 --------------------------------------------------------- same spot: it waits underwater
    pl = Riverbank(470, bank_x=1000)
    s, L = new(pl, Camera(push=0.9, drift=(-3, 2), focus=(900, 600)), 'samespot')
    days = [(L(483.41), 'MON'), (L(484.27), 'TUE'), (L(485.29), 'WED'), (L(486.89), 'THU')]
    hx_ = 1080

    def vis(i):
        a, b = days[i][0], (days[i + 1][0] if i + 1 < len(days) else s.dur + 1)
        return lambda t: max(0.0, min(1.0, (t - a) / 0.15, (b - 0.1 - t) / 0.15))
    for i, (td, lab) in enumerate(days):
        s.add(Human(pos=(hx_, pl.bank_y(hx_)), scale=0.36, pose=['stand', 'crouch', 'wave', 'stand'][i],
                    coat=['#2F6FA0', '#B5533C', '#4C7A3A', '#7A4C8C'][i], facing='left', layer='mid', z=2,
                    opacity=vis(i)))
        s.add(Pill(lab, 'dark', size=34, pos=(hx_, pl.bank_y(hx_) - 190), opacity=vis(i)))
    s.add(Bucket(pos=(hx_ + 60, pl.bank_y(hx_ + 60)), scale=0.7, layer='mid'))
    s.add(Croc(pos=(560, 860), scale=0.55, facing='right', swim=0.15, period=4.0, tint='#173029', opacity=0.9,
               layer='mid', z=1))
    s.add(Pill('WAITS UNDERWATER', 'red', size=38, pos=(560, 600), target=(560, 820), t0=L(486.29)))
    s.add(Pill('FOR THE NEXT ONE', 'dark', size=30, pos=(560, 670), t0=L(487.49)))

    # 26 --------------------------------------------------------- it's watching you
    s, L = new(Mangrove(horizon=430), Camera(push=2.4, drift=(0, 0), focus=(960, 660)), 'watching')
    s.add(NightWash(0.66))
    s.add(CrocEyes(pos=(960, 700), scale=1.9, view='front', eyeshine=K((0, 0.4), (L(489.0), 1.0)), water='#1E3A34',
                   layer='mid'))
    s.add(Label("IT'S NOT WATCHING THE WATER.", size=60, align='center', reveal='letters', pos=(960, 210),
                t0=L(488.71)))
    s.add(Punchline("…IT'S WATCHING YOU.", size=96, pos=(960, 340), t0=L(490.29)))
    s.camera.emphasis(L(490.3), s.dur, 0.08, target=(960, 690))

    return shots
