// Интерфейс общается с FastAPI через fetch(). Все данные из Excel
// вставляются в страницу через textContent, поэтому содержимое ячеек
// не может выполниться как HTML.
"use strict";

const $ = (id) => document.getElementById(id);
let meta = null;      // ответ /api/upload: file_id, колонки, значения по умолчанию
let chartToken = 0;   // чтобы медленный старый ответ не затёр свежий график
let analysisToken = 0;

/* ---------- Вспомогательное ---------- */
function showError(msg) {
  const box = $("error");
  box.textContent = msg || "";
  box.hidden = !msg;
}

async function api(path, options) {
  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error("Нет связи с сервером. Проверьте, что он запущен.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Что-то пошло не так.");
  return data;
}

function fillSelect(select, values, selected) {
  select.replaceChildren(...values.map((v) => {
    const o = document.createElement("option");
    o.value = o.textContent = v;
    return o;
  }));
  if (selected && values.includes(selected)) select.value = selected;
}

function renderTable(table, columns, rows) {
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  columns.forEach((c) => {
    const th = document.createElement("th");
    th.textContent = c;
    hr.append(th);
  });
  thead.append(hr);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell;
      if (typeof cell === "number") td.className = "num";
      tr.append(td);
    });
    tbody.append(tr);
  });
  table.replaceChildren(thead, tbody);
}

/* ---------- Шаг 1: загрузка ---------- */
async function loadFile(file) {
  showError("");
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".xlsx")) {
    showError("Нужен файл в формате .xlsx");
    return;
  }
  $("status").className = "status";
  $("status").textContent = "Читаю файл…";
  const form = new FormData();
  form.append("file", file);
  try {
    onLoaded(await api("/api/upload", { method: "POST", body: form }));
  } catch (e) {
    $("status").textContent = "";
    showError(e.message);
  }
}

async function loadSample() {
  showError("");
  $("status").className = "status";
  $("status").textContent = "Загружаю пример…";
  try {
    onLoaded(await api("/api/sample", { method: "POST" }));
  } catch (e) {
    $("status").textContent = "";
    showError(e.message);
  }
}

function onLoaded(data) {
  meta = data;
  $("status").className = "status ok";
  $("status").textContent = `Файл успешно загружен. Количество строк: ${data.rows}`;

  renderTable($("preview"), data.columns, data.preview);
  $("preview-wrap").hidden = false;

  const yDefault = data.defaults.price && data.numeric.includes(data.defaults.price)
    ? data.defaults.price : data.numeric[0];
  fillSelect($("x-col"), data.columns, data.defaults.name);
  fillSelect($("y-col"), data.numeric, yDefault);
  const pieCols = data.categorical.length ? data.categorical : data.columns;
  fillSelect($("pie-col"), pieCols, pieCols.includes("Производитель") ? "Производитель" : pieCols[0]);

  fillSelect($("name-col"), data.columns, data.defaults.name);
  fillSelect($("metric-col"), data.numeric);
  fillSelect($("price-col"), data.numeric, data.defaults.price);
  renderPerfList();

  const hasNumbers = data.numeric.length > 0;
  $("step-chart").classList.toggle("locked", !hasNumbers);
  $("step-analysis").classList.toggle("locked", !hasNumbers);
  if (!hasNumbers) {
    showError("В таблице нет числовых столбцов — строить графики и считать показатели нечего.");
    return;
  }
  document.querySelectorAll(".opt, #opt-all").forEach((c) => (c.checked = false));
  document.querySelectorAll(".opt").forEach((c) => (c.disabled = false));
  $("analysis-wrap").hidden = true;
  $("analysis-empty").hidden = false;
  drawChart();
}

function renderPerfList() {
  const price = $("price-col").value;
  const box = $("perf-list");
  box.replaceChildren();
  meta.numeric.filter((c) => c !== price).forEach((c) => {
    const label = document.createElement("label");
    label.className = "check";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = c;
    input.className = "perf";
    input.checked = meta.defaults.perf.includes(c);
    input.addEventListener("change", runAnalysis);
    label.append(input, document.createTextNode(" " + c));
    box.append(label);
  });
}

/* ---------- Шаг 2: график ---------- */
async function drawChart() {
  if (!meta) return;
  const type = $("chart-type").value;
  $("bar-controls").hidden = type !== "bar";
  $("pie-controls").hidden = type !== "pie";

  const params = new URLSearchParams({ file_id: meta.file_id });
  let url;
  if (type === "bar") {
    params.set("x", $("x-col").value);
    params.set("y", $("y-col").value);
    url = "/api/chart/bar?" + params;
  } else {
    params.set("column", $("pie-col").value);
    url = "/api/chart/pie?" + params;
  }

  const token = ++chartToken;
  $("chart-empty").hidden = false;
  $("chart-empty").textContent = "Строю график…";
  $("chart-img").hidden = true;
  $("chart-note").hidden = true;
  try {
    const data = await api(url);
    if (token !== chartToken) return;
    showError("");
    const img = $("chart-img");
    img.src = "data:image/png;base64," + data.image;
    img.alt = type === "bar"
      ? `Столбчатая диаграмма: ${$("y-col").value} по ${$("x-col").value}`
      : `Круговая диаграмма долей по столбцу ${$("pie-col").value}`;
    img.hidden = false;
    $("chart-empty").hidden = true;

    const note = $("chart-note");
    if (type === "bar") {
      note.replaceChildren();
      const sw = document.createElement("span");
      sw.className = "swatch";
      const b = document.createElement("b");
      b.textContent = data.max_label;
      note.append(sw, "Максимум: ", b, ` (${data.max_value})`);
      note.hidden = false;
    }
  } catch (e) {
    if (token !== chartToken) return;
    $("chart-empty").textContent = "Не удалось построить график.";
    showError(e.message);
  }
}

/* ---------- Шаг 3: анализ ---------- */
async function runAnalysis() {
  if (!meta) return;
  const options = [...document.querySelectorAll(".opt:checked")].map((c) => c.value);
  if (!options.length) {
    $("analysis-wrap").hidden = true;
    $("analysis-empty").hidden = false;
    return;
  }
  const token = ++analysisToken;
  try {
    const data = await api("/api/analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_id: meta.file_id,
        options,
        name_col: $("name-col").value,
        metric_col: $("metric-col").value,
        price_col: $("price-col").value || null,
        perf_cols: [...document.querySelectorAll(".perf:checked")].map((c) => c.value),
      }),
    });
    if (token !== analysisToken) return;
    showError("");
    renderTable($("analysis"), data.columns, data.rows);
    $("analysis-wrap").hidden = false;
    $("analysis-empty").hidden = true;
  } catch (e) {
    if (token !== analysisToken) return;
    $("analysis-wrap").hidden = true;
    $("analysis-empty").hidden = false;
    showError(e.message);
  }
}

function onAllToggled() {
  const all = $("opt-all").checked;
  document.querySelectorAll(".opt").forEach((c) => {
    c.checked = all;
    c.disabled = all;
  });
  runAnalysis();
}

/* ---------- Подключение событий ---------- */
$("file").addEventListener("change", (e) => loadFile(e.target.files[0]));
$("sample").addEventListener("click", loadSample);

const drop = $("drop");
["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => loadFile(e.dataTransfer.files[0]));

["chart-type", "x-col", "y-col", "pie-col"].forEach((id) => $(id).addEventListener("change", drawChart));
["name-col", "metric-col"].forEach((id) => $(id).addEventListener("change", runAnalysis));
$("price-col").addEventListener("change", () => { renderPerfList(); runAnalysis(); });
$("opt-all").addEventListener("change", onAllToggled);
document.querySelectorAll(".opt").forEach((c) => c.addEventListener("change", runAnalysis));
