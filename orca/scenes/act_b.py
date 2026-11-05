"""Act B — chapters 1 SIZE + 2 MENU. Absolute range [91.60, 224.50).
Render: python -m engine.render scenes.act_b renders/act_b.mp4 --words audio/words.json
"""
import math
from engine import *
from engine.core import Element
from scenes.assets_b import (NavChapterTitle, FadeIn, Dolphin, StrikeLabel, DorsalFin, BalanceRig, SplitFlap,
                             PinGlobe, CallWave, House, Envelope, Beach, WaveCrest, ChalkSign, TopFloe, Reticle,
                             MenuCard, draw_glasses, Tooth, Ruler, ZipJaws, ZipStrip, SoundRings, SpeechBubble,
                             HeartX, orca_nose, icon as nav_icon)

T_START, T_END = 91.60, 224.50
CUTS = [91.60, 94.60, 98.85, 104.15, 108.55, 113.10, 115.10, 118.30, 120.65, 122.55, 125.95, 127.98,
        131.60, 135.10, 141.55, 143.60, 145.95, 149.45, 153.95, 158.70, 161.35, 163.25, 169.95, 173.10,
        177.30, 180.25, 182.45, 187.95, 191.25, 196.15, 200.25, 205.25, 211.80, 215.90, 218.30, 222.80, T_END]

CRAB = '#B8AC9C'      # crabeater seal (pale)
WEDDELL = '#4F5A66'   # Weddell seal (dark)


def _shot(i, plate, camera=None, name='', trans_in=None):
    s = Shot(round(CUTS[i + 1] - CUTS[i], 4), plate=plate, camera=camera or Camera(), name=name, trans_in=trans_in)
    s._c0 = CUTS[i]
    return s


def lt(s, t_abs):
    """absolute VO time -> shot-local"""
    return round(t_abs - s._c0, 3)


class Half(Element):
    """renders `el` clipped to its left half (half an elephant)."""
    def __init__(self, el, keep=0.5, x0=0, x1=320, **kw):
        super().__init__(**kw); self.el, self.k, self.x0, self.x1 = el, keep, x0, x1
    def draw(self, ctx, t):
        ctx.save(); ctx.rectangle(-2000, -2000, 2000 + self.x0 + (self.x1 - self.x0) * self.k, 4000); ctx.clip()
        self.el.render(ctx, t); ctx.restore()


class Clip(Element):
    """renders `el` clipped to a rounded box (x, y, w, h) in parent coords."""
    def __init__(self, el, box, **kw):
        super().__init__(**kw); self.el, self.box = el, box
    def draw(self, ctx, t):
        x, y, w, h = self.box
        ctx.save(); rrect(ctx, x, y, w, h, 24); ctx.clip(); self.el.render(ctx, t); ctx.restore()
        rrect(ctx, x, y, w, h, 24); set_col(ctx, PAL.WHITE, 0.35); ctx.set_line_width(3); ctx.stroke()


class Beach2(Beach):
    """Beach with the seabed edge off-screen; shoreline near x=1210."""
    def __init__(self, wl=640, **kw):
        super().__init__(wl=wl, x_water=200, **kw)
    def y_at(self, x):
        k = (x + 300) / (W + 900)
        return self.wl + 300 - k * 560


BY = Beach2(wl=640).y_at


class Glasses(Element):
    def draw(self, ctx, t):
        draw_glasses(ctx, 0, 0, 1.7)


def build(words=None):
    S = []

    # 0 ── chapter card 1/6 SIZE (fade from black)
    s = _shot(0, Board(), Camera(push=0.6, drift=(-6, 0), wander=3), 'ch1')
    s.abs_start = T_START
    s.add(Orca(pos=K((0, (1500, 430)), (3.0, (1300, 420), 'linear')), scale=0.62, variant='xray', swim=0.8))
    s.add(DimensionLine((1190, 600), (1810, 600), label='', t0=0.6))
    s.add(NavChapterTitle('SIZE', 'HOW BIG IT REALLY IS', 1, t0=lt(s, 92.0)))
    s.add(FadeIn(0.5))
    S.append(s)

    # 1 ── dolphin line-up
    s = _shot(1, Underwater(depth=0.25, seed=5), Camera(push=0.7, drift=(-8, 0)), 'lineup')
    xs = [(Dolphin('bottlenose', pos=K((0, (330, 640)), (4.3, (290, 640), 'linear')), scale=0.26, phase=0.3)),
          (Dolphin('risso', pos=K((0, (650, 630)), (4.3, (610, 630), 'linear')), scale=0.33, phase=1.1)),
          (Dolphin('pilot', pos=K((0, (1010, 620)), (4.3, (970, 620), 'linear')), scale=0.42, phase=0.6))]
    for d in xs: s.add(d)
    s.add(Orca(pos=K((0, (1530, 600)), (4.3, (1480, 600), 'linear')), scale=0.6, swim=1.0))
    s.add(FishSchool(pos=(1500, 230), n=40, radius=120, mode='stream', fish_len=22, layer='back', scale=0.7))
    s.add(Bubbles(pos=(240, 1000), rate=2, spread=40, layer='fg'))
    s.add(StrikeLabel('WHALE', size=96, t_strike=lt(s, 95.2) - lt(s, 94.78), pos=(1480, 290), t0=lt(s, 94.78)))
    s.add(Pill('DOLPHIN', 'orange', size=40, pos=(1480, 390), target=(1440, 540), t0=lt(s, 95.95)))
    s.add(Pill('DOLPHIN', 'dark', size=24, pos=(300, 520), t0=lt(s, 96.1)))
    s.add(Pill('DOLPHIN', 'dark', size=24, pos=(620, 500), t0=lt(s, 96.2)))
    s.add(Pill('DOLPHIN', 'dark', size=24, pos=(980, 480), t0=lt(s, 96.3)))
    s.add(Label('THE LARGEST DOLPHIN', size=64, align='center', pos=(960, 930), t0=lt(s, 97.07), reveal='wipe'))
    s.camera.emphasis(lt(s, 97.1), lt(s, 98.8), 0.15, target=(1350, 600))
    S.append(s)

    # 2 ── x-ray orca: 9.8 m, ~10 tonnes
    s = _shot(2, Board(), Camera(push=0.6, drift=(4, 0), wander=3), 'xray')
    s.add(Orca(pos=(960, 560), scale=1.05, variant='xray', swim=0.6))
    s.add(StatBox('LARGEST EVER RECORDED', t0=0.15, size=44))
    s.add(DimensionLine((435, 820), (1485, 820), label='9.8 M', sub='LONG', t0=lt(s, 100.30), size=56))
    s.add(Counter(0, 10, dur=0.7, prefix='~', suffix=' TONNES', size=96, pos=(1500, 230), t0=lt(s, 102.67) - 0.1,
                  unit='weight'))
    S.append(s)

    # 3 ── balance: 1.5 male elephants
    s = _shot(3, Board(), Camera(push=0.5, drift=(0, 0), wander=3), 'balance')
    e1 = Elephant(height=200, t0=lt(s, 104.80))
    e2 = Half(Elephant(height=200), keep=0.5, x0=58 * 200 / 320, x1=518 * 200 / 320, t0=lt(s, 105.09))
    orca_small = Orca(scale=0.34, swim=0.8)
    t_e1, t_e2 = lt(s, 104.80), lt(s, 105.09)
    tilt = K((0, 22), (t_e1, 22), (t_e1 + 0.3, 12, 'eo'), (t_e2, 12), (t_e2 + 0.35, 6, 'eo'), (4.4, 6))
    s.add(BalanceRig(tilt=tilt, width=980, pos=(960, 430),
                     left_items=[(e1, (-150, -10)), (e2, (20, -10))],
                     right_items=[(orca_small, (0, -40))]))
    s.add(Label('1½ MALE ELEPHANTS', size=56, align='center', pos=(560, 200), t0=lt(s, 105.3), reveal='wipe'))
    s.add(Pill('ONE ORCA', 'orange', size=34, pos=(1400, 200), t0=0.2))
    s.add(Punchline('…STILL A DOLPHIN.', size=84, pos=(960, 960), t0=lt(s, 107.38)))
    s.camera.shake(lt(s, 107.38), amp=10)
    S.append(s)

    # 4 ── dorsal fin vs person
    s = _shot(4, Board(), Camera(push=0.6, drift=(-3, 0), wander=3), 'fin')
    s.add(DorsalFin(height=560, pos=(820, 900), sway=1.0))
    s.add(Person(height=500, pos=(1200, 900), color='#DDE3E3'))
    s.add(Fn(lambda ctx, t: (ctx.move_to(380, 900), ctx.line_to(1540, 900), set_col(ctx, PAL.WHITE, 0.5),
                             ctx.set_line_width(3), ctx.stroke()), layer='mid'))
    s.add(DimensionLine((560, 900), (560, 340), label='1.8 M', t0=lt(s, 110.22), size=52))
    s.add(Pill('MALE DORSAL FIN', 'dark', size=30, pos=(820, 240), target=(800, 420), t0=lt(s, 109.08)))
    s.add(Label('TALLER THAN MOST PEOPLE', size=54, align='center', pos=(1200, 1010), t0=lt(s, 111.36), reveal='wipe'))
    s.add(Pill('YOU', 'grey', size=28, pos=(1380, 380), target=(1230, 430), t0=lt(s, 112.3)))
    S.append(s)

    # 5 ── x-ray fin: no bones
    s = _shot(5, Board(), Camera(push=1.2, drift=(0, 0), wander=2), 'finxray')
    s.add(DorsalFin(height=640, pos=(900, 960), xray=True, scan=0.9))
    s.add(Label('CARTILAGE + COLLAGEN', size=34, font='bold', track=0.2, pos=(1180, 700), t0=0.3))
    s.add(Stamp('BONES: 0', PAL.RED, 92, pos=(1380, 420), t0=lt(s, 113.97)))
    S.append(s)

    # 6 ── crash zoom on the jaw, 56 teeth
    s = _shot(6, Underwater(depth=0.3, seed=7), Camera(push=0.6, drift=(-6, 0)), 'mouth')
    jt = lt(s, 115.95)
    opos = K((0, (1150, 560)), (3.2, (1080, 560), 'linear'))
    s.add(Orca(pos=opos, scale=1.0, jaw=K((0, 0), (jt - 0.1, 0), (jt + 0.3, 28, 'eo'), (3.2, 26)), swim=0.5))
    s.camera.crash(jt, dur=0.25, amount=1.25, target=(700, 590))
    s.add(Counter(0, 56, dur=0.9, prefix='UP TO ', suffix=' TEETH', size=92, pos=(1260, 210), t0=lt(s, 117.12) - 0.05))
    s.add(Bubbles(pos=(1600, 1000), rate=3, spread=60, layer='fg'))
    S.append(s)

    # 7 ── tooth on a ruler
    s = _shot(7, Board(), Camera(push=0.8, drift=(0, -2), wander=2), 'tooth')
    s.add(Ruler(cm=12, px_per_cm=48, pos=(1040, 920)))
    s.add(Tooth(L=480, pos=(900, 920), rot=lambda t: 2 * math.sin(t * 1.6)))
    s.add(Fn(lambda ctx, t: (ctx.move_to(780, 440), ctx.line_to(1060, 440), set_col(ctx, PAL.ORANGE),
                             ctx.set_line_width(4), ctx.set_dash([12, 8]), ctx.stroke(), ctx.set_dash([])),
             layer='mid', t0=lt(s, 119.08)))
    s.add(Label('UP TO ~10 CM', size=80, pos=(1220, 470), t0=lt(s, 119.08), reveal='wipe'))
    s.add(Label('EACH', size=34, font='bold', track=0.22, pos=(1224, 380), t0=lt(s, 118.36)))
    S.append(s)

    # 8 ── interlock like a zip
    s = _shot(8, Black(particles=True), Camera(push=0.8, drift=(0, 0), wander=2), 'zip')
    tz = lt(s, 121.76)
    s.add(Clip(ZipJaws(t_close=tz - 0.35, n=9, width=1500, gap_open=320, pos=(960, 420), scale=0.75), (330, 130, 1260, 580)))
    s.add(ZipStrip(length=1100, dur=0.8, pos=(960, 850), t0=tz - 0.8))
    s.add(Pill('INTERLOCK', 'cyan', size=34, pos=(960, 90), t0=lt(s, 120.88)))
    s.add(Label('LIKE A ZIP', size=64, align='center', pos=(960, 1010), t0=tz))
    S.append(s)

    # 9 ── not for chewing / for holding on
    s = _shot(9, Black(particles=True), Camera(push=1.0, drift=(0, 0), wander=2), 'holding')
    s.add(Orca(pos=K((0, (2300, 640)), (3.4, (-400, 610), 'linear')), scale=0.9, variant='silhouette', layer='back',
               opacity=0.55))
    s.add(Label('NOT', size=60, align='center', pos=(960, 330), t0=lt(s, 122.78)))
    s.add(StrikeLabel('FOR CHEWING', size=110, t_strike=0.4, pos=(960, 500), t0=lt(s, 123.2)))
    s.add(Punchline('…FOR HOLDING ON.', size=110, pos=(960, 760), t0=lt(s, 124.48)))
    s.camera.shake(lt(s, 125.04), amp=12)
    S.append(s)

    # 10 ── orca swims head-on into the lens
    s = _shot(10, Underwater(depth=0.4, seed=9), Camera(push=0.5, drift=(0, 0)), 'headon')
    s.add(OrcaHeadOn(pos=K((0, (960, 560)), (2.03, (960, 600), 'linear')), scale=K((0, 0.35), (2.03, 3.4, 'ei')),
                     jaw=K((0, 0), (1.0, 0), (1.7, 0.8, 'eo'))))
    s.add(Bubbles(pos=(400, 1000), rate=4, spread=80, layer='fg'))
    s.add(Bubbles(pos=(1500, 1000), rate=4, spread=80, layer='fg', seed=3))
    S.append(s)

    # 11 ── chapter card 2/6 MENU
    s = _shot(11, Board(), Camera(push=0.6, drift=(6, 0), wander=3), 'ch2', trans_in=('dip', 0.7))
    prey = ['SALMON', 'SEALS', 'SHARKS', 'HERRING', 'WHALES']
    picons = ['fish', 'seal', 'fin', 'fish', 'orca']
    for i in range(5):
        x = 330 + i * 315
        s.add(Orca(pos=(x, 450 + 14 * math.sin(i)), scale=0.24, variant='xray', swim=0.9, phase=i * 0.6))
        s.add(Fn(lambda ctx, t, n=picons[i]: icon(ctx, n, 34), pos=(x, 290), layer='mid', t0=0.5 + 0.12 * i))
        s.add(Label(prey[i], size=24, font='bold', track=0.22, align='center', pos=(x, 360), t0=0.5 + 0.12 * i))
    s.add(NavChapterTitle('MENU', 'EVERY FAMILY HAS A RECIPE', 2, t0=0.3))
    S.append(s)

    # 12 ── split-flap: it depends which orca you ask
    s = _shot(12, Underwater(depth=0.3, seed=11), Camera(push=0.6, drift=(-4, 0)), 'flap')
    s.add(Orca(pos=K((0, (2100, 820)), (3.5, (-300, 800), 'linear')), scale=0.4, layer='back', swim=1.1))
    s.add(SplitFlap([(0.1, 'SALMON'), (0.45, 'SEALS'), (0.8, 'SHARK LIVER'), (lt(s, 132.83), 'IT DEPENDS')],
                    header="TODAY'S SPECIAL", pos=(960, 430)))
    s.add(Label('…WHICH ORCA YOU ASK', size=56, align='center', pos=(960, 700), t0=lt(s, 133.12), reveal='wipe'))
    S.append(s)

    # 13 ── globe of ecotypes
    s = _shot(13, Black(particles=True), Camera(push=0.4, drift=(0, 0), wander=2), 'globe')
    tp = lt(s, 136.60)
    pins = [(-125, 49), (-150, 58), (-64, -42), (-60, -65), (-20, 64), (-170, -75), (-95, -72), (-40, -60), (-135, 30), (-10, 45)]
    s.add(PinGlobe(timed_pins=[(lo, la, tp + 0.12 * k) for k, (lo, la) in enumerate(pins)], center=(-85, 15), radius=360,
                   spin=4, pos=(1260, 560)))
    s.add(Counter(0, 10, dur=1.0, prefix='AT LEAST ', size=78, pos=(470, 470), t0=tp - 0.05, unit='types of orca'))
    s.add(Pill('ECOTYPES', 'orange', size=44, pos=(470, 620), t0=lt(s, 138.20)))
    s.add(Label('COMPLETELY DIFFERENT MENUS', size=34, font='bold', track=0.2, align='center', pos=(470, 760),
                t0=lt(s, 139.6)))
    S.append(s)

    # 14 ── zoom on Washington / British Columbia
    s = _shot(14, Black(particles=True), Camera(push=0.5, drift=(0, 0), wander=2), 'pnw')
    s.add(PinGlobe(timed_pins=[(-124, 48.5, 0.35)], center=(-110, 40), radius=360, spin=-3, pos=(1180, 640),
                   R_track=K((0, 360), (2.0, 450, 'eio'))))
    s.add(StatBox('WASHINGTON & BRITISH COLUMBIA', t0=lt(s, 141.74), size=46))
    S.append(s)

    # 15 ── fish-eaters
    s = _shot(15, Underwater(depth=0.25, seed=13), Camera(push=0.8, drift=(-10, 0)), 'salmon')
    fish_pos = K((0, (700, 560)), (2.35, (350, 570), 'linear'))
    s.add(FishSchool(pos=fish_pos, n=36, radius=140, mode='stream', fish_len=46, color='#D9A79A', back='#5D6F78'))
    s.add(Orca(pos=K((0, (1500, 590)), (2.35, (1050, 580), 'linear')), scale=0.62, swim=1.3, period=2.2,
               jaw=K((0, 0), (1.2, 0), (1.5, 12), (1.8, 0))))
    s.add(Pill('MOSTLY SALMON', 'dark', size=30, pos=(520, 330), target=(560, 520), t0=lt(s, 144.52)))
    s.add(Pill('FISH-EATERS', 'green', size=44, pos=(1300, 260), t0=lt(s, 144.88)))
    S.append(s)

    # 16 ── same water: mammal-hunters
    s = _shot(16, Underwater(depth=0.3, seed=15), Camera(push=0.6, drift=(-4, 0)), 'mammal')
    s.add(FishSchool(pos=(400, 300), n=30, radius=110, mode='stream', fish_len=34, color='#D9A79A', back='#5D6F78',
                     layer='back'))
    s.add(Orca(pos=K((0, (700, 330)), (3.5, (560, 320), 'linear')), scale=0.36, layer='back', swim=1.0))
    s.add(Pill('FISH-EATERS', 'green', size=26, pos=(700, 170), t0=0.1))
    s.add(Seal(pos=K((0, (900, 760)), (3.5, (380, 780), 'linear')), scale=0.6, look=K((0, 0), (1.0, 1), (2, 0.3))))
    s.add(Dolphin('pilot', pos=K((0, (1150, 900)), (3.5, (650, 900), 'linear')), scale=0.16, color=None)
          if False else Dolphin('bottlenose', pos=K((0, (1150, 900)), (3.5, (660, 910), 'linear')), scale=0.17))
    s.add(Orca(pos=K((0, (2200, 790)), (3.5, (1250, 800), 'linear')), scale=0.62, swim=1.3, period=2.0,
               jaw=K((0, 0), (2.4, 0), (2.8, 16), (3.3, 6))))
    s.add(Pill('MAMMAL-HUNTERS', 'red', size=44, pos=(1300, 560), t0=lt(s, 146.66)))
    s.add(Pill('SEALS', 'dark', size=28, pos=(700, 620), target=(700, 740), t0=lt(s, 147.66)))
    s.add(Pill('PORPOISES', 'dark', size=28, pos=(900, 1010), target=(850, 920), t0=lt(s, 148.36)))
    s.add(Label('SAME WATER', size=34, font='bold', track=0.22, pos=(96, 100), t0=lt(s, 146.56)))
    S.append(s)

    # 17 ── no interbreeding, own dialects
    s = _shot(17, Underwater(depth=0.35, seed=17), Camera(push=0.5, drift=(0, 0)), 'dialect')
    s.add(Orca(pos=(470, 700), scale=0.5, facing='right', swim=1.0))
    s.add(Orca(pos=(330, 820), scale=0.3, facing='right', dorsal='female', swim=1.1, phase=0.7))
    s.add(Orca(pos=(1450, 700), scale=0.5, facing='left', swim=1.0, phase=0.4))
    s.add(Orca(pos=(1600, 830), scale=0.3, facing='left', dorsal='female', swim=1.1, phase=1.3))
    s.add(HeartX(r=60, t_x=0.35, pos=(960, 640), t0=lt(s, 149.72)))
    s.add(Label('NOT KNOWN TO INTERBREED', size=48, align='center', pos=(960, 820), t0=lt(s, 150.16)))
    s.add(SoundRings(direction=-60, pos=(720, 640), t0=lt(s, 152.40) - 0.2))
    s.add(SoundRings(direction=-120, pos=(1200, 640), color=PAL.CYAN, t0=lt(s, 152.40)))
    s.add(CallWave('DIALECT A', PAL.ORANGE, seed=1, pos=(560, 340), t0=lt(s, 152.40) - 0.2))
    s.add(CallWave('DIALECT B', PAL.CYAN, seed=7, pos=(1360, 340), t0=lt(s, 152.40) + 0.1))
    S.append(s)

    # 18 ── paper street: never once eaten at each other's house
    s = _shot(18, Sepia(), Camera(push=0.5, drift=(0, 0), wander=2), 'street')
    s.add(Fn(lambda ctx, t: (ctx.move_to(0, 905), ctx.line_to(1920, 905), set_col(ctx, '#2A2F30'),
                             ctx.set_line_width(5), ctx.stroke()), layer='mid'))
    s.add(House(pos=(470, 905), scale=0.95, seed=1))
    s.add(House(pos=(1450, 905), scale=0.95, wall='#C9D6C9', roof='#3F6E7A', door='#A9483B', seed=2))
    s.add(Label('SAME STREET', size=40, font='black', color='#2A2F30', align='center', pos=(960, 150),
                t0=lt(s, 155.18), shadow=False))
    t_r = lt(s, 157.74)
    env_pos = K((0, (640, 760)), (0.5, (640, 760)), (t_r - 0.2, (1220, 700), 'eio'), (t_r + 0.5, (1220, 700)),
                (4.75, (760, 760), 'eio'))
    s.add(Envelope(title='DINNER INVITE', pos=env_pos, rot=lambda t: 4 * math.sin(t * 2.2), scale=0.9, t0=0.3))
    s.add(Stamp('RETURN TO SENDER', PAL.RED, 56, pos=(1150, 560), t0=t_r))
    S.append(s)

    # 19 ── every menu comes with recipes
    s = _shot(19, Sepia(), Camera(push=0.8, drift=(0, 0), wander=2), 'recipes')
    s.add(MenuCard('HOUSE RECIPES', items=[('SALMON', None, None), ('SEALS', None, None), ('SEA LION PUPS', None, lt(s, 160.18))],
                   pos=K((0, (960, 1400)), (0.4, (960, 560), 'eo')), rot=lambda t: -3 + 1.5 * math.sin(t * 1.4)))
    s.add(Label('EVERY MENU…', size=44, font='black', color='#2A2F30', pos=(110, 150), t0=lt(s, 158.86), shadow=False))
    s.add(Stamp('+ RECIPES', PAL.RED, 64, pos=(1480, 300), t0=lt(s, 160.18)))
    S.append(s)

    # 20 ── globe: Punta Norte, Argentina
    s = _shot(20, Black(particles=True), Camera(push=0.5, drift=(0, 0), wander=2), 'punta')
    s.add(PinGlobe(timed_pins=[(-63.9, -42.1, 0.25)], center=(-75, -25), radius=380, spin=-4, pos=(960, 600),
                   R_track=K((0, 380), (1.9, 500, 'eio'))))
    s.add(StatBox('PUNTA NORTE', sub='ARGENTINA', t0=lt(s, 161.52), t_sub=lt(s, 162.98) - lt(s, 161.52), size=52))
    S.append(s)

    # 21 ── beach stranding: ride wave, grab pup, roll back out
    plate = Surface('day', waterline=640, sun=(0.75, 0.16))
    s = _shot(21, plate, Camera(push=0.4, drift=(0, 0), wander=3), 'beach')
    beach = s.add(Beach2(wl=640, z=0))
    t_w, t_b, t_g, t_g2, t_r = lt(s, 163.66), lt(s, 164.84), lt(s, 165.40), lt(s, 166.44), lt(s, 167.92)
    s.add(WaveCrest(K((0, 100), (t_w, 380), 'linear', ), wl=640, height=80, width=380, z=1) if False else
          WaveCrest(K((0, -200), (t_b + 0.2, 1250, 'eo'), (t_b + 1.5, 1320, 'linear')), wl=640, height=110, width=440, z=1,
                    opacity=K((0, 1), (t_b + 0.3, 1), (t_b + 1.2, 0))))
    s.add(WaveCrest(K((t_r - 0.8, -200), (t_r + 0.4, 1150, 'eo'), (6.7, 1250, 'linear')), wl=640, height=90, width=420, z=1,
                    opacity=K((0, 0), (t_r - 0.8, 0), (t_r - 0.6, 1), (t_r + 0.6, 1), (t_r + 1.4, 0))))
    ok = K((0, (-250, 700)), (t_b, (1150, 640), 'eo'), (t_g2 + 0.3, (1180, 632)), (t_r, (1180, 636)),
           (t_r + 1.4, (650, 720), 'eio'), (6.7, (200, 760), 'linear'))
    orot = K((0, 0), (t_b - 0.4, -6), (t_b, -14, 'eo'), (t_r, -14), (t_r + 0.6, 4, 'eio'), (6.7, 6))
    s.add(Orca(pos=ok, rot=orot, scale=0.48, facing='right', z=3, swim=K((0, 1), (t_b, 0.2), (t_r, 0.2), (t_r + 0.5, 1)),
               jaw=K((0, 0), (t_g - 0.25, 0), (t_g, 24, 'eo'), (t_g + 0.45, 4, 'ei'), (6.7, 4))))
    pup0 = (1440, BY(1440) + 2)
    def pup_pos(t):
        if t < t_g + 0.4: return pup0
        n = orca_nose(ok(t), 0.48, orot(t), 'right')
        return (n[0] - 30, n[1] + 30)
    s.add(Seal(pos=pup_pos, scale=0.34, facing='left', z=4, look=K((0, 0), (t_g - 0.5, 1), (t_g + 0.4, 0.2)),
               rot=lambda t: -8 if t < t_g + 0.4 else orot(t) - 20))
    s.add(Splash(size=240, pos=(1150, 650), t0=t_b - 0.05))
    s.add(Splash(size=220, pos=(900, 660), t0=t_r + 0.7, seed=4))
    s.add(Pill('WAVE', 'cyan', size=30, pos=(500, 470), target=(560, 560), t0=t_w, t1=t_b + 0.8))
    s.add(Pill('SEA LION PUP', 'orange', size=30, pos=(1500, 440), target=(1430, 590), t0=lt(s, 165.86), t1=t_r))
    s.add(Pill('ROLL BACK OUT', 'dark', size=30, pos=(560, 460), t0=t_r + 0.1))
    s.add(StatBox('PUNTA NORTE', t0=0.1, size=40))
    S.append(s)

    # 22 ── beach lessons: practice attacks with the young
    plate = Surface('day', waterline=640, sun=(0.75, 0.16))
    s = _shot(22, plate, Camera(push=0.5, drift=(-3, 0), wander=3), 'lessons')
    s.add(Beach2(wl=640, z=0))
    s.add(ChalkSign('BEACH LESSONS', pos=(1700, BY(1700) - 110), scale=0.9, z=1))
    s.add(Orca(pos=K((0, (300, 720)), (3.15, (420, 715), 'linear')), scale=0.46, facing='right', z=2, swim=1.0))
    s.add(Orca(pos=K((0, (520, 760)), (1.1, (1000, 690), 'eo'), (1.7, (1030, 685)), (2.6, (640, 760), 'eio'),
                     (3.15, (700, 740))), rot=K((0, 0), (1.1, -10), (1.7, -10), (2.6, 4)), scale=0.24, facing='right',
               dorsal='female', z=3, swim=1.3, period=1.6))
    s.add(Splash(size=150, pos=(1040, 650), t0=1.0))
    s.add(Pill('PRACTICE ATTACKS', 'orange', size=36, pos=(900, 470), target=(1000, 640), t0=lt(s, 170.84)))
    s.add(Pill('THE YOUNG', 'dark', size=26, pos=(560, 930), target=(650, 790), t0=lt(s, 172.24)))
    S.append(s)

    # 23 ── human parent: stay out of the water
    plate = Surface('day', waterline=640, sun=(0.3, 0.16))
    s = _shot(23, plate, Camera(push=0.6, drift=(0, 0), wander=3), 'humans')
    s.add(Beach2(wl=640, z=0))
    s.add(Human(pos=(1640, BY(1640)), scale=1.0, pose='wave', facing='left', coat='#D96B4B',
                hat=None, z=2))
    kid = K((0, (1120, BY(1120) + 40)), (1.8, (1120, BY(1120) + 40)), (4.2, (1380, BY(1380)), 'eio'))
    s.add(Human(pos=kid, scale=0.55, pose='stand', facing='right', coat='#F0A54A', hat=None, z=2))
    s.add(Fn(lambda ctx, t: None))
    s.add(SpeechBubble('OUT OF THE WATER!', size=36, pos=(1520, 160), t0=lt(s, 174.56)))
    s.add(Pill('MOST PARENTS', 'dark', size=28, pos=(240, 160), t0=lt(s, 173.22)))
    S.append(s)

    # 24 ── orca parent teaches the calf to leave it
    plate = Surface('day', waterline=640, sun=(0.75, 0.16))
    s = _shot(24, plate, Camera(push=0.8, drift=(0, 0), wander=3), 'teach')
    s.add(Beach2(wl=640, z=0))
    calf = K((0, (620, 720)), (1.6, (1120, 650), 'eo'), (2.95, (1150, 645)))
    s.add(Orca(pos=calf, rot=K((0, -4), (1.6, -12)), scale=0.26, facing='right', dorsal='female', z=3, swim=K((0, 1.2), (1.6, 0.3))))
    s.add(Orca(pos=K((0, (250, 740)), (1.6, (760, 700), 'eo'), (2.95, (800, 700))), rot=K((0, -2), (1.6, -8)), scale=0.46,
               facing='right', z=2, swim=1.0))
    s.add(Splash(size=150, pos=(1100, 650), t0=1.4))
    s.add(Pill('THESE ONES', 'orange', size=28, pos=(400, 470), target=(700, 640), t0=lt(s, 177.38)))
    s.add(Punchline('…HOW TO LEAVE IT.', size=88, pos=(960, 960), t0=lt(s, 178.62)))
    s.camera.shake(lt(s, 179.26), amp=10)
    S.append(s)

    # 25 ── globe: Antarctica, 2009
    s = _shot(25, Black(particles=True), Camera(push=0.5, drift=(0, 0), wander=2), 'antarctica')
    s.add(PinGlobe(timed_pins=[(-64, -66, 0.3)], center=(-60, -45), radius=380, spin=-4, pos=(960, 600),
                   R_track=K((0, 380), (2.2, 470, 'eio'))))
    s.add(StatBox('ANTARCTICA', sub='2009', t0=lt(s, 180.42), t_sub=lt(s, 181.46) - lt(s, 180.42), size=56))
    S.append(s)

    # 26 ── seal on a floe, ~75 hours of watching
    plate = Surface('haze', waterline=650, sun=(0.3, 0.2))
    s = _shot(26, plate, Camera(push=0.5, drift=(-4, 0), wander=3), 'floe')
    seal = Seal(pos=(0, -44), scale=0.55, facing='left', look=K((0, 0), (2.5, 0), (3.0, 1), (4.0, 0.2)))
    s.add(IceFloe(width=640, plate=plate, pos=(1060, 650), z=1, children=[seal]))
    s.add(DorsalFin(height=90, pos=K((0, (300, 652)), (5.5, (700, 652), 'linear')), z=2))
    s.add(DorsalFin(height=60, pos=K((0, (1700, 652)), (5.5, (1480, 652), 'linear')), scale=(-1, 1), z=2))
    s.add(Counter(0, 75, dur=1.0, prefix='~', suffix=' HOURS', size=90, pos=(960, 230), t0=lt(s, 183.58) - 0.05,
                  unit='of watching'))
    s.add(Pill('SEAL', 'dark', size=28, pos=(1250, 470), target=(1060, 590), t0=lt(s, 185.98)))
    s.add(Pill('FLOATING ICE', 'cyan', size=28, pos=(1350, 830), target=(1250, 690), t0=lt(s, 186.72)))
    S.append(s)

    # 27 ── top-down: line up side by side, charge
    s = _shot(27, TopDown(), Camera(push=0.6, drift=(0, 0), wander=2), 'charge')
    s.add(TopFloe(r=230, pos=(1520, 540)))
    tc = lt(s, 190.14)
    for k in range(4):
        y = 330 + k * 140
        s.add(OrcaTop(pos=K((0, (-200 - 120 * (k % 2), y + 60 * (k - 1.5))), (lt(s, 188.9), (330, y), 'eo'),
                            (tc, (420, y), 'linear'), (3.3, (1120, y), 'ei')),
                      rot=180, scale=0.3, period=1.4))
    s.add(Pill('SIDE BY SIDE', 'dark', size=30, pos=(420, 150), t0=lt(s, 188.86)))
    s.add(Pill('CHARGE', 'red', size=40, pos=(960, 150), t0=tc))
    s.add(SpeedLines(pos=(700, 540), t0=tc) if hasattr(fx, 'SpeedLines') else Fn(lambda c, t: None))
    S.append(s)

    # 28 ── cross-section: dive under, push the wave, seal washed off
    plate = Surface('haze', waterline=520, sun=(0.3, 0.2))
    s = _shot(28, plate, Camera(push=0.5, drift=(0, 0), wander=3), 'washoff')
    td, tw, ts0, ts1 = lt(s, 191.42), lt(s, 193.56), lt(s, 194.72), lt(s, 195.42)
    floe_tilt = K((0, 0), (tw, 0), (tw + 0.6, 9, 'eo'), (ts1, 12), (4.9, 3, 'eio'))
    s.add(IceFloe(width=620, plate=plate, pos=(1250, 520), tilt=floe_tilt, z=1))
    p28 = plate
    def seal_pos(t):
        bob = p28.water_y(1250, t) - 520
        a = math.radians(floe_tilt(t) + 1.2 * math.sin(t * 1.1))
        if t < ts0: x = 1250
        else: x = 1250 + 420 * min(1, (t - ts0) / (ts1 - ts0)) ** 1.5 + 200 * max(0, t - ts1)
        dx = x - 1250
        y = 478 + bob + dx * math.tan(a)
        if dx > 300: y += 0.5 * 900 * ((dx - 300) / 500) ** 2
        return (x, y)
    s.add(Seal(pos=seal_pos, scale=0.5, facing='left', z=2, rot=lambda t: 0 if t < ts0 else min(40, (t - ts0) * 45),
               look=K((0, 0), (tw, 0), (tw + 0.3, 1))))
    for k in range(3):
        s.add(Orca(pos=K((0, (-100 - 160 * k, 560 + 40 * k)), (td, (500 - 120 * k, 580 + 40 * k), 'linear'),
                         (tw, (1150 - 90 * k, 760 + 40 * k), 'eio'), (4.9, (2100, 760 + 40 * k), 'ei')),
                   rot=K((0, 0), (td, 0), (td + 0.5, 18, 'eo'), (tw - 0.3, 6), (tw + 0.5, -10)), scale=0.36 - 0.04 * k,
                   facing='right', z=3 + k, swim=1.4, period=1.8))
    s.add(WaveCrest(K((tw - 0.7, 600), (tw + 0.4, 1350, 'eo'), (4.9, 1700, 'linear')), wl=520, height=100, width=420, z=4,
                    opacity=K((0, 0), (tw - 0.7, 0), (tw - 0.5, 1), (ts1 + 0.3, 1), (4.9, 0))))
    s.add(Splash(size=200, pos=(1640, 525), t0=ts1))
    s.add(Pill('DIVE', 'dark', size=30, pos=(560, 900), target=(620, 700), t0=td, t1=tw))
    s.add(Pill('WAVE', 'cyan', size=34, pos=(1250, 260), target=(1150, 430), t0=tw))
    s.add(Pill('SEAL OFF', 'red', size=34, pos=(1650, 330), t0=ts0 + 0.2))
    S.append(s)

    # 29 ── counters: 22 attacks, 120 waves
    s = _shot(29, Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'counts')
    ta, tw2 = lt(s, 196.36), lt(s, 198.22)
    s.add(Counter(0, 22, dur=0.8, size=130, pos=(520, 300), t0=ta - 0.05, unit='attacks'))
    s.add(IconGrid(22, 11, 'orca', cell=64, pos=(520, 500), t0=ta, stagger=0.03))
    s.add(Counter(0, 120, dur=1.0, size=130, pos=(1400, 300), t0=tw2 - 0.05, unit='waves'))
    s.add(IconGrid(120, 15, 'wave', cell=40, pos=(1400, 600), t0=tw2, stagger=0.008))
    S.append(s)

    # 30 ── spy-hop over a crowded floe: crabeaters
    plate = Surface('haze', waterline=660, sun=(0.7, 0.2))
    s = _shot(30, plate, Camera(push=0.6, drift=(0, 0), wander=3), 'spyhop')
    kids = [Seal(pos=(-300 + 120 * k, -44), scale=0.34, facing='left' if k % 2 else 'right', color=CRAB if k != 3 else WEDDELL,
                 look=(lambda t, k=k: 0.5 + 0.5 * math.sin(t * 1.3 + k))) for k in range(6)]
    s.add(IceFloe(width=900, plate=plate, pos=(1220, 660), z=1, children=kids))
    s.add(Orca(pos=K((0, (430, 1050)), (1.2, (430, 720), 'eo'), (5.0, (430, 705))), rot=90, scale=0.44, swim=0.3, z=2))
    s.add(Label("HERE'S THE STRANGE PART", size=40, font='bold', track=0.18, pos=(96, 120), t0=lt(s, 200.86)))
    s.add(Pill('CRABEATERS', 'grey', size=40, pos=(1220, 380), target=(1100, 600), t0=lt(s, 204.10)))
    S.append(s)

    # 31 ── seal line-up: ignored crabeaters, locks on Weddell; 1 in 7
    s = _shot(31, Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'weddell')
    sx = [300 + 220 * k for k in range(7)]
    WI = 4
    tl, t17 = lt(s, 208.06), lt(s, 209.40)
    for k, x in enumerate(sx):
        s.add(Seal(pos=(x, 620), scale=0.46, facing='left', color=WEDDELL if k == WI else CRAB,
                   look=(lambda t, k=k: 0.5 + 0.5 * math.sin(t * 1.5 + k)),
                   opacity=(lambda t, k=k: 1.0) if k == WI else K((0, 1), (lt(s, 205.78), 1), (lt(s, 206.3), 0.45))))
    s.add(Label('CRABEATERS', size=28, font='bold', track=0.22, align='center', pos=(960, 760), t0=0.1))
    ret = K((0, (sx[0] + 30, 590)), (lt(s, 205.78), (sx[2] + 30, 590), 'eio'), (lt(s, 206.9), (sx[6] + 30, 590), 'eio'),
            (tl, (sx[WI] + 30, 590), 'eio'))
    s.add(Reticle(r=80, locked_at=tl, pos=ret))
    s.add(Pill('WEDDELL', 'red', size=34, pos=(sx[WI] + 30, 860), t0=tl))
    s.add(Label('1 IN 7', size=120, align='center', pos=(960, 260), t0=t17, reveal='wipe'))
    s.add(Label('ALMOST ONLY', size=34, font='bold', track=0.22, align='center', pos=(960, 140), t0=lt(s, 207.02)))
    S.append(s)

    # 32 ── reading the menu first
    s = _shot(32, Underwater(depth=0.3, seed=21), Camera(push=0.7, drift=(0, 0), wander=3), 'menu')
    tm = lt(s, 213.92)
    s.add(MenuCard('ANTARCTIC SEAL CAFÉ', items=[('CRABEATER', 0.9, None), ('CRABEATER', 1.1, None), ('CRABEATER', 1.3, None),
                                                 ('WEDDELL', None, tm)],
                   pos=K((0, (1250, 520)), (4.1, (1230, 510), 'linear')), rot=lambda t: 4 + 1.5 * math.sin(t * 1.2)))
    g = Group(pos=K((0, (330, 760)), (4.1, (360, 750), 'linear')), rot=-18, scale=0.62)
    g.add(Orca(facing='right', swim=0.4))
    g.add(Glasses(pos=(322, -6), t0=tm - 0.15))
    s.add(g)
    s.add(StrikeLabel('JUST MAKING WAVES', size=46, t_strike=0.5, pos=(560, 160), t0=0.0))
    s.add(Punchline("…THEY'RE READING THE MENU FIRST.", size=64, pos=(960, 1000), t0=tm))
    s.camera.shake(lt(s, 214.80), amp=8)
    S.append(s)

    # 33 ── picture being anywhere near that
    s = _shot(33, Underwater(depth=0.5, seed=23), Camera(push=1.0, drift=(0, 0)), 'diver')
    s.add(Orca(pos=K((0, (2100, 380)), (2.4, (1300, 380), 'linear')), scale=0.55, variant='silhouette', layer='back'))
    s.add(Diver(pos=(900, 640), scale=0.3, facing='right', torch=True))
    s.add(Pill('YOU', 'dark', size=30, pos=(900, 500), target=(900, 600), t0=lt(s, 216.54)))
    S.append(s)

    # 34 ── plans, picks, teaches
    s = _shot(34, Board(), Camera(push=0.6, drift=(-4, 0), wander=3), 'plans')
    s.add(Orca(pos=K((0, (760, 580)), (4.5, (680, 580), 'linear')), scale=0.8, variant='xray', swim=0.8))
    s.add(Pill('PLANS', 'orange', size=48, pos=(1560, 330), t0=lt(s, 219.06), tick=True))
    s.add(Pill('PICKS ITS TARGET', 'orange', size=48, pos=(1560, 470), t0=lt(s, 219.44), tick=True))
    s.add(Pill('TEACHES ITS KIDS', 'red', size=48, pos=(1560, 610), t0=lt(s, 221.06), tick=True))
    s.add(Label('AN ANIMAL THAT…', size=36, font='bold', track=0.2, pos=(96, 120), t0=lt(s, 218.40)))
    S.append(s)

    # 35 ── and it doesn't stop at seals (shark enters)
    s = _shot(35, Underwater(depth=0.55, seed=25), Camera(push=1.0, drift=(0, 0)), 'shark')
    s.add(Shark(pos=K((0, (2200, 520)), (1.7, (1150, 500), 'linear')), scale=0.6, layer='back'))
    s.add(Orca(pos=K((0, (2600, 760)), (1.7, (1700, 740), 'linear')), scale=0.5, variant='silhouette', layer='mid'))
    s.add(Label("IT DOESN'T STOP AT SEALS", size=52, align='center', pos=(760, 230), t0=lt(s, 223.08)))
    S.append(s)

    tot = sum(x.dur for x in S)
    assert abs(tot - (T_END - T_START)) < 0.02, tot
    return S
