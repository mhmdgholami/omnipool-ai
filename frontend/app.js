import { request } from "./api.js";

const app = document.querySelector("#app");
const walletButton = document.querySelector("#wallet");
const toastElement = document.querySelector("#toast");

const state = {
  view: "radar",
  wallet: localStorage.getItem("omni_wallet") || "",
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[character];
  });
}

function showToast(message) {
  toastElement.textContent = message;
  toastElement.style.display = "block";
  window.setTimeout(() => {
    toastElement.style.display = "none";
  }, 2400);
}

function closeModal() {
  document.querySelector("#modal")?.remove();
}

function openModal(content, maxWidth = "980px") {
  closeModal();
  document.body.insertAdjacentHTML(
    "beforeend",
    '<div class="modal" id="modal"><div class="modalBox" style="max-width:' +
      maxWidth +
      '">' +
      content +
      "</div></div>",
  );
  document
    .querySelector("[data-close-modal]")
    ?.addEventListener("click", closeModal);
}

async function connectWallet() {
  if (state.wallet) {
    showToast("Connected as " + state.wallet);
    return true;
  }

  const provider = window.solana;
  if (provider?.connect) {
    try {
      const result = await provider.connect();
      state.wallet = result.publicKey.toString();
    } catch {
      showToast("Wallet connection was cancelled.");
      return false;
    }
  } else {
    state.wallet = "Demo7Yx2D";
    showToast("No Solana wallet detected. Using a local demo identity.");
  }

  localStorage.setItem("omni_wallet", state.wallet);
  walletButton.textContent = state.wallet;
  return true;
}

function heroMarkup() {
  return [
    '<section class="hero">',
    '<div class="panel">',
    '<div class="eyebrow">Real-time cultural launch engine</div>',
    "<h1>FROM TREND → TOKEN.<br>IN SECONDS.</h1>",
    '<p class="lead">Market signals are clustered into narratives, scored for opportunity, confidence and launch risk, then tested with Proof of Demand before any graduation step.</p>',
    '<div class="actions">',
    '<button class="btn primary" id="scan">Scan live sources</button>',
    '<button class="btn" id="custom">Generate from my idea</button>',
    "</div>",
    "</div>",
    '<div class="panel">',
    "<h3>Pipeline</h3>",
    '<div class="steps">',
    '<div class="step"><b>1</b><span>Detect + cluster</span></div>',
    '<div class="step"><b>2</b><span>Quantify evidence + risk</span></div>',
    '<div class="step"><b>3</b><span>Generate 3 concepts</span></div>',
    '<div class="step"><b>4</b><span>Prove demand, then sign</span></div>',
    "</div>",
    '<p class="muted">The server never signs the user wallet.</p>',
    "</div>",
    "</section>",
  ].join("");
}

function trendCard(trend) {
  const riskFlags = (trend.risk_flags || [])
    .map(
      (flag) =>
        '<span class="tag fallback">' + escapeHtml(flag) + "</span>",
    )
    .join("");

  const sourceClass = trend.source.includes("curated_demo")
    ? "tag fallback"
    : "tag";

  return [
    '<article class="card">',
    '<div class="score">' + Math.round(trend.score) + "</div>",
    "<h3>" + escapeHtml(trend.title) + "</h3>",
    '<p class="muted">' + escapeHtml(trend.summary) + "</p>",
    '<div class="tags">',
    '<span class="' + sourceClass + '">' + escapeHtml(trend.source) + "</span>",
    riskFlags,
    "</div>",
    '<div class="metrics">',
    '<div class="metric"><span>Confidence</span><b>' +
      Math.round(trend.confidence || 0) +
      "</b></div>",
    '<div class="metric"><span>Launch risk</span><b>' +
      Math.round(trend.risk || 0) +
      "</b></div>",
    '<div class="metric"><span>Saturation</span><b>' +
      Math.round(trend.saturation) +
      "%</b></div>",
    "</div>",
    '<button class="btn primary" data-generate="' +
      escapeHtml(trend.id) +
      '">Generate 3 ideas</button>',
    "</article>",
  ].join("");
}

async function renderRadar() {
  const [trends, sources] = await Promise.all([
    request("/api/v1/trends"),
    request("/api/v1/sources"),
  ]);

  const sourceMarkup = sources
    .map((source) => {
      const isFallback = ["fallback", "adapter"].includes(source.mode);
      return [
        '<div class="source">',
        "<div><b>" +
          escapeHtml(source.label) +
          "</b><span>" +
          escapeHtml(source.detail) +
          "</span></div>",
        '<span class="tag ' +
          (isFallback ? "fallback" : "") +
          '">' +
          escapeHtml(source.mode) +
          "</span>",
        "</div>",
      ].join("");
    })
    .join("");

  app.innerHTML = [
    heroMarkup(),
    '<section class="section">',
    '<div class="sectionHead"><div><h2>AI Radar</h2>',
    "<p>Opportunity is not treated as the same thing as confidence or safety.</p>",
    "</div></div>",
    '<div class="grid">' + trends.map(trendCard).join("") + "</div>",
    "</section>",
    '<section class="section panel" style="padding:18px">',
    '<div class="sectionHead"><div><h2>Source health</h2>',
    "<p>Live sources and future adapters are labeled separately.</p>",
    "</div></div>",
    '<div class="sourceList">' + sourceMarkup + "</div>",
    "</section>",
  ].join("");

  document.querySelector("#scan").addEventListener("click", async () => {
    showToast("Refreshing market signals…");
    await request("/api/v1/trends/scan", {
      method: "POST",
      timeoutMs: 15000,
    });
    await renderRadar();
  });

  document
    .querySelector("#custom")
    .addEventListener("click", openCustomIdeaModal);

  document.querySelectorAll("[data-generate]").forEach((button) => {
    button.addEventListener("click", () => {
      generateConcepts({ trend_id: button.dataset.generate });
    });
  });
}

function openCustomIdeaModal() {
  openModal(
    [
      '<div class="sectionHead">',
      '<div><div class="eyebrow">Custom signal</div><h2>Generate from an idea</h2></div>',
      '<button class="btn" data-close-modal>Close</button>',
      "</div>",
      '<label class="fieldLabel" for="idea">Trend, phrase or event</label>',
      '<input id="idea" class="fieldInput" maxlength="100" placeholder="e.g. robots boxing on livestream">',
      '<div class="actions"><button class="btn primary" id="generate-custom">Generate</button></div>',
    ].join(""),
    "560px",
  );

  document.querySelector("#generate-custom").addEventListener("click", () => {
    const title = document.querySelector("#idea").value.trim();
    if (!title) {
      showToast("Enter an idea first.");
      return;
    }
    closeModal();
    generateConcepts({ title, summary: title });
  });
}

function conceptCard(concept) {
  const flags = (concept.risk_flags || [])
    .map(
      (flag) =>
        '<span class="tag fallback">' + escapeHtml(flag) + "</span>",
    )
    .join("");

  return [
    '<article class="card">',
    "<h3>" +
      escapeHtml(concept.name) +
      ' <span class="muted">$' +
      escapeHtml(concept.ticker) +
      "</span></h3>",
    "<p>" + escapeHtml(concept.thesis) + "</p>",
    '<div class="metrics">',
    '<div class="metric"><span>Momentum</span><b>' +
      Math.round(concept.momentum_score) +
      "</b></div>",
    '<div class="metric"><span>Novelty</span><b>' +
      Math.round(concept.novelty_score) +
      "</b></div>",
    '<div class="metric"><span>Target</span><b>' +
      concept.target_sol +
      " SOL</b></div>",
    "</div>",
    '<div class="tags">' + flags + "</div>",
    '<button class="btn primary" style="margin-top:12px" data-launch="' +
      escapeHtml(concept.id) +
      '">Start Proof Market</button>',
    "</article>",
  ].join("");
}

async function generateConcepts(payload) {
  showToast("Generating concepts…");

  try {
    const concepts = await request("/api/v1/generate", {
      method: "POST",
      body: payload,
      timeoutMs: 20000,
    });

    openModal(
      [
        '<div class="sectionHead">',
        '<div><div class="eyebrow">Concept engine</div><h2>Choose one to test demand</h2></div>',
        '<button class="btn" data-close-modal>Close</button>',
        "</div>",
        '<div class="concepts">' +
          concepts.map(conceptCard).join("") +
          "</div>",
      ].join(""),
    );

    document.querySelectorAll("[data-launch]").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!(await connectWallet())) {
          return;
        }

        await request("/api/v1/campaigns", {
          method: "POST",
          body: {
            concept_id: button.dataset.launch,
            creator_wallet: state.wallet,
            duration_minutes: 30,
            risk_acknowledged: true,
          },
        });

        closeModal();
        state.view = "proof";
        showToast("Proof market created.");
        await render();
      });
    });
  } catch (error) {
    openModal(
      [
        '<div class="sectionHead"><h2>Generation failed</h2>',
        '<button class="btn" data-close-modal>Close</button></div>',
        '<p class="muted">' + escapeHtml(error.message) + "</p>",
      ].join(""),
    );
  }
}

function campaignCard(campaign) {
  const percent = Math.min(
    100,
    Math.round((campaign.raised_sol / campaign.target_sol) * 100),
  );

  let action = "";
  if (campaign.status === "funding") {
    action =
      '<button class="btn primary" data-fund="' +
      campaign.id +
      '">Commit 1 demo SOL</button>';
  } else if (campaign.status === "ready") {
    action =
      '<button class="btn primary" data-graduate="' +
      campaign.id +
      '">Prepare graduation</button>';
  }

  return [
    '<article class="card">',
    "<h3>" +
      escapeHtml(campaign.name) +
      ' <span class="muted">$' +
      escapeHtml(campaign.ticker) +
      "</span></h3>",
    "<p>" + escapeHtml(campaign.thesis) + "</p>",
    '<div class="bar"><i style="width:' + percent + '%"></i></div>',
    '<div class="row"><span>' +
      campaign.raised_sol.toFixed(3) +
      " / " +
      campaign.target_sol +
      " SOL</span><b>" +
      escapeHtml(campaign.status) +
      "</b></div>",
    '<div class="row"><span>Creator genesis allocation</span><b>0%</b></div>',
    '<div class="row"><span>Contributor / liquidity</span><b>50% / 50%</b></div>',
    action,
    "</article>",
  ].join("");
}

async function renderProof() {
  const campaigns = await request("/api/v1/campaigns");

  app.innerHTML = [
    '<div class="sectionHead"><div>',
    '<div class="eyebrow">Proof of demand</div>',
    "<h2>Fund the idea before the token exists.</h2>",
    '<p class="muted">Commitments remain demo state until the on-chain escrow program is deployed.</p>',
    "</div></div>",
    '<div class="grid">',
    campaigns.length
      ? campaigns.map(campaignCard).join("")
      : '<p class="muted">No proof markets yet.</p>',
    "</div>",
  ].join("");

  document.querySelectorAll("[data-fund]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!(await connectWallet())) {
        return;
      }

      const result = await request(
        "/api/v1/campaigns/" + button.dataset.fund + "/contribute",
        {
          method: "POST",
          body: {
            wallet: state.wallet,
            amount_sol: 1,
            idempotency_key: crypto.randomUUID(),
          },
        },
      );

      showToast(
        result.idempotent_replay
          ? "Request was safely replayed."
          : "Accepted " + result.accepted_sol + " SOL.",
      );
      await renderProof();
    });
  });

  document.querySelectorAll("[data-graduate]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!(await connectWallet())) {
        return;
      }

      const result = await request(
        "/api/v1/campaigns/" + button.dataset.graduate + "/graduate",
        { method: "POST" },
      );

      showToast(
        "Graduation plan " +
          result.plan.plan_id.slice(0, 8) +
          "… is ready; user signature is still required.",
      );
      await renderProof();
    });
  });
}

function renderArchitecture() {
  app.innerHTML = [
    '<div class="eyebrow">Architecture</div>',
    "<h2>Small runtime now. Clean scaling boundary later.</h2>",
    '<p class="lead">FastAPI owns orchestration, quantitative logic stays in pure Python, funds are represented as integer lamports, and external I/O reuses a bounded connection pool.</p>',
    '<div class="grid section">',
    '<div class="card"><h3>Correctness first</h3><p class="muted">SQLite transactions serialize campaign writes and idempotency keys make retries safe.</p></div>',
    '<div class="card"><h3>Bounded memory</h3><p class="muted">Caches, rate-limit clients, observations and list endpoints all have explicit upper bounds.</p></div>',
    '<div class="card"><h3>Cloud boundary</h3><p class="muted">SQLite is intentionally single-replica. PostgreSQL + Redis comes before horizontal API scaling.</p></div>',
    "</div>",
  ].join("");
}

async function render() {
  try {
    if (state.view === "proof") {
      await renderProof();
    } else if (state.view === "architecture") {
      renderArchitecture();
    } else {
      await renderRadar();
    }
  } catch (error) {
    app.innerHTML = [
      '<div class="card"><h3>Request failed</h3>',
      '<p class="muted">' + escapeHtml(error.message) + "</p></div>",
    ].join("");
  }
}

walletButton.textContent = state.wallet || "Connect wallet";
walletButton.addEventListener("click", connectWallet);

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    state.view = button.dataset.view;
    render();
  });
});

render();
