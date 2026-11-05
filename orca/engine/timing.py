"""Word-timing helpers so scene modules sync visuals to the VO.

words = list of {"word": str, "start": float, "end": float} (global seconds,
e.g. audio/words.json from whisper). All helpers are forgiving about
punctuation and case.
"""
import re

def _norm(s):
    return re.sub(r"[^a-z0-9']", '', s.lower())

class Words:
    def __init__(self, words):
        self.w = words or []
        self.n = [_norm(x.get('word', x.get('text', ''))) for x in self.w]

    def find(self, phrase, after=0.0, which='start'):
        """Global time of the first occurrence of `phrase` (one or more words)
        starting at/after `after` seconds. which='start'|'end'."""
        toks = [_norm(t) for t in phrase.split()]
        for i in range(len(self.n) - len(toks) + 1):
            if self.w[i]['start'] + 1e-6 < after: continue
            if self.n[i:i + len(toks)] == toks:
                return self.w[i]['start'] if which == 'start' else self.w[i + len(toks) - 1]['end']
        raise KeyError(f'phrase not found after {after:.2f}s: {phrase!r}')

    def sentence_starts(self, t0=0.0, t1=1e9):
        """Start times of words that begin a sentence (after . ? ! or a gap > 0.45 s)."""
        out = []
        for i, x in enumerate(self.w):
            if not (t0 <= x['start'] < t1): continue
            prev = self.w[i - 1] if i else None
            if prev is None or re.search(r'[.?!…]$', prev.get('word', '').strip()) or x['start'] - prev['end'] > 0.45:
                out.append(x['start'])
        return out

def cut_at(t_sentence, lead_frames=3, fps=30):
    """House rule: hard cuts land ~3 frames before the sentence's first word."""
    return max(0.0, t_sentence - lead_frames / fps)

def local(t_global, shot_start):
    """Convert a global VO time to shot-local time."""
    return t_global - shot_start
