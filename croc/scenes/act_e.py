"""Act E — PEOPLE (cont.): global deaths map, Bhitarkanika, Ramree myth vs reality.
Absolute range [326.3, 402.0), beats B45–B51. Plan: scenes/plan_e.md."""
import math
from engine import *
from engine.core import StaticCamera
from scenes.assets_e import (FlatMap, range_dots, Panel, Soldiers, Book, RecordBook, Rosette, Pie, SpeechBubble,
                             CreditRoll, sepia_wash, PersonRow)

T_START, T_END = 326.3, 402.0
CUTS = [326.30, 329.27, 332.50, 336.43, 341.67, 344.44, 348.92, 352.13, 353.16, 355.76, 359.13, 363.71,
        368.08, 371.92, 376.72, 379.21, 381.99, 386.81, 391.99, 396.34, 399.92, T_END]

RANGE = ['India', 'Sri Lanka', 'Bangladesh', 'Myanmar', 'Malaysia', 'Brunei', 'Indonesia', 'Philippines',
         'Timor-Leste', 'Papua New Guinea', 'Solomon Is.', 'Australia']
LON = {'India': 78, 'Sri Lanka': 81, 'Bangladesh': 90, 'Myanmar': 96, 'Malaysia': 102, 'Brunei': 114,
       'Indonesia': 112, 'Philippines': 122, 'Timor-Leste': 125, 'Papua New Guinea': 145, 'Solomon Is.': 159,
       'Australia': 135}
GREEN = '#3E9A68'
RIVER = '#24443A'
BHITAR = (86.87, 20.72)
RAMREE_C = (93.8, 19.1)
NAV_SAFE = None


def range_hl(t_base=-5.0, spread=0.0, alpha=0.75, dim_after=None, except_=()):
    out = []
    for n in RANGE:
        h = dict(name=n, color=GREEN, t=t_base + spread * (LON[n] - 78) / 80, alpha=alpha)
        if n == 'Australia': h['lat_min'] = -21
        if dim_after is not None and n not in except_: h['off'] = dim_after
        out.append(h)
    return out


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

    # ------------------------------------------------ 1 Australia: the safe end of the map (pan west)
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=3), 'aus')
    m = s.add(FlatMap(center=K((0, (142, -19)), (3.0, (131, -15), 'linear')), zoom=K((0, 34), (3.0, 31, 'linear')),
                      hl=[dict(name='Australia', color=GREEN, t=0.1, alpha=0.8, pulse=True)]))
    s.add(CrocTop(pos=K((0, (2100, 300)), (3.0, (1300, 330), 'linear')), scale=0.45, rot=180, variant='silhouette',
                  sil_color='#05141B', opacity=0.55, layer='back', turn=K((0, 8), (1.5, -8), (3, 8))))
    s.add(Pill('AUSTRALIA', 'dark', size=36, pos=(1180, 820), target=lambda t, m=m: m.xy(133, -24, t), t0=L(326.70)))
    s.add(Pill('THE SAFE END OF THE MAP', 'green', size=44, tick=True, pos=(960, 160), t0=L(327.80)))

    # ------------------------------------------------ 2 across their range (pull out, light up W->E)
    s, L = new(Board(), Camera(push=0.4, drift=(-4, 0), wander=2), 'range')
    hl = range_hl(t_base=L(329.82), spread=1.6)
    for h in hl:
        if h['name'] == 'Australia': h['t'] = -1
    m = s.add(FlatMap(center=K((0, (128, -12)), (1.4, (114, 4), 'eio'), (3.23, (112, 5), 'linear')),
                      zoom=K((0, 31), (1.4, 20.5, 'eio'), (3.23, 20, 'linear')), hl=hl))
    s.add(CrocTop(pos=K((0, (-300, 900)), (3.23, (500, 860), 'linear')), scale=0.32, rot=0, variant='silhouette',
                  sil_color='#05141B', opacity=0.5, layer='back'))
    s.add(Label('SALTWATER CROCODILE RANGE', size=40, font='bold', track=0.22, align='center', pos=(960, 130),
                t0=L(330.52)))
    s.add(Pill('INDIA', 'dark', size=30, pos=(330, 300), target=lambda t, m=m: m.xy(79, 22, t), t0=L(329.82)))
    s.add(Pill('SE ASIA', 'dark', size=30, pos=(1150, 250), target=lambda t, m=m: m.xy(104, 15, t), t0=L(330.52)))
    s.add(Pill('NORTHERN AUSTRALIA', 'dark', size=30, pos=(1500, 980), target=lambda t, m=m: m.xy(133, -15, t), t0=L(331.02)))

    # ------------------------------------------------ 3 ~120-130 people a year (dots pop)
    s, L = new(Board(), Camera(push=0.5, drift=(-4, 0), wander=2), 'count')
    dots = range_dots(RANGE[:-1], 70, L(332.96), 3.6, seed=5) + range_dots(['Australia'], 4, 1.5, 3.4, seed=2, lat_min=-18)
    s.add(FlatMap(center=(111.5, 5), zoom=20, hl=range_hl(alpha=0.55), dots=dots))
    s.add(Panel(w=980, h=300, pos=(960, 520), alpha=0.72, t0=L(332.70)))
    s.add(Counter(0, 120, dur=0.45, prefix='~', align='right', size=150, font='black', pos=(1000, 560), t0=L(332.96)))
    s.add(Label('–130', size=150, font='black', color=PAL.WHITE, align='left', pos=(1000, 560), reveal='wipe', t0=L(334.36)))
    s.add(Label('PEOPLE A YEAR', size=40, font='bold', track=0.24, align='center', pos=(960, 635), t0=L(334.80)))
    s.add(Pill('RECORDED', 'outline', size=28, pos=(960, 410), t0=L(332.60)))

    # ------------------------------------------------ 4 Indonesia 85+ in 2023
    s, L = new(Board(), Camera(push=0.8, drift=(0, 0), wander=2), 'indo')
    t_in = L(337.00)
    hl = range_hl(alpha=0.5, dim_after=t_in, except_=('Indonesia',))
    hl.append(dict(name='Indonesia', color=PAL.RED, t=t_in, alpha=0.75, pulse=True))
    m = s.add(FlatMap(center=K((0, (111.5, 5)), (1.2, (117, -3), 'eio'), (5.24, (118, -3.5), 'linear')),
                      zoom=K((0, 20), (1.2, 34, 'eio'), (5.24, 36, 'linear')), hl=hl,
                      dots=range_dots(['Indonesia'], 85, L(338.18), L(339.6), seed=9)))
    s.add(Pill('INDONESIA', 'red', size=40, pos=(560, 880), target=lambda t, m=m: m.xy(113, -7, t), t0=t_in + 0.1))
    s.add(Panel(w=700, h=280, pos=(1350, 230), alpha=0.8, t0=L(338.0)))
    s.add(Counter(0, 85, dur=0.6, prefix='AT LEAST ', suffix='+', size=110, font='black', color=PAL.RED, align='center',
                  pos=(1350, 245), t0=L(338.08)))
    s.add(Label('KILLED IN 2023 ALONE', size=36, font='bold', track=0.22, align='center', pos=(1350, 320), t0=L(339.88)))

    # ------------------------------------------------ 5 India: Bhitarkanika
    s, L = new(Board(), Camera(push=0.8, drift=(0, 0), wander=2), 'india')
    m = s.add(FlatMap(center=K((0, (100, 12)), (1.3, (85, 20), 'eio'), (2.77, (86, 20.5), 'linear')),
                      zoom=K((0, 24), (1.3, 40, 'eio'), (2.77, 44, 'linear')),
                      hl=[dict(name='India', color=GREEN, t=-1, alpha=0.6)], dots=[(BHITAR[0], BHITAR[1], L(342.64))]))
    s.add(Pill('INDIA', 'dark', size=34, pos=(700, 300), target=lambda t, m=m: m.xy(78, 22, t), t0=0.15))
    s.add(Pill('BHITARKANIKA NATIONAL PARK, ODISHA', 'orange', size=38, pos=(1250, 780),
               target=lambda t, m=m: m.xy(*BHITAR, t), t0=L(342.64)))

    # ------------------------------------------------ 6 22 killed in five years, one district
    pl = Riverbank(560, mud=True, mangroves=True, bank_x=1350, seed=7)
    s, L = new(pl, Camera(push=0.7, drift=(-6, 0), wander=2), 'odisha22')
    s.add(CrocEyes(pos=K((0, (300, 640)), (4.48, (620, 630), 'linear')), scale=0.9, view='side', water=RIVER, layer='mid'))
    s.add(Bucket(pos=(1600, pl.bank_y(1600)), scale=0.8, layer='mid'))
    s.add(Panel(w=900, h=420, pos=(960, 330), alpha=0.75, t0=L(345.0)))
    s.add(Counter(0, 22, dur=0.5, size=150, font='black', color=PAL.WHITE, align='center', pos=(960, 300), t0=L(345.22)))
    s.add(Label('PEOPLE KILLED', size=36, font='bold', track=0.24, align='center', pos=(960, 360), t0=L(345.52)))
    s.add(PersonRow(22, cols=11, cell=58, t_a=0.0, t_b=1.3, pos=(960, 450), t0=L(345.4)))
    s.add(Pill('IN 5 YEARS', 'orange', size=34, pos=(780, 590), t0=L(346.74)))
    s.add(Pill('IN ONE DISTRICT', 'outline', size=34, pos=(1150, 590), t0=L(347.88)))

    # ------------------------------------------------ 7 ordinary things: fishing
    pl = Riverbank(560, mud=True, mangroves=True, bank_x=1150, seed=3)
    s, L = new(pl, Camera(push=0.8, drift=(4, 0), wander=2), 'fishing')
    s.add(Fisherman(pos=(1450, pl.bank_y(1450)), scale=0.62, facing='left', line_to=(-760, 160),
                    bite=K((0, 0), (2.2, 0), (2.4, 0.4), (2.7, 0)), layer='mid'))
    s.add(Bucket(pos=(1640, pl.bank_y(1640)), scale=0.9, layer='mid'))
    s.add(CrocEyes(pos=K((0, (140, 610)), (3.21, (420, 600), 'linear')), scale=0.75, view='side', water=RIVER, layer='mid'))
    s.add(Pill('ORDINARY THINGS', 'dark', size=40, pos=(960, 130), t0=L(349.52)))
    s.add(Pill('FISHING', 'orange', size=40, pos=(560, 960), t0=L(351.19)))

    # ------------------------------------------------ 8 bathing
    pl = Riverbank(600, mud=True, mangroves=True, bank_x=1450, seed=9)
    s, L = new(pl, Camera(push=1.2, drift=(0, 0), wander=2), 'bathing')
    s.add(Human(pos=(1000, 690), scale=0.62, pose=lambda t: 'wave' if (t % 0.8) < 0.4 else 'stand', facing='left',
                hat=None, coat='#C26A3A', layer='mid', z=0))

    def water_over(ctx, t, pl=pl):
        ctx.rectangle(820, 600 + 2 * math.sin(t * 3), 380, 140)
        ctx.set_source_rgba(0.14, 0.27, 0.23, 0.92); ctx.fill()
        for j in range(3):
            k = (t * 0.9 + j / 3) % 1
            ctx.save(); ctx.translate(1000, 602); ctx.scale(1, 0.22)
            circle(ctx, 0, 0, 60 + 160 * k); ctx.set_source_rgba(0.85, 0.9, 0.8, 0.4 * (1 - k)); ctx.set_line_width(12); ctx.stroke()
            ctx.restore()
    s.add(Fn(water_over, layer='mid', z=1))
    s.add(Splash(pos=(1000, 600), size=110, layer='mid', z=2))
    s.add(CrocEyes(pos=K((0, (330, 650)), (1.03, (380, 648), 'linear')), scale=0.7, view='side', water=RIVER, layer='mid'))
    s.add(Pill('FISHING', 'orange', size=40, pos=(560, 960), t0=-1))
    s.add(Pill('BATHING', 'orange', size=40, pos=(960, 960), t0=L(352.23)))

    # ------------------------------------------------ 9 washing their feet in a village pond
    pl = Riverbank(600, mud=True, mangroves=False, bank_x=1050, roots=False, seed=11)
    s, L = new(pl, Camera(push=1.0, drift=(-3, 0), wander=2), 'feet')
    s.add(Human(pos=(1180, pl.bank_y(1180)), scale=0.6, pose='crouch', facing='left', hat=None, coat='#3F7F6A',
                layer='mid'))
    s.add(Bucket(pos=(1330, pl.bank_y(1330)), scale=0.85, layer='mid'))
    s.add(CrocEyes(pos=K((0, (180, 660)), (1.8, (520, 640), 'linear'), (2.6, (560, 660), 'ei')), scale=0.75, view='side',
                   water=RIVER, layer='mid', opacity=K((0, 1), (1.9, 1), (2.6, 0.0))))
    s.add(Pill('FISHING', 'orange', size=40, pos=(560, 960), t0=-1))
    s.add(Pill('BATHING', 'orange', size=40, pos=(960, 960), t0=-1))
    s.add(Pill('WASHING', 'orange', size=40, pos=(1360, 960), t0=L(353.26)))
    s.add(Label('A VILLAGE POND', size=30, font='bold', track=0.24, align='center', pos=(960, 120), t0=L(354.44)))

    # ------------------------------------------------ 10 the most famous crocodile attack in history (sepia)
    s, L = new(Sepia(), Camera(push=1.0, drift=(0, 0), wander=2), 'famous')
    s.add(Croc(pos=K((0, (2300, 760)), (3.37, (1250, 760), 'linear')), scale=0.85, facing='left', variant='silhouette',
               sil_color='#4A3826', gait=1.0, swim=0.3, layer='mid'))
    s.add(Typewriter('THE MOST FAMOUS', size=72, font='black', color='#2A2018', cps=26, cursor=False, pos=(160, 300),
                     t0=L(356.05)))
    s.add(Typewriter('CROCODILE ATTACK IN HISTORY', size=72, font='black', color='#2A2018', cps=30, cursor=True,
                     pos=(160, 400), t0=L(356.92)))

    # ------------------------------------------------ 11 February 1945, Ramree Island, off Burma (sepia map)
    s, L = new(Sepia(), Camera(push=0.5, drift=(0, 0), wander=2), 'ramree_map')
    m = s.add(FlatMap(center=K((0, (91, 20.5)), (1.6, (91, 20.5), 'hold'), (3.8, (93.3, 19.3), 'eio'), (4.58, (93.4, 19.25), 'linear')),
                      zoom=K((0, 55), (1.6, 60), (3.8, 150, 'eio'), (4.58, 158, 'linear')), style='sepia', island=True,
                      circle_=(RAMREE_C[0], RAMREE_C[1], 95, L(361.2))))
    s.add(StatBox('FEBRUARY 1945', t0=L(359.23)))
    s.add(Pill('RAMREE ISLAND', 'red', size=40, pos=(1400, 260), target=lambda t, m=m: m.xy(94.0, 19.3, t), t0=L(361.08)))
    s.add(Pill('BURMA', 'dark', size=36, pos=(1500, 760), target=lambda t, m=m: m.xy(95.2, 19.6, t), t0=L(362.96)))

    # ------------------------------------------------ 12 ~1,000 soldiers retreat into the mangroves
    s, L = new(Mangrove(horizon=430, haze=0.6, seed=4), Camera(push=0.9, drift=(-8, 0), wander=2), 'retreat')
    s.add(Soldiers(n=34, spread=(820, 120), size=0.95, pos=K((0, (1500, 640)), (4.37, (1050, 630), 'linear')),
                   ripple='#B8C2A0', layer='mid'))
    s.add(Soldiers(n=18, spread=(600, 60), size=0.6, seed=8, pos=K((0, (1250, 520)), (4.37, (900, 515), 'linear')),
                   ripple='#B8C2A0', layer='back', opacity=0.8))
    s.add(CrocEyes(pos=(330, 860), scale=1.1, view='side', water='#1E3A34', layer='fg'))
    s.add(Panel(w=700, h=200, pos=(960, 150), alpha=0.75, t0=L(364.0)))
    s.add(Counter(0, 1000, dur=0.7, prefix='~', size=110, font='black', align='center', pos=(960, 185), t0=L(364.18)))
    s.add(Label('JAPANESE SOLDIERS', size=30, font='bold', track=0.24, align='center', pos=(960, 232), t0=L(364.48)))
    s.add(Pill('INTO THE MANGROVES', 'dark', size=34, pos=(560, 340), target=(420, 520), t0=L(366.70)))
    s.post.append(sepia_wash(0.75))

    # ------------------------------------------------ 13 naturalist: only about 20 came out alive
    s, L = new(Sepia(), Camera(push=1.2, drift=(0, -3), wander=2), 'book')
    s.add(Book(t_circle=L(370.26), title='A NATURALIST\'S ACCOUNT', pos=(960, 560), scale=0.95, layer='mid'))
    s.add(Pill('WRITTEN LATER', 'dark', size=30, pos=(400, 140), t0=L(368.78)))
    s.add(Label('~20 CAME OUT ALIVE', size=64, font='black', color=PAL.RED_DARK if hasattr(PAL, 'RED_DARK') else PAL.RED,
                align='center', pos=(960, 1020), t0=L(370.58)))
    s.camera.emphasis(L(370.1), L(371.9), 0.12, target=(1200, 520))

    # ------------------------------------------------ 14 Guinness: worst animal attack ever recorded
    s, L = new(Sepia(), Camera(push=0.7, drift=(0, 0), wander=2), 'record')
    s.add(RecordBook(pos=(560, 520), layer='mid', t0=L(372.08)))
    ros = Rosette(pos=(1300, 330), scale=0.95, layer='mid', t0=L(373.94),
                  rot=K((0, 0), (0.15, -4, 'eo')))
    s.add(ros)
    s.camera.shake(L(373.98), amp=8)

    # ------------------------------------------------ 15 except it probably didn't happen like that
    s, L = new(Sepia(), Camera(push=0.6, drift=(0, 0), wander=2), 'myth')
    s.add(RecordBook(pos=(560, 520), layer='mid', t0=-1))
    s.add(Rosette(pos=K((0, (1300, 330)), (L(377.0), (1300, 330)), (L(377.5), (1320, 360), 'eo')), scale=0.95, layer='mid',
                  rot=K((0, -4), (L(377.0), -4), (L(377.5), 14, 'eo')), t0=-1))
    s.add(Stamp('PROBABLY A MYTH', PAL.RED, 96, angle=-8, pos=(960, 880), t0=L(377.26)))
    s.camera.shake(L(377.3), amp=14)

    # ------------------------------------------------ 16 the writer wasn't on the island
    s, L = new(Sepia(), Camera(push=0.6, drift=(0, 0), wander=2), 'writer')
    m = s.add(FlatMap(center=K((0, (93.6, 19.15)), (2.78, (93.3, 19.15), 'linear')), zoom=K((0, 170), (2.78, 160, 'linear')),
                      style='sepia', island=True,
                      smoke=[(93.75, 19.2, 0.0), (93.85, 19.0, 0.3), (93.65, 19.3, 0.6), (93.9, 18.9, 0.9)]))
    s.add(Human(pos=lambda t, m=m: (m.xy(92.75, 19.15, t)[0], m.xy(92.75, 19.15, t)[1] + 60), scale=0.42, pose='clipboard',
                coat='#6B5A3E', hat=None, facing='right', layer='mid'))
    s.add(Pill('THE WRITER', 'dark', size=30, pos=(420, 200), target=lambda t, m=m: m.xy(92.75, 19.6, t), t0=0.2))
    s.add(Pill('THE BATTLE', 'red', size=30, pos=(1500, 200), target=lambda t, m=m: m.xy(93.8, 19.35, t), t0=0.4))
    s.add(Pill('NOT ON THE ISLAND', 'cyan', size=44, pos=(700, 900), t0=L(380.28)))

    # ------------------------------------------------ 17 2000: herpetologist interviews survivors
    pl = Riverbank(600, mud=True, mangroves=True, bank_x=700, seed=13)
    s, L = new(pl, Camera(push=0.8, drift=(4, 0), wander=2), 'interviews')
    s.add(Human(pos=(1000, pl.bank_y(1000)), scale=0.6, pose='clipboard', coat='lab', glasses=True, hat=None, facing='right',
                layer='mid'))
    s.add(Human(pos=(1330, pl.bank_y(1330)), scale=0.58, pose=lambda t: 'point' if 2.4 < t < 3.6 else 'stand', coat='#8A6D4A',
                hat=None, hair='#D8D4CC', facing='left', layer='mid'))
    s.add(Human(pos=(1530, pl.bank_y(1530)), scale=0.55, pose='shrug', coat='#5E6E8A', hat=None, hair='#E4E0D8',
                facing='left', layer='mid'))
    s.add(SpeechBubble(pos=(1390, 270), tail=(-1, 1), t0=L(384.14)))
    s.add(SpeechBubble(pos=(1600, 330), tail=(-1, 1), t0=L(385.66)))
    s.add(StatBox('2000', sub='INTERVIEWS ON RAMREE', t0=L(382.16), t_sub=L(383.76) - L(382.16)))
    s.add(Pill('HERPETOLOGIST', 'cyan', size=32, pos=(800, 330), target=(1000, 430), t0=L(383.20)))
    s.add(Pill('LIVED THROUGH IT', 'dark', size=30, pos=(1450, 950), t0=L(385.66)))

    # ------------------------------------------------ 18 only 10-15 soldiers crossing a tidal creek
    s, L = new(Mangrove(horizon=430, haze=0.4, seed=12), Camera(push=0.8, drift=(-6, 0), wander=2), 'creek')
    s.add(Soldiers(n=13, spread=(460, 70), size=1.2, seed=12, pos=K((0, (1350, 640)), (5.18, (900, 650), 'linear')),
                   color='#1E2A24', ripple='#C9D2B0', layer='mid'))
    s.add(CrocEyes(pos=K((0, (300, 820)), (5.18, (600, 760), 'linear')), scale=1.0, view='side', water='#1E3A34', layer='mid'))
    s.add(CrocEyes(pos=K((0, (1750, 860)), (5.18, (1500, 800), 'linear')), scale=0.9, view='side', water='#1E3A34', layer='mid'))
    s.add(Panel(w=760, h=220, pos=(960, 160), alpha=0.78, t0=L(388.6)))
    s.add(Counter(0, 10, dur=0.25, size=120, font='black', color=PAL.RED, align='right', pos=(985, 200), t0=L(388.78)))
    s.add(Label('–15', size=120, font='black', color=PAL.RED, align='left', pos=(985, 200), reveal='wipe', t0=L(389.16)))
    s.add(Label('KNOWN CROCODILE DEATHS', size=30, font='bold', track=0.24, align='center', pos=(960, 248), t0=L(388.78)))
    s.add(Pill('TIDAL CREEK', 'dark', size=36, pos=(560, 980), target=(700, 700), t0=L(391.12) - 0.05))

    # ------------------------------------------------ 19 the rest: gunfire, drowning, disease, starvation
    s, L = new(Board(), Camera(push=0.6, drift=(0, 0), wander=2), 'pie')
    s.add(Croc(pos=K((0, (2200, 860)), (4.35, (-200, 860), 'linear')), scale=0.55, variant='xray', opacity=0.3, layer='back'))
    grey = ['#8A9497', '#6F7A7D', '#9DA6A8', '#7B8588']
    s.add(Pie([('CROCODILES', 0.018, PAL.RED, 0.15),
               ('GUNFIRE', 0.2455, grey[0], L(393.08)), ('DROWNING', 0.2455, grey[1], L(393.94)),
               ('DISEASE', 0.2455, grey[2], L(394.72)), ('STARVATION', 0.2455, grey[3], L(395.30))],
              R=270, start=-100, pos=(960, 590), layer='mid'))
    s.add(Label('HOW MOST OF THE REST DIED', size=36, font='bold', track=0.22, align='center', pos=(960, 160),
                t0=L(392.44)))

    # ------------------------------------------------ 20 mostly a war
    s, L = new(Sepia(), Camera(push=0.7, drift=(0, 0), wander=2), 'war')
    s.add(Rosette(pos=(960, 260), scale=1.0, layer='mid', strike=((0, 1), L(396.5)), rot=K((0, -3), (3.6, 3)), t0=-1))
    s.add(Stamp('MOSTLY A WAR', PAL.RED, 120, angle=-7, pos=(960, 840), t0=L(399.20)))
    s.camera.shake(L(399.24), amp=14)

    # ------------------------------------------------ 21 the crocodiles just got the credit
    s, L = new(Black(particles=True), Camera(push=1.2, drift=(0, 0), wander=2), 'credit')
    s.add(Croc(pos=K((0, (1620, 790)), (2.08, (1520, 790), 'linear')), scale=0.5, facing='left', gait=1.0, swim=0.3,
               jaw=K((0, 0), (1.3, 0), (1.6, 22), (2.08, 18)), layer='mid'))
    s.add(CreditRoll([('STARRING', 34, PAL.ORANGE), ('', 20, PAL.WHITE), ('CROCODILES', 150, PAL.WHITE),
                      ('', 40, PAL.WHITE), ('ALSO FEATURING', 26, PAL.GREY), ('GUNFIRE', 30, PAL.GREY),
                      ('DROWNING', 30, PAL.GREY), ('DISEASE', 30, PAL.GREY), ('STARVATION', 30, PAL.GREY)],
                     speed=70, pos=(960, 180)))
    s.add(Punchline('…GOT THE CREDIT.', size=96, pos=(960, 1010), t0=L(401.34) - 0.05))
    s.camera.shake(L(401.36), amp=10)
    return shots
