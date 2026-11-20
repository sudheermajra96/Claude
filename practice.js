"use strict";
// A1 practice: topic list, word list, flashcards and multiple-choice quiz.
const P = document.getElementById("pview");
const PTITLE = document.getElementById("ptitle");
const PBACK = document.getElementById("pback");
const SESSION = 10;

const words = A1_TOPICS.flatMap((t) => t.words.map((w) => {
  const [fr, en] = w.split("|");
  return { key: t.id + ":" + fr, topic: t.id, fr, en };
}));
const byTopic = (id) => words.filter((w) => id === "all" || w.topic === id);
const topicName = (id) => id === "all" ? "All A1 words" : A1_TOPICS.find((t) => t.id === id).name;

function load(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch (e) { return fallback; } }
function save(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }
let known = new Set(load("a1known", []));
function setKnown(w, yes) { yes ? known.add(w.key) : known.delete(w.key); save("a1known", [...known]); }
const knownCount = (list) => list.filter((w) => known.has(w.key)).length;

function speak(text) {
  if (!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/\(.*?\)/g, ""));
  u.lang = "fr-FR";
  u.rate = 0.85;
  speechSynthesis.speak(u);
}
const sayBtn = (fr) => window.speechSynthesis ? `<button class="say" data-say="${esc(fr)}" aria-label="Pronounce">🔊</button>` : "";
const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const bar = (n, total) => `<div class="bar"><i style="width:${total ? (100 * n / total) : 0}%"></i></div>`;

// Pick words for a session, unlearned first.
function pickSession(id) {
  const list = shuffle(byTopic(id).slice());
  list.sort((a, b) => known.has(a.key) - known.has(b.key));
  return list.slice(0, SESSION);
}

let back = null;
function screen(title, html, onBack) {
  PTITLE.textContent = title;
  back = onBack || null;
  PBACK.hidden = !onBack;
  P.innerHTML = html;
  window.scrollTo(0, 0);
}
PBACK.addEventListener("click", () => back && back());

function home() {
  const all = words.length, k = knownCount(words);
  screen("Learn French · A1",
    `<div class="hero"><div class="hero-top"><div><div class="big">${k} / ${all}</div><div class="meta">words learned</div></div>` +
    `<div class="pill">A1</div></div>${bar(k, all)}` +
    `<div class="row"><button class="btn" data-go="cards" data-t="all">🃏 Flashcards</button><button class="btn primary" data-go="quiz" data-t="all">✅ Quiz</button></div></div>` +
    `<div class="section">Topics</div>` +
    A1_TOPICS.map((t) => {
      const list = byTopic(t.id), n = knownCount(list);
      return `<button class="topic" data-go="topic" data-t="${t.id}"><span class="ico">${t.icon}</span>` +
        `<span class="tname">${esc(t.name)}<span class="meta">${n} / ${list.length}${n === list.length ? " · done ✓" : ""}</span>${bar(n, list.length)}</span><span class="chev">›</span></button>`;
    }).join("") +
    `<p class="hint">Progress is saved on this phone.</p>`);
}

function topic(id) {
  const list = byTopic(id);
  screen(topicName(id),
    `<div class="row"><button class="btn" data-go="cards" data-t="${id}">🃏 Flashcards</button><button class="btn primary" data-go="quiz" data-t="${id}">✅ Quiz</button></div>` +
    `<div class="section">${list.length} words · ${knownCount(list)} learned</div>` +
    list.map((w) => `<div class="entry">${sayBtn(w.fr)}<div class="head"><span class="word">${esc(w.fr)}</span>${known.has(w.key) ? `<span class="tick">✓</span>` : ""}</div><div class="trans">${esc(w.en)}</div></div>`).join(""),
    home);
}

function exit(id) { return id === "all" ? home : () => topic(id); }

function done(id, mode, right, total) {
  const pct = Math.round(100 * right / total);
  screen(topicName(id),
    `<div class="result"><div class="emoji">${pct >= 80 ? "🎉" : pct >= 50 ? "👍" : "💪"}</div>` +
    `<div class="big">${right} / ${total}</div><div class="meta">${pct >= 80 ? "Excellent !" : pct >= 50 ? "Bien joué !" : "Keep practising — continue !"}</div></div>` +
    `<div class="row"><button class="btn" data-go="back" data-t="${id}">Back</button><button class="btn primary" data-go="${mode}" data-t="${id}">Practice again</button></div>`,
    exit(id));
}

function cards(id) {
  const queue = pickSession(id), total = queue.length;
  let firstTry = 0;
  const missed = new Set();
  const show = () => {
    if (!queue.length) return done(id, "cards", firstTry, total);
    const w = queue[0];
    screen(topicName(id),
      `<div class="progress">${queue.length} card${queue.length > 1 ? "s" : ""} left</div>` +
      `<button class="card" id="card"><div class="fr">${esc(w.fr)}</div><div class="en">${esc(w.en)}</div><div class="tap">Tap to reveal</div></button>` +
      `<div class="row"><button class="btn" id="again">↺ Again</button><button class="btn primary" id="got">Got it ✓</button></div>` +
      `<div class="center">${sayBtn(w.fr)}</div>`,
      exit(id));
    speak(w.fr);
    const card = document.getElementById("card");
    card.onclick = () => card.classList.add("flipped");
    document.getElementById("again").onclick = () => { missed.add(w.key); setKnown(w, false); queue.push(queue.shift()); show(); };
    document.getElementById("got").onclick = () => { if (!missed.has(w.key)) firstTry++; setKnown(w, true); queue.shift(); show(); };
  };
  show();
}

function quiz(id) {
  const qs = pickSession(id), pool = words;
  let i = 0, right = 0;
  const show = () => {
    if (i >= qs.length) return done(id, "quiz", right, qs.length);
    const w = qs[i];
    // Distractors: prefer the same topic, never the same English meaning.
    const same = shuffle(byTopic(w.topic).filter((x) => x.en !== w.en));
    const other = shuffle(pool.filter((x) => x.topic !== w.topic));
    const opts = [];
    for (const x of same.concat(other)) { if (opts.length === 3) break; if (!opts.some((o) => o.en === x.en)) opts.push(x); }
    const choices = shuffle([w, ...opts]);
    screen(topicName(id),
      `<div class="progress">Question ${i + 1} of ${qs.length}</div>${bar(i, qs.length)}` +
      `<div class="qword">${esc(w.fr)} ${sayBtn(w.fr)}</div><div class="meta center">What does this mean?</div>` +
      `<div class="opts">${choices.map((c, n) => `<button class="opt" data-n="${n}">${esc(c.en)}</button>`).join("")}</div>` +
      `<div id="next"></div>`,
      exit(id));
    speak(w.fr);
    P.querySelectorAll(".opt").forEach((b) => b.onclick = () => {
      const pick = choices[+b.dataset.n], ok = pick === w;
      P.querySelectorAll(".opt").forEach((o) => {
        o.disabled = true;
        if (choices[+o.dataset.n] === w) o.classList.add("right");
      });
      if (ok) { right++; setKnown(w, true); setTimeout(() => { i++; show(); }, 700); }
      else {
        b.classList.add("wrong");
        setKnown(w, false);
        const next = document.getElementById("next");
        next.innerHTML = `<button class="btn primary wide">Next →</button>`;
        next.firstChild.onclick = () => { i++; show(); };
      }
    });
  };
  show();
}

P.addEventListener("click", (e) => {
  const s = e.target.closest("[data-say]");
  if (s) { e.stopPropagation(); return speak(s.dataset.say); }
  const g = e.target.closest("[data-go]");
  if (!g) return;
  const t = g.dataset.t;
  ({ topic, cards, quiz, back: (x) => exit(x)() })[g.dataset.go](t);
});

home();
