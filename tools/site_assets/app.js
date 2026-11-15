/* DOM layer of the browse page. Kept thin: all filtering lives in filter.js.
   Entry content is untrusted, so text only ever enters the page through
   textContent and createElement, never as markup. */
(function () {
  "use strict";

  var payload = JSON.parse(document.getElementById("fewiki-data").textContent);
  var fields = payload.fields;
  var entries = payload.entries;
  var state = {text: "", facets: {}, ranges: {}};

  var BADGE_TEXT = {
    "agent-written": "Agent-written", "unreviewed": "Unreviewed", "contested": "Contested",
    "superseded": "Superseded", "retry-welcome": "Retry welcome"
  };

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function safeLink(url, label) {
    var text = label || url;
    if (typeof url === "string" && /^https?:\/\//i.test(url)) {
      var a = el("a", null, text);
      a.href = url;
      a.rel = "noopener noreferrer";
      return a;
    }
    return el("span", null, text);
  }

  function fileLink(entry) {
    var a = el("a", null, payload.repo_url ? "Entry file on GitHub" : "Entry file");
    a.href = entry.file_url;   // built by build_site.py: a GitHub URL or a relative path, never entry content
    return a;
  }

  /* ---------- filter panel ---------- */

  function renderFilters() {
    var panel = document.getElementById("filters");
    panel.textContent = "";
    payload.groups.forEach(function (group) {
      var controls = [];
      fields.filter(function (f) { return f.group === group.id; }).forEach(function (field) {
        var control = field.control === "facet" ? facetControl(field) : field.control === "range" ? rangeControl(field) : null;
        if (control) { controls.push(control); }
      });
      if (controls.length === 0) { return; }
      var details = el("details", "group");
      details.open = !!group.open;
      details.appendChild(el("summary", null, group.label));
      controls.forEach(function (control) { details.appendChild(control); });
      panel.appendChild(details);
    });
  }

  function facetControl(field) {
    var counts = FewikiFilter.facetCounts(entries, field.path);
    if (counts.length === 0) { return null; }             // hide fields no entry uses
    var box = el("fieldset", "facet");
    box.appendChild(el("legend", null, field.label));
    var list = el("div", "facet-values");
    counts.forEach(function (item) {
      var label = el("label", "facet-value");
      var input = document.createElement("input");
      input.type = "checkbox";
      input.checked = (state.facets[field.path] || []).indexOf(item.value) !== -1;
      input.addEventListener("change", function () {
        var chosen = (state.facets[field.path] || []).filter(function (v) { return v !== item.value; });
        if (input.checked) { chosen.push(item.value); }
        state.facets[field.path] = chosen;
        renderResults();
      });
      label.appendChild(input);
      label.appendChild(el("span", "facet-name", field.path === "badges" ? (BADGE_TEXT[item.value] || item.value) : item.value));
      label.appendChild(el("span", "facet-count", item.count));
      list.appendChild(label);
    });
    box.appendChild(list);
    return box;
  }

  function rangeControl(field) {
    var present = entries.some(function (entry) { return FewikiFilter.entryValues(entry, field.path).length > 0; });
    if (!present) { return null; }
    var box = el("fieldset", "range");
    box.appendChild(el("legend", null, field.label));
    ["min", "max"].forEach(function (bound) {
      var label = el("label", "range-bound", bound === "min" ? "from " : "to ");
      var input = document.createElement("input");
      input.type = field.kind === "date" ? "date" : "number";
      if (field.kind === "number") { input.step = "any"; }
      input.value = (state.ranges[field.path] || {})[bound] || "";
      input.addEventListener("input", function () {
        var range = state.ranges[field.path] || {};
        range[bound] = input.value;
        state.ranges[field.path] = range;
        renderResults();
      });
      label.appendChild(input);
      box.appendChild(label);
    });
    return box;
  }

  /* ---------- results ---------- */

  function chips(values, className) {
    var wrap = el("span", "chips");
    values.forEach(function (value) { wrap.appendChild(el("span", "chip " + (className || ""), value)); });
    return wrap;
  }

  function metaRow(label, node) {
    var row = el("div", "meta-row");
    row.appendChild(el("span", "meta-label", label));
    if (typeof node === "string" || typeof node === "number" || typeof node === "boolean") { node = el("span", null, node); }
    row.appendChild(node);
    return row;
  }

  function renderValue(value) {
    if (Array.isArray(value)) {
      if (value.length === 0) { return el("span", "muted", "none"); }
      if (value.every(function (v) { return v === null || typeof v !== "object"; })) { return chips(value); }
      var list = el("div", "nested-list");
      value.forEach(function (item) { list.appendChild(renderValue(item)); });
      return list;
    }
    if (value !== null && typeof value === "object") {
      var table = el("dl", "nested");
      Object.keys(value).forEach(function (key) {
        table.appendChild(el("dt", null, key));
        var dd = el("dd");
        dd.appendChild(renderValue(value[key]));
        table.appendChild(dd);
      });
      return table;
    }
    if (typeof value === "string" && /^https?:\/\//i.test(value)) { return safeLink(value); }
    return el("span", null, value === null ? "" : String(value));
  }

  function card(entry) {
    var data = entry.data;
    var article = el("article", "card");
    var head = el("header", "card-head");
    head.appendChild(el("span", "entry-id", entry.id));
    var badges = el("span", "badges");
    (entry.badges || []).forEach(function (badge) { badges.appendChild(el("span", "badge badge-" + badge, BADGE_TEXT[badge] || badge)); });
    if ((data.review || {}).status === "reviewed") { badges.appendChild(el("span", "badge badge-reviewed", "Reviewed")); }
    head.appendChild(badges);
    article.appendChild(head);
    article.appendChild(el("h2", "card-title", data.title));

    var note = (data.contributor || {}).note;
    if (note) { article.appendChild(el("p", "contributor-note", note)); }

    var meta = el("div", "meta");
    meta.appendChild(metaRow("Area", chips(data.research_area || [])));
    meta.appendChild(metaRow("Method", chips(data.method || [])));
    meta.appendChild(metaRow("Models", chips(FewikiFilter.getValues(data, "models.name"))));
    meta.appendChild(metaRow("Result", (data.result || {}).direction || ""));
    meta.appendChild(metaRow("Failure type", data.failure_type || ""));
    meta.appendChild(metaRow("Confidence it is a true negative", data.confidence_true_negative || ""));
    meta.appendChild(metaRow("Evidence", data.evidence_level || ""));
    meta.appendChild(metaRow("Review", (data.review || {}).status || ""));
    meta.appendChild(metaRow("Written by", ((data.contributor || {}).type || "") + " · " + ((data.contributor || {}).handle || "")));
    article.appendChild(meta);

    var source = data.source || {};
    var quote = el("blockquote", "quote", source.quote || "");
    article.appendChild(quote);
    var cite = el("p", "cite");
    cite.appendChild(safeLink(source.url, source.title || source.url));
    cite.appendChild(el("span", null, " — " + (source.authors || []).join(", ") + ", " + (source.published || "")));
    article.appendChild(cite);

    var details = el("details", "all-fields");
    details.appendChild(el("summary", null, "All fields"));
    details.appendChild(renderValue(data));
    if (entry.body) {
      details.appendChild(el("h3", null, "Notes"));
      details.appendChild(el("pre", "body", entry.body));
    }
    var links = el("p", "links");
    links.appendChild(fileLink(entry));
    details.appendChild(links);
    article.appendChild(details);
    return article;
  }

  function renderResults() {
    var shown = FewikiFilter.filter(entries, state, fields);
    document.getElementById("count").textContent = shown.length + " of " + entries.length + " entries";
    document.getElementById("clear").disabled = !FewikiFilter.isActive(state);
    var results = document.getElementById("results");
    results.textContent = "";
    if (shown.length === 0) {
      results.appendChild(el("p", "empty", "No entry matches these filters. That means nobody has filed one here, not that the idea is untested."));
    }
    shown.forEach(function (entry) { results.appendChild(card(entry)); });
  }

  /* ---------- wiring ---------- */

  var search = document.getElementById("search");
  search.addEventListener("input", function () { state.text = search.value; renderResults(); });
  document.getElementById("clear").addEventListener("click", function () {
    state = {text: "", facets: {}, ranges: {}};
    search.value = "";
    renderFilters();
    renderResults();
  });

  renderFilters();
  renderResults();
})();
