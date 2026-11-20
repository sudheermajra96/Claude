"use strict";
// Vocab game: pick a level (A1–B2), then 10 questions with 4 choices each.
// After each answer: right/wrong, the correct meaning and an example sentence.
const GAME_LEN = 10;
const LEVEL_ICONS = { A1: "🌱", A2: "🌿", B1: "🌳", B2: "🏔️" };
let best = load("gameBest", {});

function gameLevels() {
  screen("Vocab game",
    `<p class="meta center" style="margin-top:16px">Choose your level</p>` +
    LEVELS.map((l) => `<button class="level" data-go="play" data-t="${l.id}">` +
      `<span class="lvl">${l.id}</span><span class="tname">${LEVEL_ICONS[l.id]} ${esc(l.name)}` +
      `<span class="meta">${l.words.length} words${best[l.id] != null ? ` · best ${best[l.id]}/${GAME_LEN}` : ""}</span></span>` +
      `<span class="chev">›</span></button>`).join(""),
    home);
}

function gamePlay(levelId) {
  const level = LEVELS.find((l) => l.id === levelId);
  const qs = shuffle(level.words.slice()).slice(0, GAME_LEN);
  let i = 0, score = 0;

  const show = () => {
    if (i >= qs.length) return gameOver(levelId, score);
    const w = qs[i];
    const others = shuffle(level.words.filter((x) => x.en !== w.en)).slice(0, 3);
    const choices = shuffle([w, ...others]);
    screen(`${levelId} · Vocab game`,
      `<div class="progress">Question ${i + 1} of ${qs.length} · Score ${score}</div>${bar(i, qs.length)}` +
      `<div class="qword">${esc(w.fr)} ${sayBtn(w.fr)}</div><div class="meta center">What does this mean?</div>` +
      `<div class="opts">${choices.map((c, n) => `<button class="opt" data-n="${n}">${esc(c.en)}</button>`).join("")}</div>` +
      `<div id="feedback"></div>`,
      gameLevels);
    speak(w.fr);

    P.querySelectorAll(".opt").forEach((b) => b.onclick = () => {
      const ok = choices[+b.dataset.n] === w;
      if (ok) score++;
      P.querySelectorAll(".opt").forEach((o) => {
        o.disabled = true;
        if (choices[+o.dataset.n] === w) o.classList.add("right");
      });
      if (!ok) b.classList.add("wrong");
      const fb = document.getElementById("feedback");
      fb.innerHTML =
        `<div class="verdict ${ok ? "good" : "bad"}">${ok ? "✓ Correct!" : `✗ Wrong — <b>${esc(w.fr)}</b> means <b>${esc(w.en)}</b>`}</div>` +
        `<div class="example"><div class="ex-label">Example</div>` +
        `<div class="ex-fr">${esc(w.exFr)} ${sayBtn(w.exFr)}</div><div class="ex-en">${esc(w.exEn)}</div></div>` +
        `<button class="btn primary wide" id="gnext">${i + 1 < qs.length ? "Next →" : "See score"}</button>`;
      document.getElementById("gnext").onclick = () => { i++; show(); };
      fb.scrollIntoView({ behavior: "smooth", block: "end" });
    });
  };
  show();
}

function gameOver(levelId, score) {
  const isBest = best[levelId] == null || score > best[levelId];
  if (isBest) { best[levelId] = score; save("gameBest", best); }
  const pct = score / GAME_LEN;
  screen(`${levelId} · Vocab game`,
    `<div class="result"><div class="emoji">${pct >= 0.8 ? "🎉" : pct >= 0.5 ? "👍" : "💪"}</div>` +
    `<div class="big">${score} / ${GAME_LEN}</div>` +
    `<div class="meta">${isBest ? "New best score!" : `Best: ${best[levelId]} / ${GAME_LEN}`}</div></div>` +
    `<div class="row"><button class="btn" data-go="levels">Change level</button><button class="btn primary" data-go="play" data-t="${levelId}">Play again</button></div>`,
    gameLevels);
}
