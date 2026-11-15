/* The page loaded from a link that carries filters. Run order:
     jsc data.js (which also sets __FEWIKI_HASH__) tests/js/fake_dom.js filter.js app.js tests/js/link_test.js
   The preset link is:
     #f.failure_type=underpowered&q=sae&min.source.published=2025-01-01&open=fe-2026-0002&f.not_a_field=x&junk
   Prints "link tests passed: N" or throws. */
(function () {
  "use strict";
  var passed = 0;
  function eq(actual, expected, label) {
    if (actual !== expected) { throw new Error(label + ": expected " + JSON.stringify(expected) + ", got " + JSON.stringify(actual)); }
    passed += 1;
  }
  var count = document.getElementById("count");
  var results = document.getElementById("results");
  var filters = document.getElementById("filters");
  function cards() { return results.find(function (n) { return n.className === "card"; }); }

  eq(document.getElementById("search").value, "sae", "the search box shows the text from the link");
  eq(count.textContent, "1 of 3 entries", "facet, text and range from the link are all applied");
  eq(cards().length, 1, "one card is shown");
  eq(cards()[0].id, "entry-fe-2026-0002", "it is the entry the filters select");

  var opened = results.find(function (n) { return n.className === "all-fields" && n.open === true; });
  eq(opened.length, 1, "the entry named in the link has its full view open");

  var ticked = filters.find(function (n) { return n.tagName === "input" && n.type === "checkbox" && n.checked === true; });
  eq(ticked.length, 1, "the facet value from the link is ticked");

  var dates = filters.find(function (n) { return n.tagName === "input" && n.type === "date" && n.value === "2025-01-01"; });
  eq(dates.length, 1, "the range from the link is filled in");

  eq(document.getElementById("clear").disabled, false, "clear is enabled");
  eq(location.hash.indexOf("not_a_field"), -1, "unknown fields in a link are dropped");
  eq(location.hash, "#q=sae&f.failure_type=underpowered&min.source.published=2025-01-01&open=fe-2026-0002", "the link is rewritten in canonical form");

  print("link tests passed: " + passed);
})();
