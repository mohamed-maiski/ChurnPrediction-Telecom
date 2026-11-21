"use strict";
const $ = selector => document.querySelector(selector);
let rows = [], columns = [], filter = "all", page = 1;
const pageSize = 25;
const pending = new Map();
const labels = {
  "Churn Prediction": "Prediction", SeniorCitizen: "Senior citizen", Dependents: "Dependents",
  tenure: "Tenure (months)", OnlineSecurity: "Online security", OnlineBackup: "Online backup",
  DeviceProtection: "Device protection", TechSupport: "Tech support", Contract: "Contract",
  MonthlyCharges: "Monthly charges", TotalCharges: "Total charges"
};
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function message(target, text, kind = "") {
  target.replaceChildren(element("span", text));
  target.className = `result ${kind}`;
  target.hidden = false;
}
function visibleRows() {
  const query = $("#result-search").value.trim().toLowerCase();
  return rows.filter(row => (filter === "all" || row["Churn Prediction"] === filter)
    && (!query || columns.some(column => String(row[column]).toLowerCase().includes(query))));
}
function renderSummary() {
  const churn = rows.filter(row => row["Churn Prediction"] === "Churn").length;
  const summary = $("#prediction-summary");
  summary.replaceChildren();
  [[rows.length, "Customers analysed", ""], [churn, "Churn predicted", "churn"],
    [rows.length - churn, "Not Churn predicted", "retained"]].forEach(([count, label, kind]) => {
    const item = element("div", undefined, `summary-item ${kind}`);
    item.append(element("strong", count), element("span", label));
    summary.append(item);
  });
}
function renderTable() {
  const selected = visibleRows();
  const head = $("#results-table thead"), body = $("#results-table tbody");
  head.replaceChildren(); body.replaceChildren();
  const header = element("tr");
  const displayColumns = ["Churn Prediction", ...columns.filter(column => column !== "Churn Prediction")];
  displayColumns.forEach(column => {
    const cell = element("th", labels[column] || column);
    cell.scope = "col"; header.append(cell);
  });
  head.append(header);
  const fragment = document.createDocumentFragment();
  const pageCount = Math.max(1, Math.ceil(selected.length / pageSize));
  page = Math.min(page, pageCount);
  selected.slice((page - 1) * pageSize, page * pageSize).forEach(row => {
    const tr = element("tr");
    displayColumns.forEach(column => {
      const cell = element("td");
      if (column === "Churn Prediction") {
        cell.append(element("span", row[column], `prediction-badge ${row[column] === "Churn" ? "churn" : "retained"}`));
      } else {
        cell.textContent = ["MonthlyCharges", "TotalCharges"].includes(column)
          ? Number(row[column]).toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2})
          : row[column];
      }
      tr.append(cell);
    });
    fragment.append(tr);
  });
  body.append(fragment);
  $("#result-count").textContent = `${selected.length} of ${rows.length} customers`;
  $("#page-status").textContent = selected.length ? `Page ${page} of ${pageCount}` : "No results";
  $("#previous-page").disabled = page <= 1;
  $("#next-page").disabled = page >= pageCount;
  $("#container-table").hidden = selected.length === 0;
  $(".pagination").hidden = selected.length === 0;
  $("#empty-filter").hidden = selected.length !== 0;
  document.querySelectorAll("[data-filter]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.filter === filter));
  });
  $("#export-csv").disabled = selected.length === 0;
  $("#export-excel").disabled = selected.length === 0;
}
function renderSingle(churn, details) {
  const target = $("#single-result");
  target.replaceChildren();
  target.className = `result ${churn ? "churn" : "retained"}`;
  const verdict = element("div", undefined, "single-verdict");
  const text = element("div");
  text.append(element("p", "Prediction result", "verdict-label"),
    element("h3", churn ? "Churn predicted" : "Not Churn predicted", "verdict-title"),
    element("p", churn
      ? "This customer may cancel their subscription. Consider reviewing their needs and retention options."
      : "This customer is likely to continue their subscription based on the information provided.", "verdict-description"));
  verdict.append(text);
  const recap = element("dl", undefined, "customer-recap");
  [["Contract", details.get("contract")], ["Tenure", `${details.get("tenure")} months`],
    ["Monthly charges", Number(details.get("monthlycharges")).toFixed(2)]].forEach(([label, value]) => {
    const item = element("div"); item.append(element("dt", label), element("dd", value)); recap.append(item);
  });
  target.append(verdict, recap, element("p", "Model estimate — not a guarantee of future customer behaviour.", "result-footnote"));
  target.hidden = false;
  target.scrollIntoView({block: "nearest", behavior: "auto"});
}
document.querySelectorAll("[data-panel]").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll("[data-panel]").forEach(other => {
    const active = other === button;
    other.classList.toggle("active", active);
    other.setAttribute("aria-pressed", String(active));
    document.getElementById(other.dataset.panel).hidden = !active;
  });
  $("#batch-results").hidden = button.dataset.panel !== "Predict_from_CSVExcel" || rows.length === 0;
}));
$("#file_csv").addEventListener("change", event => {
  pending.get($("#batch-form"))?.abort();
  const file = event.target.files[0];
  $("#filename").textContent = file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : "No file selected";
  rows = []; columns = [];
  $("#batch-results").hidden = true; $("#batch-message").hidden = true;
});
document.querySelectorAll("form").forEach(form => form.addEventListener("submit", async event => {
  event.preventDefault();
  const batch = form.id === "batch-form";
  const output = $(batch ? "#batch-message" : "#single-result");
  const button = form.querySelector("button[type=submit]");
  const label = button.textContent;
  const details = new FormData(form);
  const controller = new AbortController();
  pending.set(form, controller);
  button.disabled = true; button.textContent = "Predicting…";
  form.setAttribute("aria-busy", "true"); output.hidden = true;
  if (batch) { rows = []; columns = []; $("#batch-results").hidden = true; }
  try {
    if (batch && !$("#file_csv").files.length) throw new Error("Choose a file before predicting.");
    if (batch && $("#file_csv").files[0]?.size > 5 * 1024 * 1024) throw new Error("The file exceeds the 5 MB limit.");
    const response = await fetch(form.action, {method: "POST", body: details, signal: controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Prediction failed. Please check your data.");
    if (batch) {
      rows = data.rows; columns = data.columns; filter = "all"; page = 1; $("#result-search").value = "";
      renderSummary(); renderTable();
      $("#batch-results").hidden = $("#Predict_from_CSVExcel").hidden;
      if (!$("#Predict_from_CSVExcel").hidden) $("#batch-results").scrollIntoView({block: "start", behavior: "auto"});
    } else {
      renderSingle(data.churn, details);
    }
  } catch (error) {
    if (error.name === "AbortError") return;
    message(output, error instanceof TypeError
      ? "Unable to connect. Check that the server is running, then try again." : error.message, "error");
  } finally {
    pending.delete(form);
    button.disabled = false; button.textContent = label; form.removeAttribute("aria-busy");
  }
}));
document.querySelectorAll("[data-filter]").forEach(button => button.addEventListener("click", () => {
  filter = button.dataset.filter; page = 1; renderTable();
}));
$("#result-search").addEventListener("input", () => { page = 1; renderTable(); });
$("#previous-page").addEventListener("click", () => { if (page > 1) { page--; renderTable(); } });
$("#next-page").addEventListener("click", () => {
  if (page * pageSize < visibleRows().length) { page++; renderTable(); }
});
$("#single-form").addEventListener("input", () => {
  pending.get($("#single-form"))?.abort();
  $("#single-result").hidden = true;
});
function exportData() {
  const safe = value => typeof value === "string" && /^[=+\-@\t\r\n]/.test(value) ? `'${value}` : value;
  return [columns, ...visibleRows().map(row => columns.map(column => safe(row[column])))];
}
$("#export-csv").addEventListener("click", () => {
  const csv = exportData().map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["\ufeff", csv], {type: "text/csv;charset=utf-8"}));
  const link = element("a"); link.href = url; link.download = "telecom_predictions.csv"; link.click();
  $(".dropdown").open = false;
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("#export-excel").addEventListener("click", async () => {
  const button = $("#export-excel");
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "Preparing Excel…";
  try {
    const response = await fetch("/export/xlsx", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({rows: visibleRows()})
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Excel export could not be prepared.");
    }
    const url = URL.createObjectURL(await response.blob());
    const link = element("a");
    link.href = url; link.download = "telecom_predictions.xlsx"; link.click();
    $(".dropdown").open = false;
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    message($("#batch-message"), error instanceof TypeError
      ? "Unable to connect. Please try the export again." : error.message, "error");
  } finally {
    button.disabled = visibleRows().length === 0;
    button.textContent = label;
  }
});
