# Depth Theory motion-graphics engine — API

Code-driven 2D vector engine (cairo via **cairocffi**, which uses the system `libcairo.so.2`;
`pip install pycairo` does not build on this aarch64 box — `pip install cairocffi fonttools` is all
that's needed). Frames are drawn in **design units (1920×1080)** whatever the output size, piped as raw
BGRA to ffmpeg → H.264 yuv420p, 30 fps.

```
engine/
  core.py         colours (PAL), easing, K() keyframes, Element/Group/Fn, Camera, Shot
  text.py         fonts (Raleway XB/Black/Bold/SemiBold/Regular, Archivo Black, Poppins, Marker), draw_text
  plates.py       Underwater, Abyss, Board, Black, Danger, Sepia, Surface, TopDown, Sonar, corner_brackets,
                  + croc kit: Riverbank, Mangrove, Reef, MurkyWater
  chars/          orca.py (Orca, OrcaHeadOn, OrcaBelow, OrcaTop), diver.py, boats.py, animals.py, human.py, props.py,
                  croc.py (Croc, CrocTop, CrocHead, CrocHeadOn, CrocEyes, Hatchling), wildlife.py (croc-video cast)
  ui.py           pills, labels, stamps, counters, chapter card, REC, globe, polaroid, lists, charts …
  fx.py           impact(), Ring, Debris, Bubbles, SonarRings, Splash, SpeedLines, white_flash
  transitions.py  cut, dip, dissolve, ink, lens (silhouette passes lens), flash
  presets.py      chapter_shot()
  timing.py       Words(words).find('phrase', after=…), cut_at(), sentence_starts()
  render.py       Timeline, CLI
  demo_scene.py   the proof-of-concept scene (demo.mp4)
  fonts/dt/       renamed static TTFs (auto-registered into ~/.fonts on import)
  data/           Natural Earth 110 m land + countries (globe)
  ref/            reference stills pulled from the two source videos
  test/           kit_scene.py (every asset once), stills.py, comparison sheets,
                  croc_kit.py (+ croc_kit_sheet.py -> croc_kit_sheet.png): every croc-kit asset
```

## 1. Quick start

```python
# scenes/act2.py
from engine import *

def build(words=None):          # words = list of {"word","start","end"} (global s) or None
    s = Shot(4.0, plate=Underwater(depth=0.3), camera=Camera(push=0.8))
    orca = s.add(Orca(pos=K((0, (2100, 480)), (4, (500, 450), 'linear')), scale=0.7))
    s.add(Diver(pos=(1150, 640), scale=0.42, facing='left'))
    s.add(Pill('YOU', 'dark', pos=(1150, 480), target=(1140, 610), t0=0.6))
    s.camera.emphasis(2.0, 3.8, 0.2, target=(1100, 560))
    return [s]
```
Render (from `/workspace/work/orca`):
```
python -m engine.render scenes.act2 renders/act2_prev.mp4 --scale 0.5            # 960x540 preview
python -m engine.render scenes.act1 scenes.act2 renders/a12.mp4 --scale 1 --jobs 2 # several modules, 1080p
python -m engine.render scenes.act2 out.mp4 --start 12 --end 18                    # time range only
python -m engine.render scenes.act2 frame.png --still 3.2 --scale 1                # one PNG
python -m engine.render scenes.act2 out.mp4 --words audio/words.json              # passes words to build()
```
Python: `Timeline(shots).render(path, scale=0.5, t_start=0, t_end=None, jobs=2)`, `.still(T, png, scale)`.
Ignore the harmless `RuntimeWarning: 'engine.render' found in sys.modules` from `python -m`.

**Scene-module contract:** each module exposes `build(words) -> list[Shot]`. Shots play end to end
in list order (modules concatenated in CLI order). To lock a cut to the VO, set
`shot.abs_start = cut_at(W.find('Then the water'))`; the Timeline stretches/trims the previous shot so
the cut lands on that frame. Inside a shot, all times are **shot-local seconds** (`t_global - shot.start`).

```python
from engine.timing import Words, cut_at
W = Words(words)
t_cut = cut_at(W.find('In July 2024'))          # 3 frames before the sentence (house rule)
s = Shot(dur, ...); s.abs_start = t_cut
s.add(StatBox('JULY 2024', t0=W.find('July') - t_cut))   # text on the word's first frame
```

## 2. Core model

### Element
Every drawable subclasses `Element(pos=(x,y), scale=1, rot=deg, opacity=1, t0=0, t1=None, layer='mid', z=0, anchor=(0,0), children=[])`.
- Any of `pos/scale/rot/opacity` can be a constant, a keyframe track `K(...)`, or a callable `f(local_t)`.
- `t0/t1` = visibility window in shot time; `draw(ctx, t)` receives **local** time `t - t0`.
- `scale` may be `(sx, sy)`. Children inherit the transform (`Group().add(a, b)`).
- `el.proc(fn)` attaches per-frame procedural motion: `fn(el, lt) -> {'dpos':(dx,dy), 'drot':d, 'dscale':k, 'pos':…, 'rot':…, 'opacity':…}`.
- `Fn(lambda ctx, t: ..., pos=…)` wraps a plain drawing function.

### Keyframes & easing
```python
K((0, (100, 500)), (1.2, (900, 480), 'eio'), (2.0, (900, 480), 'hold'), (2.5, (1200, 300), 'eo'))
```
Key = `(t, value[, ease])`; the ease applies to the segment *starting* at that key (default `'eio'`).
Values: numbers, tuples, or `'#RRGGBB'` colours. Eases: `linear`, `eio` (AE easy-ease 70 % influence,
cubic-bezier .7,0,.3,1), `eio66`, `eo` (graphics), `ei` (accelerate toward lens), `eo3`, `ei2`, `sine`,
`hold`, `back` (tiny overshoot – badges only). Helpers: `remap(t, t0, t1, v0, v1, e)`, `ease(name, x)`, `lerp`.

### Shot & layers
`Shot(dur, plate=None, camera=Camera(), name='', trans_in=None)`; `s.add(el, layer=…)` returns the element.
Draw order: plate bg (parallax .35, Surface/TopDown 1.0) → `back` (.7) → `mid` (1.0) → `fg` (1.35) →
plate fg (vignette, brackets, waterline) → `overlay` (screen space, no camera) → `shot.post` fns.

### Camera (world layers only)
`Camera(push=0.8 %/s, drift=(10,-3) px/s, wander=6 px, focus=(960,540), zoom=1.0)` — always moving by default.
- `.emphasis(t0, t1, amount=0.2, target=(x,y), e='eio')` push +15–30 % re-centring on target
- `.crash(t0, dur=0.25, amount=1.2, target=…)` crash zoom (ease-in)
- `.pull(t0, t1, amount)` pull back
- `.shake(t0, amp=14, decay=0.4)` decaying ±8–20 px shake
- `.handheld(amp=2.5, freq=1.0, t0, t1)` REC wobble
- `StaticCamera()` for locked shots; `.to_screen(p, t)` world→screen.
UI elements created with `world=True` (Pills with a `target` default to this) ride the camera while
staying crisp: their `pos`/`target` are world coordinates.

### Transitions (`shot.trans_in` on the INCOMING shot; they straddle the cut, shot timing never changes)
`None`/`'cut'` · `('dip', 0.7)` topic break / before chapter cards · `('dissolve', 1.0)` continuity ·
`('ink', 0.6)` smoke blooms through black · `('lens', 0.8)` defocused orca silhouette sweeps across
the lens, cut hidden behind it · `('flash', 0.2)` white flash at head of shot. Impacts inside a shot
use `fx.impact()` (its own 6-frame white frame).

## 3. Plates (`engine.plates`)
| Plate | Notes |
|---|---|
| `Underwater(style='v2'|'v1', depth=0..1, rays=True, particles=True, surface=False, vignette=.42, tint=None)` | v2 soft fan of god-rays from top centre (blurred), v1 hard wedges from top-left; gradient × oval vignette; specks + soft discs in 3 parallax depths; rays shimmer/sway. No grain. |
| `Abyss()` | depth .95, no rays |
| `Board(tint='teal'|'maroon'|'indigo'|'sepia', grid=49, brackets=True)` | blueprint data board #0B2530, grid one shade lighter, white corner brackets (2 px, inset 18, arms 60) |
| `Black(particles=False)` / `Danger(grid=False)` / `Sepia(dark=False, grid=False)` | void / maroon danger / cream paper with painted speckle + fibres (dark=True: sepia grid world) |
| `Surface(preset='day'|'haze'|'dawn'|'storm', waterline=620, sun=(.62,.18), mountains=False, wave_amp=5)` | sky gradient + sun glow + horizon band, animated white waterline, water below with soft rays & particles. `plate.water_y(x, t)` for floating props (boats/floes pass `plate=`). Drawn at parallax 1. |
| `TopDown()` | teal top-down ocean with drifting wavy-line texture |
| `Sonar(origin=(80,600))` | #000503 screen, green polar grid, 1.2 s sweep |
`corner_brackets(ctx, inset, arm, width, alpha, box)` is reusable anywhere.

## 4. Characters (`engine.chars`) — local units, flat fills + v2 outline/line detail
- **`Orca(facing='left'|'right', dorsal='male'|'female', variant='side'|'xray'|'silhouette', swim=1, period=3.0, jaw=deg|K, blink='auto'|[t…], bend=0, pec_flap=1, outline=8, tint=None, xray_color=PAL.CYAN)`**
  Body 1000 units nose→flukes (scale .6 ≈ 600 px). Black body with painted sheen + navy rim light, white eye patch, belly/flank patch, grey saddle, interlocking conical teeth when `jaw>0` (≈25–30° = wide open), eye blink, pectoral flap, head-pinned sine swim (tail ±13 px at scale .6, mid-body ≈3 px), fluke pitch.
  `variant='xray'`: cyan glowing outline + skeleton (skull, jaw, spine, ribs, flipper bones), translucent fill — use on `Board()`, put `Diver(xray=True)` (orange outline) inside.
  `Orca.breach(pos, scale, facing)` = nose-up arched pose, almost no swim (animate pos on linear keys: rise 280 px/s, hang 0.7 s, fall 585 px/s).
- `OrcaHeadOn(jaw=0..1, dorsal)` front view toward the lens (animate `scale` with `'ei'`).
- `OrcaBelow(colored=False, color='#05151F')` silhouette seen from below (chapter-card overhead pass); `colored=True` shows the white belly.
- `OrcaTop()` top-down (black back, saddle, patch slivers, dorsal ridge, beating flukes).
- `orca_silhouette_path(ctx)` adds the side silhouette path (for masks).
- **`Diver(facing='right', kick=1, period=0.78, torch=False, bubbles=True, panic=0..1, xray=False)`** black suit, yellow fins with rib lines, white tank, teal BCD, white-framed mask, regulator bubble puffs.
- **`Sailboat(facing='right', plate=<Surface>, rudder=deg|K, damage='ok'|'cracked'|'broken'|'missing' or callable(lt), heel=deg, sails=True, crew=1)`** keel + spade rudder visible below the waterline (submerged parts water-tinted). `boat.rudder_world(t)` → impact point; `boat.rudder_piece(t_break)` → snapped blade tumbling down. `Speedboat(crew=2, plate=…)`.
- `Shark(jaw=deg)` great white side view; `Seal(look=0..1)`; `IceFloe(width, plate, tilt)`; `Fish(length)`;
  `FishSchool(n, radius, mode='ball'|'stream', fish_len, tighten=K, scatter=K)` herring ball / school;
  `BlueWhale(silhouette=False)` (1000 units = 30 m → orca 8 m is scale ×0.27 of it);
  `Human(coat='#2F6FA0'|'lab', pose='stand'|'point'|'shrug'|'clipboard'|'wave'|'panic', glasses, hat)`.
- Size props: `Bus/Elephant/Car/Person(height=px, color, outline)`; `comparison_silhouette('bus', metres_per_px)` builds one at true scale (bus 12×3 m, elephant 6×3.2, car 4.5×1.5, person 1.8).

## 4b. Croc kit (saltwater-crocodile video) — all exported by `from engine import *`
### Crocodile rig (`chars/croc.py`) — one 2.5-D model for every view; 1000 units snout→tail tip, faces LEFT, origin mid-body (belly ≈ +72/+86, walking feet ≈ +118, back ≈ −78)
- **`Croc(facing='left'|'right', variant='side'|'xray'|'silhouette', swim=1|K, period=2.6, gait=0..1|K (0 swim … 1 high-walk), walk_period=1.4, jaw=deg|K (0..55), blink='auto'|[t…]|None, submerged=0..1|K, waterline=0, water='#2B4A3E', roll=deg|K, turn=0, legs=True|False|'sprawl', domes=False, dome_glow=0..1|K, eye_scale=1.2, tooth_scale=0.9, outline=6, tint=None, palette='adult'|'hatchling', sil_color, xray_color, phase=0)`**
  - `roll`: rotation about the long axis. 0 = hero side view, −90 = top view; animate 0→−360 for the **death roll** (pale belly comes round).
  - `submerged` (0..1) + `waterline` (local y of the surface): parts below the line are tinted toward `water` (match the plate: `'#24443A'` river, `'#2C8F94'` reef). Put the croc's `pos.y` on the plate's waterline and set `submerged≈0.5` for "eyes and back showing".
  - Helpers (all return LOCAL, pre-transform points; add `pos`/`scale` yourself): `point(t, x, th_deg=0, depth=0)` any body location (x along body, theta round it); `stomach_point(t)` (x-ray stomach contents, swallowed stones); `jaw_tip(t)` between the jaw tips (prey/objects held in the mouth).
- `CrocTop(**Croc kw)` top-down (roll −90, legs sprawled, `turn` bends the body). `CrocHead(jaw, domes=True, dome_glow=K, breathe=1)` big profile head, origin mid-head, use scale 2–4 (jaw/teeth/sensory-dome close-ups). `Hatchling(**Croc kw)` banded yellow baby, big eyes.
- `CrocHeadOn(jaw=0..1|K, bob=1, eyes_glow=0..1|K, legs=True, outline=6)` front view toward the lens, ~640 units wide, origin = jaw line centre.
- `CrocEyes(view='side'|'front', ripples=True, body=True, eyeshine=0..1|K, drift=1, water)` just eyes + nostrils breaking a waterline at local y=0 (~300 units); `eyeshine` = orange night torch reflection.
- **Limits:** open jaw is only correct near `roll≈0` (side view); ~40 ms per croc per frame at 1080p (budget 2–3 crocs per shot); no tongue/palatal-valve articulation.

### Cast (`chars/wildlife.py`) — side views facing LEFT, `facing`, `style='color'|'silhouette'|'outline'` (outline = cyan line-art for evidence boards; `outline_color`, `dash`), `sil_color`, `outline=6`; origin = ground under the body
- `Tiger(pose='stand'|'drink'|'dragged'|'lying', walk=0..1, missing_leg=False)` ~620 units. `Buffalo(pose, walk)` water buffalo ~560. `Pig(pose='stand'|'root', walk)` feral boar ~300. `Hyena(jaw=deg, walk)` ~420.
- `BullShark(swim=1, period=2.0, jaw=deg, thrash=0..1)` origin mid-body.
- `Snorkeller(kick=1, period=0.7, panic=0..1, suit, fins, snorkel)` face-down AT the surface: local y=0 = waterline (put `pos.y` on the plate's `surface_y`).
- `Fisherman(line_to=(dx,dy) local end of the line, bite=0..1, cap=True, coat, pants)` standing with rod. Props: `Esky(color)` cooler ~110 wide, `Bucket(color)` ~60 wide (origin bottom-centre).
- `Human(pose='crouch')` new: squatting at the water's edge, hands forward (all other poses unchanged).

### Plates (`plates.py`) — flat house look, each gently animated
| Plate | Notes |
|---|---|
| `Riverbank(waterline_y=560, mud=True, mangroves=True, bank_x=1250, wave_amp=3, roots=True, particles=True, vignette=.3)` | split view: hazy sky + far mangrove treeline + mud bank (right, from `bank_x`) with mangroves; below: murky olive river (#24443A→#0A1714), river bed, silt. Animated waterline, drifting ripple dashes, swaying hanging roots, silt drift. Parallax 1. `water_y(x,t)` surface, `bank_y(x)` top of the mud (stand people/buckets on it). |
| `Mangrove(horizon=430, density=1, haze=.5, particles=True, vignette=.4)` | swamp at water level: layered forest, side stands with prop roots + reflections, still olive-teal water (#1E3A34) with drifting ripple lines, floating leaves. Put `CrocEyes`/submerged crocs on the water (y > horizon). Parallax 1. |
| `Reef(surface_y=None|y, floor=True, rays=True, particles=True, vignette=.32)` | clear turquoise shallows (#4DB3AE→#2C8F94→#0F4C55), bright god-ray fan, pale sand, far teal + near coral (#E08A6B/cyan) silhouettes, swaying soft corals. `surface_y` draws the bright surface underside (snorkellers). |
| `MurkyWater(surface_y=238|None, roots=True, silt=1.0, haze=.6, vignette=.6)` | low-visibility green-brown water, dense drifting silt + haze clouds, roots hanging from the surface (drawn in fg, over characters), flat murk wash + heavy vignette. Give far crocs `tint='#24443A'`, `opacity≈.45`. |

### Size prop
`comparison_silhouette('croc', metres_per_unit)` → `CrocSil` at true scale (6.17 m long, 0.85 m tall; built on the Croc rig, `legs=False` lying flat by default, `legs=True` standing), origin bottom-left like the other silhouettes. Pair with `comparison_silhouette('person', mpu)` (1.8 m) and a `DimensionLine`; `.length` gives its px length.

## 5. Overlay / UI kit (`engine.ui`, default `layer='overlay'`; pops on `t0`, no exit animations)
```python
Pill('ATTACKS', kind='red', pos=(x,y), target=(tx,ty), t0=…)   # kinds: dark red orange cyan green outline white grey
Pill('COMPLETELY UNHURT', 'green', tick=True)  ;  Pill('A PHONE', 'dark', ghost=0.4)  # grey → solid at 0.4 s
Label('TEXT', size=48, font='xb', reveal='fade'|'wipe'|'letters'|'type'|None, align='center')
Typewriter('MICHAEL PACKARD', cps=30)            StatBox('JULY 2024', sub='3 KM OFFSHORE', t_sub=0.5)   # top-left default
CalloutCard('Migration', 'body text…', target=(x,y))   Punchline('…AND RAMMED AGAIN', style='v1'|'v2')
Stamp('NEVER PROVEN', color=PAL.RED, size=64, angle=-6)   # slams 130→100 % in 5 frames, distressed
Counter(26, 30, dur=1.2, suffix=' TONNES', unit='record weight')   QuoteReveal(text, kicker, attribution, word_times=[…])
ChapterTitle('BREACH', 'It comes from above', n=3, total=6, icons=[…], labels=[…])   # or presets.chapter_shot(...)
RecOverlay(tc_start=13.03, jumps=[(2.1, 21.4)])  ;  rec_shot(shot, tc_start, jumps)   # + handheld wobble
Checklist([('Big','tick',0.6), ('Harmless','x',1.4)])   OptionsMenu(['Swim','Dive','Stay still','Fight'], strikes={0:1.2}, selects={3:2.0})
BarChart([1,7], ['Humans','Orcas'])   IconGrid(50, 10, 'orca', lost_from=30, t_lost=0.8)
DimensionLine((x0,y0), (x1,y1), label='8 M', sub='largest males')   # layer 'mid' by default (rides camera)
Balance(tilt=K(...), left='BRAIN', right=callable)   Badge('question', 'A SIGNAL?')   Stopwatch(start=0)
Globe(center=(lon,lat), radius=260, highlight=['Spain','Portugal'], pins=[(lon,lat)], routes=[[a,b,c]], caption='…')
Polaroid(content=fn(ctx,t,w,h) | Element, caption='JUNE 2021', angle=5)   ProgressBar('Translating orca…', t_cancel=2.0)
Letterbox()  Dim(alpha)  icon(ctx, 'orca'|'fin'|'tooth'|'wave'|'eye'|'brain'|'globe'|'question'|'boat'|'fish'|'sonar'|'skull'|'seal'|'heart'|'person', r)
```
Text helpers: `draw_text(ctx, s, x, y_baseline, font, size, color, track_em, align, shadow=True)` (tight hard
shadow), `measure()`. Fonts: `'xb'` Raleway ExtraBold (titles/pills), `'black'` (stamps, punchlines, paper),
`'bold'` (wide-tracked labels, use track≈0.22), `'semi'`, `'reg'`, `'archivo'` (v1 punchlines), `'poppins'`,
`'marker'` (polaroid captions). Raleway's default figures are old-style, as in the reference.
Colours: `PAL.RED #D73F3C, RED_DARK, ORANGE #F0A54A, WHITE #F2F0EB, GREEN #4DB271, CYAN #7FC1CB, CYAN_HI, BOARD, PAPER, INK, SONAR, YELLOW`.

## 6. FX (`engine.fx`)
`impact(shot, t, pos, amp=14, gravity=320)` = white frame fading over 6 frames + two expanding rings +
debris shards & bubbles + camera shake decaying in 0.4 s. Pieces: `Ring`, `Debris`, `white_flash(t)`.
`Bubbles(rate, spread, rise)`, `SonarRings(period=1.2, direction=deg|None)`, `Splash(size)` (surface crown),
`SpeedLines`.

## 7. Recipes
**Chapter card:** `shots.append(chapter_shot('BOATS', 'It comes for the rudder', 5, labels=[...], background=[Orca(..., layer='back')]))` (dip in 0.7 s, title letters 0.2 s, subtitle +0.5 s, navigator, hold ≥3 s).
**REC recreation:** establish the filmer in a plain shot, hard-cut to the same plate with `rec_shot(s, tc_start=13, jumps=[...])`; exit with a hard cut to the plate without REC + status pill.
**Rudder hit:** see `demo_scene.py` shot 4 (`damage=lambda lt: 'ok' if lt < t_hit else 'broken'`, `rudder=K(...)`, `boat.rudder_piece(t_hit)`, `impact(s, t_hit, boat.rudder_world(t_hit))`).
**Stamp gag:** hard cut → `Stamp('PARKED', PAL.RED, t0=word)` (+ sub-drop boom in the mix ~0.3 s before).
**x-ray:** `Board()` + `Orca(variant='xray', jaw=K(...))` + `Diver(xray=True, scale=.25)` + `DimensionLine`.

## 8. Performance (measured on this 2-vCPU sandbox, demo scene)
- 1080p **draw only**, single process: 18–34 fps depending on the shot (heaviest: full-frame underwater with rays + particles + orca).
- 1080p **draw + x264 veryfast**, `--jobs 1`: **12.3 fps**; `--jobs 2`: **18.0 fps** (621 frames in 34.5 s).
- 960×540 preview, `--jobs 2`: ~41–58 fps.
- ⇒ a 10-minute 1080p30 video (18 000 frames) ≈ 17 min with both cores, ≈ 25 min with one. Static plate
  layers are cached per output scale; first frame of each new plate costs ~0.3 s.
Other agents share the 2 CPUs: preview at `--scale 0.5`, render ranges with `--start/--end`.

## 9. Limitations / notes
- Text uses cairo's toy font API: no kerning/ligatures (fine for caps titles); tracking done per glyph.
- Orca jaw rotates the lower contour about a hinge (good to ~35°); no tongue articulation.
- Head-on orca, shark, seal, humans are simpler than the hero side-orca; no top-down boat or ship asset yet.
- No motion blur (house style), defocus only via the `lens` transition. Stock footage is not handled here (grade/insert it in the edit, or add a `VideoPlate` later).
- Pill leader targets on moving characters: pass a callable `target=lambda t: …` (shot time) — see demo.
