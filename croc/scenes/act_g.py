"""Act G: chapter 6 'THE REAL DANGER' + outro. Absolute range [491.4, 590.0)."""
import math
from engine import *
from engine.core import Fn, set_col, W, H
from engine.text import draw_text
from engine.timing import Words
from scenes.assets_g import *

T_START, T_END = 491.4, 590.0
CUTS = [491.40, 494.63, 496.61, 499.77, 503.78, 506.59, 509.33, 513.62, 516.69, 520.03, 523.67, 529.72,
        533.40, 536.87, 539.73, 542.48, 545.07, 548.62, 549.94, 551.60, 553.98, 556.71, 559.99, 566.46,
        568.50, 571.70, 575.03, 577.44, 579.72, 584.05, 585.93, T_END]
LABELS = ['SIZE', 'BITE', 'RIVALS', 'PEOPLE', 'YOUR MOVE', 'REAL DANGER']
RIVER_W = '#24443A'


def fade_in(dur=0.5):
    def fn(ctx, t):
        a = max(0.0, 1 - t / dur)
        if a > 0:
            ctx.rectangle(-50, -50, W + 100, H + 100); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()
    return Fn(fn, layer='overlay', t1=dur + 0.05, z=50)


def fade_out(t0, dur=0.6):
    def fn(ctx, t):
        a = min(1.0, t / dur)
        ctx.rectangle(-50, -50, W + 100, H + 100); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()
    return Fn(fn, layer='overlay', t0=t0, z=50)


def build(words=None):
    shots = []
    D = [CUTS[i + 1] - CUTS[i] for i in range(len(CUTS) - 1)]
    it = iter(range(len(D)))

    def new(plate, cam=None, name=''):
        i = next(it)
        s = Shot(D[i], plate=plate, camera=cam or Camera(push=0.7, drift=(6, -2)), name=name or f'g{i}')
        s.c = CUTS[i]
        if i == 0:
            s.abs_start = T_START
        shots.append(s)
        return s

    L = lambda s, t: t - s.c

    # 1 — chapter card 6/6 (maroon): croc silhouette under a hanging price tag; arrow human -> croc
    s = new(Danger(), Camera(push=0.6, drift=(6, 0)), 'chapter6')
    s.add(Croc(variant='silhouette', sil_color='#2A0C0E', pos=K((0, (1420, 600)), (s.dur, (1330, 605), 'linear')),
               scale=0.7, facing='left', gait=0.0, swim=0.6, layer='mid'))
    s.add(PriceTag('$$$', w=200, string=230, pos=(1300, -20), layer='mid', z=2, t0=0.2))
    s.add(PersonIcon(h=160, color=PAL.WHITE, pos=(470, 470), layer='mid', t0=0.5))
    s.add(BigArrow(length=360, color=PAL.RED, pos=(760, 400), layer='mid', t0=0.9))
    s.add(ChapterTitle('THE REAL DANGER', 'IT GOES THE OTHER WAY', 6, 6, labels=LABELS,
                       icons=['eye', 'tooth', 'fin', 'question', 'wave', 'brain'], t0=0.3))
    s.add(fade_in(0.5))

    # 2 — fifty years ago: an empty swamp, reticle finds nothing
    s = new(Mangrove(horizon=430), Camera(push=0.5, drift=(-10, 0)), 'empty')
    s.add(Reticle(r=60, color=PAL.WHITE, dash=True, layer='mid',
                  pos=lambda lt: (900 + 380 * math.sin(lt * 1.3), 650 + 90 * math.sin(lt * 2.1))))
    s.add(StatBox('50 YEARS AGO', t0=0.1))
    s.add(Label('HARD TO FIND ONE', size=60, align='center', pos=(960, 960), t0=L(s, 495.03), reveal='letters'))

    # 3 — post-war skin trade: hides and handbags with price tags (sepia)
    s = new(Sepia(), Camera(push=0.8, drift=(-30, 0)), 'skins')
    for k, (x, y, sc) in enumerate(((300, 640, 1.0), (620, 700, 0.9), (420, 760, 1.1), (760, 800, 1.0))):
        s.add(HideRoll(w=300 * sc, pos=(x, y), layer='mid', rot=-4 + k * 3))
    for k, (x, c) in enumerate(((1020, '#6B4A2E'), (1300, '#4E3A28'), (1580, '#7A5634'))):
        s.add(Handbag(w=240, color=c, pos=(x, 880), layer='mid', t0=0.15 * k))
        s.add(PriceTag(['$', '$$', '$$$'][k], w=110, string=60, pos=(x + 70, 640), layer='mid', z=2, t0=0.15 * k + 0.1,
                       swing=8))
    s.add(StatBox('AFTER WWII', t0=0.1))
    s.add(Stamp('SKIN TRADE', PAL.RED, 96, angle=-7, pos=(1100, 330), t0=L(s, 498.43)))

    # 4 — Northern Territory numbers fall to ~3,000
    s = new(Board(tint='maroon'), Camera(push=0.5, drift=(2, 0), wander=3), 'nt_fall')
    s.add(Label('NORTHERN TERRITORY', size=56, pos=(410, 230), t0=L(s, 500.21), reveal='letters'))
    s.add(Label('WILD SALTWATER CROCODILES', size=26, font='bold', track=0.22, color=PAL.CYAN, pos=(414, 280),
                t0=L(s, 500.97)))
    s.add(FallGraph([(0, 0.92), (0.2, 0.86), (0.4, 0.62), (0.6, 0.38), (0.8, 0.14), (0.97, 0.05)],
                    xlabels=[(0, 'POST-WAR'), (0.97, '1971')], dur=L(s, 502.41) - 0.2, t0=0.2, pos=(410, 860)))
    s.add(Counter(0, 3000, dur=0.01, prefix='~', size=150, color=PAL.RED, pos=(1440, 560), unit='left in the NT',
                  t0=L(s, 502.41)))
    s.camera.shake(L(s, 502.41), amp=6, decay=0.3)

    # 5 — protected in 1971
    s = new(Board(), Camera(push=0.7, drift=(0, 0), wander=3), 'protected')
    s.add(Croc(pos=K((0, (1300, 640)), (s.dur, (1040, 640), 'linear')), scale=0.75, facing='left', gait=1.0,
               layer='mid'))
    s.add(Label('THEY WERE', size=34, font='bold', track=0.22, align='center', pos=(960, 230), t0=0.05))
    s.add(Stamp('PROTECTED 1971', PAL.GREEN, 96, angle=-6, pos=(960, 360), t0=L(s, 504.97)))

    # 6 — today about 100,000: eyes pop up across the swamp
    s = new(Mangrove(horizon=430), Camera(push=0.8, drift=(0, 0)), 'many')
    t_pop = L(s, 507.47)
    import random
    r = random.Random(6)
    for i in range(16):
        x = r.uniform(120, 1800); y = r.uniform(470, 1020); sc = 0.25 + 0.55 * (y - 470) / 550
        s.add(CrocEyes(pos=(x, y), scale=sc, view='side' if i % 3 else 'front', layer='mid', z=y / 1000,
                       t0=max(0.0, t_pop - 0.6 + i * 0.08), water=RIVER_W))
    s.add(StatBox('TODAY', t0=0.1))
    s.add(Counter(3000, 100000, dur=0.9, prefix='~', size=150, color=PAL.GREEN, pos=(960, 250), t0=t_pop - 0.3))
    s.add(Pill('NORTHERN TERRITORY', 'dark', size=30, pos=(960, 330), t0=t_pop + 0.2))

    # 7 — Bhitarkanika, 1975: 95
    s = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'bhitar')
    s.add(Globe(center=(84, 20), radius=380, spin=1.0, highlight=['India'], pins=[(86.9, 20.7)], pos=(620, 580)))
    s.add(Label('BHITARKANIKA', size=64, pos=(1110, 330), t0=L(s, 509.53), reveal='letters'))
    s.add(Label('ODISHA, INDIA', size=26, font='bold', track=0.22, color=PAL.CYAN, pos=(1114, 380), t0=L(s, 509.9)))
    s.add(StatBox('1975', pos=(1110, 470), t0=L(s, 511.13)))
    s.add(Counter(0, 95, dur=0.5, size=200, color=PAL.WHITE, align='left', pos=(1110, 800), unit='crocodiles counted',
                  t0=L(s, 512.43) - 0.25))

    # 8 — this year: 1,858
    s = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'bars')
    s.add(Label('BHITARKANIKA COUNT', size=30, font='bold', track=0.22, align='center', pos=(960, 170), t0=0.05))
    s.add(BarChart([95, 1858], ['1975', 'THIS YEAR'], colors=[PAL.WHITE, PAL.GREEN], max_h=560, bar_w=200, gap=260,
                   stagger=L(s, 514.47) - 0.1, pos=(960, 900), t0=0.05))
    s.add(Croc(pos=K((0, (2100, 950)), (s.dur, (1600, 950), 'linear')), scale=0.3, facing='left', layer='back',
               opacity=0.35))

    # 9 — other places weren't so lucky: SE Asia globe
    countries = ['Thailand', 'Cambodia', 'Vietnam', 'China']
    s = new(Underwater(depth=0.85, rays=False), Camera(push=0.9, drift=(0, 0), wander=2), 'globe_wide')
    s.add(Globe(center=(108, 14), radius=400, spin=2.5, highlight=countries + ['Indonesia', 'Malaysia', 'Philippines',
                'Papua New Guinea', 'Australia', 'India', 'Myanmar', 'Bangladesh'], pos=(960, 600)))
    s.add(Label('OTHER PLACES', size=64, align='center', pos=(960, 140), t0=0.05, reveal='letters'))
    s.add(Label("WEREN'T SO LUCKY", size=30, font='bold', track=0.22, align='center', color=PAL.RED, pos=(960, 192),
              t0=L(s, 517.27)))
    s.add(Pill('SALTWATER CROC RANGE', 'orange', size=30, pos=(1500, 980), t0=L(s, 518.86)))

    # 10 — gone from Thailand, Cambodia, Vietnam, China
    s = new(Underwater(depth=0.85, rays=False), Camera(push=0.5, drift=(0, 0), wander=2), 'globe_grey')
    tw = {'Thailand': (520.59, (-330, 40)), 'Cambodia': (521.51, (-170, 330)), 'Vietnam': (522.25, (330, 140)),
          'China': (522.81, (40, -230))}
    s.add(GreyGlobe(center=(106, 18), radius=560, spin=0.6, grey={k: (L(s, v[0]), v[1]) for k, v in tw.items()},
                    pos=(960, 600)))
    s.add(Label('GONE FROM', size=34, font='bold', track=0.22, pos=(96, 120), t0=0.05))

    # 11 — Ramree Island callback: crocodiles wiped out too
    s = new(Sepia(), Camera(push=0.8, drift=(0, 0), wander=2), 'ramree')
    s.add(RamreeMap(t_gone=L(s, 526.77), pos=(960, 520)))
    s.add(Label('RAMREE ISLAND', size=72, align='center', color=INK, pos=(960, 160), t0=L(s, 524.09), reveal='letters',
                shadow=False))
    s.add(StatBox('LATER 20TH CENTURY', size=40, pos=(96, 930), t0=L(s, 528.31)))
    s.add(Stamp('CROCODILES GONE', '#5E6A6E', 80, angle=-6, pos=(1250, 820), t0=L(s, 527.15)))

    # 12 — the real massacre: arrow flips croc -> soldier into soldier -> croc
    s = new(Danger(grid=True), Camera(push=1.0, drift=(0, 0)), 'massacre')
    s.add(PersonIcon(h=240, color=PAL.WHITE, pos=(470, 760), layer='mid'))
    s.add(Croc(pos=(1420, 700), scale=0.5, facing='left', layer='mid', swim=0.5, gait=0.0))
    s.add(BigArrow(length=440, color=PAL.WHITE, width=34, pos=(940, 640), layer='mid', t0=0.05, rot=180,
                   flip_at=L(s, 532.34) - 0.1))
    s.add(Label('THE REAL MASSACRE', size=80, align='center', reveal='letters', pos=(960, 230), t0=L(s, 529.98)))
    s.add(Label('IN THOSE SWAMPS', size=30, font='bold', track=0.22, align='center', color=PAL.ORANGE, pos=(960, 290),
                t0=L(s, 530.68)))
    s.add(Pill('THE CROCODILES', 'red', size=36, pos=(1420, 460), target=(1420, 620), t0=L(s, 532.34)))
    s.camera.emphasis(L(s, 532.4), s.dur, 0.12, target=(1200, 640))

    # 13 — that one animal they should fear? Us.
    s = new(Board(tint='maroon'), Camera(push=0.5, drift=(0, 0), wander=2), 'fears')
    s.add(RedactCard(t_rev=L(s, 535.88), pos=(960, 500), t0=0.05))
    s.add(Label('THE ONE ANIMAL THEY SHOULD FEAR', size=30, font='bold', track=0.22, align='center', pos=(960, 200),
                t0=L(s, 533.84)))
    s.add(PersonIcon(h=220, color=PAL.RED, pos=(1260, 640), layer='overlay', z=5, t0=L(s, 535.88)))
    s.camera.shake(L(s, 535.88), amp=12, decay=0.35)

    # 14 — a side we rarely see: calm dawn, croc basking at the waterline
    s = new(Mangrove(horizon=430, haze=0.7), Camera(push=0.5, drift=(-6, 0)), 'calm')
    s.add(Croc(pos=K((0, (1180, 640)), (s.dur, (1080, 640), 'linear')), scale=0.6, facing='left', swim=0.3,
               submerged=0.5, waterline=0, water=RIVER_W, layer='mid'))
    s.add(Label('A SIDE WE RARELY SEE', size=56, align='center', pos=(960, 960), t0=L(s, 537.26), reveal='letters'))

    # 15 — sensory domes light up on the jaw
    s = new(Black(particles=True), Camera(push=1.0, drift=(0, 0), wander=2), 'domes')
    tg = L(s, 541.0)
    s.add(Fn(lambda ctx, t: (ctx.rectangle(-400, -400, W + 800, H + 800), set_col(ctx, '#141A10', 1), ctx.fill()),
             layer='back'))
    s.add(DomeHead(pos=(860, 560), scale=2.6, jaw=K((0, 4), (2, 8), (2.7, 6)), domes=True,
                   dome_glow=K((0, 0), (tg, 0), (tg + 1.0, 1.0)), layer='mid'))
    s.add(Label('SENSORY DOMES', size=72, pos=(96, 180), t0=L(s, 541.26), reveal='letters'))
    s.add(Pill('COVER THE JAWS', 'cyan', size=30, pos=(1380, 300), target=(560, 640), t0=L(s, 541.76)))

    # 16 — more sensitive to touch than fingertips
    s = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'finger')
    s.add(SenseCompare(t_bars=L(s, 543.38) - 0.3, pos=(1010, 540), scale=1.2, t0=0.05))
    s.add(Pill('MORE SENSITIVE THAN FINGERTIPS', 'cyan', size=36, pos=(960, 900), t0=L(s, 544.08)))
    s.add(Label('TOUCH', size=30, font='bold', track=0.22, align='center', pos=(960, 170), t0=L(s, 543.38)))

    # 17 — babies call from inside the nest
    plate = Riverbank(waterline_y=700, bank_x=700)
    s = new(plate, Camera(push=0.6, drift=(-4, 0)), 'nest')
    nx = 1350
    s.add(Nest(w=380, call_t=L(s, 546.72), pos=(nx, plate.bank_y(nx) + 6), layer='mid'))
    s.add(Label('THE BABIES CALL', size=56, pos=(96, 180), t0=L(s, 546.44), reveal='letters'))
    s.add(Label('FROM INSIDE THE NEST', size=28, font='bold', track=0.22, color=PAL.ORANGE, pos=(100, 230),
                t0=L(s, 547.32)))

    # 18 — the mother digs them out
    plate = Riverbank(waterline_y=700, bank_x=700)
    s = new(plate, Camera(push=0.9, drift=(0, 0)), 'dig')
    s.add(Nest(w=380, call_t=0.0, dig=K((0, 0.0), (0.45, 0.0), (1.3, 1.0)), pos=(nx, plate.bank_y(nx) + 6),
               layer='mid', z=2))
    s.add(Croc(pos=K((0, (880, plate.bank_y(880) - 50)), (0.5, (950, plate.bank_y(950) - 55), 'eo')),
               scale=0.55, facing='right', gait=1.0, layer='mid', z=1, rot=-4))
    s.add(Pill('MOTHER DIGS', 'orange', size=30, pos=(1200, 330), t0=L(s, 548.96)))

    # 19 — carries them down to the water in her jaws
    plate = Riverbank(waterline_y=700, bank_x=900)
    s = new(plate, Camera(push=0.6, drift=(-8, 0)), 'carry')
    mx = K((0, 1560), (s.dur, 1150, 'linear'))
    mom = Croc(pos=lambda lt: (mx(lt), plate.bank_y(mx(lt)) - 44), scale=0.5, facing='left', gait=1.0, jaw=10,
               layer='mid', rot=lambda lt: -9 if mx(lt) < 1300 else -5)
    s.add(mom)

    def baby_pos(lt):
        jx, jy = mom.jaw_tip(lt)
        p = mom.pos(lt) if callable(mom.pos) else mom.pos
        return (p[0] + jx * 0.5, p[1] + jy * 0.5 + 4)
    s.add(Hatchling(pos=baby_pos, scale=0.15, facing='left', swim=0.6, layer='mid', z=2))
    s.add(Label('CARRIES THEM TO THE WATER', size=48, pos=(96, 180), t0=L(s, 550.14), reveal='letters'))

    # 20 — in the same jaws that set the record
    s = new(Board(), Camera(push=0.9, drift=(0, 0), wander=2), 'samejaws')
    head = s.add(DomeHead(pos=(860, 600), scale=2.2, jaw=7, domes=True, dome_glow=0.4, layer='mid'))
    s.add(Hatchling(pos=(860 - 2.2 * 470 + 2.2 * 420 - 120, 600 + 20), scale=0.3, facing='left', swim=0.3,
                    layer='mid', z=2))
    s.add(Label('16,414 N', size=110, color='#8A979B', pos=(1240, 320),
                opacity=K((0, 0), (L(s, 552.02), 0), (L(s, 552.3), 1), (L(s, 553.6), 1), (s.dur, 0.2)), t0=0.0))
    s.add(Label('SAME JAWS', size=60, pos=(1240, 420), t0=L(s, 551.78), reveal='letters'))
    s.add(Label('THAT SET THE RECORD', size=28, font='bold', track=0.22, color=PAL.ORANGE, pos=(1244, 470),
                t0=L(s, 552.76)))

    # 21 — she guards them for up to five weeks
    s = new(Mangrove(horizon=430), Camera(push=0.5, drift=(-5, 0)), 'creche')
    s.add(Croc(pos=K((0, (1100, 640)), (s.dur, (1060, 640), 'linear')), scale=0.6, facing='left', swim=0.3,
               submerged=0.55, water=RIVER_W, layer='mid'))
    for i, (x, y) in enumerate(((620, 700), (760, 740), (520, 780), (880, 800), (690, 860))):
        s.add(CrocEyes(pos=(x, y), scale=0.22, view='side', layer='mid', z=1, water=RIVER_W, t0=0.1 * i))
    s.add(Label('UP TO', size=34, font='bold', track=0.22, pos=(1206, 230), t0=L(s, 555.24)))
    s.add(Counter(0, 5, dur=0.4, size=150, suffix=' WEEKS', color=PAL.ORANGE, align='left', pos=(1200, 380),
                  t0=L(s, 555.46) - 0.2))
    s.add(Pill('GUARDING', 'dark', size=30, pos=(1100, 480), target=(1050, 610), t0=L(s, 554.34)))

    # 22 — Marcus McGowan: the cold-open reef, calm now
    s = new(Reef(surface_y=230), Camera(push=0.5, drift=(-6, 0)), 'reefcalm')
    s.add(Snorkeller(pos=K((0, (700, 230)), (s.dur, (820, 230), 'linear')), scale=0.6, kick=0.5, layer='mid'))
    s.add(StatBox('MARCUS McGOWAN', t0=L(s, 557.08)))
    s.add(Pill('AFTER HIS ATTACK', 'dark', size=30, pos=(1300, 720), t0=L(s, 559.02)))

    # 23 — quote card, word by word
    s = new(Black(particles=True), StaticCamera(), 'quote')
    qwords = ['When', 'you', 'enter', 'the', 'marine', 'environment', 'you', 'are', 'entering', 'territory',
              'that', 'belongs', 'to', 'potentially', 'dangerous', 'animals']
    qt = []
    if words:
        Wd = Words(words)
        tt = s.c
        for w in qwords:
            try:
                tt = Wd.find(w, after=tt - 0.01); qt.append(tt - s.c); tt += 0.02
            except Exception:
                qt.append(qt[-1] + 0.3 if qt else 0.2)
    s.add(QuoteReveal('“When you enter the marine environment, you are entering territory that belongs to potentially '
                      'dangerous animals.”', attribution='— MARCUS McGOWAN', word_times=qt or None, size=58,
                      width=1400, pos=(960, 520), t_attr=L(s, 565.4), t0=0.0))

    # 24 — along a lot of tropical coastline (dusk)
    plate = TintedSurface(DUSK, waterline=640)
    s = new(plate, Camera(push=0.5, drift=(-8, 0)), 'coast')
    s.add(Fn(lambda ctx, t: _coast(ctx, t), layer='mid'))
    s.add(Label('TROPICAL COASTLINE', size=30, font='bold', track=0.22, align='center', pos=(960, 980),
                t0=L(s, 567.3)))

    # 25 — something lying very still, just under the surface (night river)
    s = new(Mangrove(horizon=430, particles=False), Camera(push=1.2, drift=(0, 0), wander=2), 'still')
    s.add(Grade('#030A16', 0.62, z=-10))
    s.add(MoonGlint(water_y=430 - 120, pos=(1450, 120), z=-9))
    s.add(CrocEyes(pos=(860, 720), scale=1.7, view='side', drift=0.2, eyeshine=K((0, 0.3), (1.2, 1.0)), water='#071612',
                   layer='mid', z=1))
    s.add(Grade('#030A16', 0.3, z=2))
    s.add(Label('LYING VERY STILL', size=30, font='bold', track=0.22, align='center', pos=(960, 980),
                t0=L(s, 569.36)))

    # 26 — waiting to see if you come back tomorrow
    s = new(Mangrove(horizon=360, particles=False), Camera(push=1.6, drift=(0, 0), wander=1), 'tomorrow')
    s.add(Grade('#030A16', 0.62, z=-10))
    s.add(CrocEyes(pos=(960, 640), scale=2.2, view='front', drift=0.1, eyeshine=1.0, water='#071612', layer='mid', z=1))
    s.add(Grade('#030A16', 0.3, z=2))
    s.add(Label('SAME SPOT…', size=30, font='bold', track=0.22, align='center', pos=(960, 200), t0=L(s, 573.44)))
    s.add(Label('TOMORROW?', size=80, align='center', pos=(960, 300), t0=L(s, 574.08), reveal='letters'))

    # 27 — "I think I'd stand five metres back."
    plate = Riverbank(waterline_y=640, bank_x=700)
    s = new(plate, Camera(push=0.7, drift=(0, 0)), 'fiveback')
    edge = 760
    s.add(CrocEyes(pos=(420, 640), scale=0.5, view='side', water=RIVER_W, layer='mid'))
    bx = edge + 650
    s.add(StickWaver(h=170, color='#F2F0EB', pos=(bx, plate.bank_y(bx) + 4), layer='mid', z=2, t0=0.0))
    s.add(DimensionLine((edge, plate.bank_y(bx) + 110), (bx, plate.bank_y(bx) + 110), label='5 M',
                        t0=L(s, 575.64)))
    s.add(Punchline("I'D STAND 5 M BACK.", size=86, color=PAL.ORANGE, pos=(720, 200), t0=L(s, 575.48)))
    s.camera.shake(L(s, 576.4), amp=8, decay=0.3)

    # 28 — thanks for watching
    s = new(Mangrove(horizon=430), Camera(push=0.6, drift=(-6, 0)), 'thanks')
    s.add(Croc(pos=K((0, (2200, 700)), (s.dur, (1150, 700), 'linear')), scale=0.55, facing='left', swim=1.0,
               submerged=0.5, water=RIVER_W, layer='mid'))
    s.add(Label('THANKS FOR WATCHING', size=80, align='center', pos=(960, 300), t0=L(s, 578.06), reveal='letters'))

    # 29 — comment box
    s = new(Board(), Camera(push=0.4, drift=(0, 0), wander=2), 'comment')
    s.add(Label('WHICH ANIMAL SHOULD WE COVER NEXT?', size=48, align='center', pos=(960, 260), t0=L(s, 580.14),
                reveal='letters'))
    s.add(CommentBox(text='Do the hippo next', cps=10, t_type=1.0, pos=(960, 560), t0=0.0))
    s.add(Pill('COMMENT BELOW', 'orange', size=36, pos=(960, 840), t0=L(s, 583.06)))
    s.add(CrocTop(pos=K((0, (200, 1010)), (s.dur, (1700, 990), 'linear')), scale=0.35, layer='back', opacity=0.25,
                  facing='right'))

    # 30 — heart: I do actually read them
    s = new(Board(), Camera(push=1.0, drift=(0, 0), wander=2), 'read')
    s.add(CommentBox(text='Do the hippo next', cps=200, t_type=-1, t_heart=L(s, 584.70), pos=(960, 560)))
    s.add(Label('I DO ACTUALLY READ THEM', size=44, font='bold', track=0.14, align='center', pos=(960, 300),
                t0=L(s, 584.24)))

    # 31 — end card
    s = new(Board(), Camera(push=0.25, drift=(0, 0), wander=2), 'endcard')
    s.add(CrocTop(pos=K((0, (-400, 900)), (s.dur, (2300, 880), 'linear')), scale=0.35, layer='back', facing='right',
                  opacity=0.6))
    s.add(VideoCard(w=620, h=350, label='WATCH NEXT', seed=1, pos=(560, 470), t0=0.15))
    s.add(VideoCard(w=620, h=350, label='YOU MIGHT LIKE', seed=2, pos=(1360, 470), t0=0.3))
    s.add(SubscribeButton(t_click=2.2, pos=(960, 820), t0=0.5))
    s.add(fade_out(s.dur - 0.7, 0.7))

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-6, sum(x.dur for x in shots)
    assert len(shots) == len(D)
    return shots


def _coast(ctx, t):
    """Dusk coastline silhouette: beach curve on the left, river mouth, mangrove clumps, palms."""
    set_col(ctx, '#1A1A22')
    ctx.move_to(-300, 640); ctx.line_to(820, 640); ctx.curve_to(700, 600, 400, 560, -300, 540); ctx.close_path(); ctx.fill()
    ctx.move_to(1120, 640); ctx.curve_to(1300, 590, 1700, 580, 2300, 560); ctx.line_to(2300, 640); ctx.close_path(); ctx.fill()
    for x, h in ((150, 210), (320, 170), (1500, 190), (1720, 230)):
        sway = 4 * math.sin(t * 0.8 + x)
        ctx.move_to(x, 600); ctx.curve_to(x + 10, 600 - h * 0.5, x + sway, 600 - h * 0.8, x + 20 + sway, 600 - h)
        ctx.set_line_width(10); ctx.stroke()
        for a in range(5):
            ang = math.radians(-160 + a * 35)
            ctx.move_to(x + 20 + sway, 600 - h)
            ctx.line_to(x + 20 + sway + math.cos(ang) * 90, 600 - h + math.sin(ang) * 40 + 30)
        ctx.set_line_width(8); ctx.stroke()
    import random
    r = random.Random(3)
    for i in range(14):
        x = 980 + r.uniform(-80, 80); y = 660 + i * 26
        w = 60 + i * 18
        ctx.rectangle(x - w / 2 + 6 * math.sin(t + i), y, w, 4); set_col(ctx, '#F2B98C', 0.25); ctx.fill()
    set_col(ctx, '#1A1A22')
