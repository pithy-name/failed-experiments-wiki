/* DOM layer of the browse page. Kept thin: all filtering lives in filter.js.
   Entry content is untrusted, so text only ever enters the page through
   textContent and createElement, never as markup. */
(function () {
  "use strict";

  var payload = JSON.parse(document.getElementById("fewiki-data").textContent);
  var fields = payload.fields;
  var entries = payload.entries;
  var state = {text: "", facets: {}, ranges: {}};
  var openId = null;   // entry whose "All fields" view is open when the page loads from a link

  /* ---------- link state ----------
     The current filters live in the URL fragment, so a filtered view can be shared:
       #q=words&f.failure_type=underpowered|unknown&min.source.published=2025-01-01&open=fe-2026-0010
     Only fields in the catalogue are accepted; anything else in the fragment is ignored. */
  var fieldByPath = {};
  fields.forEach(function (f) { fieldByPath[f.path] = f; });

  function decode(text) {
    try { return decodeURIComponent(String(text).replace(/\+/g, " ")); } catch (e) { return ""; }
  }

  function readLink() {
    var raw = (typeof location !== "undefined" && location.hash) ? String(location.hash).replace(/^#/, "") : "";
    raw.split("&").forEach(function (pair) {
      if (!pair) { return; }
      var cut = pair.indexOf("=");
      var key = decode(cut < 0 ? pair : pair.slice(0, cut));
      var value = decode(cut < 0 ? "" : pair.slice(cut + 1));
      var path, field;
      if (key === "q") {
        state.text = value;
      } else if (key === "open") {
        if (/^fe-\d{4}-\d{4}$/.test(value)) { openId = value; }
      } else if (key.indexOf("f.") === 0) {
        path = key.slice(2); field = fieldByPath[path];
        if (field && field.control === "facet") { state.facets[path] = value.split("|").filter(Boolean); }
      } else if (key.indexOf("min.") === 0 || key.indexOf("max.") === 0) {
        path = key.slice(4); field = fieldByPath[path];
        if (field && field.control === "range") {
          state.ranges[path] = state.ranges[path] || {};
          state.ranges[path][key.slice(0, 3)] = value;
        }
      }
    });
  }

  function writeLink() {
    if (typeof history === "undefined" || typeof history.replaceState !== "function") { return; }
    var parts = [];
    if (String(state.text || "").trim()) { parts.push("q=" + encodeURIComponent(state.text)); }
    Object.keys(state.facets).sort().forEach(function (path) {
      if (state.facets[path] && state.facets[path].length) {
        parts.push("f." + encodeURIComponent(path) + "=" + state.facets[path].map(encodeURIComponent).join("|"));
      }
    });
    Object.keys(state.ranges).sort().forEach(function (path) {
      ["min", "max"].forEach(function (bound) {
        var value = (state.ranges[path] || {})[bound];
        if (value !== undefined && value !== null && value !== "") {
          parts.push(bound + "." + encodeURIComponent(path) + "=" + encodeURIComponent(value));
        }
      });
    });
    if (openId) { parts.push("open=" + encodeURIComponent(openId)); }
    try { history.replaceState(null, "", "#" + parts.join("&")); } catch (e) { /* file:// pages in some browsers refuse; filters still work */ }
  }

  function groupHasActiveFilter(groupId) {
    return fields.some(function (f) {
      if (f.group !== groupId) { return false; }
      var range = state.ranges[f.path] || {};
      return (state.facets[f.path] || []).length > 0 || !!range.min || !!range.max;
    });
  }

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
      details.setAttribute("data-group", group.id);
      details.open = !!group.open || groupHasActiveFilter(group.id);
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
      input.setAttribute("data-facet", field.path);     // lets tests and scripts find a control without relying on layout
      input.setAttribute("data-value", item.value);
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
      input.setAttribute("data-range", field.path);
      input.setAttribute("data-bound", bound);
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
    article.id = "entry-" + entry.id;
    var head = el("header", "card-head");
    head.appendChild(el("span", "entry-id", entry.id));
    var badges = el("span", "badges");
    (entry.badges || []).forEach(function (badge) { badges.appendChild(el("span", "badge badge-" + badge, BADGE_TEXT[badge] || badge)); });
    if ((data.review || {}).status === "reviewed") {
      // Say who reviewed: an agent review is weaker than a human one, and readers should see which it was.
      var kinds = FewikiFilter.getValues(data, "review.reviewers.type");
      var by = kinds.indexOf("human") !== -1 ? "by a person" : kinds.indexOf("agent") !== -1 ? "by an agent only" : "";
      badges.appendChild(el("span", "badge badge-reviewed", by ? "Reviewed " + by : "Reviewed"));
    }
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
    details.open = (entry.id === openId);
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
    writeLink();
  }

  /* ---------- wiring ---------- */

  var search = document.getElementById("search");
  search.addEventListener("input", function () { state.text = search.value; renderResults(); });
  document.getElementById("clear").addEventListener("click", function () {
    state = {text: "", facets: {}, ranges: {}};
    openId = null;
    search.value = "";
    renderFilters();
    renderResults();
  });

  readLink();
  search.value = state.text;
  renderFilters();
  renderResults();
  if (openId) {
    var target = document.getElementById("entry-" + openId);
    if (target && typeof target.scrollIntoView === "function") { target.scrollIntoView(); }
  }
})();
