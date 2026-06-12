let locked = false;

/* =========================
   Progress bar by level
========================= */
function setBar(levelName){
  const map = { "Easy": 33, "Medium": 66, "Hard": 100 };
  document.getElementById("barfill").style.width =
    (map[levelName] || 0) + "%";
}

/* =========================
   Enable / Disable buttons
========================= */
function setButtonsDisabled(disabled){
  document.querySelectorAll(".opt").forEach(btn => {
    btn.disabled = disabled;
    btn.classList.toggle("disabled", disabled);
  });
}

/* =========================
   Render question
========================= */
function renderQuestion(q){
  if(!q || !q.question){
    console.warn("Invalid question payload", q);
    return;
  }

  document.getElementById("counter").textContent =
    `Question ${q.question_number} / ${q.total_questions}`;

  document.getElementById("level").textContent =
    `Level: ${q.student_level}`;

  document.getElementById("chosen").textContent =
    `AI chose: ${q.ai_chosen_difficulty}`;

  document.getElementById("eps").textContent =
    `ε: ${q.epsilon}`;

  setBar(q.student_level);

  document.getElementById("question").textContent = q.question;
  document.getElementById("A").textContent = `A) ${q.A}`;
  document.getElementById("B").textContent = `B) ${q.B}`;
  document.getElementById("C").textContent = `C) ${q.C}`;
  document.getElementById("D").textContent = `D) ${q.D}`;

  const result = document.getElementById("result");
  result.textContent = "";
  result.className = "result";

  locked = false;
  setButtonsDisabled(false);
}

/* =========================
   Load next question
========================= */
async function loadQuestion(){
  setButtonsDisabled(true);

  const res = await fetch("/api/next");
  const q = await res.json();

  if(q.done){
    // IMPORTANT: ensure summary is finalized before redirect
    await fetch("/api/summary");
    window.location.href = "/results";
    return;
  }

  renderQuestion(q);
}

/* =========================
   Submit answer
========================= */
async function submitAnswer(choice){
  if(locked) return;

  locked = true;
  setButtonsDisabled(true);

  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer: choice })
  });

  const out = await res.json();

  const result = document.getElementById("result");
  const reward =
    typeof out.reward === "number"
      ? out.reward.toFixed(2)
      : out.reward;

  if(out.correct){
    result.textContent =
      `✅ Correct | Reward: ${reward} | Next Level: ${out.new_state}`;
    result.classList.add("good");
  } else {
    result.textContent =
      `❌ Wrong (Correct: ${out.correct_option}) | Reward: ${reward} | Next Level: ${out.new_state}`;
    result.classList.add("bad");
  }

  setTimeout(async () => {
    if(out.done){
      // IMPORTANT: finalize summary before redirect
      await fetch("/api/summary");
      window.location.href = "/results";
    } else {
      loadQuestion();
    }
  }, 1200);
}

/* =========================
   Bind buttons
========================= */
document.querySelectorAll(".opt").forEach(btn => {
  btn.addEventListener("click", () => {
    submitAnswer(btn.dataset.choice);
  });
});

/* =========================
   Start quiz
========================= */
loadQuestion();
