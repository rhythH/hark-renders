"""Act A — cold open (abs 0.0–91.6 s). Shot plan: scenes/plan_a.md. Assets: scenes/assets_a.py."""
import math
from engine import *
from engine.core import PAL, Fn, Group, K, set_col, circle, rrect
from engine.text import draw_text
from engine import plates as P
from scenes.assets_a import (NightSurface, NightWater, NightSailboat, Fin, WheelPOV, CockpitDeck, SternRail,
                             StraitMap, sailor_photo, Calendar, Helicopter, Beacon, Poster, Panda, Liver, Panel,
                             FadeIn, Swell, Ripples, Blip, Underline, WordReveal)

CUTS = [0.0, 4.33, 6.89, 8.46, 12.17, 16.89, 19.02, 21.15, 24.75, 28.54, 31.36, 35.19, 38.52, 41.52, 44.21,
        47.16, 49.85, 52.13, 53.64, 56.40, 60.49, 64.49, 69.10, 72.39, 73.86, 76.58, 78.34, 81.17, 83.25, 87.90, 91.60]

SIL = '#02080C'


def build(words=None):
    shots = []
    it = iter(range(len(CUTS) - 1))

    def new(plate, cam=None, name=''):
        i = next(it)
        a, b = CUTS[i], CUTS[i + 1]
        s = Shot(round(b - a, 4), plate=plate, camera=cam or Camera(push=0.8, drift=(6, -2)), name=name or f'a{i+1}')
        if i == 0: s.abs_start = 0.0
        s.T = a
        shots.append(s)
        return s, (lambda t, a=a: t - a)

    # 1 — wide night yacht 0.00–4.33
    pl = NightSurface(waterline=650)
    s, L = new(pl, Camera(push=0.6, drift=(-8, 0)))
    boat = s.add(NightSailboat(pos=K((0, (760, 650)), (4.4, (880, 650), 'linear')), scale=0.5, plate=pl, layer='mid'))
    s.add(Ripples(pos=K((0, (900, 666)), (4.4, (1020, 666), 'linear')), period=1.6, rmax=140, layer='mid'))
    s.add(Swell(pos=(0, 1010), speed=50, layer='fg'))
    s.add(FadeIn(dur=1.0))
    s.add(Pill('STRAIT OF GIBRALTAR', 'dark', size=34, pos=(960, 170), t0=L(2.83)))
    s.add(Pill('NIGHT', 'orange', size=30, pos=(960, 245), t0=L(3.89)))

    # 2 — strait map 4.33–6.89
    s, L = new(P.Board(), Camera(push=0.6, drift=(3, 0), wander=2))
    m = StraitMap(t_route=0.15, route_dur=1.8)
    s.add(m)
    ex, ey = m.xy(-5.55, 35.98)
    s.add(Pill('PORT, SPANISH COAST', 'orange', size=28, pos=(ex + 120, ey - 190), target=(ex, ey - 6), t0=L(5.53)))

    # 3 — close yacht, calm 6.89–8.46
    pl = NightSurface(waterline=720, wave_amp=3)
    s, L = new(pl, Camera(push=1.0, drift=(-6, 0)))
    s.add(NightSailboat(pos=K((0, (900, 720)), (1.6, (950, 720), 'linear')), scale=0.95, plate=pl, heel=K((0, -1), (0.8, 1), (1.6, -1))))
    s.add(Ripples(pos=(1260, 736), period=1.8, rmax=200))
    s.add(Pill('CALM', 'green', size=34, tick=True, pos=(560, 240), t0=L(7.41)))

    # 4 — underwater hull, rumble 8.46–12.17
    s, L = new(NightWater(depth=0.7), Camera(push=0.7, drift=(0, 2)))
    s.add(Fn(lambda ctx, t: (ctx.set_source_rgba(0.55, 0.75, 0.82, 0.25), ctx.rectangle(-200, 0, 2400, 175), ctx.fill()), layer='back'))
    s.add(NightSailboat(pos=K((0, (900, 170)), (3.8, (1000, 170), 'linear')), scale=1.25, night=0.55, lamps=False))
    s.add(Orca(pos=K((0, (2300, 820)), (3.8, (-300, 860), 'linear')), scale=0.55, facing='left', variant='silhouette',
               sil_color='#01070A', opacity=0.75, layer='back'))
    s.add(Bubbles(pos=(1000, 600), rate=3, spread=300, layer='fg'))
    s.camera.shake(L(10.33), amp=16, decay=0.9)
    s.add(Pill('A LOUD RUMBLE', 'dark', size=32, pos=(960, 760), t0=L(10.33)))
    s.add(Pill('UNDER THE HULL', 'orange', size=28, pos=(960, 840), t0=L(11.41)))

    # 5 — sonar: nothing to hit 12.17–16.89
    s, L = new(P.Sonar(origin=(120, 560)), StaticCamera())
    s.add(SonarRings(pos=(120, 560), period=1.2, direction=0, spread=40, rmax=900, color='#3BE07A', layer='mid'))
    s.add(Pill('HIT SOMETHING?', 'dark', size=40, pos=(1180, 220), t0=L(13.63)))
    s.add(Checklist([('ROCKS', 'x', L(14.95) - L(13.9)), ('REEF', 'x', L(15.3) - L(13.9))], size=52, gap=96,
                    pos=(980, 430), t0=L(13.9), t_items=[0, 0.3]))
    s.add(Label('NO ROCKS. NO REEF.', size=56, font='xb', color=PAL.WHITE, align='center', pos=(1180, 780), t0=L(15.67)))
    s.add(Blip(pos=(1500, 600), r=9, t0=L(16.1)))

    # 6 — wheel POV jerk 16.89–19.02
    pl = NightSurface(waterline=470, coast=True)
    s, L = new(pl, Camera(push=0.4, drift=(0, 0), wander=3))
    j = L(17.35)
    s.add(WheelPOV(pos=(960, 830), R=340, wheel=K((0, -2), (j, 2), (j + 0.12, 42, 'eo'), (j + 0.45, -18), (j + 0.8, 25), (j + 1.3, -6), (2.2, 4)),
                   layer='fg', z=1))
    s.add(CockpitDeck(layer='fg', z=0))
    s.camera.shake(j, amp=20, decay=0.6)
    s.add(Pill('THE WHEEL JERKS', 'red', size=32, pos=(1450, 200), t0=j))

    # 7 — rudder shoved by silhouette 19.02–21.15
    pl = NightSurface(waterline=430, coast=False)
    s, L = new(pl, Camera(push=0.8, drift=(0, 0)))
    h1, h2 = L(19.59), L(20.31)
    bt = s.add(NightSailboat(pos=(1060, 430), scale=0.9, plate=pl, night=0.4,
                             rudder=K((0, 0), (h1, 0), (h1 + 0.08, 32, 'eo'), (h1 + 0.4, 10), (h2, 8), (h2 + 0.08, -30, 'eo'), (h2 + 0.5, 6))))
    rw = bt.rudder_world(0)
    s.add(Orca(pos=K((0, (rw[0] - 560, rw[1] + 200)), (h1 - 0.05, (rw[0] - 245, rw[1] + 40), 'ei'), (h1 + 0.25, (rw[0] - 330, rw[1] + 80), 'eo'),
                     (h2 - 0.05, (rw[0] - 245, rw[1] + 35), 'ei'), (h2 + 0.3, (rw[0] - 360, rw[1] + 100))),
               rot=K((0, -12), (h1, -6), (h2, -4), (2.2, -10)), scale=0.45, facing='right', variant='silhouette', sil_color=SIL, layer='mid', z=2))
    for h in (h1, h2):
        impact(s, h, (rw[0] - 20, rw[1] + 10), amp=12, flash=False, debris=True, scale=0.6, bubbles=10, gravity=60)
    s.add(Pill('RUDDER', 'red', size=30, pos=(rw[0] + 260, rw[1] + 260), target=(rw[0], rw[1] + 20), t0=L(20.31)))
    s.add(Pill('SOMETHING', 'dark', size=30, pos=(420, 300), t0=L(19.05)))

    # 8 — rudder close: not bumping, shoving 21.15–24.75
    s, L = new(NightWater(depth=0.65), Camera(push=0.9, drift=(0, 0)))
    hits = [L(22.67), L(23.29), L(23.83)]
    sc = 2.2
    bpos = (1000 + 262 * sc, 520 - 115 * sc)
    rk = [(0, 0), (hits[0] - 0.02, -3)]
    for k, h in enumerate(hits):
        rk += [(h, -3 if k == 0 else 4), (h + 0.08, 28 if k % 2 == 0 else -26, 'eo'), (h + 0.35, 2)]
    s.add(Fn(lambda ctx, t, y=bpos[1] + 4: (ctx.set_source_rgba(0.55, 0.75, 0.82, 0.22), ctx.rectangle(-300, -300, 2600, y + 300), ctx.fill()), layer='back'))
    bt = s.add(NightSailboat(pos=bpos, scale=sc, night=0.5, lamps=False, rudder=K(*rk), layer='mid', z=1))
    rx, ry = 1000, 520
    ok = [(0, (rx - 980, ry + 120)), (0.9, (rx - 620, ry + 90))]
    for h in hits:
        ok += [(h - 0.12, (rx - 520, ry + 70), 'ei'), (h, (rx - 400, ry + 50), 'ei'), (h + 0.22, (rx - 540, ry + 80), 'eo')]
    ok += [(3.6, (rx - 600, ry + 90))]
    s.add(Orca(pos=K(*ok), scale=0.75, facing='right', variant='silhouette', sil_color=SIL, rot=-4, layer='mid', z=2))
    for h in hits:
        impact(s, h, (rx - 40, ry + 40), amp=16, flash=(h == hits[0]), scale=0.7, bubbles=12, gravity=60)
    s.add(Label('NOT BUMPING.', size=70, font='xb', align='center', pos=(960, 840), t0=L(21.18), reveal='wipe'))
    s.add(Punchline('…SHOVING.', size=92, pos=(960, 970), t0=L(22.67)))
    s.add(Bubbles(pos=(900, 700), rate=4, spread=200, layer='fg'))

    # 9 — first fin off the stern 24.75–28.54
    pl = NightSurface(waterline=720, coast=False, wave_amp=3)
    s, L = new(pl, Camera(push=0.6, drift=(0, 0), wander=4))
    tf = L(26.23)
    fin1 = K((0, (1650, 720)), (tf - 0.3, (1450, 720), 'linear'), (3.8, (620, 720), 'linear'))
    s.add(Fin(plate=pl, pos=fin1, height=230, facing='left', rise=K((0, 0), (tf - 0.45, 0), (tf, 1, 'eo')), layer='mid'))
    s.add(SternRail(layer='overlay', z=0))
    s.camera.handheld(amp=2.5, freq=0.8)
    s.add(Pill('A TALL BLACK FIN', 'dark', size=30, pos=(1180, 320), target=lambda t: (fin1(t)[0] + 10, 520), t0=tf + 0.2))

    # 10 — wide: fins 2 and 3, counter 28.54–31.36
    pl = NightSurface(waterline=600, coast=True)
    s, L = new(pl, Camera(push=0.5, drift=(-4, 0)))
    s.add(NightSailboat(pos=K((0, (1380, 600)), (2.9, (1440, 600), 'linear')), scale=0.38, plate=pl))
    s.add(Fin(plate=pl, pos=K((0, (900, 600)), (2.9, (700, 600), 'linear')), height=120, facing='left'))
    s.add(Fin(plate=pl, pos=K((0, (1200, 612)), (2.9, (960, 612), 'linear')), height=100, facing='left',
              rise=K((0, 0), (L(28.77) - 0.3, 0), (L(28.77), 1, 'eo'))))
    s.add(Fin(plate=pl, pos=K((0, (560, 625)), (2.9, (380, 625), 'linear')), height=105, facing='left',
              rise=K((0, 0), (L(30.16) - 0.3, 0), (L(30.16), 1, 'eo'))))
    t2, t3 = L(28.77), L(30.16)

    def fin_count(ctx, t, t2=t2, t3=t3):
        n = 1 if t < t2 else (2 if t < t3 else 3)
        tl = t - (0 if n == 1 else (t2 if n == 2 else t3))
        sc_ = 1.0 + 0.3 * max(0, 1 - tl / 0.15)
        ctx.save(); ctx.translate(200, 230); ctx.scale(sc_, sc_)
        rrect(ctx, -90, -110, 180, 160, 12); ctx.set_source_rgba(0.03, 0.05, 0.06, 0.85); ctx.fill_preserve()
        set_col(ctx, PAL.WHITE, 0.9); ctx.set_line_width(2.4); ctx.stroke()
        draw_text(ctx, str(n), 0, 22, 'xb', 120, PAL.ORANGE if n < 3 else PAL.RED, 0.0, 'center', shadow=False)
        ctx.restore()
        draw_text(ctx, 'FINS', 200, 340, 'bold', 26, PAL.WHITE, 0.24, 'center')
    s.add(Fn(fin_count, layer='overlay'))

    # 11 — black card: taken apart 31.36–35.19
    s, L = new(P.Black(particles=True), Camera(push=0.5, drift=(0, 0)))
    s.add(Orca(pos=K((0, (2200, 640)), (3.9, (-400, 600), 'linear')), scale=0.9, facing='left', variant='silhouette',
               sil_color='#0A1418', opacity=0.6, layer='back'))
    txt = "YOU'RE NOT BEING HIT BY SOMETHING."
    s.add(WordReveal(txt, [L(x) for x in (31.39, 31.49, 31.59, 31.85, 32.13, 32.37)], size=64, pos=(960, 470)))
    s.add(Punchline("…YOU'RE BEING TAKEN APART.", size=84, pos=(960, 640), t0=L(33.97)))
    s.camera.shake(L(33.97), amp=8, decay=0.4)

    # 12 — polaroid: skipper 35.19–38.52
    s, L = new(P.Sepia(dark=True, grid=True), Camera(push=0.7, drift=(4, 0)))
    s.add(Polaroid(content=sailor_photo, caption='THE SKIPPER', w=520, h=440, pos=(620, 520), angle=-4, t0=0.1, layer='overlay'))
    s.add(Label('SKIPPER', size=26, font='bold', color=PAL.ORANGE, track=0.24, pos=(1000, 470), t0=L(36.15)))
    s.add(Typewriter('WERNER', size=70, pos=(1000, 560), t0=L(36.87), cps=24))
    s.add(Typewriter('SCHAUFELBERGER', size=70, pos=(1000, 650), t0=L(37.21), cps=24))

    # 13 — calendar 4 MAY 2023 38.52–41.52
    s, L = new(P.Sepia(), Camera(push=0.9, drift=(0, 0)))
    s.add(Calendar(pos=(960, 560), scale=1.05, t_flip=(L(38.67), L(38.85), L(39.07) - 0.1)))
    s.add(Pill('NIGHT', 'dark', size=30, pos=(1410, 300), t0=L(38.67)))
    s.add(Stamp('4 MAY 2023', PAL.RED, 62, pos=(1510, 880), t0=L(40.03), angle=-8))

    # 14 — quote card 41.52–44.21
    s, L = new(P.Black(particles=True), Camera(push=0.4, drift=(0, 0)))
    q = '"THE ATTACKS WERE BRUTAL."'
    s.add(QuoteReveal(q, kicker='WERNER SCHAUFELBERGER', attribution='TO GERMAN MAGAZINE YACHT',
                      word_times=[L(41.55), L(41.63), L(41.89), L(42.21)], t_attr=L(43.0), size=78, pos=(960, 580)))

    # 15 — big orca rams hull, Champagne 44.21–47.16
    pl = NightSurface(waterline=420, coast=False)
    s, L = new(pl, Camera(push=0.7, drift=(0, 0)))
    tr = L(45.01)
    s.add(NightSailboat(pos=(1080, 420), scale=0.8, plate=pl, night=0.35,
                        heel=K((0, 0), (tr, 0), (tr + 0.1, 12, 'eo'), (tr + 0.6, -5), (2.9, 2))))
    hit = (1080 - 40, 420 + 60)
    s.add(Orca(pos=K((0, (-400, 760)), (tr, (hit[0] - 420, hit[1] + 60), 'ei'), (tr + 0.4, (hit[0] - 520, hit[1] + 130), 'eo'),
                     (2.95, (hit[0] - 900, hit[1] + 300))),
               rot=K((0, -14), (tr, -8), (tr + 0.4, 6), (2.95, 10)), scale=0.75, facing='right', variant='silhouette', sil_color=SIL, z=2))
    impact(s, tr, hit, amp=22, scale=1.0, gravity=60)
    s.add(Pill('THE BIGGEST ONE', 'dark', size=30, pos=(380, 200), t0=L(44.31)))
    s.add(Pill('THE CHAMPAGNE', 'orange', size=32, pos=(1500, 160), target=(1150, 300), t0=L(46.31)))

    # 16 — two smaller orcas destroy the rudder 47.16–49.85
    pl = NightSurface(waterline=380, coast=False)
    s, L = new(pl, Camera(push=0.8, drift=(0, 0)))
    tb = L(48.33)
    bt = s.add(NightSailboat(pos=(1100, 380), scale=0.85, plate=pl, night=0.35,
                             damage=lambda lt, tb=tb: 'ok' if lt < tb else 'broken',
                             rudder=K((0, 0), (0.6, 18), (0.9, -14), (tb, 20), (tb + 0.1, 35, 'eo'), (tb + 0.6, -6))))
    rw = bt.rudder_world(tb)
    s.add(bt.rudder_piece(tb, layer='mid', z=0))
    s.add(Orca(pos=K((0, (rw[0] - 600, rw[1] + 300)), (tb, (rw[0] - 240, rw[1] + 30), 'ei'), (2.7, (rw[0] - 420, rw[1] + 160), 'eo')),
               rot=K((0, -10), (tb, -6), (2.7, 6)), scale=0.36, facing='right', variant='silhouette', sil_color=SIL, z=2))
    s.add(Orca(pos=K((0, (rw[0] + 700, rw[1] + 340)), (tb, (rw[0] + 230, rw[1] + 60), 'ei'), (2.7, (rw[0] + 420, rw[1] + 200), 'eo')),
               rot=K((0, 10), (tb, 4), (2.7, -6)), scale=0.34, facing='left', variant='silhouette', sil_color=SIL, z=2, phase=0.4))
    impact(s, tb, rw, amp=18, scale=0.8, gravity=60)
    s.add(Pill('TWO SMALLER ONES', 'dark', size=30, pos=(420, 200), t0=L(47.33)))
    s.add(Stamp('RUDDER: DESTROYED', PAL.RED, 60, pos=(1300, 930), t0=L(49.05), angle=-6))

    # 17 — dawn rescue 49.85–52.13
    pl = Surface('dawn', waterline=700, sun=(0.25, 0.3))
    s, L = new(pl, Camera(push=0.6, drift=(-6, 0)))
    s.add(Sailboat(pos=(1000, 700), scale=0.55, plate=pl, damage='missing', heel=7, crew=0))
    s.add(Helicopter(pos=K((0, (1350, 230)), (2.3, (1150, 250))), scale=0.8, line=K((0, 0), (1.0, 260)), beam=True))
    s.add(Beacon(pos=K((0, (380, 690)), (2.3, (470, 690), 'linear')), color=(0.4, 0.7, 1.0)))
    s.add(Pill('EVERYONE ON BOARD RESCUED', 'green', size=34, tick=True, pos=(960, 930), t0=L(51.11)))

    # 18 — the boat wasn't 52.13–53.64
    pl = Surface('dawn', waterline=650, sun=(0.25, 0.3))
    s, L = new(pl, Camera(push=1.2, drift=(0, 0)))
    s.add(Sailboat(pos=K((0, (960, 680)), (1.6, (990, 860), 'linear')), scale=0.65, damage='missing', heel=K((0, 12), (1.6, 34, 'linear')), crew=0))
    s.add(Bubbles(pos=(980, 760), rate=10, spread=160, layer='fg'))
    s.add(Punchline("…THE BOAT WASN'T.", size=90, pos=(960, 230), t0=L(52.41)))

    # 19 — silhouette becomes an orca 53.64–56.40
    s, L = new(P.Underwater(depth=0.4), Camera(push=0.8, drift=(-6, 0)))
    to = L(54.97)
    opos = K((0, (1300, 560)), (2.8, (900, 540), 'linear'))
    s.add(Orca(pos=opos, scale=0.8, facing='left', z=1))
    s.add(Orca(pos=opos, scale=0.8, facing='left', variant='silhouette', sil_color=SIL, z=2,
               opacity=lambda lt, to=to: 1.0 - min(1, max(0, (lt - to) / 0.35))))
    s.add(Label('ORCA', size=150, font='xb', align='center', pos=(960, 930), t0=to + 0.1, reveal='letters'))
    s.add(Pill('THE ANIMALS', 'dark', size=30, pos=(400, 200), t0=L(53.75)))

    # 20 — aquarium poster 56.40–60.49
    s, L = new(P.Board(tint='teal'), Camera(push=1.0, drift=(0, -2)))
    s.add(Poster(pos=(960, 560), scale=0.92, t0=L(58.69) - 0.9))
    s.add(Pill('STRANGE', 'red', size=32, pos=(960, 540), t0=L(56.05), t1=L(58.69) - 0.9))
    s.add(Pill('AQUARIUM POSTERS', 'dark', size=30, pos=(1560, 930), t0=L(58.69)))

    # 21 — orca = panda 60.49–64.49
    s, L = new(P.Board(tint='teal'), Camera(push=0.6, drift=(0, 0)))
    s.add(Orca(pos=(560, 540), scale=0.5, facing='right', blink=[1.2, 3.0]))
    s.add(Label('=', size=180, font='xb', align='center', pos=(1040, 600), t0=L(62.31)))
    s.add(Panda(pos=(1420, 540), scale=0.75, t0=L(62.70), rot=lambda t: 3 * math.sin(t * 1.6)))
    s.add(Pill('BLACK & WHITE', 'white', size=30, pos=(560, 250), t0=L(60.52)))
    s.add(Pill('ALWAYS SMILING', 'dark', size=30, pos=(560, 320), t0=L(61.26)))
    s.add(Label('A PANDA THAT SWIMS?', size=60, font='xb', align='center', color=PAL.ORANGE, pos=(960, 930), t0=L(62.90), reveal='wipe'))

    # 22 — no confirmed case 64.49–69.10
    s, L = new(P.Board(), Camera(push=0.6, drift=(3, 0)))
    s.add(Orca(pos=K((0, (1500, 760)), (4.7, (1250, 760), 'linear')), scale=0.42, facing='left', variant='xray', swim=0.8))
    s.add(Diver(pos=K((0, (480, 770)), (4.7, (560, 760), 'linear')), scale=0.26, facing='right', xray=True, bubbles=False))
    s.add(Label('CONFIRMED CASES: WILD ORCA KILLS A PERSON', size=30, font='bold', color=PAL.CYAN_HI, track=0.18,
                align='center', pos=(960, 200), t0=L(64.89)))
    s.add(Counter(9, 0, dur=1.6, size=260, pos=(960, 500), t0=L(65.16), color=PAL.WHITE))
    s.add(Stamp('NONE CONFIRMED', PAL.GREEN, 66, pos=(960, 600), t0=L(68.14), angle=-7))

    # 23 — sharks for their livers 69.10–72.39
    s, L = new(P.Danger(grid=True), Camera(push=0.8, drift=(-4, 0)))
    sh = Group(pos=K((0, (1250, 400)), (3.3, (1050, 410), 'linear')), scale=0.7)
    sh.add(Shark(pos=(0, 0), facing='left'))
    sh.add(Liver(pos=(10, 30), scale=0.6, t0=L(71.75)))
    s.add(sh)
    s.add(Orca(pos=K((0, (350, 1050)), (3.3, (720, 730), 'eo')), rot=K((0, -22), (3.3, -12)), scale=0.6, facing='right', z=2))
    s.add(Pill('GREAT WHITE SHARK', 'dark', size=30, pos=(1250, 170), t0=L(70.42)))
    s.add(Pill('LIVER', 'red', size=34, pos=(1600, 640), target=lambda t: (1250 - 200 * t / 3.3 + 7, 425), t0=L(71.75)))

    # 24 — kills blue whales 72.39–73.86
    s, L = new(P.Underwater(depth=0.45), Camera(push=0.7, drift=(-8, 0)))
    s.add(BlueWhale(pos=K((0, (1050, 430)), (1.5, (980, 430), 'linear')), scale=1.6))
    for k, (x, y, ph) in enumerate(((380, 800, 0.0), (960, 850, 0.3), (1520, 790, 0.6))):
        s.add(Orca(pos=K((0, (x + 90, y)), (1.5, (x, y - 10), 'linear')), scale=1.6 * 0.27, facing='left', phase=ph, z=2))
    s.add(Pill('BLUE WHALE', 'dark', size=32, pos=(1450, 180), t0=L(72.69)))
    s.add(Pill('ORCAS', 'red', size=28, pos=(960, 1000), target=(960, 880), t0=L(72.69) + 0.2))

    # 25 — since 2020, boats at night 73.86–76.58
    pl = NightSurface(waterline=560, coast=True)
    s, L = new(pl, Camera(push=0.7, drift=(-5, 0)))
    s.add(NightSailboat(pos=K((0, (1100, 560)), (2.8, (1160, 560), 'linear')), scale=0.55, plate=pl))
    s.add(Fin(plate=pl, pos=K((0, (400, 560)), (2.8, (720, 560), 'linear')), height=120, facing='right'))
    s.add(Fin(plate=pl, pos=K((0, (250, 575)), (2.8, (560, 575), 'linear')), height=95, facing='right'))
    s.add(StatBox('SINCE 2020', t0=L(74.14), size=58))
    s.add(Pill('A SMALL GROUP', 'red', size=30, pos=(560, 400), target=lambda t: (400 + 114 * t, 500), t0=L(75.33)))

    # 26 — triptych taking apart boats 76.58–78.34
    s, L = new(P.Board(), Camera(push=0.5, drift=(0, 0)))
    for k, (x, tp, cap) in enumerate(((380, 76.61, 'RAMMED'), (960, 76.92, 'RUDDER GONE'), (1540, 77.17, 'SINKING'))):
        pn = Panel(w=480, h=520, caption=cap, cap_color=PAL.WHITE if k < 2 else PAL.RED, bg='#0E3140',
                   pos=(x, 500), t0=L(tp) - 0.03)
        if k == 0:
            pn.add(Sailboat(pos=(40, 60), scale=0.42, heel=K((0, 0), (0.1, 10, 'eo'), (0.6, -3))),
                   Orca(pos=K((0, (-260, 180)), (0.15, (-150, 120), 'eo'), (2, (-200, 160))), scale=0.28, facing='right', variant='silhouette', sil_color=SIL))
        elif k == 1:
            pn.add(Sailboat(pos=(80, 0), scale=0.55, damage='broken', rudder=K((0, 30), (0.4, -10), (1.4, 5))),
                   Orca(pos=K((0, (-200, 200)), (1.4, (-160, 170))), scale=0.22, facing='right', variant='silhouette', sil_color=SIL))
        else:
            pn.add(Sailboat(pos=K((0, (0, 40)), (1.4, (10, 140), 'ei')), scale=0.5, damage='missing', heel=K((0, 10), (1.4, 30))),
                   Bubbles(pos=(0, 150), rate=8, spread=90))
        pn.add(Fn(lambda ctx, t: (ctx.set_source_rgba(0.6, 0.85, 0.9, 0.5), ctx.set_line_width(3),
                                  ctx.move_to(-300, 40 + 3 * math.sin(t * 3)), ctx.line_to(300, 40 - 3 * math.sin(t * 3)), ctx.stroke())))
        s.add(pn, layer='mid')
    s.camera.shake(L(77.17), amp=8, decay=0.4)

    # 27 — lone orca: WHY? 78.34–81.17
    s, L = new(P.Underwater(depth=0.5), Camera(push=0.9, drift=(-4, 0)))
    s.add(Orca(pos=K((0, (1250, 600)), (2.9, (820, 580), 'linear')), scale=0.7, facing='left', blink=[1.0]))
    s.add(Label('WHY?', size=200, font='xb', color=PAL.ORANGE, align='center', pos=(960, 300), t0=L(78.80), reveal='letters'))
    s.add(Pill('THE UNSETTLING PART', 'red', size=30, pos=(960, 960), t0=L(79.64)))

    # 28 — one orca becomes five 81.17–83.25
    s, L = new(P.Board(), Camera(push=0.6, drift=(0, 0)))
    tsplit = L(82.25)
    xs = [260, 610, 960, 1310, 1660]
    for k, x in enumerate(xs):
        s.add(Orca(pos=K((0, (960, 560)), (tsplit, (960, 560)), (tsplit + 0.5, (x, 560 + (k % 2) * 30), 'eo')),
                   scale=K((0, 0.36), (tsplit, 0.36), (tsplit + 0.5, 0.26)), facing='left', phase=k * 0.3, z=5 - abs(k - 2)))
    s.add(Label("THERE ISN'T REALLY ONE ORCA", size=52, font='xb', align='center', pos=(960, 240), t0=L(81.20), reveal='wipe'))

    # 29 — every family: menu, language, fun 83.25–87.90
    s, L = new(P.Board(), Camera(push=0.5, drift=(2, 0)))
    for k, x in enumerate(xs):
        s.add(Orca(pos=(x + 10 * math.sin(k), 700), scale=0.22, facing='left', phase=k * 0.37))
        s.add(Orca(pos=(x + 70, 770), scale=0.15, facing='left', dorsal='female', phase=k * 0.21 + 0.5))
    s.add(Pill('EVERY FAMILY', 'dark', size=30, pos=(960, 150), t0=L(83.28)))
    menu = ['fish', 'seal', 'fish', 'seal', 'fish']
    for k, x in enumerate(xs):
        s.add(Badge(menu[k], r=50, pos=(x, 330), t0=L(84.53) + 0.08 * k, t1=L(85.59)))
        s.add(SonarRings(pos=(x - 70, 700), period=1.0 + 0.17 * k, rmax=150, n=2, color=['#7FC1CB', '#F0A54A', '#F2F0EB', '#4DB271', '#D73F3C'][k],
                         t0=L(85.59) + 0.08 * k, t1=L(87.53), layer='mid'))
    s.add(Label('ITS OWN MENU', size=40, font='xb', color=PAL.ORANGE, align='center', pos=(960, 470), t0=L(84.53), t1=L(85.59)))
    s.add(Label('ITS OWN LANGUAGE', size=40, font='xb', color=PAL.ORANGE, align='center', pos=(960, 470), t0=L(85.59), t1=L(87.53)))
    s.add(Badge('boat', r=60, pos=(1310, 360), t0=L(87.53)))
    s.add(Fn(lambda ctx, t: (set_col(ctx, PAL.RED), ctx.set_line_width(8),
                             ctx.arc(0, 0, 84, -math.pi / 2, -math.pi / 2 + 2 * math.pi * min(1, t / 0.25)), ctx.stroke()),
             pos=(1310, 360), t0=L(87.53) + 0.08, layer='overlay'))
    s.add(Label('ITS OWN IDEA OF FUN', size=40, font='xb', color=PAL.RED, align='center', pos=(960, 470), t0=L(87.53)))

    # 30 — title 87.90–91.60
    s, L = new(P.Abyss(), Camera(push=0.8, drift=(0, 0)))
    s.add(FadeIn(dur=0.55))
    s.add(Orca(pos=K((0, (2200, 760)), (3.7, (-300, 700), 'linear')), scale=0.6, facing='left', variant='silhouette', sil_color='#010507', layer='back'))
    s.add(Label("WHY YOU'D NEVER WANT", size=92, font='xb', align='center', pos=(960, 470), t0=L(89.66), reveal='letters', dur=0.5))
    s.add(Label('TO MEET AN ORCA', size=120, font='xb', align='center', pos=(960, 610), t0=L(90.44), reveal='letters', dur=0.4))
    s.add(Underline(w=1000, pos=(960, 650), t0=L(90.89)))
    s.camera.shake(L(90.89), amp=10, decay=0.35)
    s.add(Ring(pos=(960, 560), t0=L(90.89), r0=40, r1=700, dur=0.5, width=10, color='#FFFFFF', layer='fg'))
    return shots
