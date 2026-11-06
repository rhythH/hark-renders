"""Depth Theory-style 2D vector motion-graphics engine (pycairo/cairocffi -> ffmpeg).
See ENGINE.md. Typical import:

    from engine import *
"""
from .core import (W, H, FPS, PAL, K, Track, ev, ease, remap, lerp, hexc, mix, Element, Group, Fn, Camera,
                   StaticCamera, Shot, set_col, rrect, circle, poly, catmull, stroke_glow, rng)
from . import plates, ui, fx, transitions, chars, text
from .plates import (Underwater, Abyss, Board, Black, Danger, Sepia, Surface, TopDown, Sonar, corner_brackets,
                     Riverbank, Mangrove, Reef, MurkyWater)
from .chars import (Orca, OrcaHeadOn, OrcaBelow, OrcaTop, Diver, Sailboat, Speedboat, rudder_piece, Shark, Seal,
                    IceFloe, FishSchool, BlueWhale, Fish, Human, Bus, Elephant, Car, Person, comparison_silhouette,
                    CrocSil, Croc, CrocTop, CrocHead, CrocHeadOn, CrocEyes, Hatchling,
                    Tiger, BullShark, Buffalo, Pig, Hyena, Snorkeller, Fisherman, Esky, Bucket)
from .ui import (Pill, Label, Typewriter, StatBox, CalloutCard, Punchline, Stamp, Counter, QuoteReveal, ChapterTitle,
                 RecOverlay, rec_shot, Letterbox, Stopwatch, Checklist, OptionsMenu, BarChart, IconGrid, DimensionLine,
                 Balance, Badge, ProgressBar, Globe, Polaroid, Dim, icon)
from .fx import Ring, Debris, Bubbles, SonarRings, Splash, SpeedLines, white_flash, impact
from .presets import chapter_shot
from .text import draw_text, measure
from .render import Timeline
