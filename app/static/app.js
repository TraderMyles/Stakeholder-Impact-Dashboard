const form = document.getElementById("evaluation-form");
const output = document.getElementById("result-output");
const policySelect = document.getElementById("policy-choice");
const companyInput = document.getElementById("company-name");
const profitAfterTaxInput = document.getElementById("profit-after-tax");
const equityInput = document.getElementById("equity");
const debtInput = document.getElementById("debt");
const sharesOutstandingInput = document.getElementById("shares-outstanding");
const stakeholderGrid = document.getElementById("stakeholder-grid");
const summaryGrid = document.getElementById("summary-grid");

const metricFormatters = {
  eps: (value) => value.toFixed(2),
  gearing: (value) => `${value.toFixed(1)}%`,
  bonus_estimate: (value) => value.toFixed(1),
  prudence_score: (value) => value.toFixed(1),
};

const getBestMetrics = (scenarios) => {
  const best = {};
  Object.keys(metricFormatters).forEach((metricKey) => {
    const values = scenarios
      .map((scenario) => scenario?.headline_metrics?.[metricKey])
      .filter((value) => typeof value === "number" && !Number.isNaN(value));
    if (values.length) {
      best[metricKey] = Math.max(...values);
    }
  });
  return best;
};

const formatDelta = (metricKey, delta) => {
  const sign = delta >= 0 ? "+" : "-";
  const absValue = Math.abs(delta);
  if (metricKey === "eps") {
    return `${sign}${absValue.toFixed(2)}`;
  }
  if (metricKey === "gearing") {
    return `${sign}${absValue.toFixed(1)}pp`;
  }
  return `${sign}${absValue.toFixed(1)}`;
};

const renderSummaryCards = (scenarios) => {
  if (!summaryGrid) {
    return;
  }
  summaryGrid.innerHTML = "";
  const bestMetrics = getBestMetrics(scenarios);
  const baseMetrics = scenarios[0]?.headline_metrics || {};

  scenarios.forEach((scenario, index) => {
    if (!scenario) {
      return;
    }
    const card = document.createElement("article");
    card.className = "stakeholder-card summary-card";

    const title = document.createElement("h3");
    title.textContent = scenario.label || "Scenario";

    const sublabel = document.createElement("p");
    sublabel.className = "summary-label";
    sublabel.textContent = "Headline metrics";

    const list = document.createElement("dl");
    list.className = "metrics";

    Object.keys(metricFormatters).forEach((metricKey) => {
      const row = document.createElement("div");
      row.className = "metric-row";

      const label = document.createElement("dt");
      label.textContent = metricKey
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

      const value = document.createElement("dd");
      const metricValue = scenario.headline_metrics?.[metricKey];
      if (metricValue === undefined || metricValue === null || Number.isNaN(metricValue)) {
        value.textContent = "-";
      } else {
        const formatter = metricFormatters[metricKey];
        const displayValue = formatter ? formatter(metricValue) : String(metricValue);
        const valueText = document.createElement("span");
        valueText.textContent = displayValue;
        value.appendChild(valueText);

        if (index > 0 && typeof baseMetrics[metricKey] === "number") {
          const delta = metricValue - baseMetrics[metricKey];
          const deltaText = document.createElement("span");
          deltaText.className = "metric-delta";
          deltaText.textContent = `Delta ${formatDelta(metricKey, delta)}`;
          value.appendChild(deltaText);
        }

        if (bestMetrics[metricKey] === metricValue) {
          valueText.classList.add("metric-best");
        }
      }

      row.appendChild(label);
      row.appendChild(value);
      list.appendChild(row);
    });

    card.appendChild(title);
    card.appendChild(sublabel);
    card.appendChild(list);
    summaryGrid.appendChild(card);
  });
};

const renderStakeholders = (data) => {
  const stakeholders = ["investors", "lenders", "management", "regulators"];
  if (!stakeholderGrid) {
    return;
  }
  stakeholderGrid.innerHTML = "";
  stakeholders.forEach((key) => {
    const impact = data.stakeholders?.[key];
    if (!impact) {
      return;
    }
    const card = document.createElement("article");
    card.className = "stakeholder-card";

    const title = document.createElement("h3");
    title.textContent = impact.title;

    const list = document.createElement("ul");
    list.className = "impact-list";
    (impact.bullet_impacts || []).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });

    const narrative = document.createElement("p");
    narrative.className = "narrative";
    narrative.textContent = impact.narrative || "";

    card.appendChild(title);
    card.appendChild(list);
    card.appendChild(narrative);
    stakeholderGrid.appendChild(card);
  });
};

const render = (payload) => {
  output.textContent = JSON.stringify(payload, null, 2);
  if (payload && payload.base_case) {
    renderSummaryCards([payload.base_case, payload.option_a, payload.option_b]);
    renderStakeholders(payload);
  }
};

const renderError = (message) => {
  render({ error: message });
};

const toNumber = (input) => {
  if (!input) {
    return undefined;
  }
  const value = Number(input.value);
  return Number.isFinite(value) ? value : undefined;
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  render({ status: "Submitting..." });

  const payload = {
    policy_choice: policySelect.value,
    company_name: companyInput.value.trim() || "SampleCo",
    currency: "GBP",
    profit_after_tax: toNumber(profitAfterTaxInput),
    equity: toNumber(equityInput),
    debt: toNumber(debtInput),
    shares_outstanding: toNumber(sharesOutstandingInput),
  };

  try {
    const response = await fetch("/api/v1/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorText = `Request failed with status ${response.status}`;
      try {
        const errorBody = await response.json();
        errorText = errorBody.detail || JSON.stringify(errorBody);
      } catch (parseError) {
        const fallbackText = await response.text();
        if (fallbackText) {
          errorText = fallbackText;
        }
      }
      renderError(errorText);
      return;
    }

    const data = await response.json();
    render(data);
  } catch (error) {
    renderError(error.message || "Network error");
  }
});
