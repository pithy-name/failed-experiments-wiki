/* Executes the page script against the fake DOM. Run order:
     jsc data.js tests/js/fake_dom.js tools/site_assets/filter.js tools/site_assets/app.js tests/js/dom_test.js
   Prints "dom tests passed: N" or throws. */
(function () {
  "use strict";
  var passed = 0;
  function eq(actual, expected, label) {
    if (actual !== expected) { throw new Error(label + ": expected " + JSON.stringify(expected) + ", got " + JSON.stringify(actual)); }
    passed += 1;
  }
  function ok(value, label) { eq(!!value, true, label); }

  var total = JSON.parse(__FEWIKI_DATA__).entries.length;
  var count = document.getElementById("count");
  var results = document.getElementById("results");
  var filters = document.getElementById("filters");
  var search = document.getElementById("search");
  var clear = document.getElementById("clear");
  function cards() { return results.find(function (n) { return n.className === "card"; }); }

  eq(count.textContent, total + " of " + total + " entries", "initial count");
  eq(cards().length, total, "one card per entry");
  eq(clear.disabled, true, "clear is disabled with no filters");

  var page = results.textContent;
  ok(page.indexOf("Unreviewed") !== -1, "badges are rendered");
  ok(page.indexOf("Draft awaiting verification.") !== -1, "contributor note is rendered on the card");
  ok(page.indexOf("</script><script>alert(1)</script>") !== -1, "hostile title is shown as plain text");
  ok(page.indexOf("All fields") !== -1, "detail view exists");

  var links = results.find(function (n) { return n.tagName === "a"; });
  ok(links.length >= total, "entries have links");
  links.forEach(function (a) {
    ok(/^https?:\/\//.test(a.href) || /^\.\.\/entries\/fe-\d{4}-\d{4}\.md$/.test(a.href), "link target is http(s) or an entry file: " + a.href);
  });

  ok(filters.textContent.indexOf("failure type") !== -1, "facet for failure_type exists");
  ok(filters.textContent.indexOf("source › published") !== -1, "range control for the published date exists");
  ok(filters.textContent.indexOf("result › ci low") === -1, "fields no entry uses are hidden");

  search.value = "quokka";
  search.fire("input");
  eq(count.textContent, "1 of " + total + " entries", "search narrows the list");
  eq(cards().length, 1, "search re-renders the cards");
  eq(clear.disabled, false, "clear is enabled when a filter is active");

  clear.fire("click");
  eq(count.textContent, total + " of " + total + " entries", "clear restores everything");
  eq(search.value, "", "clear empties the search box");

  var boxes = document.getElementById("filters").find(function (n) { return n.tagName === "input" && n.type === "checkbox"; });
  ok(boxes.length > 5, "facet checkboxes exist");
  var changed = false;
  for (var i = 0; i < boxes.length && !changed; i++) {
    boxes[i].checked = true;
    boxes[i].fire("change");
    var shown = cards().length;
    if (shown > 0 && shown < total) { changed = true; }
    boxes[i].checked = false;
    boxes[i].fire("change");
  }
  ok(changed, "ticking a facet value narrows the list");
  eq(cards().length, total, "unticking restores everything");

  search.value = "no-entry-says-this";
  search.fire("input");
  eq(cards().length, 0, "no cards when nothing matches");
  ok(results.textContent.indexOf("nobody has filed one") !== -1, "empty state explains what no match means");

  print("dom tests passed: " + passed);
})();
