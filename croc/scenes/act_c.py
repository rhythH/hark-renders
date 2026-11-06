"""Act C — BITE: bite-force study, weak opening muscles, death roll, basketball stomach (abs 169.1 – 238.7)."""
import math
from engine import *
from engine.timing import Words
from engine.core import ev, Fn, set_col, circle, rrect, W as FW, H as FH
from engine.text import draw_text
from scenes.assets_c import *

T_START, T_END = 169.1, 238.7
CUTS = [169.10, 170.70, 173.50, 177.60, 179.55, 182.20, 184.95, 188.20, 192.38, 194.70, 198.55, 200.38,
        205.30, 209.20, 213.15, 215.90, 218.45, 222.80, 226.60, 229.40, 232.50, 237.05, 238.70]
RIVER = '#24443A'


def build(words=None):
    Wd = Words(words) if words else None

    def wt(phrase, fallback):
        if Wd is None: return fallback
        try:
            v = Wd.find(phrase, after=fallback - 1.0)
            return v if abs(v - fallback) < 1.5 else fallback
        except Exception:
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

    # 1 "Then it bites." -------------------------------------------------------------
    s = new(MurkyWater(surface_y=None), Camera(push=1.2, drift=(-4, 0), wander=3), 'bites')
    tb = L(s, wt('bites', 169.83))
    s.add(CrocHead(pos=K((0, (1180, 600)), (s.dur, (1120, 590), 'linear')), scale=2.8, domes=False,
                   jaw=K((0, 34), (tb - 0.06, 40, 'ei'), (tb + 0.05, 0, 'hold')), layer='mid'))
    s.add(Bubbles(pos=(800, 900), rate=5, spread=300, layer='fg'))
    impact(s, tb + 0.05, (900, 600), amp=16)

    # 2 2012 study: bite bar -----------------------------------------------------------
    s = new(Board(), Camera(push=0.7, drift=(-3, 0), wander=3), '2012')
    tbite = L(s, wt('bite', 172.83))
    cpos = (1300, 640); csc = 0.7
    tip = (cpos[0] + csc * -470, cpos[1] + csc * -4)
    s.add(BiteBar(tip, (520, 330), t_bite=tbite, layer='mid', z=2))
    s.add(Croc(pos=cpos, scale=csc, jaw=K((0, 16), (tbite - 0.1, 22, 'ei'), (tbite, 7, 'hold')), swim=0.4, layer='mid', z=1))
    s.add(Human(pos=(300, 860), scale=0.75, pose='clipboard', coat='lab', glasses=True, facing='right', layer='mid', z=3))
    s.add(StatBox('2012 STUDY', sub='BITE FORCE', t_sub=L(s, 172.83) - L(s, 170.83), t0=L(s, wt('2012', 170.83)), pos=(96, 90)))
    s.camera.shake(tbite, amp=8, decay=0.3)

    # 3 all 23 species ------------------------------------------------------------------
    s = new(Board(), Camera(push=0.0, drift=(0, 0), wander=2, zoom=1.12), '23')
    s.camera.pull(0.0, s.dur, 0.12)
    t23 = L(s, wt('23', 176.07))
    s.add(SpeciesGrid(t_in=L(s, 173.61), stagger=0.09, pos=(960, 500), layer='mid'))
    s.add(Label('EVERY LIVING CROCODILIAN', size=40, font='xb', align='center', pos=(960, 120), t0=L(s, 173.61)))
    s.add(Counter(1, 23, dur=0.5, suffix=' SPECIES', size=92, pos=(960, 1000), t0=t23))

    # 4 the winner ------------------------------------------------------------------------
    s = new(Board(), Camera(push=0.8, drift=(0, 0), wander=2), 'winner')
    tw = L(s, wt('winner', 177.76))
    s.add(SpeciesGrid(t_in=-5, stagger=0, pos=(960, 500), winner=14, t_dim=tw, layer='mid'))
    s.camera.emphasis(tw, s.dur, 0.25, target=(960 + (14 % 6 - 2.5) * 230, 500 + (14 // 6 - 1.5) * 150))
    s.add(Pill('THE WINNER', 'orange', size=40, pos=(960, 110), t0=tw))
    s.add(Pill('SALTWATER CROCODILE', 'dark', size=34, pos=(960, 980), t0=L(s, wt('saltwater', 178.26))))

    # 5 4.59 m ------------------------------------------------------------------------------
    s = new(Board(), Camera(push=0.6, drift=(-4, 0), wander=2), '459')
    t459 = L(s, wt('4.59', 179.72))
    s.add(Croc(pos=K((0, (1010, 520)), (s.dur, (950, 520), 'linear')), scale=1.25, swim=0.8, layer='mid'))
    s.add(DimensionLine((345, 760), (1605, 760), label='4.59 M', sub='long', size=64, t0=t459))
    s.add(Pill('SALTWATER CROCODILE', 'dark', size=30, pos=(960, 130), t0=0.0))

    # 6 16,414 N gauge -----------------------------------------------------------------------
    s = new(Black(color='#0B1A15', particles=True), Camera(push=0.4, drift=(0, 0), wander=2), 'gauge')
    tn = L(s, wt('16,414', 182.32))
    s.add(Gauge(K((0, 0), (tn, 0), (tn + 1.4, 16414, 'eo')), pos=(560, 560), r=300, layer='mid'))
    s.add(Counter(0, 16414, dur=1.4, suffix=' N', size=140, pos=(1430, 590), t0=tn, unit='newtons'))
    s.add(Label('BITE FORCE', size=36, font='bold', track=0.22, align='center', pos=(1430, 420), t0=0.1))
    s.camera.emphasis(tn, tn + 0.5, 0.08, target=(800, 560))
    s.camera.shake(tn + 1.4, amp=8, decay=0.3)

    # 7 strongest bite ever measured ------------------------------------------------------------
    s = new(MurkyWater(surface_y=238), Camera(push=1.0, drift=(-3, 0), wander=3), 'record')
    tm = L(s, wt('measured', 186.28))
    s.add(CrocHead(pos=(1180, 640), scale=2.5, domes=False,
                   jaw=K((0, 4), (0.3, 36, 'eo'), (tm - 0.08, 40, 'ei'), (tm + 0.04, 0, 'hold')), layer='mid'))
    s.add(Pill('STRONGEST BITE EVER MEASURED', 'orange', size=44, pos=(960, 120), t0=L(s, wt('strongest', 185.12))))
    s.add(Stamp('RECORD', PAL.RED, 96, pos=(560, 820), t0=tm + 0.04))
    s.add(Label('IN ANY ANIMAL', size=40, font='xb', align='center', pos=(560, 960), t0=L(s, wt('any', 187.04))))
    impact(s, tm + 0.04, (930, 640), amp=14)

    # 8 1.5 tonnes on the back teeth -------------------------------------------------------------
    s = new(Board(), Camera(push=0.5, drift=(0, 0), wander=2), 'tonnes')
    tt = L(s, wt('tonnes', 189.54))
    hp = (980, 660); hsc = 2.4
    s.add(CrocHead(pos=K((0, hp), (tt, hp, 'hold'), (tt + 0.08, (hp[0], hp[1] + 14), 'eo'), (tt + 0.4, (hp[0], hp[1] + 6))),
                   scale=hsc, domes=False, jaw=K((0, 8), (tt, 8, 'hold'), (tt + 0.06, 0, 'hold')), layer='mid'))
    bx = hp[0] + 0.0 * hsc + 190
    by = hp[1] - 58 * hsc + 16
    s.add(WeightBlock(pos=K((0, (bx, -320)), (tt - 0.35, (bx, -320), 'ei2'), (tt, (bx, by), 'hold'),
                           (tt + 0.08, (bx, by + 14), 'eo'), (tt + 0.4, (bx, by + 6))), layer='mid', z=2))
    s.add(DownArrows(pos=(bx, by - 270), t0=tt + 0.3, layer='mid', z=3))
    s.add(Pill('BACK TEETH', 'red', size=34, pos=(1500, 900), target=(hp[0] + 60 * hsc, hp[1] + 8), t0=L(s, wt('back', 191.26))))
    s.add(Label('MORE THAN 1.5 TONNES', size=48, font='xb', align='center', pos=(560, 150), t0=tt))
    s.camera.shake(tt, amp=16, decay=0.4)

    # 9 hardest-biting mammal --------------------------------------------------------------------
    s = new(Board(), Camera(push=0.7, drift=(-3, 0), wander=2), 'hyena')
    s.add(Hyena(pos=K((0, (1750, 760)), (s.dur, (1020, 760), 'linear')), scale=1.2, walk=1.0,
                jaw=lambda t: 0.5 + 0.5 * math.sin(t * 6), layer='mid'))
    s.add(Pill('HARDEST-BITING MAMMAL', 'dark', size=40, pos=(700, 200), t0=L(s, wt('hardest-biting', 192.48))))
    s.add(Label('IN THE STUDY', size=28, font='bold', track=0.22, align='center', pos=(700, 290), t0=L(s, wt('compared', 193.68))))

    # 10 bar chart ------------------------------------------------------------------------------
    s = new(Board(), Camera(push=0.4, drift=(0, 0), wander=2), 'bars')
    th = L(s, wt('hyena', 195.18)); t45 = L(s, wt('4,500', 196.62))
    LMAX = 1000
    s.add(Croc(pos=(270, 720), scale=0.32, swim=0.8, layer='mid'))
    s.add(HBar(LMAX, 'SALTWATER CROCODILE', '16,414 N', color=PAL.RED, t_value=0.3, pos=(480, 720), t0=0.0, layer='overlay'))
    s.add(Hyena(pos=(280, 500), scale=0.42, walk=0.0, jaw=lambda t: 0.3 + 0.3 * math.sin(t * 5), layer='mid', t0=th))
    s.add(HBar(LMAX * 4500 / 16414, 'SPOTTED HYENA', '~4,500 N', color=PAL.WHITE, t_value=t45 - th, pos=(480, 440), t0=th, layer='overlay'))
    s.add(Label('BITE FORCE', size=34, font='bold', track=0.22, align='center', pos=(960, 160), t0=0.0))
    s.add(Stamp('NOT EVEN CLOSE', PAL.ORANGE, 60, pos=(1450, 960), t0=t45 + 0.6))

    # 11 the strange part -----------------------------------------------------------------------
    s = new(Mangrove(horizon=430), Camera(push=1.0, drift=(3, 0), wander=2), 'strange')
    s.add(CrocEyes(pos=K((0, (1060, 720)), (s.dur, (980, 720), 'linear')), scale=1.6, view='side', layer='mid'))
    s.add(Badge('question', 'THE STRANGE PART', pos=(960, 280), r=80, t0=L(s, wt('strange', 199.14))))

    # 12 closing vs opening muscles ----------------------------------------------------------------
    s = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'muscles')
    tc = L(s, wt('closing', 201.5)); to = L(s, wt('open', 203.06)); tk = L(s, wt('weak', 203.98))
    hp = (980, 600); hsc = 2.6
    s.add(CrocHead(pos=hp, scale=hsc, domes=False, jaw=K((0, 18), (tc - 0.1, 22, 'ei'), (tc + 0.02, 0, 'hold'),
                                                      (to, 0), (to + 0.6, 4, 'eo'), (to + 1.2, 0)), layer='mid'))
    s.add(MuscleBlob(150, 82, PAL.RED, angle=-10, pos=(hp[0] + 72 * hsc, hp[1] - 10 * hsc), t0=tc, layer='mid', z=2))
    s.add(MuscleBlob(34, 8, '#8E9496', angle=8, pulse=0.3, pos=(hp[0] + 112 * hsc, hp[1] + 44 * hsc), t0=to, layer='mid', z=2))
    s.add(Pill('CLOSING', 'red', size=46, pos=(1250, 300), target=(hp[0] + 72 * hsc, hp[1] - 10 * hsc), t0=tc))
    s.add(Pill('OPENING', 'grey', size=22, pos=(1560, 990), target=(hp[0] + 112 * hsc, hp[1] + 44 * hsc), t0=to))
    s.add(Stamp('WEAK', PAL.RED, 70, pos=(1750, 860), t0=tk))
    s.add(Label('ALL THAT POWER GOES INTO CLOSING', size=36, font='xb', align='center', pos=(700, 1010), t0=tc))
    s.camera.emphasis(to - 0.2, to + 1.0, 0.07, target=(hp[0] + 112 * hsc, hp[1] + 30 * hsc))

    # 13 taped shut ------------------------------------------------------------------------------
    s = new(Board(), Camera(push=0.8, drift=(0, 0), wander=2), 'tape')
    thd = L(s, wt('held', 207.48)); ttp = L(s, wt('taped', 208.02)); tsh = L(s, wt('shut', 208.22))
    hp = (1150, 600); hsc = 2.6
    strain = lambda t: max(0.0, 2.5 + 2.5 * math.sin(t * 9)) if t > 0.6 else 0.0
    s.add(CrocHead(pos=hp, scale=hsc, domes=False, jaw=strain, layer='mid'))
    s.add(TapeBand(h=200, pos=(hp[0] - 70 * hsc, hp[1] - 2 * hsc), t0=thd, layer='mid', z=2))
    s.add(TapeBand(h=210, pos=(hp[0] - 40 * hsc, hp[1] - 2 * hsc), t0=ttp, layer='mid', z=2))
    s.add(Label("CAN'T OPEN", size=56, font='black', color=PAL.WHITE, align='center', pos=(420, 300), t0=L(s, wt("can't", 205.98))))
    s.add(Pill('TAPE: WINS', 'orange', size=44, pos=(420, 860), t0=tsh))

    # 14 doesn't chew, teeth can't cut ----------------------------------------------------------------
    s = new(MurkyWater(surface_y=238), Camera(push=0.8, drift=(-3, 0), wander=3), 'chew')
    cpos = K((0, (1100, 640)), (s.dur, (1040, 640), 'linear')); csc = 0.75
    croc = s.add(Croc(pos=cpos, scale=csc, jaw=7, swim=0.6, layer='mid', z=1))
    s.add(Log(L=300, rot=80, pos=lambda t, cpos=cpos, csc=csc, croc=croc: (ev(cpos, t)[0] + csc * croc.jaw_tip(t)[0], ev(cpos, t)[1] + csc * croc.jaw_tip(t)[1]),
              layer='mid', z=2))
    s.add(Checklist([("CHEWS", 'x', L(s, wt('chew', 210.74)) + 0.1), ("TEETH THAT CUT", 'x', L(s, wt('cut', 212.38)))],
                    t_items=[L(s, 209.86), L(s, 211.57)], size=46, pos=(1120, 420)))
    s.add(Croc(pos=(300, 920), scale=0.35, opacity=0.4, tint=RIVER, swim=1.2, layer='back'))

    # 15 the death roll -------------------------------------------------------------------------
    s = new(MurkyWater(surface_y=238), Camera(push=1.0, drift=(0, 0), wander=3), 'roll')
    tth = L(s, wt('this', 213.74)); tdr = L(s, wt('death', 214.76)); trl = L(s, wt('roll', 214.94))
    rollf = lambda t, tth=tth: 0.0 if t < tth else -(min(t - tth, 0.8) ** 2 * 280 + max(0, t - tth - 0.8) * 450)
    cpos = (1000, 600); csc = 0.8
    croc = s.add(Croc(pos=cpos, scale=csc, jaw=7, roll=rollf, swim=0.3, layer='mid', z=1))
    s.add(Log(L=lambda t, rollf=rollf: 320 * abs(math.cos(math.radians(rollf(t)))), r=34, rot=80,
              pos=lambda t, cpos=cpos, csc=csc, croc=croc: (cpos[0] + csc * croc.jaw_tip(t)[0], cpos[1] + csc * croc.jaw_tip(t)[1]), layer='mid', z=2))
    s.add(RollArcs(rx=520, ry=190, speed=0.9, pos=cpos, t0=tth + 0.2, layer='fg'))
    s.add(Bubbles(pos=(1000, 640), rate=10, spread=500, t0=tth, layer='fg'))
    s.add(Punchline('THE DEATH ROLL', size=120, style='v1', color=PAL.WHITE, underline=False, pos=(960, 980), t0=tdr))
    s.camera.shake(trl, amp=14, decay=0.5)
    s.camera.emphasis(tth, s.dur, 0.15, target=cpos)

    # 16 diagram: spins, over and over -----------------------------------------------------------
    s = new(Board(), StaticCamera(), 'spin')
    s.add(Croc(pos=(960, 560), scale=1.0, variant='xray', roll=lambda t: -430 * t, swim=0.2, jaw=6, layer='mid'))
    s.add(RollArcs(rx=600, ry=210, speed=1.2, color=PAL.CYAN_HI, pos=(960, 560), layer='mid', z=2))
    s.add(RollCount([L(s, wt('spins', 216.72)), L(s, wt('over', 216.96)), L(s, 217.88)], pos=(1640, 220)))
    s.add(Label('HOLDS ON + SPINS', size=40, font='xb', align='center', pos=(960, 1000), t0=L(s, wt('holds', 216.06))))

    # 17 drag under / tear a piece -------------------------------------------------------------
    s = new(MurkyWater(surface_y=238), Camera(push=0.6, drift=(0, 4), wander=3), 'drag')
    cpos = K((0, (1150, 330)), (s.dur, (1020, 760), 'eio')); csc = 0.62
    rollf2 = lambda t: -380 * t
    croc = s.add(Croc(pos=cpos, scale=csc, jaw=7, roll=rollf2, swim=0.3, layer='mid', z=1))
    s.add(Log(L=lambda t: 260 * abs(math.cos(math.radians(rollf2(t)))), r=28, rot=80,
              pos=lambda t, cpos=cpos, csc=csc, croc=croc: (ev(cpos, t)[0] + csc * croc.jaw_tip(t)[0], ev(cpos, t)[1] + csc * croc.jaw_tip(t)[1]), layer='mid', z=2))
    s.add(Bubbles(pos=lambda t, cpos=cpos: (ev(cpos, t)[0], ev(cpos, t)[1] - 40), rate=12, spread=400, rise=260, layer='fg'))
    s.add(Pill('DRAG UNDER', 'red', size=44, pos=(420, 420), t0=L(s, wt('drag', 218.62))))
    s.add(Pill('TEAR A PIECE', 'orange', size=44, pos=(420, 540), t0=L(s, wt('tear', 220.2))))
    s.add(Label('SMALL ENOUGH TO SWALLOW', size=30, font='bold', track=0.2, align='center', pos=(420, 640),
                t0=L(s, wt('swallow', 221.78))))

    # 18 basketball stomach ------------------------------------------------------------------------
    s = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'stomach')
    tst = L(s, wt('stomach', 224.16)); tbb = L(s, wt('basketball', 225.82))
    cpos = (960, 520); csc = 1.2
    croc = Croc(pos=cpos, scale=csc, variant='xray', swim=0.5, layer='mid')
    s.add(croc)
    sp = lambda t, cpos=cpos, csc=csc, croc=croc: (cpos[0] + csc * croc.stomach_point(t)[0], cpos[1] + csc * croc.stomach_point(t)[1])
    s.add(Basketball(r=46, pos=sp, t0=tbb, layer='mid', z=2))
    s.add(DimensionLine((360, 760), (1560, 760), label='3 M', size=56, t0=L(s, wt('three-metre', 222.96))))
    s.add(Pill('STOMACH', 'cyan', size=34, pos=(560, 200), target=sp, t0=tst))
    s.add(Label('ABOUT A BASKETBALL', size=64, font='black', color=PAL.ORANGE, align='center', pos=(960, 960), t0=tbb))
    s.camera.emphasis(tbb - 0.1, s.dur, 0.2, target=(830, 560))

    # 19 can't eat a big animal at once ------------------------------------------------------------
    s = new(Board(), Camera(push=0.6, drift=(-3, 0), wander=2), 'toobig')
    tbig = L(s, wt('animal', 227.72))
    s.add(Basketball(r=80, pos=(420, 620), layer='mid'))
    s.add(Label('STOMACH', size=30, font='bold', track=0.22, align='center', pos=(420, 760), t0=0.1))
    s.add(Buffalo(pos=K((0, (1500, 820)), (s.dur, (1330, 820), 'linear')), scale=1.25, walk=1.0, layer='mid'))
    s.add(Label('BIG ANIMAL', size=30, font='bold', track=0.22, align='center', pos=(1330, 300), t0=L(s, wt('big', 227.48))))
    s.add(Stamp('ALL AT ONCE? NO.', PAL.RED, 64, pos=(960, 160), t0=L(s, wt('once', 228.52))))
    s.camera.shake(L(s, wt('once', 228.52)), amp=8, decay=0.3)

    # 20 leaves it, comes back over several days ------------------------------------------------------
    pl = Riverbank(waterline_y=560, bank_x=1250)
    s = new(pl, Camera(push=0.5, drift=(-3, 0), wander=2), 'days')
    tcb = L(s, wt('comes', 230.36)); tbk = L(s, wt('back', 230.54)); tdy = L(s, wt('days', 231.36))
    s.add(Lump(pos=(1130, 780), layer='mid'))
    s.add(Croc(pos=K((0, (900, 562)), (tcb, (-500, 562), 'ei')), scale=0.55, submerged=0.55, water=RIVER,
               layer='mid', z=1, t1=tcb))
    s.add(Croc(pos=K((0, (-500, 562)), (s.dur - tcb, (720, 562), 'eo')), scale=0.55, facing='right', submerged=0.55,
               water=RIVER, layer='mid', z=1, t0=tcb))
    s.add(Pill('LEFTOVERS', 'dark', size=30, pos=(1500, 900), target=(1130, 780), t0=L(s, wt('leaves', 229.54))))
    s.add(Calendar(flips=(tbk - (tcb - 0.2) + 0.3, tdy - (tcb - 0.2)), pos=(1560, 300), layer='overlay', t0=tcb - 0.2))

    # 21 punchline card ---------------------------------------------------------------------------------
    s = new(Black(particles=True), Camera(push=0.4, drift=(0, 0), wander=2), 'punch')
    tmo = L(s, wt('Most', 232.58)); tth = L(s, wt('This', 234.92)); tsm = L(s, wt('stomach', 235.98))
    s.add(Croc(pos=K((0, (2300, 860)), (s.dur, (900, 860), 'linear')), scale=0.9, variant='silhouette',
               sil_color='#0C1A17', swim=1, layer='back'))
    s.add(Label('MOST PREDATORS RUN OUT OF PATIENCE.', size=62, font='black', align='center', pos=(960, 430),
                reveal='wipe', dur=0.6, t0=tmo))
    s.add(Punchline('\u2026THIS ONE RUNS OUT OF STOMACH.', size=76, pos=(960, 600), t0=tth))
    s.camera.shake(tsm, amp=12, decay=0.4)

    # 22 doesn't stop at pigs ---------------------------------------------------------------------------
    pl = Riverbank(waterline_y=560, bank_x=1150)
    s = new(pl, Camera(push=1.0, drift=(0, 0), wander=2), 'pigs')
    tpg = L(s, wt('pigs', 238.02))
    s.add(Pig(pos=(1330, pl.bank_y(1330)), scale=0.75, pose='root', layer='mid'))
    s.add(CrocEyes(pos=K((0, (760, 560)), (s.dur, (900, 560), 'linear')), scale=0.9, view='side', water=RIVER, layer='mid'))
    s.add(SharkFin(h=70, color='#5F7177', pos=K((0, (-60, 562)), (s.dur, (330, 562), 'linear')), t0=tpg - 0.4, layer='mid'))
    s.add(Pill('PIGS', 'dark', size=40, tick=True, pos=(1330, 300), target=(1330, pl.bank_y(1330) - 120), t0=L(s, wt('stop', 237.6))))
    s.add(Pill('NOT JUST PIGS', 'red', size=34, pos=(560, 300), t0=tpg))

    assert abs(sum(x.dur for x in shots) - (T_END - T_START)) < 1e-6, sum(x.dur for x in shots)
    return shots
