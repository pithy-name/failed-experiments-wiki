/* Unit tests for tools/site_assets/filter.js. Run after filter.js in the same engine:
     jsc tools/site_assets/filter.js tests/js/filter_test.js
   Prints "filter tests passed: N" or throws. */
(function () {
  "use strict";
  var F = FewikiFilter;
  var passed = 0;

  function eq(actual, expected, label) {
    var a = JSON.stringify(actual), e = JSON.stringify(expected);
    if (a !== e) { throw new Error(label + ": expected " + e + ", got " + a); }
    passed += 1;
  }

  var fields = [
    {path: "badges", kind: "list", control: "facet"},
    {path: "title", kind: "text", control: "text"},
    {path: "claim_scope", kind: "text", control: "text"},
    {path: "method", kind: "list", control: "facet"},
    {path: "models.name", kind: "list", control: "facet"},
    {path: "failure_type", kind: "enum", control: "facet"},
    {path: "retry_welcome", kind: "bool", control: "facet"},
    {path: "result.n", kind: "number", control: "range"},
    {path: "result.effect_size", kind: "number", control: "range"},
    {path: "source.published", kind: "date", control: "range"}
  ];
  var entries = [
    {id: "fe-1", body: "Notes mention quokka.", badges: ["agent-written", "unreviewed"], data: {
      title: "Steering did nothing", claim_scope: "One vector on GPT-2 small", method: ["activation-steering"],
      models: [{name: "GPT-2 small"}], failure_type: "hypothesis_false", retry_welcome: true,
      result: {direction: "null", n: 200}, source: {published: "2025-03-01"}}},
    {id: "fe-2", body: "", badges: [], data: {
      title: "SAE probes lost", claim_scope: "Gemma dictionaries, zebra splits", method: ["sae", "linear-probing"],
      models: [{name: "Gemma 2 9B"}, {name: "GPT-4o"}], failure_type: "underpowered", retry_welcome: false,
      result: {direction: "smaller_than_expected", n: 5, effect_size: -0.12}, source: {published: "2025-06-10"}}},
    {id: "fe-3", body: "", badges: ["unreviewed"], data: {
      title: "Debate pilot", claim_scope: "Ten debates", method: ["debate"],
      models: [{name: "GPT-4o"}], failure_type: "underpowered", retry_welcome: true,
      result: {direction: "mixed"}, source: {published: "2024-01-15"}}}
  ];
  function ids(state) { return F.filter(entries, state, fields).map(function (e) { return e.id; }); }

  eq(ids({}), ["fe-1", "fe-2", "fe-3"], "no filters shows everything");
  eq(ids({text: "", facets: {}, ranges: {}}), ["fe-1", "fe-2", "fe-3"], "empty state shows everything");

  eq(ids({facets: {failure_type: ["underpowered"]}}), ["fe-2", "fe-3"], "enum facet");
  eq(ids({facets: {method: ["sae", "debate"]}}), ["fe-2", "fe-3"], "OR within one facet");
  eq(ids({facets: {method: ["sae", "debate"], failure_type: ["underpowered"], "models.name": ["Gemma 2 9B"]}}), ["fe-2"], "AND across facets");
  eq(ids({facets: {"models.name": ["GPT-4o"]}}), ["fe-2", "fe-3"], "nested list field");
  eq(ids({facets: {retry_welcome: ["true"]}}), ["fe-1", "fe-3"], "boolean facet true");
  eq(ids({facets: {retry_welcome: ["false"]}}), ["fe-2"], "boolean facet false");
  eq(ids({facets: {badges: ["agent-written"]}}), ["fe-1"], "badge facet");
  eq(ids({facets: {badges: ["unreviewed"]}}), ["fe-1", "fe-3"], "badge facet shared");
  eq(ids({facets: {method: []}}), ["fe-1", "fe-2", "fe-3"], "empty selection is no filter");
  eq(ids({facets: {method: ["rl"]}}), [], "unused value matches nothing");

  eq(ids({ranges: {"result.n": {min: "100"}}}), ["fe-1"], "numeric min, entries without the field excluded");
  eq(ids({ranges: {"result.n": {max: "100"}}}), ["fe-2"], "numeric max");
  eq(ids({ranges: {"result.n": {min: "5", max: "200"}}}), ["fe-1", "fe-2"], "numeric range is inclusive");
  eq(ids({ranges: {"result.n": {min: "9"}}}), ["fe-1"], "numbers compare numerically, not as strings");
  eq(ids({ranges: {"result.effect_size": {max: "0"}}}), ["fe-2"], "negative numbers");
  eq(ids({ranges: {"source.published": {min: "2025-01-01"}}}), ["fe-1", "fe-2"], "date min");
  eq(ids({ranges: {"source.published": {min: "2025-03-01", max: "2025-03-01"}}}), ["fe-1"], "date range inclusive");
  eq(ids({ranges: {"result.n": {min: "", max: ""}}}), ["fe-1", "fe-2", "fe-3"], "blank range is no filter");

  eq(ids({text: "zebra"}), ["fe-2"], "text in claim_scope");
  eq(ids({text: "QUOKKA"}), ["fe-1"], "text in body, case-insensitive");
  eq(ids({text: "gpt-4o debate"}), ["fe-3"], "all terms must match");
  eq(ids({text: "gemma"}), ["fe-2"], "text reaches facet fields too");
  eq(ids({text: "fe-3"}), ["fe-3"], "text matches the id");
  eq(ids({text: "nothinglikethis"}), [], "no match");
  eq(ids({text: "gpt", facets: {failure_type: ["underpowered"]}, ranges: {"source.published": {min: "2025-01-01"}}}), ["fe-2"], "text AND facet AND range");

  eq(F.facetCounts(entries, "failure_type"), [{value: "underpowered", count: 2}, {value: "hypothesis_false", count: 1}], "facet counts, most frequent first");
  eq(F.facetCounts(entries, "models.name"), [{value: "GPT-4o", count: 2}, {value: "GPT-2 small", count: 1}, {value: "Gemma 2 9B", count: 1}], "nested facet counts");
  eq(F.facetCounts(entries, "retry_welcome"), [{value: "true", count: 2}, {value: "false", count: 1}], "boolean facet counts");
  eq(F.facetCounts(entries, "badges"), [{value: "unreviewed", count: 2}, {value: "agent-written", count: 1}], "badge counts");
  eq(F.facetCounts(entries, "benchmarks"), [], "unused field has no values");

  eq(F.isActive({}), false, "inactive state");
  eq(F.isActive({text: "  "}), false, "blank text is inactive");
  eq(F.isActive({facets: {method: ["sae"]}}), true, "facet makes it active");
  eq(F.isActive({ranges: {"result.n": {min: "1"}}}), true, "range makes it active");
  eq(F.getValues({a: [{b: 1}, {b: [2, 3]}, {c: 4}]}, "a.b"), [1, 2, 3], "getValues descends into lists");

  print("filter tests passed: " + passed);
})();
