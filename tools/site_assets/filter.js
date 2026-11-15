/* Pure filter logic for the browse page. No DOM access, so it can be unit-tested
   in any JavaScript engine (tests/js/filter_test.js). */
var FewikiFilter = (function () {
  "use strict";

  /* All values at a dotted path, descending into arrays. Missing -> []. */
  function getValues(data, path) {
    var current = [data];
    var parts = path.split(".");
    for (var i = 0; i < parts.length; i++) {
      var next = [];
      for (var j = 0; j < current.length; j++) {
        var item = current[j];
        if (item !== null && typeof item === "object" && !Array.isArray(item) &&
            Object.prototype.hasOwnProperty.call(item, parts[i])) {
          var value = item[parts[i]];
          if (Array.isArray(value)) { next = next.concat(value); } else { next.push(value); }
        }
      }
      current = next;
    }
    return current.filter(function (value) { return value !== null && value !== undefined; });
  }

  /* An entry is {id, data, body, badges}. "badges" is a derived pseudo-field. */
  function entryValues(entry, path) {
    if (path === "badges") { return entry.badges || []; }
    return getValues(entry.data, path);
  }

  function facetKey(value) {
    if (value === true) { return "true"; }
    if (value === false) { return "false"; }
    return String(value);
  }

  function matchesFacet(entry, path, wanted) {
    if (!wanted || wanted.length === 0) { return true; }
    var have = entryValues(entry, path).map(facetKey);
    for (var i = 0; i < wanted.length; i++) {
      if (have.indexOf(wanted[i]) !== -1) { return true; }   // OR within one field
    }
    return false;
  }

  function isBlank(value) {
    return value === undefined || value === null || value === "";
  }

  /* Inclusive range. Numbers compare numerically, dates (YYYY-MM-DD) as strings.
     An entry without the field never matches a range that is set. */
  function matchesRange(entry, path, kind, range) {
    if (!range || (isBlank(range.min) && isBlank(range.max))) { return true; }
    var values = entryValues(entry, path);
    if (values.length === 0) { return false; }
    function norm(value) { return kind === "number" ? Number(value) : String(value); }
    for (var i = 0; i < values.length; i++) {
      var value = norm(values[i]);
      if (kind === "number" && isNaN(value)) { continue; }
      if (!isBlank(range.min) && value < norm(range.min)) { continue; }
      if (!isBlank(range.max) && value > norm(range.max)) { continue; }
      return true;
    }
    return false;
  }

  /* Everything searchable about an entry, lower-cased: every field value, the body, the badges. */
  function haystack(entry, fields) {
    var parts = [entry.id || "", entry.body || ""].concat(entry.badges || []);
    for (var i = 0; i < fields.length; i++) {
      var values = getValues(entry.data, fields[i].path);
      for (var j = 0; j < values.length; j++) {
        if (typeof values[j] !== "object") { parts.push(String(values[j])); }
      }
    }
    return parts.join(" \n ").toLowerCase();
  }

  /* Every whitespace-separated term must occur somewhere. */
  function matchesText(entry, fields, text) {
    var terms = String(text || "").toLowerCase().split(/\s+/).filter(Boolean);
    if (terms.length === 0) { return true; }
    var hay = haystack(entry, fields);
    for (var i = 0; i < terms.length; i++) {
      if (hay.indexOf(terms[i]) === -1) { return false; }
    }
    return true;
  }

  /* state = {text: "", facets: {path: [keys]}, ranges: {path: {min, max}}}.
     Different fields combine with AND. */
  function matches(entry, state, fields) {
    state = state || {};
    if (!matchesText(entry, fields, state.text)) { return false; }
    var facets = state.facets || {};
    for (var path in facets) {
      if (Object.prototype.hasOwnProperty.call(facets, path) && !matchesFacet(entry, path, facets[path])) { return false; }
    }
    var ranges = state.ranges || {};
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];
      if (field.control === "range" && !matchesRange(entry, field.path, field.kind, ranges[field.path])) { return false; }
    }
    return true;
  }

  function filter(entries, state, fields) {
    return entries.filter(function (entry) { return matches(entry, state, fields); });
  }

  /* [{value, count}] for one facet field, most frequent first; an entry counts once per value. */
  function facetCounts(entries, path) {
    var counts = {};
    entries.forEach(function (entry) {
      var seen = {};
      entryValues(entry, path).map(facetKey).forEach(function (key) {
        if (!seen[key]) { seen[key] = true; counts[key] = (counts[key] || 0) + 1; }
      });
    });
    return Object.keys(counts).map(function (key) { return {value: key, count: counts[key]}; })
      .sort(function (a, b) { return b.count - a.count || (a.value < b.value ? -1 : a.value > b.value ? 1 : 0); });
  }

  function isActive(state) {
    state = state || {};
    if (String(state.text || "").trim()) { return true; }
    var facets = state.facets || {}, ranges = state.ranges || {}, key;
    for (key in facets) { if (facets[key] && facets[key].length) { return true; } }
    for (key in ranges) { if (ranges[key] && (!isBlank(ranges[key].min) || !isBlank(ranges[key].max))) { return true; } }
    return false;
  }

  return {
    getValues: getValues, entryValues: entryValues, facetKey: facetKey, matchesFacet: matchesFacet,
    matchesRange: matchesRange, matchesText: matchesText, matches: matches, filter: filter,
    facetCounts: facetCounts, isActive: isActive
  };
})();
