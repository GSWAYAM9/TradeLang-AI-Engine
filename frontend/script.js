document.addEventListener("DOMContentLoaded", () => {
  const runBtn = document.getElementById("runBtn");
  const nlEl = document.getElementById("nl");
  const statusEl = document.getElementById("status");

  const dslEl = document.getElementById("dsl");
  const astEl = document.getElementById("ast");
  const pyEl = document.getElementById("py");
  const reportEl = document.getElementById("report");

  async function run() {
    const text = nlEl.value.trim();

    if (!text) {
      statusEl.textContent = "Please enter a rule.";
      return;
    }

    // Reset UI
    statusEl.textContent = "Running...";
    dslEl.textContent = "";
    astEl.textContent = "";
    pyEl.textContent = "";
    reportEl.textContent = "";

    try {
      // ✅ SAME ORIGIN CALL (Railway handles routing)
      const res = await fetch("/api/groq", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });

      if (!res.ok) {
        const errText = await res.text();
        reportEl.textContent = "API Error:\n" + errText;
        statusEl.textContent = "Error";
        return;
      }

      const data = await res.json();

      // Populate outputs
      dslEl.textContent = data.dsl || "";
      astEl.textContent = JSON.stringify(data.ast, null, 2);
      pyEl.textContent = data.python || "";
      reportEl.textContent = JSON.stringify(data.backtest, null, 2);

      statusEl.textContent = "Done";
    } catch (err) {
      console.error(err);
      reportEl.textContent = "Request failed:\n" + err.message;
      statusEl.textContent = "Error";
    }
  }

  runBtn.addEventListener("click", run);
});
