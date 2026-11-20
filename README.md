# Dictionnaire — French → English

A simple, black-themed French to English dictionary you can install on your iPhone.
It works offline once installed.

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

It's a static site (`index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, `data/`, `icons/`), so any static host works.
On GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**, then pick the branch and `/ (root)`.

## Data

Dictionary data comes from [FreeDict fra-eng](https://github.com/freedict/fd-dictionaries/tree/master/fra-eng),
licensed GPL-2.0 or later. `tools/build_dict.py` turns its TEI file into `data/dict.json`, and
`tools/make_icons.py` draws the icons. After changing app files, bump `CACHE` in `sw.js` so installed copies update.
