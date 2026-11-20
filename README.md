# Dictionnaire — French → English

A simple, black-themed French learning app you can install on your iPhone.
It works offline once installed.

**Vocab game (home screen):** tap *Play vocab game*, pick a level (A1, A2, B1 or B2), and answer
10 questions with 4 choices each. After every answer you see whether it was right, the correct meaning,
and an example sentence. Best score per level is saved. 50 words per level, in `levels.js`.

**A1 practice by topic:** 268 A1-level words in 18 topics (greetings, numbers, food, family…),
with flashcards and a multiple-choice quiz. Words you get right count as learned; progress is saved on the phone.
The word list is in `a1.js`.

**Dictionary:**

- 8,500 French words with English translations, pronunciation (IPA), part of speech and gender
- Accents optional: `etre` finds `être`
- Typing an English word also shows the French words that translate to it
- 🔊 button reads the word aloud in French
- Remembers your recent searches

## Install on iPhone

1. Open the app's link in **Safari**.
2. Tap the **Share** button, then **Add to Home Screen**, then **Add**.
3. Open it from the new icon on your home screen. It runs full-screen and works without internet.

## Hosting

It's a static site (`index.html`, `app.js`, `a1.js`, `practice.js`, `levels.js`, `game.js`, `sw.js`, `manifest.webmanifest`, `data/`, `icons/`), so any static host works.
On GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**, then pick the branch and `/ (root)`.

## Data

Dictionary data comes from [FreeDict fra-eng](https://github.com/freedict/fd-dictionaries/tree/master/fra-eng),
licensed GPL-2.0 or later. `tools/build_dict.py` turns its TEI file into `data/dict.json`, and
`tools/make_icons.py` draws the icons. After changing app files, bump `CACHE` in `sw.js` so installed copies update.
