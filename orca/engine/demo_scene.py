"""Engine demo (~20 s). Render:
    cd /workspace/work/orca && python -m engine.render engine.demo_scene engine/demo.mp4 --scale 0.5
"""
import math
from engine import *

def build(words=None):
    shots = []

    # 1 — open water: orca glides past the diver, pills on the words, emphasis push
    s = Shot(5.0, plate=Underwater(depth=0.25, seed=3), camera=Camera(push=0.8, drift=(-8, -2)), name='pass')
    s.add(FishSchool(pos=(420, 300), n=46, radius=170, mode='stream', fish_len=34, layer='back', scale=0.8))
    diver = s.add(Diver(pos=K((0, (1180, 640)), (5, (1120, 630), 'linear')), scale=0.42, facing='left', torch=True, layer='mid', z=2))
    orca_pos = K((0, (2050, 470)), (5.0, (420, 430), 'linear'))
    s.add(Orca(pos=orca_pos, scale=0.78, rot=-2, layer='mid', z=1))
    s.add(Bubbles(pos=(1500, 980), rate=3, spread=30, layer='fg'))
    s.add(Pill('YOU', 'dark', size=30, pos=(1180, 470), target=(1135, 600), t0=0.6))
    s.add(Pill('ORCA', 'red', size=30, pos=lambda lt: (orca_pos(lt + 1.7)[0] + 40, 230), target=lambda t: (orca_pos(t)[0] - 60, orca_pos(t)[1] - 40), t0=1.7))
    s.add(StatBox('UP TO 8 M', sub='~6 TONNES', t0=2.7, t_sub=0.45))
    s.camera.emphasis(2.4, 4.6, 0.18, target=(1060, 560))
    shots.append(s)

    # 2 — blueprint board: x-ray orca, counter, dimension line, orange diver inside the mouth
    s = Shot(4.5, plate=Board(), camera=Camera(push=0.7, drift=(4, 0), wander=3), name='xray')
    s.add(Orca(pos=(980, 600), scale=1.02, variant='xray', jaw=K((0, 0), (1.4, 0), (2.2, 26, 'eo')), swim=0.5, layer='mid'))
    s.add(Diver(pos=(575, 640), scale=0.27, xray=True, facing='left', bubbles=False, layer='mid', t0=2.4, kick=0.6))
    s.add(DimensionLine((470, 860), (1510, 860), label='8 METRES', sub='LARGEST MALES', t0=0.9, layer='mid'))
    s.add(Counter(0, 9600, dur=1.4, fmt='{:,.0f}', suffix=' KG', size=84, pos=(960, 150), t0=0.3, unit='record weight, male'))
    s.add(Stamp('NOT A FISH', PAL.CYAN, 48, pos=(1480, 300), t0=3.2))
    shots.append(s)

    # 3 — chapter card (dip to black in)
    shots.append(chapter_shot('THE HUNT', 'IT PLANS AHEAD', 2, dur=3.6,
                              labels=['SIZE', 'HUNT', 'SPEED', 'BRAINS', 'BOATS', 'VERDICT']))

    # 4 — surface cross-section, REC: orca hits the rudder
    plate = Surface('day', waterline=560, sun=(0.7, 0.16))
    s = Shot(5.0, plate=plate, camera=Camera(push=0.5, drift=(0, 0), wander=2), name='rudder')
    boat = Sailboat(pos=(1010, 560), scale=0.62, facing='right', plate=plate, layer='mid', z=1,
                    damage=lambda lt: 'ok' if lt < 2.6 else 'broken',
                    rudder=K((0, 0), (2.6, 0), (2.7, 35, 'eo'), (3.4, -10)))
    s.add(boat)
    rp = boat.rudder_world(2.6)
    hit = (rp[0] - 30, rp[1] + 10)
    s.add(Orca(pos=K((0, (-320, 900)), (2.6, (hit[0] - 250, hit[1] + 40), 'ei'), (3.2, (hit[0] - 330, hit[1] + 70), 'eo'),
                     (5, (-500, 980), 'ei')),
               rot=K((0, -8), (2.6, -12), (3.2, 10, 'eo'), (5, 12)), scale=0.5, facing='right', layer='mid', z=2,
               jaw=K((2.2, 0), (2.5, 14), (2.8, 0))))
    s.add(boat.rudder_piece(2.6, layer='mid', z=0))
    impact(s, 2.6, hit, amp=18, gravity=60)
    s.add(Pill('RUDDER', 'red', size=28, pos=(hit[0] - 260, hit[1] + 200), target=hit, t0=1.1, t1=2.6))
    s.add(StatBox('STRAIT OF GIBRALTAR', t0=0.2, size=40, pos=(96, 150)))
    rec_shot(s, tc_start=13 + 1 / 30, jumps=[(3.8, 21.4)])
    shots.append(s)

    # 5 — stamp gag (aftermath, no REC)
    s = Shot(2.6, plate=Surface('day', waterline=600, sun=(0.7, 0.16)), camera=Camera(push=1.0, drift=(0, 0)), name='gag')
    s.add(Sailboat(pos=(900, 600), scale=0.5, facing='right', plate=s.plate, damage='missing', heel=3, layer='mid',
                   rudder=0))
    s.add(Orca(pos=K((0, (1500, 640)), (2.6, (1850, 610), 'linear')), scale=0.32, facing='right', layer='mid', swim=1.2))
    s.add(Stamp('NO STEERING', PAL.RED, 68, pos=(980, 230), t0=0.45))
    s.add(Pill('ORCA', 'orange', size=26, pos=(1620, 520), target=lambda t: (1500 + 350 * t / 2.6 + 40, 620), t0=1.2))
    shots.append(s)
    return shots
