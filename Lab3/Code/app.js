let data;
let year = "2025";
let selectedSegment = "all";

const formatNumber = value =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
const formatPercent = value => `${value.toFixed(2)}%`;
const currentView = () => data.views[year][selectedSegment];

function renderCards(view) {
  const cards = [
    {
      label: "营收",
      value: formatNumber(view.revenue),
      note: view.yoy_pct === null
        ? "FY2025 年报列示的可比口径"
        : `同比 ${view.yoy_pct >= 0 ? "+" : ""}${formatPercent(view.yoy_pct)}`,
    },
    {
      label: "营业利润",
      value: formatNumber(view.operating_income),
      note: "经营活动的利润，不是净利润",
    },
    {
      label: "营业利润率",
      value: formatPercent(view.margin_pct),
      note: "营业利润 ÷ 营收，由 Python 计算",
    },
    {
      label: "净利润",
      value: view.net_income === null ? "未披露" : formatNumber(view.net_income),
      note: view.net_income === null ? "年报不披露分部净利润" : "全公司口径，扣除所得税等项目",
    },
  ];

  const container = document.querySelector("#cards");
  container.replaceChildren(...cards.map(card => {
    const element = document.createElement("article");
    element.className = "metric-card";
    const label = document.createElement("h3");
    label.textContent = card.label;
    const value = document.createElement("p");
    value.className = "metric-value";
    value.textContent = card.value;
    const note = document.createElement("small");
    note.textContent = card.note;
    element.append(label, value, note);
    return element;
  }));
}

function renderBars() {
  const container = document.querySelector("#bars");
  const buttons = data.segments.map(segment => {
    const button = document.createElement("button");
    button.className = "bar-row";
    button.type = "button";
    button.setAttribute("aria-pressed", String(selectedSegment === segment.name));
    button.setAttribute("aria-label", `筛选分部：${segment.name}`);

    const heading = document.createElement("span");
    heading.className = "bar-heading";
    const name = document.createElement("b");
    name.textContent = segment.name;
    const value = document.createElement("span");
    value.textContent = formatNumber(segment.revenue[year]);
    heading.append(name, value);

    const track = document.createElement("span");
    track.className = "bar-track";
    const fill = document.createElement("span");
    fill.className = "bar-fill";
    fill.style.width = `${segment.bar_pct[year]}%`;
    track.append(fill);
    button.append(heading, track);
    button.onclick = () => {
      selectedSegment = segment.name;
      render();
    };
    return button;
  });
  container.replaceChildren(...buttons);
}

function renderSegmentTable() {
  const body = document.querySelector("#segment-table");
  const rows = data.segments.map(segment => {
    const segmentView = data.views[year][segment.name];
    const row = document.createElement("tr");
    if (selectedSegment === segment.name) row.className = "is-selected";

    const nameCell = document.createElement("th");
    nameCell.scope = "row";
    const select = document.createElement("button");
    select.type = "button";
    select.className = "segment-link";
    select.textContent = segment.name;
    select.onclick = () => {
      selectedSegment = segment.name;
      render();
    };
    nameCell.append(select);
    row.append(nameCell);

    for (const value of [
      formatNumber(segmentView.revenue),
      formatNumber(segmentView.operating_income),
      formatPercent(segmentView.margin_pct),
    ]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    return row;
  });
  body.replaceChildren(...rows);
  document.querySelector("#segment-year").textContent = `金额：百万美元 · ${year === "2025" ? "FY2025" : "FY2024"}`;
}

function render() {
  const view = currentView();
  renderCards(view);
  renderBars();
  renderSegmentTable();
  document.querySelector("#selected-segment").textContent =
    selectedSegment === "all" ? "全部业务" : selectedSegment;
}

function renderAnalysis(result) {
  document.querySelector("#analysis-title").textContent = result.title;
  const findings = result.findings.map(finding => {
    const item = document.createElement("article");
    item.className = "finding";
    const heading = document.createElement("h3");
    heading.textContent = finding.heading;
    const explanation = document.createElement("p");
    explanation.textContent = finding.explanation;
    const metric = document.createElement("small");
    metric.textContent = `年报指标：${finding.metric}`;
    item.append(heading, explanation, metric);
    return item;
  });
  document.querySelector("#findings").replaceChildren(...findings);
  const trace = result.trace;
  document.querySelector("#trace").textContent =
    `真实 SDK 会话 · ${trace.model} / ${trace.reasoning_effort} · ${trace.mode}\n会话 ID 仅保存在本机 analysis.json\n` +
    `${result.caveat}\n观察固定针对 FY2025；筛选只更新 Python 核对后的数据视图，不会重新调用 Agent。`;
}

function renderSource() {
  document.querySelector("#provenance").textContent =
    JSON.stringify(data.source, null, 2);
  document.querySelector("#reconciliation").textContent =
    JSON.stringify(data.reconciliation, null, 2);
  document.querySelector("#comparability").textContent = data.comparability;
}

function setupControls() {
  document.querySelector("#year").onchange = event => {
    year = event.target.value;
    render();
  };
  document.querySelector("#clear").onclick = () => {
    selectedSegment = "all";
    render();
  };
  for (const button of document.querySelectorAll(".tabs button")) {
    button.onclick = () => {
      for (const tab of document.querySelectorAll(".tabs button")) {
        const active = tab === button;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
      }
      for (const section of document.querySelectorAll("[data-panel]")) {
        section.hidden = section.id !== button.dataset.view;
      }
    };
  }
}

async function load() {
  setupControls();
  try {
    const [dataResponse, analysisResponse] = await Promise.all([
      fetch("/api/data"),
      fetch("/api/analysis"),
    ]);
    const [loadedData, analysis] = await Promise.all([
      dataResponse.json(),
      analysisResponse.json(),
    ]);
    if (!dataResponse.ok) throw new Error(loadedData.error || "财报数据加载失败");
    if (!analysisResponse.ok) throw new Error(analysis.error || "单 Agent 分析加载失败");
    data = loadedData;
    render();
    renderAnalysis(analysis);
    renderSource();
    document.querySelector("#loading").hidden = true;
  } catch (error) {
    document.querySelector("#loading").hidden = true;
    document.querySelector("#error").textContent =
      `${error.message}。请运行 Lab3/Code/analyze.py 并检查 Python 服务。`;
  }
}

load();
