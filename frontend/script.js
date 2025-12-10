// frontend/script.js
// Connects UI to backend endpoint /api/groq

document.addEventListener("DOMContentLoaded", () => {
  const runBtn = document.getElementById("runBtn");
  const nlEl = document.getElementById("nl");
  const status = document.getElementById("status");
  const dslEl = document.getElementById("dsl");
  const astEl = document.getElementById("ast");
  const pyEl = document.getElementById("py");
  const reportEl = document.getElementById("report");

  function setStatus(s, busy=false){
    status.textContent = s;
    if(busy) status.style.opacity = "0.7"; else status.style.opacity = "1";
  }

  async function run() {
    const text = nlEl.value.trim();
    if(!text){
      setStatus("Enter a natural-language rule.");
      return;
    }
    setStatus("Running...", true);
    dslEl.textContent = "";
    astEl.textContent = "";
    pyEl.textContent = "";
    reportEl.textContent = "";

    try {
      const res = await fetch("/api/groq", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({text})
      });
      if(!res.ok){
        const txt = await res.text();
        setStatus("Error: " + res.status);
        reportEl.textContent = txt;
        return;
      }
      const data = await res.json();
      dslEl.textContent = data.dsl || "";
      astEl.textContent = JSON.stringify(data.ast, null, 2);
      pyEl.textContent = data.python || "";
      reportEl.textContent = JSON.stringify(data.backtest, null, 2);
      setStatus("Done");
    } catch (err) {
      setStatus("Network/error");
      reportEl.textContent = String(err);
    }
  }

  runBtn.addEventListener("click", run);

  // convenience: sample rule
  nlEl.value = "Buy when close is above the 20-day moving average and volume is above 1M. Exit when RSI(14) < 30.";
});

