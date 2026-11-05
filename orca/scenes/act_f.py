"""Act F: chapter 6 'THE REAL DANGER' + outro. Absolute range [453.8, 596.0)."""
import math
from engine import *
from engine.core import Fn, set_col, W, H
from engine.text import draw_text
from scenes.assets_f import *

T_START, T_END = 453.8, 596.0
CUTS = [453.8, 457.25, 463.17, 468.9, 475.96, 482.76, 485.8, 490.65, 495.75, 498.7, 502.4, 507.0, 512.9,
        515.8, 520.37, 525.4, 529.28, 533.7, 537.7, 543.6, 551.37, 554.42, 560.18, 563.43, 569.28, 571.39,
        576.85, 578.82, 581.16, 586.2, 588.09, T_END]
LABELS = ['SIZE', 'MENU', 'SHARKS', 'BOATS', 'YOUR MOVE', 'REAL DANGER']


def fade_in(dur=0.5):
    def fn(ctx, t):
        a = max(0.0, 1 - t / dur)
        if a > 0:
            ctx.rectangle(-50, -50, W + 100, H + 100); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()
    return Fn(fn, layer='overlay', t1=dur + 0.05)


def fade_out(t0, dur=0.6):
    def fn(ctx, t):
        a = min(1.0, t / dur)
        ctx.rectangle(-50, -50, W + 100, H + 100); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()
    return Fn(fn, layer='overlay', t0=t0)


def mother_calf(s, plate, c0, wl_y=760, scale=0.5, x0=1150, x1=820):
    """Mother orca (female) pushing a dead calf on her rostrum, slowly, facing left."""
    dur = s.dur
    mpos = K((0, (x0, wl_y)), (dur, (x1, wl_y - 10), 'linear'))
    s.add(Orca(pos=mpos, scale=scale, facing='left', dorsal='female', swim=0.45, period=4.5, layer='mid', z=2,
               blink='auto'))

    def cpos(lt):
        p = mpos(lt)
        return (p[0] - 0.5 * 1000 * scale - 15 * scale / 0.5, p[1] - 35 * scale / 0.5 + 4 * math.sin(lt * 1.2))
    s.add(Orca(pos=cpos, scale=scale * 0.32, facing='left', swim=0.0, rot=lambda lt: -14 + 2 * math.sin(lt * 1.2),
               tint='#6F7A80', layer='mid', z=3, blink=[]))
    return mpos


def build(words=None):
    shots = []
    D = [CUTS[i + 1] - CUTS[i] for i in range(len(CUTS) - 1)]
    it = iter(range(len(D)))

    def new(plate, cam=None, name=''):
        i = next(it)
        s = Shot(D[i], plate=plate, camera=cam or Camera(push=0.7, drift=(6, -2)), name=name or f'f{i}')
        s.c = CUTS[i]
        if i == 0:
            s.abs_start = T_START
        shots.append(s)
        return s

    L = lambda s, t: t - s.c

    # 1 — chapter card 6/6 (maroon): two orcas beneath a net, arrow human -> orca
    s = new(Danger(), Camera(push=0.6, drift=(6, 0)), 'chapter6')
    s.add(Net(pos=(1250, 70), width=1250, depth=360, layer='back'))
    s.add(Orca(variant='silhouette', sil_color='#2A0C0E', pos=K((0, (1250, 560)), (s.dur, (1120, 575), 'linear')),
               scale=0.42, facing='left', layer='mid'))
    s.add(Orca(variant='silhouette', sil_color='#2A0C0E', pos=K((0, (1640, 640)), (s.dur, (1500, 630), 'linear')),
               scale=0.34, facing='left', layer='mid', phase=1.2))
    s.add(PersonIcon(h=150, color=PAL.WHITE, pos=(520, 400), layer='mid', t0=0.5))
    s.add(BigArrow(length=360, color=PAL.RED, pos=(800, 330), layer='mid', t0=0.9))
    s.add(ChapterTitle('THE REAL DANGER', 'IT GOES THE OTHER WAY', 6, 6, labels=LABELS,
                       icons=['orca', 'fish', 'fin', 'boat', 'person', 'heart'], t0=0.3))
    s.add(fade_in(0.5))

    # 2 — old sailors' map: ink orcas chase a blue whale; "WHALE KILLER"
    s = new(Sepia(), Camera(push=0.9, drift=(-8, 0)), 'oldmap')
    s.add(InkWaves(n=46, seed=3, layer='back'))
    s.add(Compass(pos=(170, 900), layer='back'))
    s.add(OldShip(pos=K((0, (430, 520)), (s.dur, (520, 520), 'linear')), scale=0.62, layer='mid'))
    s.add(BlueWhale(silhouette=True, sil_color=INK, pos=K((0, (1250, 820)), (s.dur, (1550, 810), 'linear')),
                    scale=0.62, facing='right', layer='mid', period=5.5))
    for k, (dx, dy, sc) in enumerate(((-480, -40, 0.17), (-620, 70, 0.15), (-360, 110, 0.16))):
        s.add(Orca(variant='silhouette', sil_color=INK, facing='right', scale=sc, phase=k * 0.7, period=1.6,
                   pos=K((0, (1250 + dx - 150, 820 + dy)), (s.dur, (1550 + dx + 60, 810 + dy), 'linear')),
                   layer='mid', z=2))
    s.add(Label('"WHALE KILLER"', size=96, font='black', color=INK, align='center', reveal='letters', dur=0.3,
                shadow=False, pos=(1250, 250), t0=L(s, 459.07)))
    s.add(Label('SAILORS WATCHED THEM HUNT MUCH BIGGER WHALES', size=30, font='bold', color=INK, track=0.18,
                align='center', shadow=False, pos=(1250, 320), t0=L(s, 460.25)))

    # 3 — the words swap; name tag on a dolphin
    s = new(Sepia(), Camera(push=0.8, drift=(5, 0)), 'swap')
    s.add(InkWaves(n=30, seed=8, layer='back'))
    s.add(SwapLabel('WHALE', 'KILLER', size=96, t_swap=L(s, 465.35) - 0.1, pos=(960, 230), t0=0.15))
    opos = K((0, (1250, 640)), (s.dur, (820, 650), 'linear'))
    s.add(Orca(pos=opos, scale=0.5, facing='left', layer='mid', swim=1.0))
    s.add(NameTag('KILLER WHALE', w=360, pos=lambda lt: (opos(lt)[0] + 20, opos(lt)[1] - 170), layer='mid', z=3,
                  t0=L(s, 466.27)))
    s.add(Pill('DOLPHIN', 'dark', size=30, pos=lambda lt: (opos(lt)[0] - 330, 450),
               target=lambda t: (opos(t)[0] - 220, opos(t)[1] - 30), t0=L(s, 466.27)))
    s.add(Punchline('…THE WORST NAME IN THE OCEAN.', size=66, color=PAL.RED_DARK, pos=(960, 960), t0=L(s, 467.09)))

    # 4 — captivity tank (sombre)
    s = new(Black(particles=True), Camera(push=0.8, drift=(0, 0), wander=3), 'tank')
    tank_orca = Orca(pos=K((0, (330, 60)), (s.dur, (-340, 40), 'linear')), scale=0.28, facing='left', swim=0.6,
                     period=3.6, tint='#5E676B')
    s.add(Tank(w=900, h=440, orca=tank_orca, pos=(960, 600), layer='mid'))
    s.add(Label('EVERY CONFIRMED HUMAN DEATH', size=60, align='center', reveal='letters', pos=(960, 210),
                t0=L(s, 471.14)))
    s.add(Label('INVOLVING AN ORCA', size=32, font='bold', track=0.22, align='center', color=PAL.CYAN,
                pos=(960, 265), t0=L(s, 472.46)))
    s.add(Stamp('CAPTIVITY', PAL.RED, 80, angle=-5, pos=(960, 940), t0=L(s, 474.75)))

    # 5 — captivity vs wild columns
    s = new(Board(tint='maroon', particles=True), Camera(push=0.5, drift=(3, 0), wander=3), 'columns')
    s.add(Label('CAPTIVITY', size=64, align='center', pos=(560, 230), reveal='wipe'))
    s.add(Label('WILD', size=64, align='center', pos=(1360, 230), reveal='wipe', t0=L(s, 480.46)))
    s.add(Fn(lambda ctx, t: (ctx.move_to(960, 170), ctx.line_to(960, 900), set_col(ctx, PAL.WHITE, 0.35),
                             ctx.set_line_width(3), ctx.stroke()), layer='mid'))
    t_t = L(s, 477.73)
    for i in range(4):
        col = (lambda i: (lambda: None))(i)
        el = PersonIcon(h=190, color='#C9CFD1', pos=(380 + i * 120, 600), layer='mid', t0=L(s, 476.06) + i * 0.12)
        el.proc((lambda i: lambda e, lt: {'dpos': (0, 3 * math.sin(lt * 2 + i))})(i))
        s.add(el)
        if i < 3:
            s.add(PersonIcon(h=190, color=PAL.ORANGE, pos=(380 + i * 120, 600), layer='mid', z=2, t0=t_t + i * 0.1))
    s.add(Label('MARINE PARKS', size=28, font='bold', track=0.22, align='center', pos=(560, 300), color=PAL.CYAN,
                t0=L(s, 476.75)))
    s.add(Pill('TILIKUM: 3', 'orange', size=34, pos=(500, 780), target=(500, 640), t0=L(s, 479.61)))
    s.add(OutlineNumber('0', size=360, color=PAL.WHITE, width=8, pos=(1360, 560), t0=L(s, 481.75)))
    s.camera.shake(L(s, 481.75), amp=10, decay=0.35)

    # 6 — the arrow flips: the danger goes the other way
    s = new(Danger(grid=True), Camera(push=1.0, drift=(0, 0)), 'flip')
    s.add(Orca(pos=(560, 600), scale=0.45, facing='right', layer='mid', swim=0.8))
    s.add(PersonIcon(h=240, color=PAL.WHITE, pos=(1480, 720), layer='mid'))
    s.add(BigArrow(length=420, color=PAL.WHITE, width=34, pos=(1060, 600), layer='mid', t0=0.1,
                   flip_at=L(s, 484.58) - 0.1))
    s.add(Label('THE REAL DANGER', size=72, align='center', reveal='letters', pos=(960, 230), t0=L(s, 482.93)))
    s.add(Fn(lambda ctx, t: None, layer='overlay'))
    s.camera.emphasis(L(s, 484.6), s.dur, 0.12, target=(900, 600))

    # 7 — 1960s capture polaroid
    s = new(Sepia(dark=True, grid=True), Camera(push=0.8, drift=(-5, 0)), 'capture')
    s.add(Polaroid(content=capture_scene, caption='1960s', w=760, h=480, angle=-3, pos=(780, 520), t0=0.05))
    s.add(StatBox('1960s', t0=L(s, 486.02), pos=(96, 100)))
    s.add(Pill('PACIFIC NORTHWEST', 'orange', size=34, pos=(1500, 380), t0=L(s, 487.9)))
    s.add(Pill('CAUGHT FOR MARINE PARKS', 'red', size=34, pos=(1460, 640), t0=L(s, 489.14)))

    # 8 — by 1974: 71 animals
    s = new(Board(particles=True), Camera(push=0.6, drift=(2, 0), wander=3), 'grid71')
    s.add(StatBox('1974', sub='ONE POPULATION', t0=L(s, 490.88), t_sub=0.6))
    s.add(IconGrid(71, 12, 'orca', cell=72, pos=(960, 620), t0=L(s, 491.46), t_in=0.025))
    s.add(Counter(0, 71, dur=0.7, size=120, pos=(1560, 230), suffix='', unit='animals', t0=L(s, 494.06) - 0.35,
                  color=PAL.ORANGE))

    # 9 — bar chart 1974 vs 2025
    s = new(Board(particles=True), Camera(push=0.6, drift=(0, 0), wander=3), 'bars')
    s.add(BarChart([71, 74], ['1974', '2025'], max_h=480, bar_w=180, gap=200, stagger=L(s, 497.40) - 0.3,
                   pos=(960, 860), t0=0.3))
    s.add(Label('SAME POPULATION', size=30, font='bold', track=0.22, align='center', pos=(960, 200)))
    s.add(Orca(pos=K((0, (1900, 300)), (s.dur, (1500, 300), 'linear')), scale=0.18, layer='back', facing='left'))

    # 10 — fewer salmon + boat noise
    s = new(Underwater(depth=0.65, tint='#2F4A3E'), Camera(push=0.7, drift=(-4, 0)), 'noise')
    s.add(HullFromBelow(pos=K((0, (1500, 40)), (s.dur, (1250, 40), 'linear')), w=620, layer='mid', z=3))
    s.add(NoiseRings(pos=lambda lt: (1500 - 250 * lt / 3.7 - 290, 132), period=0.8, rmax=1100, layer='mid',
                     t0=L(s, 500.31)))
    s.add(FishSchool(pos=K((0, (600, 380)), (s.dur, (500, 360), 'linear')), n=26, radius=110, mode='stream',
                     fish_len=34, layer='back', opacity=K((0, 0.9), (0.6, 0.9), (2.0, 0.2))))
    opos = K((0, (1400, 680)), (s.dur, (950, 660), 'linear'))
    s.add(Orca(pos=opos, scale=0.45, facing='left', layer='mid'))
    s.add(BrokenArcs(pos=lambda lt: (opos(lt)[0] - 240, opos(lt)[1] - 10), direction=180, t_jam=L(s, 500.6),
                     layer='mid'))
    s.add(Pill('FEWER SALMON', 'dark', size=32, pos=(560, 230), target=(560, 340), t0=L(s, 499.2)))
    s.add(Pill('NOISE', 'red', size=34, pos=(1250, 330), t0=L(s, 500.44)))

    # 11 — x-ray: PCBs in blubber
    s = new(Board(particles=True), Camera(push=0.5, drift=(2, 0), wander=3), 'pcb')
    s.add(Orca(pos=(720, 620), scale=0.75, variant='xray', facing='right', swim=0.5, layer='mid'))
    s.add(Magnifier(r=230, t_specks=L(s, 503.67) - L(s, 502.67), target=(-700, 200), pos=(1440, 440),
                    t0=L(s, 502.67)))
    s.add(Label('PCBs', size=84, color=PAL.RED, align='center', pos=(1440, 760), t0=L(s, 503.67), reveal='letters'))
    s.add(Stamp('BANNED DECADES AGO', PAL.ORANGE, 56, angle=-5, pos=(960, 180), t0=L(s, 505.17)))

    # 12 — 2018 study: globe with population dots, more than half turn red
    dots = [(-125, 49), (-150, 58), (-62, 45), (-25, 66), (15, 69), (-6, 36), (-9, 42), (18, -34), (55, -45),
            (145, -42), (170, -45), (150, 45), (-70, -55), (-40, 63), (-75, 38), (-160, 20)]
    red = [0, 2, 3, 4, 5, 6, 9, 13, 14]
    s = new(Underwater(depth=0.8, rays=False), Camera(push=0.5, drift=(0, 0), wander=2), 'globe')
    s.add(DotGlobe(dots=dots, red_idx=red, t_red=L(s, 510.69), t_dots=0.3, center=(-40, 35), radius=350, spin=6,
                   pos=(1290, 560)))
    s.add(StatBox('2018 STUDY', t0=L(s, 507.19)))
    s.add(Label('MORE THAN HALF', size=72, color=PAL.RED, pos=(96, 560), t0=L(s, 510.69), reveal='letters'))
    s.add(Label("OF THE WORLD'S ORCA POPULATIONS", size=26, font='bold', track=0.2, pos=(100, 610),
                t0=L(s, 511.26)))
    s.add(Label('THREATENED BY PCBs', size=26, font='bold', track=0.2, pos=(100, 650), color=PAL.CYAN,
                t0=L(s, 509.73)))

    # 13 — zoom on the Strait of Gibraltar
    s = new(Underwater(depth=0.8, rays=False), Camera(push=1.2, drift=(0, 0), wander=2), 'gibraltar')
    s.add(Globe(center=(-5.6, 36), radius=560, spin=0.6, highlight=['Spain', 'Portugal', 'Morocco'],
                pins=[(-5.6, 36)], pos=(960, 620)))
    s.add(Reticle(r=60, pos=(960 + 0, 620 + 0), layer='mid', t0=0.3, dash=True))
    s.add(Label('STRAIT OF GIBRALTAR', size=60, align='center', pos=(960, 170), t0=L(s, 513.28), reveal='letters'))
    s.add(Pill('AMONG THE WORST', 'red', size=36, pos=(1300, 420), target=(990, 600), t0=L(s, 514.26)))

    # 14 — Iberian orcas: 30 to 40
    s = new(Board(particles=True), Camera(push=0.6, drift=(0, 0), wander=3), 'iberian')
    s.add(Label('IBERIAN ORCAS', size=60, align='center', pos=(960, 190), reveal='wipe', t0=0.1))
    s.add(IconGrid(40, 10, 'orca', cell=110, pos=(960, 600), lost_from=30, t_lost=L(s, 518.11) + 0.2,
                   lost_color='#33505A', stagger=0.06, t_in=0.02, t0=0.3))
    s.add(Label('30–40 ANIMALS', size=64, color=PAL.ORANGE, align='center', pos=(960, 960), t0=L(s, 518.11),
                reveal='letters'))

    # 15 — dawn: the oldest female, August 2026, Toñi
    plate = TintedSurface(DAWN_SOFT, waterline=420)
    s = new(plate, Camera(push=0.6, drift=(-4, 0)), 'toni')
    tpos = K((0, (1300, 720)), (s.dur, (900, 700), 'linear'))
    s.add(Orca(pos=tpos, scale=0.62, facing='left', dorsal='female', swim=0.6, period=4.0, layer='mid'))
    s.add(Bubbles(pos=(700, 1000), rate=2, spread=200, layer='fg'))
    s.add(StatBox('AUGUST 2026', t0=L(s, 520.62)))
    s.add(Pill('OLDEST IN HER POD', 'orange', size=30, pos=(1250, 280), target=lambda t: (tpos(t)[0] - 40, tpos(t)[1] - 150), t0=L(s, 522.37)))
    s.add(Pill('GRANDMOTHER', 'dark', size=30, pos=(1250, 200), t0=L(s, 523.83)))
    s.add(Typewriter('TOÑI', size=110, cps=12, pos=(110, 960), t0=L(s, 524.66)))

    # 16 — fin close-up: marks
    plate = TintedSurface(DAWN_SOFT, waterline=820)
    s = new(plate, Camera(push=1.2, drift=(0, 0), wander=3), 'fin')
    fin = s.add(FinClose(pos=(980, 900), scale=1.15, layer='mid', marks_t=0.0))
    for i, tm in enumerate((526.21, 526.5, 526.85, 527.2)):
        mx, my = FinClose.MARKS[i]
        s.add(Reticle(r=34, pos=lambda lt, mx=mx, my=my: (980 + mx * 1.15, 900 + (my + 10 * math.sin((lt + L(s, tm)) * 0.9)) * 1.15),
                      layer='mid', z=3, t0=L(s, tm)))
    s.add(Label('WHAT LOOKED LIKE', size=30, font='bold', track=0.22, pos=(96, 150), t0=L(s, 526.21)))
    s.add(Label('PELLET-GUN WOUNDS', size=72, color=PAL.RED, pos=(96, 230), t0=L(s, 526.85), reveal='letters'))

    # 17 — matriarch: at least 90
    s = new(Underwater(depth=0.35), Camera(push=0.7, drift=(-5, 0)), 'ninety')
    s.add(Orca(pos=K((0, (1500, 620)), (s.dur, (1050, 600), 'linear')), scale=0.7, facing='left', dorsal='female',
               swim=0.7, period=3.8, layer='mid'))
    s.add(Label('FEMALE ORCAS', size=34, font='bold', track=0.22, pos=(110, 180), t0=0.1))
    s.add(Label('CAN LIVE TO AT LEAST', size=34, font='bold', track=0.22, pos=(110, 230), t0=L(s, 530.12)))
    s.add(Counter(0, 90, dur=0.6, size=200, pos=(330, 470), suffix='', unit='years', t0=L(s, 530.78) - 0.3,
                  color=PAL.ORANGE))
    s.add(Pill('LONG AFTER THEIR LAST CALF', 'dark', size=28, pos=(1350, 300), t0=L(s, 531.57)))

    # 18 — the grandmother leads the pod to salmon
    s = new(Underwater(depth=0.3), Camera(push=0.6, drift=(8, 0)), 'lead')
    lead = K((0, (300, 560)), (s.dur, (1150, 520), 'linear'))
    s.add(Orca(pos=lead, scale=0.42, facing='right', dorsal='female', layer='mid', z=3))
    for k, (dx, dy, sc) in enumerate(((-380, 120, 0.3), (-560, -60, 0.32), (-760, 160, 0.22), (-900, 20, 0.2))):
        s.add(Orca(pos=lambda lt, dx=dx, dy=dy: (lead(lt)[0] + dx, lead(lt)[1] + dy), scale=sc, facing='right',
                   phase=k * 0.8, layer='mid', z=2 - k * 0.1))
    s.add(FishSchool(pos=(1600, 520), n=60, radius=170, mode='ball', fish_len=30, layer='mid', z=1))
    s.add(Pill('GRANDMOTHER', 'orange', size=30, pos=lambda lt: (lead(lt)[0], 330),
               target=lambda t: (lead(t)[0], lead(t)[1] - 60), t0=L(s, 534.0)))
    s.add(Pill('SALMON', 'dark', size=30, pos=(1600, 280), target=(1600, 380), t0=L(s, 535.59)))
    s.add(Label('WHEN FOOD IS SCARCE', size=30, font='bold', track=0.22, align='center', pos=(960, 960),
                t0=L(s, 535.83)))

    # 19 — when she dies: grandchildren risk x4.5
    s = new(Board(particles=True), Camera(push=0.5, drift=(2, 0), wander=3), 'risk')
    s.add(CalfRow(n=5, t_die=L(s, 538.02), pos=(560, 340), t0=0.1))
    s.add(RiskBars(t_grow=L(s, 540.0) - L(s, 538.76), unit=150, pos=(560, 720), t0=L(s, 538.76)))
    s.add(Label('IN THE NEXT TWO YEARS', size=30, font='bold', track=0.22, pos=(560, 940), t0=L(s, 542.0)))
    s.add(Label('RISK OF DEATH', size=30, font='bold', track=0.22, color=PAL.CYAN, pos=(560, 600),
                t0=L(s, 538.76)))

    # 20 — Tahlequah carries her calf, 2018, 17 days
    plate = TintedSurface(DAWN_SOFT, waterline=380)
    s = new(plate, Camera(push=0.4, drift=(-3, 0), wander=3), 'tahlequah')
    mother_calf(s, plate, s.c, wl_y=700, scale=0.55, x0=1250, x1=930)
    s.add(StatBox('2018', t0=L(s, 546.4)))
    s.add(Label('TAHLEQUAH', size=72, pos=(110, 960), t0=L(s, 548.09), reveal='letters'))
    s.add(Counter(0, 17, dur=0.5, size=110, suffix=' DAYS', pos=(1500, 200), t0=L(s, 550.09) - 0.25,
                  color=PAL.WHITE))

    # 21 — route map ~1,600 km
    s = new(Board(particles=True), Camera(push=0.5, drift=(0, 0), wander=2), 'route')
    pts = [(260, 640), (420, 520), (600, 600), (760, 430), (940, 520), (1100, 380), (1280, 470), (1440, 360),
           (1640, 450)]

    def route(ctx, t):
        k = min(1, t / 2.6)
        segs = []
        tot = 0
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1]); segs.append((a, b, d)); tot += d
        rem = tot * k
        ctx.set_dash([18, 12]); set_col(ctx, PAL.ORANGE); ctx.set_line_width(6)
        ctx.move_to(*pts[0]); head = pts[0]
        for a, b, d in segs:
            if rem <= 0: break
            u = min(1, rem / d); head = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            ctx.line_to(*head); rem -= d
        ctx.stroke(); ctx.set_dash([])
        ctx.save(); ctx.translate(*head); icon(ctx, 'orca', 34, PAL.WHITE); ctx.restore()
    s.add(Fn(route, layer='mid'))
    s.add(DimensionLine((260, 820), (1640, 820), label='AROUND 1,600 KM', t0=L(s, 552.09), layer='mid'))
    s.add(Label('CARRYING HER CALF', size=30, font='bold', track=0.22, align='center', pos=(960, 200)))

    # 22 — end of 2024: a second calf, carried too (grey dawn)
    plate = TintedSurface(DAWN_GREY, waterline=380)
    s = new(plate, Camera(push=0.35, drift=(-3, 0), wander=3), 'second')
    mother_calf(s, plate, s.c, wl_y=700, scale=0.55, x0=1300, x1=960)
    s.add(StatBox('END OF 2024', t0=L(s, 554.52)))
    s.add(Label('SHE CARRIED THAT ONE TOO', size=40, font='bold', track=0.18, align='center', pos=(960, 980),
                t0=L(s, 558.28), reveal='fade', dur=0.5))

    # 23 — Champagne never made port: plank sinking in dark water
    s = new(Underwater(depth=0.85, rays=True), Camera(push=0.6, drift=(0, 3)), 'plank')
    s.add(HullPlank(w=460, pos=K((0, (900, 260)), (s.dur, (1000, 720), 'linear')),
                    rot=K((0, -8), (s.dur, 22, 'linear')), layer='mid'))
    s.add(Bubbles(pos=lambda lt: (900 + 100 * lt / 3.25, 300 + 140 * lt), rate=8, spread=120, layer='fg'))
    s.add(Pill('NEVER MADE IT INTO PORT', 'dark', size=32, pos=(960, 960), t0=L(s, 561.73)))

    # 24 — night: container ships + ferry, "mostly"
    plate = NightSurface(waterline=640)
    s = new(plate, Camera(push=0.4, drift=(-6, 0)), 'ships')
    s.add(ContainerShip(plate=plate, length=900, pos=K((0, (-300, 640)), (s.dur, (500, 640), 'linear')),
                        scale=0.8, layer='back'))
    s.add(Ferry(plate=plate, length=1300, pos=K((0, (2100, 660)), (s.dur, (1350, 660), 'linear')), scale=0.6,
                facing='left', layer='mid'))
    s.add(Label('WE DECIDE WHAT HAPPENS AT SEA?', size=52, align='center', pos=(960, 200), t0=L(s, 565.18),
                reveal='letters'))
    s.add(Pill('MOSTLY.', 'green', size=40, tick=True, pos=(960, 300), t0=L(s, 567.95)))

    # 25 — a sailboat in the Strait at night
    plate = NightSurface(waterline=640)
    s = new(plate, Camera(push=0.8, drift=(4, 0)), 'sail')
    s.add(Sailboat(plate=plate, pos=K((0, (700, 640)), (s.dur, (820, 640), 'linear')), scale=0.6, facing='right',
                   layer='mid', heel=4))
    s.add(StatBox('STRAIT OF GIBRALTAR', size=44, t0=L(s, 570.12)))

    # 26 — under the boat: three orcas pass the rudder
    plate = NightSurface(waterline=300)
    s = new(plate, Camera(push=0.6, drift=(0, 0), wander=3), 'rudder')
    boat = s.add(Sailboat(plate=plate, pos=(960, 300), scale=0.75, facing='right', layer='mid', z=1, heel=2))
    rp = boat.rudder_world(L(s, 576.02))
    for k, (dy, sc, d0) in enumerate(((180, 0.4, 0.0), (360, 0.34, 1.0), (260, 0.3, 1.9))):
        s.add(Orca(pos=K((0, (2100 + d0 * 260, rp[1] + dy + 120)), (s.dur, (rp[0] + 120 + d0 * 260, rp[1] + dy), 'linear')),
                   scale=sc, facing='left', phase=k, layer='mid', z=2))
    s.add(Pill('A FAMILY OF BLACK AND WHITE DOLPHINS', 'dark', size=30, pos=(960, 1000), t0=L(s, 571.64)))
    s.add(Reticle(r=60, pos=rp, layer='mid', z=4, t0=L(s, 576.02)))
    s.add(Pill('STEERING', 'red', size=30, pos=(rp[0] - 300, rp[1] + 150), target=rp, t0=L(s, 576.02)))

    # 27 — "I'd take the ferry"
    plate = Surface('day', waterline=700, sun=(0.7, 0.18))
    s = new(plate, Camera(push=1.0, drift=(0, 0)), 'ferry')
    fpos = K((0, (1150, 700)), (s.dur, (1000, 700), 'linear'))
    s.add(Ferry(plate=plate, length=1300, pos=fpos, scale=0.7, facing='right', layer='mid'))
    s.add(StickWaver(h=50, pos=lambda lt: (fpos(lt)[0] - 120, fpos(lt)[1] - 130 * 0.7 * 1.0 - 2), layer='mid', z=2))
    s.add(Punchline("I'D TAKE THE FERRY.", size=86, color=PAL.ORANGE, pos=(960, 200), t0=L(s, 577.49)))
    s.camera.shake(L(s, 577.88), amp=8, decay=0.3)

    # 28 — thanks for watching
    s = new(Underwater(depth=0.3), Camera(push=0.6, drift=(-6, 0)), 'thanks')
    s.add(Orca(pos=K((0, (2100, 640)), (s.dur, (700, 600), 'linear')), scale=0.55, facing='left', layer='mid'))
    s.add(Label('THANKS FOR WATCHING', size=80, align='center', pos=(960, 300), t0=L(s, 579.47), reveal='letters'))

    # 29 — comment box
    s = new(Board(particles=True), Camera(push=0.4, drift=(0, 0), wander=2), 'comment')
    s.add(Label('WHICH ANIMAL SHOULD WE COVER NEXT?', size=48, align='center', pos=(960, 260), t0=L(s, 581.83),
                reveal='letters'))
    s.add(CommentBox(text='Do the leopard seal next', cps=12, t_type=1.0, pos=(960, 560), t0=0.2))
    s.add(Pill('COMMENT BELOW', 'orange', size=36, pos=(960, 840), t0=L(s, 584.61)))
    s.add(OrcaBelow(pos=K((0, (200, 1000)), (s.dur, (1700, 980), 'linear')), scale=0.6, layer='back', rot=-80,
                    opacity=0.25))

    # 30 — heart: read
    s = new(Board(particles=True), Camera(push=1.0, drift=(0, 0), wander=2), 'read')
    s.add(CommentBox(text='Do the leopard seal next', cps=200, t_type=-1, t_heart=L(s, 586.95), pos=(960, 560)))
    s.add(Label('I DO ACTUALLY READ THEM', size=44, font='bold', track=0.14, align='center', pos=(960, 300),
                t0=L(s, 586.54)))

    # 31 — end card
    s = new(Underwater(depth=0.4), Camera(push=0.25, drift=(0, 0), wander=2), 'endcard')
    s.add(Orca(pos=K((0, (-500, 860)), (s.dur, (2300, 820), 'linear')), scale=0.4, facing='right', layer='back'))
    s.add(VideoCard(w=620, h=350, label='WATCH NEXT', seed=1, pos=(560, 470), t0=0.15))
    s.add(VideoCard(w=620, h=350, label='MORE FROM THE DEEP', seed=2, pos=(1360, 470), t0=0.3))
    s.add(SubscribeButton(t_click=2.6, pos=(960, 820), t0=0.5))
    s.add(fade_out(s.dur - 0.8, 0.8))

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-6, sum(x.dur for x in shots)
    assert len(shots) == len(D)
    return shots
