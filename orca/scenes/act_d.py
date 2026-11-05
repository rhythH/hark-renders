"""Act D — chapter 4/6 BOATS (abs 302.2–379.6). Plan: scenes/plan_d.md."""
import math
from engine import *
from engine.core import Element
from engine.ui import ChapterTitle
from scenes.assets_d import (NightSurface, sepia_grade, FlatMap, Newspaper, surfer_art, _surfer_side, Surfer,
                             SurferBelow, SeaLionBelow, LegStitches, Reticle, SailboatTop, SinkingBoat, PersonIcon,
                             HatOrca, HypoBadge, ball_content, salmon_content, boat_bandage_content, NaturalistCard)

T_START, T_END = 302.2, 379.6
CUTS = [302.2, 305.68, 307.98, 310.2, 313.74, 315.92, 318.28, 322.94, 326.66, 330.57, 332.46, 336.22, 339.07,
        341.58, 344.58, 346.92, 351.6, 356.4, 358.24, 362.99, 366.03, 368.80, 371.56, 374.20, 377.60, 379.6]
LABELS = ['SIZE', 'MENU', 'SHARKS', 'BOATS', 'YOUR MOVE', 'THE REAL DANGER']
ICONS = ['orca', 'fish', 'fin', 'boat', 'person', 'heart']


def fade_in(dur=0.6):
    return Fn(lambda ctx, t: (ctx.set_source_rgba(0, 0, 0, max(0.0, 1 - t / dur)), ctx.paint()), layer='overlay', t1=dur)


def build(words=None):
    shots = []
    idx = [0]

    def new(plate, camera=None, name=''):
        i = idx[0]; idx[0] += 1
        s = Shot(round(CUTS[i + 1] - CUTS[i], 4), plate=plate, camera=camera or Camera(), name=name)
        if i == 0: s.abs_start = T_START
        c0 = CUTS[i]
        shots.append(s)
        return s, (lambda a: a - c0)

    # 1 — chapter card BOATS
    pl = NightSurface('night', waterline=600, sun=(0.75, 0.2))
    s, L = new(pl, Camera(push=0.6, drift=(5, 0)), 'card')
    boat = s.add(Sailboat(pos=K((0, (1180, 600)), (4, (1260, 600), 'linear')), scale=0.55, facing='right', plate=pl,
                          layer='mid', z=1))
    for j, (y, ph) in enumerate([(820, 0.0), (900, 0.7), (980, 1.4)]):
        s.add(Orca(pos=K((0, (380 + j * 160, y)), (4, (700 + j * 160, y - 30), 'linear')), scale=0.32, facing='right',
                   variant='silhouette', phase=ph, layer='mid', z=2))
    rp = boat.rudder_world(1.2)
    s.add(Reticle(pos=lambda t, b=boat: b.rudder_world(t + 1.2), r=60, t0=1.2, layer='mid', z=3))
    s.add(ChapterTitle('BOATS', 'THE GLADIS PROBLEM', 4, icons=ICONS, labels=LABELS, t0=0.3))
    s.add(fade_in(0.6))

    # 2 — orca approaches a diver: "on a person?"
    s, L = new(Underwater(depth=0.3, seed=7), Camera(push=0.9, drift=(-6, -2)), 'approach')
    s.add(FishSchool(pos=(1500, 300), n=30, radius=140, mode='stream', fish_len=30, layer='back', scale=0.7))
    s.add(Diver(pos=K((0, (1260, 600)), (2.3, (1230, 600), 'linear')), scale=0.42, facing='left', layer='mid', z=2))
    s.add(Orca(pos=K((0, (-250, 520)), (2.3, (520, 540), 'eo')), scale=0.62, facing='right', layer='mid', z=1))
    s.add(Pill('A PERSON', 'dark', size=34, pos=(1250, 400), target=(1235, 560), t0=L(307.06)))
    s.add(Label('?', size=180, font='xb', color=PAL.ORANGE, align='center', pos=(960, 330), t0=L(305.02)))
    s.add(Bubbles(pos=(1500, 1000), rate=3, spread=40, layer='fg'))

    # 3 — orca passes the diver. IN THE WILD / ALMOST NEVER
    s, L = new(Underwater(depth=0.3, seed=7), Camera(push=0.7, drift=(6, 0)), 'pass')
    s.add(Diver(pos=(1180, 640), scale=0.42, facing='left', layer='mid', z=2))
    s.add(Orca(pos=K((0, (380, 470)), (2.22, (2300, 430), 'linear')), scale=0.7, facing='right', layer='mid', z=1))
    s.add(StatBox('IN THE WILD', t0=L(308.08)))
    s.add(Stamp('ALMOST NEVER', PAL.GREEN, 76, pos=(960, 870), t0=L(309.10)))

    # 4 — sepia newspaper, SEPT 1972
    s, L = new(Sepia(), Camera(push=1.2, drift=(0, -4), wander=3), 'clip')
    s.add(Newspaper('SURFER BITTEN AT POINT SUR', kicker='COASTAL NEWS', dateline='SEPTEMBER 1972',
                    art=surfer_art, w=1180, h=760, pos=K((0, (960, 1400)), (0.4, (960, 560), 'eo')),
                    rot=K((0, 6), (0.4, -2, 'eo')), layer='mid'))
    s.add(StatBox('SEPTEMBER 1972', t0=L(311.98), pos=(96, 90)))
    s.post.append(sepia_grade(0.35))

    # 5 — sepia map pin: Point Sur, California
    s, L = new(Sepia(), Camera(push=1.0, drift=(0, 0), wander=2), 'map')
    s.add(FlatMap(-121.0, 36.6, k=95, box=(1500, 860), style='sepia', pos=(960, 540), layer='mid',
                  pins=[(-121.9, 36.31, L(313.98))],
                  labels=[('POINT SUR', -124.0, 36.15, L(314.0), 34), ('CALIFORNIA', -119.2, 37.6, L(314.76), 44),
                          ('PACIFIC OCEAN', -124.6, 34.4, 0.1, 28)]))
    s.camera.emphasis(0.3, 2.1, 0.15, target=(860, 600))
    s.post.append(sepia_grade(0.3))

    # 6 — polaroid of the surfer, 18, Hans Kretschmer
    s, L = new(Sepia(), Camera(push=0.9, drift=(4, 0)), 'polaroid')
    s.add(Polaroid(content=surfer_art, caption='POINT SUR, 1972', w=640, h=470, angle=-4, pos=(760, 520),
                   bg='#CDBB93'))
    s.add(Pill('18-YEAR-OLD SURFER', 'dark', size=40, pos=(1450, 330), t0=L(316.10)))
    s.add(Typewriter('HANS KRETSCHMER', size=60, font='xb', pos=(1180, 860), t0=L(317.50), cps=24))
    s.post.append(sepia_grade(0.5))

    # 7 — from below: bump, look back, the bite
    s, L = new(Underwater(depth=0.15, surface=True, seed=4), Camera(push=0.8, drift=(0, 0)), 'below')
    tb, th = L(318.78), L(321.30)
    sb = s.add(SurferBelow(pos=(980, 170), scale=0.9, layer='mid', z=2,
                           rot=lambda t: (6 * math.sin((t - tb) * 18) * math.exp(-(t - tb) * 2.5)) if t > tb else 0))
    s.add(Orca(pos=K((0, (760, 1500)), (tb - 0.2, (900, 520), 'eo'), (tb, (900, 330), 'ei'), (tb + 0.6, (820, 700), 'eo'),
                     (th - 0.5, (880, 760)), (th, (1080, 270), 'ei'), (4.66, (1100, 300))),
               rot=K((0, 75), (tb, 85), (tb + 0.6, 70), (th, 80)), scale=0.55, facing='left', layer='mid', z=1,
               jaw=K((0, 0), (th - 0.4, 0), (th - 0.15, 26), (th, 6))))
    s.add(Pill('A BUMP', 'dark', size=36, pos=(1450, 420), target=(1080, 230), t0=tb))
    s.add(Pill('A BLACK HEAD', 'red', size=36, pos=(560, 560), t0=L(320.78)))
    impact(s, th, (1080, 220), amp=18, gravity=60)
    s.post.append(sepia_grade(0.55))

    # 8 — x-ray leg: 100 stitches
    s, L = new(Board(), Camera(push=0.6, drift=(3, 0), wander=3), 'stitches')
    t100 = L(325.02)
    s.add(LegStitches(n=K((0, 0), (t100 - 0.1, 0), (t100 + 0.9, 100, 'eo')), pos=(900, 600), scale=0.95, layer='mid'))
    s.add(Pill('MADE IT TO SHORE', 'green', size=34, pos=(380, 160), tick=True, t0=L(323.50)))
    s.add(Counter(0, 100, dur=0.9, size=120, pos=(1500, 230), unit='stitches', t0=t100))

    # 9 — spot the difference: surfer vs sea lion from below
    s, L = new(Underwater(depth=0.15, surface=True, seed=11), Camera(push=0.7, drift=(0, 0)), 'spot')
    s.add(SurferBelow(pos=K((0, (520, 220)), (3.91, (560, 225), 'linear')), scale=0.75, layer='mid'))
    s.add(SeaLionBelow(pos=K((0, (1420, 230)), (3.91, (1380, 225), 'linear')), scale=0.85, layer='mid'))
    s.add(Orca(pos=K((0, (-200, 900)), (3.91, (700, 850), 'linear')), scale=0.4, facing='right', variant='silhouette',
               layer='back'))
    s.add(Pill('BLACK WETSUIT', 'dark', size=34, pos=(520, 470), target=(520, 250), t0=L(327.10)))
    s.add(Pill('SEA LION', 'orange', size=34, pos=(1420, 470), target=(1400, 250), t0=L(329.46)))
    s.add(Label('SPOT THE DIFFERENCE', size=64, align='center', pos=(960, 760), reveal='letters', t0=L(328.08)))

    # 10 — dusk sailboat, fin passes: "Boats are another story"
    pl = NightSurface('dusk', waterline=620, sun=(0.3, 0.42))
    s, L = new(pl, Camera(push=0.8, drift=(-6, 0)), 'dusk')
    s.add(Sailboat(pos=K((0, (760, 620)), (1.89, (860, 620), 'linear')), scale=0.5, facing='right', plate=pl, layer='mid'))
    s.add(Orca(pos=K((0, (2100, 700)), (1.89, (1250, 700), 'linear')), scale=0.4, facing='left', layer='mid', z=2))
    s.add(Label('BOATS: ANOTHER STORY', size=58, align='center', pos=(960, 200), reveal='letters', t0=L(330.67)))

    # 11 — Iberia map since May 2020
    s, L = new(Board(), Camera(push=0.8, drift=(0, 0), wander=2), 'iberia')
    s.add(FlatMap(-6.0, 39.6, k=95, box=(1500, 860), highlight=['Spain', 'Portugal'], pos=(960, 560), layer='mid',
                  pins=[(-5.8, 35.9, L(333.0)), (-6.6, 36.6, L(333.4)), (-9.3, 38.5, L(334.06)), (-9.1, 40.5, L(334.5)),
                        (-8.9, 42.4, L(334.9)), (-8.4, 43.5, L(335.2))],
                  labels=[('SPAIN', -3.6, 40.0, L(335.34), 44), ('PORTUGAL', -7.7, 39.6, L(335.96), 30),
                          ('GIBRALTAR', -5.4, 35.4, L(333.0), 24)]))
    s.add(StatBox('SINCE MAY 2020', t0=L(332.68), pos=(96, 90)))
    s.add(Pill('A SMALL GROUP OF ORCAS', 'orange', size=32, pos=(1450, 980), t0=L(334.06)))

    # 12 — hull from below, three orcas from behind
    pl = Surface('day', waterline=300, sun=(0.6, 0.1))
    s, L = new(pl, Camera(push=0.9, drift=(4, 0)), 'hull')
    s.add(Sailboat(pos=K((0, (1250, 300)), (2.85, (1330, 300), 'linear')), scale=0.85, facing='right', plate=pl, layer='mid'))
    for j in range(3):
        s.add(Orca(pos=K((0, (-300 - j * 220, 860 - j * 70)), (2.85, (520 - j * 200, 640 - j * 60), 'eo')), scale=0.4,
                   facing='right', phase=j * 0.6, rot=-6, layer='mid', z=2))
    s.add(Pill('SAILING BOATS', 'dark', size=34, pos=(1280, 120), t0=L(337.66)))

    # 13 — cross-section: not the people, the rudders
    pl = Surface('day', waterline=560, sun=(0.7, 0.16))
    s, L = new(pl, Camera(push=0.5, drift=(0, 0), wander=2), 'xsec')
    boat = s.add(Sailboat(pos=(1000, 560), scale=0.75, facing='right', plate=pl, crew=2, layer='mid'))
    tr = L(340.54)
    s.add(Pill('PEOPLE', 'green', size=36, tick=True, pos=(780, 240), target=(900, 470), t0=L(339.50)))
    s.add(Pill('NOT THE', 'grey', size=26, pos=(780, 175), t0=L(339.17)))
    s.add(Reticle(pos=lambda t, b=boat: b.rudder_world(t + tr), r=70, t0=tr, layer='mid', z=3))
    s.add(Pill('RUDDER', 'red', size=40, pos=(420, 880), target=lambda t, b=boat: b.rudder_world(t), t0=tr))
    s.camera.emphasis(tr - 0.2, 2.5, 0.25, target=boat.rudder_world(tr))

    # 14 — REC: from behind, ram, bite, rudder breaks
    pl = Surface('day', waterline=560, sun=(0.7, 0.16))
    s, L = new(pl, Camera(push=0.5, drift=(0, 0), wander=2), 'rec')
    t_ram, t_bite = L(343.02), L(343.58)
    boat = Sailboat(pos=(1060, 560), scale=0.62, facing='right', plate=pl, layer='mid', z=1,
                    damage=lambda lt: 'ok' if lt < t_bite else 'broken',
                    rudder=K((0, 0), (t_ram, 0), (t_ram + 0.1, 20, 'eo'), (t_bite, 0), (t_bite + 0.1, 35, 'eo'), (3.0, -10)))
    s.add(boat)
    hp = boat.rudder_world(t_bite)
    hit = (hp[0] - 30, hp[1] + 10)
    s.add(Orca(pos=K((0, (-350, 880)), (t_ram, (hit[0] - 260, hit[1] + 40), 'ei'), (t_ram + 0.25, (hit[0] - 330, hit[1] + 60), 'eo'),
                     (t_bite, (hit[0] - 250, hit[1] + 30), 'ei'), (t_bite + 0.4, (hit[0] - 330, hit[1] + 80), 'eo'),
                     (3.0, (hit[0] - 420, hit[1] + 140))),
               rot=K((0, -8), (t_ram, -10), (t_bite, -12), (3.0, 10)), scale=0.5, facing='right', layer='mid', z=2,
               jaw=K((0, 0), (t_bite - 0.35, 0), (t_bite - 0.1, 22), (t_bite + 0.05, 2))))
    s.add(boat.rudder_piece(t_bite, layer='mid', z=0))
    impact(s, t_ram, hit, amp=12, gravity=60)
    impact(s, t_bite, hit, amp=18, gravity=60)
    s.add(Pill('FROM BEHIND', 'dark', size=30, pos=(400, 300), t0=L(342.06)))
    s.add(Pill('RAM', 'red', size=40, pos=(hit[0] - 120, hit[1] + 260), t0=t_ram))
    s.add(Pill('BITE', 'red', size=40, pos=(hit[0] + 140, hit[1] + 260), t0=t_bite))
    rec_shot(s, tc_start=14 * 60 + 2.0)

    # 15 — top-down spin
    s, L = new(TopDown(), Camera(push=0.6, drift=(0, 0)), 'spin')
    ts = L(345.20)
    s.add(SailboatTop(pos=(960, 560), scale=0.9, layer='mid', z=1,
                      rot=lambda t: -10 + (0 if t < ts else 280 * ease('eio', min(1, (t - ts) / 1.1))),
                      rudder=lambda t: 30 * math.sin(t * 9) if t > ts - 0.3 else 0))
    s.add(OrcaTop(pos=K((0, (300, 760)), (ts, (560, 640), 'eo'), (2.34, (380, 900))), scale=0.45, rot=-20, layer='mid', z=2))
    s.add(Pill('SPIN', 'red', size=46, pos=(1460, 220), t0=ts))

    # 16 — at least 8 sunk, nobody hurt
    s, L = new(Board(), Camera(push=0.4, drift=(0, 0), wander=2), 'tally')
    t8, tsunk = L(347.20), L(348.02)
    for i in range(8):
        t0b = t8 - 0.1 + i * 0.07
        s.add(SinkingBoat(pos=(260 + i * 200, 420), scale=0.8, t_sink=tsunk + i * 0.08 - t0b, t0=t0b, layer='mid'))
    s.add(Label('AT LEAST', size=40, font='bold', track=0.22, align='right', pos=(760, 175), t0=t8 - 0.15))
    s.add(Counter(0, 8, dur=0.6, size=100, pos=(800, 195), align='left', suffix=' BOATS SUNK', t0=t8))
    for i in range(8):
        t0p = L(348.93) + i * 0.04
        s.add(PersonIcon(pos=(260 + i * 200, 760), t_tick=L(350.1) + i * 0.03 - t0p, t0=t0p, layer='mid'))
    s.add(Stamp('HURT: 0', PAL.GREEN, 72, pos=(960, 930), t0=L(350.36)))

    # 17 — scientists call every orca Gladis
    s, L = new(Underwater(depth=0.35, seed=9), Camera(push=0.6, drift=(4, 0)), 'gladis')
    os_ = []
    for j, (x, y) in enumerate([(1250, 300), (1500, 560), (1150, 780)]):
        p = K((0, (x + 250, y)), (4.8, (x - 250, y - 20), 'linear'))
        s.add(Orca(pos=p, scale=0.36, facing='left', phase=j * 0.8, layer='mid', z=1))
        os_.append(p)
    s.add(Human(coat='lab', pose='point', glasses=True, hat=None, pos=(380, 1000), scale=1.4, layer='mid', z=3))
    tg = L(353.34)
    for j, p in enumerate(os_):
        s.add(Pill('GLADIS', 'orange', size=34, pos=(lambda p, o: lambda t: (p(t + o)[0] + 0, p(t + o)[1] - 150))(p, tg + j * 0.12),
                   target=(lambda p, tt: lambda t: (p(t)[0] - 100, p(t)[1] - 40))(p, tg),
                   t0=tg + j * 0.12, world=True))
    s.add(Pill('SCIENTISTS', 'dark', size=30, pos=(380, 560), t0=0.1))

    # 18 — naturalist card ORCINUS GLADIATOR
    s, L = new(Sepia(), Camera(push=1.0, drift=(0, 0), wander=2), 'naturalist')
    s.add(NaturalistCard(pos=(960, 540), scale=0.95, t_type=L(356.5), layer='mid'))
    s.post.append(sepia_grade(0.25, grain=True))

    # 19 — a gang of gladiators, all called Gladis
    s, L = new(Underwater(depth=0.4, seed=12), Camera(push=0.5, drift=(-30, 0)), 'gang')
    tG = L(361.74)
    pos_list = []
    for j, (x, y) in enumerate([(1050, 330), (1600, 420), (850, 700), (1450, 780)]):
        p = K((0, (x + 450, y)), (4.75, (x - 350, y - 10), 'linear'))
        s.add(HatOrca(hat='helmet', crest=['#C8453A', '#C8453A', '#D9A23A', '#C8453A'][j], pos=p, scale=0.38,
                      facing='left', phase=j * 0.7, layer='mid', z=j))
        pos_list.append(p)
    s.add(Label('A GANG OF GLADIATORS', size=60, align='center', pos=(960, 160), reveal='letters', layer='overlay',
                t0=L(359.92)))
    for j, p in enumerate(pos_list):
        s.add(Pill('GLADIS', 'orange', size=32, pos=(lambda p, o: lambda t: (p(t + o)[0] - 40, p(t + o)[1] + 120))(p, tG + j * 0.06),
                   t0=tG + j * 0.06, world=True))
    s.camera.shake(tG, amp=14, decay=0.4)

    # 20 — scientist shrug: nobody knows
    s, L = new(Board(), Camera(push=0.7, drift=(0, 0)), 'shrug')
    s.add(Human(coat='lab', pose=lambda t: 'shrug' if t > L(364.4) else 'stand', glasses=True, hat=None,
                pos=(960, 960), scale=1.6, layer='mid'))
    s.add(Label('WHY?', size=110, align='center', color=PAL.ORANGE, pos=(960, 230), t0=L(363.09)))
    for j, (x, y, tq) in enumerate([(640, 420, 363.4), (1290, 380, 363.7), (1400, 600, 364.0)]):
        s.add(Badge('question', r=56, pos=(x, y), t0=L(tq)))
    s.add(Stamp('NOBODY KNOWS', PAL.RED, 78, pos=(960, 560), t0=L(364.65)))

    # 21 — hypotheses: play? fad?
    s, L = new(Underwater(depth=0.5, seed=13), Camera(push=0.6, drift=(0, 0)), 'hypo')
    s.add(Orca(pos=K((0, (2200, 860)), (2.77, (-300, 820), 'linear')), scale=0.3, facing='left', variant='silhouette',
               layer='back'))
    s.add(HypoBadge(ball_content, 'PLAY?', r=170, kind='orange', pos=(620, 470), t0=L(366.64)))
    s.add(HypoBadge(salmon_content, 'FAD?', r=170, kind='orange', pos=(1300, 470), t0=L(368.04)))

    # 22 — sepia 1987, Puget Sound
    def puget(ctx, t, w, h):
        ctx.rectangle(0, 0, w, h * 0.5); set_col(ctx, '#DCCCA6'); ctx.fill()
        ctx.rectangle(0, h * 0.5, w, h); set_col(ctx, '#8E7A57'); ctx.fill()
        ctx.move_to(0, h * 0.5); ctx.curve_to(w * 0.2, h * 0.32, w * 0.4, h * 0.36, w * 0.6, h * 0.5); set_col(ctx, '#6B5536'); ctx.fill()
        for k_, x0 in enumerate((0.35, 0.65)):
            x = w * x0 + 20 * math.sin(t * 0.8 + k_); y = h * 0.5 + 3 * math.sin(t * 2 + k_)
            ctx.move_to(x - 30, y); ctx.curve_to(x - 10, y - 20, x - 2, y - 70, x + 6, y - 90)
            ctx.curve_to(x + 10, y - 50, x + 20, y - 15, x + 40, y); ctx.close_path(); set_col(ctx, '#1E140C'); ctx.fill()
    s, L = new(Sepia(), Camera(push=1.0, drift=(-4, 0)), '1987')
    s.add(Polaroid(content=puget, caption='1987', w=620, h=440, angle=5, pos=(900, 500), bg='#CDBB93'))
    s.add(StatBox('1987', t0=L(368.90), size=80, pos=(96, 90)))
    s.add(Pill('PUGET SOUND', 'dark', size=40, pos=(1460, 880), t0=L(370.92)))
    s.post.append(sepia_grade(0.5))

    # 23 — orca wearing a dead salmon as a hat
    s, L = new(Underwater(depth=0.3, seed=14), Camera(push=0.9, drift=(-4, 0)), 'salmonhat')
    sp = K((0, (1350, 560)), (2.64, (850, 540), 'linear'))
    s.add(HatOrca(hat='salmon', pos=sp, scale=0.6, facing='left', layer='mid'))
    s.add(Pill('DEAD SALMON', 'orange', size=38, pos=(lambda t, o=L(372.74): (sp(t + o)[0] - 160, 160)),
               target=lambda t: (sp(t)[0] - 190, sp(t)[1] - 150), t0=L(372.74), world=True))
    s.add(Stamp('= HAT', PAL.RED, 80, pos=(1450, 860), t0=L(373.42)))
    s.add(Bubbles(pos=(400, 1000), rate=2, spread=60, layer='fg'))

    # 24 — dusk: one bad encounter with a boat
    pl = NightSurface('dusk', waterline=560, sun=(0.75, 0.4))
    s, L = new(pl, Camera(push=0.6, drift=(0, 0), wander=2), 'encounter')
    tk = L(375.66)
    boat = s.add(Sailboat(pos=K((0, (300, 560)), (tk, (860, 560), 'linear'), (3.4, (1000, 560), 'eo')), scale=0.6,
                          facing='right', plate=pl, heel=K((0, 0), (tk, 0), (tk + 0.15, -6), (3.4, 0)), layer='mid', z=1))
    s.add(Orca(pos=K((0, (1500, 820)), (tk, (1200, 660), 'eo'), (tk + 0.4, (1330, 760), 'eo'), (3.4, (1600, 900))),
               rot=K((0, 0), (tk, -4), (tk + 0.4, 18)), scale=0.42, facing='left', layer='mid', z=2,
               blink=[tk, tk + 0.5]))
    impact(s, tk, (1080, 640), amp=14, gravity=60)
    s.add(Label('ONE BAD ENCOUNTER?', size=64, align='center', pos=(960, 190), reveal='letters', layer='overlay',
                t0=L(375.24)))

    # 25 — verdict: never proven
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0)), 'verdict')
    for j, (fn, cap) in enumerate([(ball_content, 'PLAY?'), (salmon_content, 'FAD?'), (boat_bandage_content, 'TRAUMA?')]):
        s.add(HypoBadge(fn, cap, r=130, kind='dark', pos=(500 + j * 460, 420), t0=0.02 + j * 0.12))
    s.add(Stamp('NEVER PROVEN', PAL.RED, 92, pos=(960, 820), t0=L(378.90)))
    s.camera.shake(L(378.90), amp=12, decay=0.4)

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-3, sum(x.dur for x in shots)
    return shots
