const fallbackPayload = window.WWR_FALLBACK_PAYLOAD || {
  updatedAt: "2026-04-14T08:00:00Z",
  currency: "USD",
  entries: [],
};
const appConfig = window.WWR_CONFIG || {};

const state = {
  entries: [],
  pageSize: 50,
  currentPage: 1,
  filters: {
    search: "",
    category: "all",
    sort: "value-desc",
  },
};

const elements = {
  tbody: document.querySelector("#leaderboard-body"),
  rowTemplate: document.querySelector("#row-template"),
  searchInput: document.querySelector("#search-input"),
  categoryFilter: document.querySelector("#category-filter"),
  sortSelect: document.querySelector("#sort-select"),
  resultSummary: document.querySelector("#result-summary"),
  previewBanner: document.querySelector("#preview-banner"),
  prevPage: document.querySelector("#prev-page"),
  nextPage: document.querySelector("#next-page"),
  pageStatus: document.querySelector("#page-status"),
};

const formatter = {
  usdCompact: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2,
  }),
  usdLong: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }),
};

async function init() {
  bindEvents();

  const payload = await loadPayload();
  state.entries = payload.entries.map(normalizeEntry);
  render();
}

async function loadPayload() {
  if (window.location.protocol === "file:") {
    showPreviewBanner(
      "You opened the page via file://, so live JSON loading is blocked by the browser. Showing built-in sample data instead. For the real snapshot flow, open http://localhost:8080 after starting a local server."
    );
    return fallbackPayload;
  }

  try {
    const dataUrl = appConfig.dataUrl || "./data/unified-rankings.json";
    const response = await fetch(dataUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    showPreviewBanner(
      `Live JSON could not be loaded, so sample data is being shown instead. Error: ${error.message}`
    );
    return fallbackPayload;
  }
}

function bindEvents() {
  elements.searchInput.addEventListener("input", (event) => {
    state.filters.search = event.target.value.trim().toLowerCase();
    state.currentPage = 1;
    render();
  });

  elements.categoryFilter.addEventListener("change", (event) => {
    state.filters.category = event.target.value;
    state.currentPage = 1;
    render();
  });

  elements.sortSelect.addEventListener("change", (event) => {
    state.filters.sort = event.target.value;
    state.currentPage = 1;
    render();
  });

  elements.prevPage.addEventListener("click", () => {
    state.currentPage = Math.max(1, state.currentPage - 1);
    render();
  });

  elements.nextPage.addEventListener("click", () => {
    state.currentPage += 1;
    render();
  });
}

function showPreviewBanner(message) {
  elements.previewBanner.textContent = message;
  elements.previewBanner.classList.remove("is-hidden");
}

function normalizeEntry(entry) {
  return {
    ...entry,
    searchKey: [entry.name, entry.symbol, entry.region, entry.metricLabel]
      .filter(Boolean)
      .join(" ")
      .toLowerCase(),
  };
}

function getVisibleEntries() {
  const filtered = state.entries.filter((entry) => {
    const categoryMatch =
      state.filters.category === "all" || entry.category === state.filters.category;
    const searchMatch =
      state.filters.search.length === 0 ||
      entry.searchKey.includes(state.filters.search);

    return categoryMatch && searchMatch;
  });

  filtered.sort((left, right) => {
    switch (state.filters.sort) {
      case "value-asc":
        return left.valueUsd - right.valueUsd;
      case "name-asc":
        return left.name.localeCompare(right.name);
      case "value-desc":
      default:
        return right.valueUsd - left.valueUsd;
    }
  });

  return filtered.map((entry, index) => ({
    ...entry,
    uiRank: index + 1,
  }));
}

function render() {
  const visibleEntries = getVisibleEntries();
  const totalPages = Math.max(1, Math.ceil(visibleEntries.length / state.pageSize));
  state.currentPage = Math.min(state.currentPage, totalPages);
  const pageStart = (state.currentPage - 1) * state.pageSize;
  const pageEntries = visibleEntries.slice(pageStart, pageStart + state.pageSize);

  elements.tbody.replaceChildren();

  if (visibleEntries.length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "empty-state";
    cell.textContent = "No entries match the current filters.";
    row.append(cell);
    elements.tbody.append(row);
    elements.resultSummary.textContent = "0 results";
    updatePagination(0, 1);
    return;
  }

  const fragment = document.createDocumentFragment();
  pageEntries.forEach((entry) => {
    const clone = elements.rowTemplate.content.cloneNode(true);
    clone.querySelector(".rank-cell").textContent = `#${entry.uiRank}`;
    clone.querySelector(".entry-name").textContent = entry.name;
    clone.querySelector(".entry-symbol").textContent = entry.symbol || entry.metricLabel;

    const categoryPill = clone.querySelector(".category-pill");
    categoryPill.textContent = capitalize(entry.category);
    categoryPill.dataset.kind = entry.category;

    clone.querySelector(".metric-label").textContent = entry.metricLabel;
    clone.querySelector(".entry-value").textContent = formatter.usdLong.format(entry.valueUsd);
    clone.querySelector(".entry-meta").textContent = entry.region || entry.notes || "-";

    fragment.append(clone);
  });

  elements.tbody.append(fragment);
  elements.resultSummary.textContent = `${visibleEntries.length} results, showing ${pageStart + 1}-${pageStart + pageEntries.length}`;
  updatePagination(visibleEntries.length, totalPages);
}

function updatePagination(totalEntries, totalPages) {
  elements.prevPage.disabled = state.currentPage <= 1 || totalEntries === 0;
  elements.nextPage.disabled = state.currentPage >= totalPages || totalEntries === 0;
  elements.pageStatus.textContent = `Page ${state.currentPage} of ${totalPages}`;
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

init();
