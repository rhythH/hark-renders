"""Act D — card 3/6 RIVALS + card 4/6 PEOPLE (abs 238.7–326.3, B34–B44). Plan: scenes/plan_d.md."""
import math
import random
from engine import *
from engine.core import Element, ev
from engine.timing import Words
from scenes.assets_d import (fade_in, sepia_grade, tint_grade, TouristBoat, Thongs, Poster, DashedCircle, Scoreboard,
                             StrikeLabel, Crown, SoundWave, SplashRing, Redacted, ToothDots, TugArrow, MudIsland,
                             BankSil, RiverMap, NavChapterTitle, bull_shark)

T_START, T_END = 238.7, 326.3
CUTS = [238.70, 243.64, 246.24, 249.22, 253.82, 256.58, 259.02, 261.91, 263.86, 266.53, 269.92, 273.99, 275.72,
        280.91, 284.48, 288.98, 292.58, 295.72, 300.35, 304.68, 308.24, 313.46, 316.08, 319.89, 324.10, 326.30]
RIVER = '#24443A'


def darken(alpha=0.35, col='#10141A'):
    return Fn(lambda ctx, t: (set_col(ctx, col, alpha), ctx.rectangle(-1500, -1500, 5000, 4000), ctx.fill()),
              layer='fg', z=50)


def follow(el, t_off, dx=0, dy=0):
    """world pos callable following an element's pos (shot time)."""
    return lambda t: (ev(el.pos, t - t_off)[0] + dx, ev(el.pos, t - t_off)[1] + dy)


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

    # 1 — chapter card 3/6 RIVALS (maroon): bull-shark silhouette above, red croc silhouette rising
    s, L = new(Danger(), Camera(push=0.6, drift=(6, 0)), 'card_rivals')
    s.add(BullShark(pos=K((0, (1500, 250)), (4.94, (900, 230), 'linear')), scale=0.62, style='silhouette',
                    sil_color='#0A0203', layer='back'))
    s.add(Croc(pos=K((0, (900, 1250)), (4.94, (1180, 760), 'eo')), rot=-14, scale=0.95, variant='silhouette',
               sil_color='#9E2A2B', swim=1.2, legs=False, layer='mid'))
    s.add(Fn(lambda ctx, t: (set_col(ctx, '#F0A54A', 0.07), ctx.rectangle(1500, 60, 20, 300), ctx.fill(),
                             ctx.rectangle(1560, 80, 16, 260), ctx.fill(), ctx.rectangle(1612, 60, 20, 300), ctx.fill()),
             layer='back'))   # faint tiger-stripe glyph
    s.add(NavChapterTitle('RIVALS', 'WHAT IT BEATS', 3, t0=0.3))
    s.add(StatBox('ADELAIDE RIVER, NT', sub='AUGUST 2014', t0=L(240.92), t_sub=0.4, pos=(96, 100)))
    s.add(fade_in(0.6))

    # 2 — tourist boat, phones up
    pl = Riverbank(560, bank_x=1700, mangroves=True)
    s, L = new(pl, Camera(push=0.6, drift=(-8, 0)), 'boat')
    s.add(TouristBoat(plate=pl, pos=K((0, (760, 560)), (2.6, (860, 560), 'linear')), scale=0.95, n=10,
                      t_phones=L(244.72), layer='mid'))
    s.add(Pill('A BOATLOAD OF TOURISTS', 'dark', size=36, pos=(760, 230), t0=L(244.0)))
    s.add(Pill('PHONES OUT', 'orange', size=30, pos=(1300, 300), t0=L(244.85)))

    # 3 — REC: Brutus with something thrashing in his jaws
    pl = Riverbank(560, bank_x=1500, mangroves=True)
    s, L = new(pl, Camera(push=1.0, drift=(4, 0), wander=2), 'rec_brutus')
    cpos, csc = (1080, 570), 0.7
    croc = s.add(Croc(pos=cpos, scale=csc, facing='left', submerged=0.3, water=RIVER, swim=0.4,
                      jaw=K((0, 26), (1.0, 32), (2.0, 24), (2.98, 30)), layer='mid', z=1))
    jt = croc.jaw_tip(0)
    s.add(BullShark(pos=(cpos[0] + csc * jt[0] + 40, cpos[1] + csc * jt[1] - 10), rot=-28, scale=(0.34, 0.42),
                    style='silhouette', sil_color='#2A3438', thrash=0.9, layer='mid', z=0))
    s.add(Splash(pos=(cpos[0] + csc * jt[0], 560), size=0.6, t0=L(247.52), layer='fg'))
    s.add(Pill('BRUTUS', 'red', size=40, pos=(1250, 260), target=(1150, 520), t0=L(246.34)))
    s.add(Pill('SOMETHING THRASHING', 'dark', size=30, pos=(560, 300), target=(cpos[0] + csc * jt[0] - 40, 470),
               t0=L(247.40)))
    rec_shot(s, tc_start=2 * 60 + 14.0)

    # 4 — Brutus stats: ~5.5 m, ~80 years old
    s, L = new(Board(), Camera(push=0.6, drift=(4, 0), wander=2), 'brutus_stats')
    s.add(Croc(pos=K((0, (1030, 560)), (4.6, (950, 560), 'linear')), scale=0.95, gait=1.0, layer='mid'))
    s.add(Typewriter('BRUTUS', size=72, pos=(120, 170), t0=0.1, cps=18))
    s.add(DimensionLine((470, 790), (1440, 790), label='~5.5 M', sub='LONG', t0=L(249.96)))
    s.add(Counter(0, 80, dur=0.7, size=110, pos=(1500, 230), prefix='~', unit='years old (thought)', t0=L(252.40)))

    # 5 — the thing in his mouth: a bull shark
    pl = Riverbank(470, bank_x=2100, mangroves=True)
    s, L = new(pl, Camera(push=1.0, drift=(0, 0), wander=3), 'bullshark')
    cpos, csc = (1150, 500), 0.7
    croc = s.add(Croc(pos=cpos, scale=csc, submerged=0.55, waterline=-10, water=RIVER, swim=0.5,
                      jaw=K((0, 24), (1.4, 30), (2.76, 26)), layer='mid', z=1))
    jt = croc.jaw_tip(0)
    hold = (cpos[0] + csc * jt[0], cpos[1] + csc * jt[1])
    s.add(bull_shark(pos=(hold[0] + 60, hold[1] - 20), rot=-24, scale=0.52, thrash=K((0, 0.8), (2.76, 0.6)),
                     layer='mid', z=0))
    tsh = L(255.44)
    s.add(Splash(pos=(hold[0] - 60, 470), size=0.8, t0=tsh, layer='fg'))
    s.add(Pill('BULL SHARK', 'red', size=44, pos=(560, 820), target=(hold[0] - 120, hold[1] + 90), t0=L(255.24)))
    s.add(Label('THE THING IN HIS MOUTH:', size=36, font='bold', track=0.18, pos=(120, 130), t0=L(253.96)))
    s.camera.shake(tsh, amp=8, decay=0.4)

    # 6 — poster: MISSING: 1 FRONT LEG
    s, L = new(Sepia(), Camera(push=1.2, drift=(0, -3), wander=2), 'poster')
    s.add(Poster(pos=K((0, (960, 1300)), (0.4, (960, 560), 'eo')), rot=K((0, 5), (0.4, -1.5, 'eo')), t_sub=L(257.42) - 0.0,
                 layer='mid'))
    s.add(Croc(pos=K((0, (980, 1420)), (0.4, (980, 660), 'eo')), scale=0.75, legs=False, swim=0.3, layer='mid', z=2))
    s.add(DashedCircle(r=70, pos=(980 - 0.75 * 150, 660 + 0.75 * 120), t0=L(258.0), layer='mid', z=3))
    s.add(Label('?', size=90, color=PAL.RED, align='center', pos=(980 - 0.75 * 150 - 130, 660 + 0.75 * 120 + 30),
                t0=L(258.24), layer='mid', z=3))

    # 7 — the local story: lost it to a shark (sepia flashback polaroid)
    shark7 = BullShark(pos=K((0, (720, 160)), (0.9, (470, 180), 'eo'), (2.89, (440, 185))), scale=0.32, style='silhouette',
                       sil_color='#2B2016', jaw=K((0, 0), (0.6, 22), (0.9, 4)), facing='left')
    croc7 = Croc(pos=K((0, (210, 250)), (2.89, (240, 252), 'linear')), scale=0.33, variant='silhouette', sil_color='#4A3A26',
                 legs=True, gait=0.3, facing='right', swim=1.2)

    def flash_content(ctx, t, w, h):
        set_col(ctx, '#BFA77E'); ctx.paint()
        set_col(ctx, '#A68E62'); ctx.rectangle(0, 0, w, 40); ctx.fill()
        croc7.render(ctx, t); shark7.render(ctx, t)
    s, L = new(Sepia(), Camera(push=1.0, drift=(-3, 0), wander=2), 'flashback')
    s.add(Polaroid(content=flash_content, caption='YEARS AGO…?', w=680, h=420, angle=-3, pos=(860, 500), bg='#BFA77E'))
    s.add(Pill('LOCAL STORY', 'cyan', size=40, pos=(1480, 230), t0=L(259.12)))
    s.add(Pill('LOST IT TO A SHARK', 'dark', size=32, pos=(1480, 860), t0=L(260.42)))
    s.post.append(sepia_grade(0.45))

    # 8 — "I'm not saying it was revenge"
    s, L = new(Danger(), Camera(push=1.6, drift=(0, 0), wander=2), 'revenge')
    s.add(CrocHead(pos=(1100, 600), scale=2.6, jaw=0, domes=False, blink=[L(262.6)], layer='mid'))
    s.add(Label('REVENGE?', size=120, color=PAL.RED, align='center', pos=(700, 250), reveal='letters', t0=L(262.94)))
    s.add(Pill("NOT SAYING IT WAS", 'grey', size=30, pos=(700, 120), t0=L(262.08)))
    s.camera.emphasis(0.0, 1.9, 0.12, target=(900, 560))

    # 9 — scoreboard: he didn't let this one go
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'score')
    tgo = L(265.58)
    c9 = s.add(Croc(pos=(1300, 820), scale=0.55, jaw=K((0, 24), (2.67, 28)), swim=0.5, layer='mid', z=1))
    j9 = c9.jaw_tip(0)
    s.add(bull_shark(pos=(1300 + 0.55 * j9[0] + 50, 820 + 0.55 * j9[1] - 15), rot=-24, scale=0.32, thrash=0.5,
                     layer='mid', z=0))
    s.add(Scoreboard([('SHARKS', 1, 1, None), ('BRUTUS', 0, 1, tgo)], pos=(640, 300), t0=0.05))
    s.add(Pill("DIDN'T LET THIS ONE GO", 'orange', size=32, pos=(640, 640), t0=L(264.84)))
    s.camera.shake(tgo, amp=12, decay=0.4)

    # 10 — globe: Sundarbans, India, August 2011
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'globe_sund')
    s.add(Globe(center=(86, 20), radius=330, spin=1.5, highlight=['India'], pins=[(89.2, 21.9)], pos=(1180, 560),
                caption='SUNDARBANS'))
    s.add(StatBox('AUGUST 2011', t0=L(267.04), pos=(96, 100)))
    s.add(Pill('INDIA', 'dark', size=34, pos=(560, 420), target=(1060, 520), t0=L(268.96)))
    s.add(Pill('RANGERS', 'cyan', size=34, pos=(560, 560), t0=L(268.22)))

    # 11 — mangrove low tide: tiger lying on a marshy island, rangers' boat
    pl = Mangrove(horizon=420)
    s, L = new(pl, Camera(push=0.7, drift=(-10, 0), wander=2), 'tiger_found')
    s.add(MudIsland(w=1100, pos=(1050, 640), layer='mid'))
    s.add(Tiger(pose='lying', pos=(1050, 640), scale=0.65, layer='mid', z=1))
    s.add(Speedboat(crew=2, pos=K((0, (2200, 860)), (4.07, (1550, 860), 'eo')), scale=0.5, facing='left', layer='mid', z=2))
    s.add(Label('TIGER, 8 YRS', size=44, font='xb', align='center', pos=(1050, 470), t0=L(271.08), layer='mid', z=3))
    s.add(Pill('MARSHY ISLAND', 'dark', size=30, pos=(560, 330), t0=L(272.76)))
    s.add(Pill('RANGERS', 'cyan', size=28, pos=(1560, 640), target=(1520, 780), t0=0.3))
    s.post.append(tint_grade('#C8C2B0', 0.25))

    # 12 — poachers? ruled out
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'poachers')
    tr = L(274.60)
    s.add(StrikeLabel('POACHERS', size=150, t_strike=tr, pos=(960, 560), t0=0.05))
    s.add(Stamp('RULED OUT', PAL.RED, 80, pos=(1220, 760), t0=L(274.88)))
    s.camera.shake(L(274.88), amp=8, decay=0.35)

    # 13 — post-mortem board: 25 tooth marks, hind leg ripped away
    s, L = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'postmortem')
    tx, ty, ts = 900, 800, 1.45
    s.add(Tiger(style='outline', missing_leg=True, pos=(tx, ty), scale=ts, layer='mid'))
    r = random.Random(25)
    pts = []
    while len(pts) < 25:
        u, v = r.uniform(-1, 1), r.uniform(-1, 1)
        if u * u + v * v > 1: continue
        pts.append((tx + ts * (170 + 120 * u), ty + ts * (-190 + 55 * v)))
    t25 = L(276.68)
    s.add(ToothDots(pts, dur=0.9, t0=t25, layer='mid'))
    s.add(Stamp('POST-MORTEM', PAL.RED, 60, angle=-5, pos=(380, 170), t0=L(275.88)))
    s.add(Counter(0, 25, dur=0.9, size=120, pos=(1500, 230), unit='tooth marks', t0=t25))
    s.add(Pill('HIND LEG: RIPPED AWAY', 'red', size=34, pos=(1420, 900), target=(tx + ts * 260, ty - ts * 60),
               t0=L(279.14)))

    # 14 — grabbed its leg and kept pulling
    s, L = new(Danger(), Camera(push=0.7, drift=(0, 0), wander=3), 'tug')
    tg = [L(282.16), L(283.36), L(283.54) + 0.3]
    tug = lambda t: -sum(26 * math.sin(math.pi * min(1, max(0, (t - x) / 0.45))) for x in tg)
    s.add(Tiger(pose='dragged', style='silhouette', sil_color='#0A0203', layer='mid',
                pos=lambda t: (640 + tug(t) * -0.6, 660), scale=0.9))
    s.add(Croc(variant='silhouette', sil_color='#9E2A2B', facing='left', jaw=18, swim=0.3, legs=False, scale=0.8,
               pos=lambda t: (1330 + tug(t) * -1.0, 700), layer='mid', z=1))
    s.add(TugArrow(times=tg, length=260, pos=(1000, 430), t0=L(282.16) - 0.25))
    s.add(Pill('PROBABLE CAUSE: CROCODILE', 'cyan', size=34, pos=(960, 170), t0=L(281.66)))

    # 15 — the tiger rules the islands; the water belongs to someone else
    pl = Riverbank(600, bank_x=1050, mangroves=True)
    s, L = new(pl, Camera(push=0.5, drift=(0, 0), wander=2), 'crown')
    tw, te = L(286.70), L(287.72)
    s.add(Tiger(pos=(1480, pl.bank_y(1480)), scale=0.5, facing='left', walk=0.0, layer='mid'))
    s.add(CrocEyes(pos=(520, 600), scale=1.0, view='side', layer='mid', water=RIVER))
    s.add(Crown(pos=K((0, (1400, 230)), (tw, (1400, 230), 'eio'), (tw + 0.9, (520, 470), 'eio'), (5, (520, 470))),
                t0=L(284.62), layer='mid', z=3))
    s.add(Label('THE ISLANDS', size=46, font='bold', track=0.2, align='center', pos=(1480, 110), t0=L(285.64)))
    s.add(Label('THE WATER', size=46, font='bold', track=0.2, align='center', pos=(520, 760), t0=tw))
    s.add(Punchline('…SOMEONE ELSE.', size=80, pos=(960, 930), t0=te))
    s.camera.shake(L(287.98), amp=10, decay=0.4)

    # 16 — what does it fear?
    s, L = new(Black(particles=True), Camera(push=1.4, drift=(0, 0), wander=2), 'fear')
    s.add(CrocHeadOn(pos=(960, 700), scale=1.25, eyes_glow=K((0, 0), (L(291.72), 0.2), (L(291.72) + 0.6, 1.0)),
                     layer='mid'))
    s.add(Label('WHAT DOES IT FEAR?', size=72, align='center', pos=(960, 200), reveal='letters', t0=L(291.28)))
    s.add(Pill('FULLY GROWN', 'dark', size=30, pos=(960, 90), t0=L(289.52)))

    # 17 — FEARS: one redacted line, later
    s, L = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'fears')
    s.add(Redacted(t_line=L(292.88), t_lock=L(293.14), pos=(820, 520), t0=0.05))
    s.add(Badge('question', 'ONLY ONE ANIMAL', r=80, pos=(1500, 400), t0=L(292.88)))
    s.add(Pill('LATER', 'orange', size=44, pos=(1500, 760), t0=L(294.25)))

    # 18 — chapter card 4/6 PEOPLE (maroon)
    s, L = new(Danger(), Camera(push=0.5, drift=(4, 0)), 'card_people')
    s.add(BankSil(pos=(0, 560), layer='back'))
    s.add(Human(pos=(1290, 448), scale=0.32, pose='stand', facing='left', coat='#3A1012', layer='back', z=2))
    s.add(Croc(pos=K((0, (520, 590)), (4.63, (760, 588), 'linear')), scale=0.6, submerged=0.6, water='#1C0507',
               variant='silhouette', sil_color='#9E2A2B', legs=False, swim=0.6, layer='mid'))
    s.add(CrocEyes(pos=K((0, (900, 562)), (4.63, (1000, 562), 'linear')), scale=0.5, view='side', body=False,
                   eyeshine=0.8, water='#1C0507', layer='mid'))
    s.add(NavChapterTitle('PEOPLE', 'IT DEPENDS WHERE YOU ARE', 4, t0=0.6))
    s.add(fade_in(0.5))

    # 19 — Australia: about one or two people a year
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'australia')
    s.add(Globe(center=(134, -22), radius=330, spin=1.0, highlight=['Australia'], pins=[(132, -12.8), (145, -16)],
                pos=(620, 560), caption='AUSTRALIA'))
    s.add(Counter(0, 1, dur=0.3, size=170, pos=(1290, 520), t0=L(302.90)))
    s.add(Label('–2', size=170, font='xb', pos=(1350, 520), t0=L(303.34), reveal=None))
    s.add(Label('PEOPLE A YEAR', size=40, font='bold', track=0.22, pos=(1180, 620), t0=L(303.48)))
    s.add(Pill('ABOUT', 'grey', size=30, pos=(1250, 330), t0=L(302.64)))
    s.add(Pill('KILLED BY SALTWATER CROCODILES', 'outline', size=26, pos=(1360, 720), t0=L(302.40)))

    # 20 — April 2023, riverbank, two fishermen
    pl = Riverbank(560, bank_x=820, mangroves=True)
    s, L = new(pl, Camera(push=0.4, drift=(-6, 0), wander=2), 'kb_wide')
    s.add(Fisherman(pos=(1120, pl.bank_y(1120)), scale=0.45, facing='left', line_to=(-520, 120), layer='mid'))
    s.add(Fisherman(pos=(1620, pl.bank_y(1620)), scale=0.45, facing='left', line_to=(-700, 160), coat='#A0563A',
                    layer='mid'))
    s.add(Esky(pos=(1360, pl.bank_y(1360)), scale=0.8, layer='mid'))
    s.add(StatBox('APRIL 2023', t0=L(304.84), pos=(96, 100)))
    s.add(Pill('65-YEAR-OLD PUBLICAN', 'dark', size=34, pos=(1120, 250), target=(1120, 380), t0=L(306.46)))
    s.post.append(tint_grade('#E8B888', 0.25))

    # 21 — Kevin Darmody, fishing with friends at Kennedy Bend
    pl = Riverbank(600, bank_x=700, mangroves=True)
    s, L = new(pl, Camera(push=0.8, drift=(4, 0), wander=2), 'kevin')
    s.add(Fisherman(pos=(1000, pl.bank_y(1000)), scale=0.62, facing='left', line_to=(-560, 160), layer='mid'))
    s.add(Fisherman(pos=(1450, pl.bank_y(1450)), scale=0.55, facing='left', line_to=(-700, 180), coat='#A0563A',
                    layer='mid'))
    s.add(Fisherman(pos=(1750, pl.bank_y(1750)), scale=0.5, facing='left', line_to=(-900, 190), coat='#4A6E8A',
                    layer='mid'))
    s.add(Typewriter('KEVIN DARMODY, 65', size=64, pos=(110, 170), t0=L(308.34), cps=24))
    s.add(Pill('FISHING WITH FRIENDS', 'orange', size=32, pos=(1450, 280), t0=L(309.52)))
    s.add(StatBox('KENNEDY BEND, QLD', sub='FAR NORTH QUEENSLAND', t0=L(310.66), t_sub=L(311.86) - L(310.66),
                  pos=(110, 900)))
    s.post.append(tint_grade('#E8B888', 0.25))

    # 22 — a yell, then a loud splash (no depiction of the attack)
    pl = Riverbank(600, bank_x=900, mangroves=True)
    s, L = new(pl, Camera(push=0.6, drift=(0, 0), wander=2), 'yell')
    ty_, tsp = L(314.02), L(315.00)
    s.add(Fisherman(pos=(1450, pl.bank_y(1450)), scale=0.6, facing='left', line_to=(-700, 170), layer='mid'))
    s.add(SoundWave(pos=(1980, 330), t0=ty_, t1=ty_ + 1.4, layer='mid'))
    s.add(Pill('A YELL', 'dark', size=34, pos=(1600, 200), t0=ty_))
    s.add(SplashRing(pos=(420, 600), t0=tsp, layer='mid', z=3))
    s.add(Splash(pos=(420, 600), size=0.9, t0=tsp, layer='mid', z=3))
    s.add(Pill('SPLASH', 'red', size=40, pos=(420, 330), t0=tsp + 0.05))
    s.camera.shake(tsp, amp=6, decay=0.3)
    s.post.append(tint_grade('#D9A27A', 0.3))

    # 23 — "no sign of him, just his thongs on the bank and nothing else."
    pl = Riverbank(640, bank_x=600, mangroves=True)
    s, L = new(pl, Camera(push=1.0, drift=(0, 0), wander=1.5), 'thongs')
    s.add(Thongs(pos=(1150, pl.bank_y(1150) + 150), scale=1.5, layer='mid'))
    s.add(darken(0.42, '#141216'))
    q = 'NO SIGN OF HIM, JUST HIS THONGS ON THE BANK AND NOTHING ELSE.'
    qw = ['There', 'was', 'no', 'sign', 'of', 'him', 'just', 'his', 'thongs', 'on', 'the', 'bank', 'and', 'nothing', 'else']
    W_ = Words(words) if words else None
    wt = []
    t_cur = 316.30
    for w_ in qw[2:]:
        try:
            t_cur = W_.find(w_, after=t_cur - 0.01); wt.append(L(t_cur))
        except Exception:
            wt.append((wt[-1] + 0.25) if wt else 0.3)
    s.add(QuoteReveal(q, kicker='WHAT HIS FRIENDS FOUND', word_times=wt, size=50, width=1500, pos=(960, 200),
                      t_attr=99))
    s.camera.emphasis(0.0, 3.8, 0.12, target=(1150, pl.bank_y(1150) + 150))
    s.post.append(tint_grade('#9A8CA8', 0.35))

    # 24 — two days later: two crocodiles upstream
    s, L = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'upstream')
    mx, my = 960, 580
    s.add(RiverMap(t_arrow=L(323.10), pos=(mx, my), layer='mid', t0=0.02))
    s.add(Label('THE BANK', size=26, font='bold', track=0.2, align='center', pos=(mx - 480, my + 250), t0=0.3, layer='mid'))
    for j, (dx, dy, rt) in enumerate([(380, 70, 10), (590, -40, -30)]):
        s.add(CrocTop(pos=(mx + dx, my + dy), rot=rt, scale=0.2, t0=L(322.18) + j * 0.15, layer='mid', z=2))
    s.add(StatBox('TWO DAYS LATER', t0=L(319.99), pos=(96, 100)))
    s.add(Pill('WILDLIFE OFFICERS', 'cyan', size=32, pos=(560, 300), t0=L(320.92)))
    s.add(Pill('TWO CROCODILES', 'red', size=34, pos=(1460, 860), target=(mx + 480, my + 30), t0=L(322.18)))
    s.add(Label('UPSTREAM', size=40, font='bold', track=0.22, color=PAL.ORANGE, pos=(760, 380), t0=L(323.10)))

    # 25 — remains inside one of them (quiet, no gore)
    pl = Mangrove(horizon=420)
    s, L = new(pl, Camera(push=1.0, drift=(0, 0), wander=2), 'one_of_them')
    s.add(CrocEyes(pos=K((0, (640, 650)), (2.2, (600, 650), 'linear')), scale=1.2, view='side', layer='mid'))
    s.add(CrocEyes(pos=K((0, (1300, 760)), (2.2, (1260, 760), 'linear')), scale=1.6, view='side', layer='mid'))
    s.camera.emphasis(0.3, 2.2, 0.12, target=(1260, 740))
    s.add(Label('HIS REMAINS WERE INSIDE ONE OF THEM.', size=36, font='bold', track=0.12, align='center',
                pos=(960, 960), t0=L(324.28)))
    s.post.append(tint_grade('#8C88A8', 0.4))

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-3, sum(x.dur for x in shots)
    assert len(shots) == len(CUTS) - 1
    return shots
