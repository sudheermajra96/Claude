"use strict";
// Each entry: [french, ipa, partOfSpeech, gender("m"/"f"/""), [english...]]
let DICT = [];
let NORM = []; // normalized French words
const LIMIT = 60;
const q = document.getElementById("q");
const out = document.getElementById("out");
const clearBtn = document.getElementById("clear");

const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function store(key, val) {
  try { if (val === undefined) return JSON.parse(localStorage.getItem(key)); localStorage.setItem(key, JSON.stringify(val)); }
  catch (e) { return null; }
}

function search(text) {
  const n = norm(text);
  if (!n) return { fr: [], en: [] };
  const exact = [], prefix = [], contains = [];
  for (let i = 0; i < DICT.length; i++) {
    const w = NORM[i];
    if (w === n) exact.push(i);
    else if (w.startsWith(n)) prefix.push(i);
    else if (n.length > 2 && w.includes(n)) contains.push(i);
  }
  prefix.sort((a, b) => NORM[a].length - NORM[b].length);
  const fr = exact.concat(prefix, contains).slice(0, LIMIT);
  // Also look in the English side so typing an English word still helps.
  const en = [];
  if (n.length > 1) {
    const re = new RegExp("(^|[^a-z])" + n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^a-z])");
    for (let i = 0; i < DICT.length && en.length < 30; i++) {
      if (fr.includes(i)) continue;
      if (DICT[i][4].some((t) => re.test(norm(t)))) en.push(i);
    }
  }
  return { fr, en };
}

function entryHTML(i) {
  const [w, ipa, pos, gen, tr] = DICT[i];
  const meta = [ipa && "/" + ipa + "/", pos && pos + (gen ? " (" + gen + ")" : "")].filter(Boolean).join(" · ");
  return `<div class="entry"><div class="head"><span class="word">${esc(w)}</span>` +
    `<span class="meta">${esc(meta)}</span>` +
    (window.speechSynthesis ? `<button class="say" data-say="${esc(w)}" aria-label="Pronounce">🔊</button>` : "") +
    `</div><div class="trans">${tr.map(esc).join(", ")}</div></div>`;
}

function showHome() {
  const recent = store("recent") || [];
  out.innerHTML = (recent.length
    ? `<div class="section">Recent</div><div class="chips">${recent.map((r) => `<button class="chip" data-q="${esc(r)}">${esc(r)}</button>`).join("")}</div>`
    : `<p class="empty">Search ${DICT.length.toLocaleString()} French words.<br>Accents are optional — “etre” finds “être”.</p>`) +
    `<footer>Dictionary data: <a href="https://freedict.org/">FreeDict</a> fra-eng, GPL-2.0+</footer>`;
}

function render() {
  const text = q.value;
  clearBtn.style.display = text ? "block" : "none";
  if (!text.trim()) return showHome();
  const { fr, en } = search(text);
  let html = fr.map(entryHTML).join("");
  if (en.length) html += `<div class="section">English matches</div>` + en.map(entryHTML).join("");
  out.innerHTML = html || `<p class="empty">No results for “${esc(text)}”.</p>`;
}

function remember() {
  const t = q.value.trim();
  if (!t) return;
  const recent = (store("recent") || []).filter((r) => r !== t);
  recent.unshift(t);
  store("recent", recent.slice(0, 12));
}

let timer;
q.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(render, 80); });
q.addEventListener("keydown", (e) => { if (e.key === "Enter") { remember(); q.blur(); } });
q.addEventListener("blur", remember);
clearBtn.addEventListener("click", () => { q.value = ""; render(); q.focus(); });
out.addEventListener("click", (e) => {
  const say = e.target.closest("[data-say]");
  if (say) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(say.dataset.say);
    u.lang = "fr-FR";
    u.rate = 0.9;
    speechSynthesis.speak(u);
    return;
  }
  const chip = e.target.closest("[data-q]");
  if (chip) { q.value = chip.dataset.q; render(); }
});

fetch("data/dict.json")
  .then((r) => r.json())
  .then((d) => { DICT = d; NORM = d.map((e) => norm(e[0])); render(); })
  .catch(() => { out.innerHTML = `<p class="empty">Couldn't load the dictionary. Check your connection and reopen the app.</p>`; });

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");

// When a new version is installed, reload once so the update shows straight away.
if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
  let reloaded = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => { if (!reloaded) { reloaded = true; location.reload(); } });
}
