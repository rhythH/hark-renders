"""Act B — chapter 1 SIZE + chapter 2 BITE (beats B13–B24). Absolute range [92.1, 169.1).
Render: python -m engine.render scenes.act_b renders/act_b_q.mp4 --words audio/words.json --scale 0.25 --jobs 1
"""
import math
from engine import *
from engine.core import Element
from scenes.assets_b import (FadeIn, StrikeLabel, BalanceRig, SplitFlap, NavChapterTitle, Clip, LyingPeople,
                             PersonPile, ECG, JawGauge, Readout, ReactionBar, Bang, DashedGate, CafeMenu,
                             CappedStopwatch, INK)

T_START, T_END = 92.10, 169.10
# cut times = 3 frames before the word (cut_at), see plan_b.md
CUTS = [92.10, 98.14, 103.74, 108.89, 111.85, 114.51, 117.35, 120.41, 125.57, 128.83, 132.11, 134.04,
        137.67, 140.77, 145.43, 149.52, 151.11, 153.15, 155.14, 156.98, 159.73, 163.76, 166.33, T_END]
RIVER = '#24443A'


def Ke(*keys):
    """K() with the ease written on the key that ENDS a segment (shifted to the key that starts it)."""
    out = []
    for i, k in enumerate(keys):
        nxt = keys[i + 1] if i + 1 < len(keys) else None
        e = nxt[2] if (nxt is not None and len(nxt) > 2) else ('eio' if nxt is not None else None)
        out.append((k[0], k[1], e) if e else (k[0], k[1]))
    return K(*out)


def _shot(i, plate, camera=None, name='', trans_in=None):
    s = Shot(round(CUTS[i + 1] - CUTS[i], 4), plate=plate, camera=camera or Camera(), name=name, trans_in=trans_in)
    s._c0 = CUTS[i]
    return s


def lt(s, t_abs):
    return round(t_abs - s._c0, 3)


def build(words=None):
    S = []

    # 0 ── chapter card 1/6 SIZE: hero croc walking left on the blueprint, 6 m bar ticks out on "6"
    s = _shot(0, Board(), Camera(push=0.5, drift=(-5, 0), wander=3), 'ch1')
    s.abs_start = T_START
    s.add(Croc(pos=Ke((0, (1080, 400)), (s.dur, (960, 400), 'linear')), scale=0.75, gait=1.0, walk_period=1.6,
               variant='side'))
    t6 = lt(s, 96.75)
    nose = 1080 - 120 * t6 / s.dur - 375
    s.add(DimensionLine((nose, 575), (nose + 750, 575), label='~6 M', sub='LONG', t0=t6, size=52))
    s.add(NavChapterTitle('SIZE', 'THE LARGEST REPTILE ALIVE', 1, pos=(110, 790), t0=lt(s, 92.47) + 0.1))
    s.add(FadeIn(0.5))
    S.append(s)

    # 1 ── globe: Lolong, Philippines, 2011
    s = _shot(1, Board(), Camera(push=0.6, drift=(0, 0), wander=3), 'globe')
    s.add(Globe(center=(118, 6), radius=330, spin=-1.2, highlight=['Philippines'], pins=[(125.9, 8.2)],
                pos=(1290, 560)))
    s.add(StatBox('BIGGEST EVER RELIABLY MEASURED', size=40, t0=0.15))
    s.add(Typewriter('LOLONG', size=120, pos=(140, 520), t0=lt(s, 100.51) - 0.05, cps=18))
    s.add(Pill('PHILIPPINES', 'dark', size=40, pos=(300, 640), t0=lt(s, 101.83)))
    s.add(Pill('2011', 'orange', size=44, pos=(300, 740), t0=lt(s, 102.61)))
    S.append(s)

    # 2 ── x-ray croc, 6.17 m tape + ~1,075 kg counter
    s = _shot(2, Board(), Camera(push=0.8, drift=(6, 0), wander=3), 'xray')
    s.add(Croc(pos=(960, 520), scale=1.1, variant='xray', swim=0.35, gait=0.0))
    s.add(StatBox('LOLONG', sub='PHILIPPINES — 2011', t0=0.1, size=44))
    s.add(DimensionLine((410, 720), (1510, 720), label='6.17 M', sub='LONG', t0=lt(s, 103.99), size=60))
    s.add(Counter(0, 1075, dur=0.8, prefix='~', suffix=' KG', size=104, pos=(1460, 230), t0=lt(s, 106.61) - 0.1,
                  unit='weight'))
    S.append(s)

    # 3 ── three and a half of you, head to toe
    s = _shot(3, Board(), Camera(push=0.3, wander=2), 'headtoe')
    L = 300
    s.add(comparison_silhouette('croc', 6.17 / (3.5 * L), pos=(435, 430), color='#DDE3E3'))
    s.add(LyingPeople(3.5, L, times=[lt(s, t) for t in (109.21, 109.40, 109.58, 109.76)], color=PAL.ORANGE,
                      pos=(435, 650)))
    s.add(Label('3½ OF YOU', size=96, align='center', pos=(960, 880), t0=lt(s, 109.93), reveal='wipe'))
    s.add(Pill('HEAD TO TOE', 'dark', size=30, pos=(960, 960), t0=lt(s, 110.59)))
    S.append(s)

    # 4 ── fourteen of you on the scales
    s = _shot(4, Board(), Camera(push=0.3, wander=2), 'scales')
    tf, tl_ = lt(s, 112.19), lt(s, 113.20)
    times = [tf + i * (tl_ - tf) / 13 for i in range(14)]
    tilt = Ke((0, -16), (tf, -16, 'linear'), (tl_ + 0.25, 0, 'eo'), (s.dur, 0))
    croc_small = comparison_silhouette('croc', 6.17 / 420, color='#DDE3E3')
    s.add(BalanceRig(tilt=tilt, width=1000, pos=(960, 360),
                     left_items=[(croc_small, (-210, -2))],
                     right_items=[(PersonPile(14, 78, times=times, color=PAL.ORANGE), (0, -2))]))
    s.add(Label('14 OF YOU', size=84, align='center', pos=(1460, 190), t0=lt(s, 112.59), reveal='wipe'))
    s.add(Label('1 CROC', size=60, align='center', pos=(460, 190), t0=0.05, reveal='fade'))
    s.add(Pill('(STILL ONE CROCODILE)', 'orange', size=40, pos=(960, 980), t0=lt(s, 113.47)))
    s.camera.shake(lt(s, 113.47), amp=10)
    S.append(s)

    # 5 ── eyes, ears, nostrils on top (close at the waterline)
    s = _shot(5, Riverbank(560, bank_x=2400, mud=False), Camera(push=0.6, drift=(-6, 0), wander=2), 'ears')
    s.add(Croc(pos=(1500, 600), scale=2.0, submerged=0.85, waterline=-20, water=RIVER, swim=0.2, gait=0))
    s.add(Pill('EYES', 'white', size=34, pos=(640, 330), target=(806, 528), t0=lt(s, 114.73)))
    s.add(Pill('EARS', 'white', size=34, pos=(1050, 330), target=(900, 530), t0=lt(s, 115.03)))
    s.add(Pill('NOSTRILS', 'white', size=34, pos=(330, 400), target=(560, 540), t0=lt(s, 115.93)))
    s.add(Label('ON TOP OF ITS HEAD', size=52, align='center', pos=(960, 900), t0=lt(s, 116.81), reveal='wipe'))
    S.append(s)

    # 6 ── everything else hidden: x-ray reveal of the body under the surface
    s = _shot(6, Riverbank(560, bank_x=1550), Camera(push=0.4, drift=(0, 12), wander=2), 'iceberg')
    s.add(Croc(pos=(900, 590), scale=0.9, submerged=0.85, waterline=-30, water=RIVER, swim=0.4, gait=0))
    tx = lt(s, 117.95)
    s.add(Croc(pos=(900, 590), scale=0.9, variant='xray', swim=0.4, gait=0,
               opacity=Ke((0, 0), (tx, 0), (tx + 0.4, 0.9, 'eo'))))
    s.add(Pill('WHAT YOU SEE', 'white', size=30, pos=(600, 380), target=(560, 545), t0=0.2))
    s.add(Pill('HIDDEN', 'cyan', size=40, pos=(1300, 880), target=(1100, 690), t0=lt(s, 119.03)))
    S.append(s)

    # 7 ── up to an hour under, heart at 2-3 beats a minute
    s = _shot(7, MurkyWater(surface_y=180), Camera(push=0.5, drift=(-4, 0), wander=2), 'breath')
    s.add(Croc(pos=(1000, 820), scale=0.85, swim=0.12, gait=0, blink=[1.2, 3.8]))
    s.add(Bubbles(pos=(600, 780), rate=0.6, spread=10, layer='fg'))
    th = lt(s, 120.91)
    s.add(CappedStopwatch(cap=60.0, start=0.0, rate=60 / (lt(s, 122.19) - th), r=56, pos=(170, 180), t0=th,
                          fmt=lambda v: f'{int(min(v, 60)):02d}:00'))
    s.add(Label('UP TO 1 HOUR', size=64, pos=(110, 330), t0=lt(s, 121.83), reveal='wipe', align='left'))
    s.add(ECG(beats=[0.4, lt(s, 123.25) - lt(s, 122.6)], label='2–3 BEATS/MIN', w=560, h=140,
              pos=(1160, 110), t0=lt(s, 122.6)))
    S.append(s)

    # 8 ── teeth: crash zoom, ~66 counter
    s = _shot(8, MurkyWater(surface_y=None, roots=False, silt=0.6, haze=0.3, vignette=0.75),
              Camera(push=0.6, wander=2), 'teeth')
    s.add(CrocHead(domes=False, pos=(860, 520), scale=2.6, jaw=Ke((0, 4), (2.0, 10, 'eio'), (3.3, 6))))
    s.camera.crash(lt(s, 126.01), dur=0.25, amount=1.3, target=(720, 540))
    s.add(Counter(0, 66, dur=0.5, prefix='~', suffix=' TEETH', size=120, pos=(1440, 900), t0=lt(s, 127.09) - 0.05))
    S.append(s)

    # 9 ── not for cutting, for holding on
    s = _shot(9, Black(particles=True), Camera(push=0.5, wander=2), 'holding')
    th = lt(s, 131.23)
    s.add(CrocHead(domes=False, pos=(1480, 860), scale=1.5, opacity=0.55, jaw=Ke((0, 0), (0.8, 30, 'eo'), (th - 0.08, 30, 'ei'),
                                                                     (th + 0.05, 0))), layer='back')
    s.add(StrikeLabel('NOT FOR CUTTING.', size=88, t_strike=lt(s, 129.53) - lt(s, 129.0), pos=(960, 420),
                      t0=lt(s, 129.0)))
    s.add(Punchline('…FOR HOLDING ON.', size=100, pos=(960, 640), t0=lt(s, 130.77)))
    s.camera.shake(th + 0.05, amp=12)
    S.append(s)

    # 10 ── "and it looks like this": hero rises toward the lens
    s = _shot(10, Mangrove(horizon=430), Camera(push=1.0, wander=2), 'hero')
    s.add(CrocEyes(pos=(960, 700), scale=Ke((0, 1.3), (0.7, 1.6)), view='front', t1=0.7, water='#1E3A34'))
    s.add(CrocHeadOn(pos=Ke((0, (960, 800)), (s.dur, (960, 1000), 'ei')), scale=Ke((0, 0.9), (s.dur, 3.4, 'ei')),
                     opacity=Ke((0, 0), (0.6, 0), (0.85, 1)), t0=0.0, bob=1.0))
    S.append(s)

    # 11 ── chapter card 2/6 BITE: head + jaw gauge into the red
    s = _shot(11, Board(), Camera(push=0.5, drift=(-4, 0), wander=3), 'ch2', trans_in=('dip', 0.7))
    s.add(CrocHead(domes=False, pos=(1180, 430), scale=1.7, jaw=Ke((0, 0), (1.2, 0), (1.9, 32, 'eo'), (2.6, 32, 'ei'), (2.75, 0))))
    s.add(JawGauge(value=Ke((0, 0.05), (1.4, 0.05), (2.7, 1.0, 'eo')), r=150, pos=(1640, 760), t0=0.5))
    s.add(NavChapterTitle('BITE', 'THE STRONGEST EVER MEASURED', 2, pos=(110, 790), t0=0.45))
    S.append(s)

    # 12 ── split-flap: how does it hunt? -> WAITING
    s = _shot(12, Board(), Camera(push=0.4, wander=2), 'flap')
    s.add(SplitFlap([(0.15, 'CHASING'), (0.75, 'STALKING'), (lt(s, 139.42), 'WAITING')], header='HOW DOES IT HUNT?',
                    cells=12, pos=(960, 400)))
    s.add(Croc(pos=(1000, 830), scale=0.75, variant='xray', swim=0.15, gait=0, blink=[1.0, 2.6]))
    S.append(s)

    # 13 ── usually fish
    s = _shot(13, MurkyWater(surface_y=200), Camera(push=0.5, wander=2), 'fish')
    ts = lt(s, 141.27)
    s.add(Croc(pos=Ke((0, (520, 640)), (ts - 0.15, (540, 640)), (ts + 0.1, (640, 620), 'eo'), (s.dur, (700, 630))),
               facing='right', scale=0.85, swim=0.4, jaw=Ke((0, 0), (ts - 0.25, 0), (ts - 0.05, 38, 'eo'), (ts + 0.12, 0))))
    s.add(Fish(length=90, pos=Ke((0, (1150, 560)), (ts, (1020, 600), 'linear')), scale=(-1, 1), t1=ts + 0.08))
    s.add(FishSchool(pos=Ke((0, (1500, 420)), (s.dur, (1250, 420), 'linear')), n=26, radius=110, mode='stream',
                     fish_len=26, scale=(-1, 1), layer='back', opacity=0.6))
    s.add(Bubbles(pos=(1000, 600), rate=8, spread=30, t0=ts, t1=ts + 1.0, layer='fg'))
    s.add(Pill('FISH', 'orange', size=40, pos=(1100, 380), t0=ts))
    s.add(Label('…ALMOST ANYTHING IT CAN OVERPOWER', size=56, align='center', pos=(960, 960),
                t0=lt(s, 143.05), reveal='wipe'))
    S.append(s)

    # 14 ── TOP END CAFE menu
    s = _shot(14, Sepia(), Camera(push=0.5, wander=2), 'menu')
    items = [('FISH', 0.0, INK, 'DAILY SPECIAL'), ('PIGS', lt(s, 145.53), INK, None),
             ('CATTLE', lt(s, 145.75), INK, None), ('HORSES', lt(s, 146.29), INK, None),
             ('BUFFALO', lt(s, 146.87), INK, None), ('OTHER CROCODILES', lt(s, 148.19), PAL.RED, None)]
    s.add(CafeMenu('TOP END CAFÉ', items, w=680, h=780, pos=(720, 540)))
    s.add(Pig(pos=(1480, 330), scale=0.6, style='silhouette', sil_color=INK, t0=lt(s, 145.53)))
    s.add(Buffalo(pos=(1520, 640), scale=0.5, style='silhouette', sil_color=INK, t0=lt(s, 146.87)))
    s.add(Croc(pos=(1520, 860), scale=0.42, variant='silhouette', sil_color=PAL.RED, swim=0.6, t0=lt(s, 148.19)))
    s.camera.shake(lt(s, 148.19), amp=8)
    S.append(s)

    # 15 ── waits at the water's edge
    pl = Riverbank(560, bank_x=1150)
    s = _shot(15, pl, Camera(push=0.4, wander=2), 'wait')
    s.add(Buffalo(pos=(1380, pl.bank_y(1380)), scale=0.62, pose='drink', facing='left'))
    s.add(CrocEyes(pos=Ke((0, (520, 562)), (s.dur, (640, 562), 'linear')), scale=0.9, view='side', water=RIVER,
                   facing='right'))
    s.add(Pill('AMBUSH', 'outline', size=44, pos=(960, 160), t0=lt(s, 150.29)))
    S.append(s)

    # 16 ── lunge / snap sideways
    pl = Riverbank(560, bank_x=1150)
    s = _shot(16, pl, Camera(push=0.6, zoom=1.12, focus=(1000, 520), wander=2), 'lunge')
    tl0 = lt(s, 151.21); tsn = lt(s, 151.83)
    s.add(Croc(pos=Ke((0, (640, 600)), (tl0, (640, 600)), (tl0 + 0.25, (930, 520), 'eo'), (tsn, (950, 520)),
                     (tsn + 0.2, (960, 540), 'eo'), (s.dur, (900, 580))),
               rot=Ke((0, 0), (tl0, 0), (tl0 + 0.25, -14, 'eo'), (tsn, -14), (tsn + 0.18, 6, 'eo'), (s.dur, 2)),
               facing='right', scale=0.75, swim=0.6,
               submerged=Ke((0, 0.85), (tl0, 0.85), (tl0 + 0.25, 0.25, 'eo'), (s.dur, 0.6)), waterline=-20, water=RIVER,
               jaw=Ke((0, 0), (tl0, 0), (tl0 + 0.2, 45, 'eo'), (tsn, 45), (tsn + 0.12, 0))))
    s.add(Buffalo(pos=(1380, pl.bank_y(1380)), scale=0.62, pose='drink', facing='left', t1=tl0 + 0.3))
    s.add(Buffalo(pos=Ke((0, (1420, pl.bank_y(1420))), (1.4, (2300, pl.bank_y(1800)), 'ei')), scale=0.62,
                  facing='right', walk=1.0, t0=tl0 + 0.3))
    s.add(Splash(size=380, pos=(1000, 562), t0=tl0 + 0.1), layer='fg')
    impact(s, tl0 + 0.25, (1080, 520), amp=12, debris=False)
    s.add(Pill('AMBUSH', 'outline', size=44, pos=(960, 160)))
    S.append(s)

    # 17 ── whatever comes down to drink
    pl = Riverbank(560, bank_x=1050)
    s = _shot(17, pl, Camera(push=1.0, focus=(1000, 540), wander=2), 'drink')
    s.add(Pig(pos=(1180, pl.bank_y(1180)), scale=0.75, pose='root', facing='left'))
    s.add(CrocEyes(pos=Ke((0, (700, 562)), (s.dur, (820, 562), 'linear')), scale=1.0, view='side', water=RIVER,
                   facing='right'))
    S.append(s)

    # 18 ── it doesn't need to chase
    s = _shot(18, Board(), Camera(push=0.5, wander=2), 'chase')
    s.add(Croc(pos=Ke((0, (980, 640)), (s.dur, (930, 640), 'linear')), scale=0.7, gait=1.0, walk_period=2.0,
               variant='xray'))
    s.add(StrikeLabel('CHASE', size=140, t_strike=lt(s, 156.13) - 0.15, pos=(960, 330), t0=0.15))
    S.append(s)

    # 19 ── one researcher measured adult saltwater crocodiles
    s = _shot(19, Board(), Camera(push=0.5, wander=2), 'researcher')
    s.add(Human(pose='clipboard', coat='lab', glasses=True, hat='hair', facing='right', pos=(400, 860), scale=0.95))
    s.add(Croc(pos=(1250, 700), scale=0.8, gait=0.0, swim=0.3, variant='side'))
    s.add(Pill('ONE RESEARCHER', 'dark', size=34, pos=(400, 330), target=(400, 450), t0=lt(s, 157.19)))
    s.add(Pill('ADULT SALTWATER CROCODILES', 'orange', size=34, pos=(1250, 330), target=(1150, 620),
               t0=lt(s, 158.49)))
    S.append(s)

    # 20 ── speed trap: 12 m/s for about a quarter of a second
    s = _shot(20, Board(), Camera(push=0.3, wander=2), 'speedtrap')
    t12 = lt(s, 160.51); tq = lt(s, 162.35)
    Lc = 350   # 12 m/s x 0.25 s = 3 m ~ half of a ~6 m croc (drawn 700 px)
    s.add(DashedGate(h=360, label='', pos=(650, 860)))
    s.add(DashedGate(h=360, label='', pos=(650 + Lc, 860)))
    s.add(Croc(pos=Ke((0, (300, 740)), (tq, (300, 740)), (tq + 0.25, (300 + Lc, 740), 'linear'),
                     (tq + 0.7, (300 + Lc + 120, 740), 'eo'), (s.dur, (300 + Lc + 130, 740))),
               facing='right', scale=0.7, gait=1.0, walk_period=0.9, jaw=Ke((0, 0), (tq, 0), (tq + 0.15, 25), (tq + 0.6, 0))))
    s.add(SpeedLines(n=12, length=380, spread=200, pos=(560, 720), t0=tq, t1=tq + 0.55), layer='back')
    def spd(t, t12=t12):
        t += 0.2
        k = max(0.0, min(1.0, (t - (t12 - 0.4)) / 0.35))
        return f'{12 * ease("eo", k):04.1f} M/S'
    s.add(Readout(spd, label='RADAR', pos=(1400, 220), t0=0.2))
    def dur_fn(t, tq=tq):
        t += 0.4
        if t < tq - 0.4: return '0.00 S'
        return f'{min(0.25, max(0.0, (t - tq) * 1.0)):.2f} S'
    s.add(Readout(dur_fn, label='BURST', pos=(540, 220), color=PAL.WHITE, t0=0.4))
    s.add(Pill('0.25 S', 'white', size=30, pos=(650 + Lc / 2, 940), t0=tq + 0.3))
    S.append(s)

    # 21 ── more than 40 km/h
    s = _shot(21, Board(), Camera(push=0.5, wander=2), 'kmh')
    s.add(Label('12 M/S  =', size=64, align='center', pos=(960, 300), t0=0.1))
    s.add(Counter(0, 40, dur=0.5, prefix='> ', suffix=' KM/H', size=170, pos=(960, 560), t0=lt(s, 164.41) - 0.1,
                  color=PAL.WHITE))
    s.add(Croc(pos=Ke((0, (-500, 850)), (s.dur, (2400, 850), 'linear')), facing='right', scale=0.45, gait=1.0,
               walk_period=0.45, variant='silhouette', sil_color='#2E5866'), layer='back')
    s.add(SpeedLines(n=10, length=300, spread=120, pos=Ke((0, (-900, 840)), (s.dur, (2000, 840), 'linear'))), layer='back')
    S.append(s)

    # 22 ── a whole body length before you've even reacted — too late
    s = _shot(22, Board(), Camera(push=0.4, wander=2), 'toolate')
    ta = lt(s, 166.95); tr = lt(s, 168.13)
    s.add(Croc(pos=Ke((0, (250, 700)), (0.3, (250, 700)), (ta, (950, 700), 'eo'), (s.dur, (970, 700))),
               facing='right', scale=0.7, gait=1.0, walk_period=0.6, jaw=Ke((0, 0), (ta - 0.2, 0), (ta, 30), (s.dur, 30))))
    s.add(Human(pose='stand', facing='left', pos=(1580, 800), scale=0.9, t1=tr))
    s.add(Human(pose='panic', facing='left', pos=(1580, 800), scale=0.9, t0=tr))
    s.add(Bang(pos=(1640, 420), t0=tr))
    s.add(ReactionBar(t_fill=0.2, dur=tr - 0.2, w=900, frac_arrive=(ta - 0.2) / (tr - 0.2), t_arrive=ta,
                      pos=(510, 900), t0=0.0))
    s.add(Punchline('…TOO LATE.', size=110, pos=(960, 250), t0=lt(s, 168.37)))
    s.camera.shake(lt(s, 168.37), amp=12)
    S.append(s)

    return S
