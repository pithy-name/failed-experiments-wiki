/* A very small stand-in for the browser DOM, enough to execute tools/site_assets/app.js
   in a bare JavaScript engine. It is not a browser: layout, CSS and real events are
   not modelled. It lets a test prove that the page script runs, renders one card
   per matching entry, and reacts to the search box, a facet checkbox and "clear".

   Expects a global __FEWIKI_DATA__ (the page's embedded JSON, as a string). */
var __elements = {};

function FakeElement(tag) {
  this.tagName = tag;
  this.children = [];
  this.listeners = {};
  this._text = "";
  this.className = "";
}
Object.defineProperty(FakeElement.prototype, "textContent", {
  get: function () {
    return this._text + this.children.map(function (c) { return c.textContent; }).join("");
  },
  set: function (value) { this.children = []; this._text = String(value); }
});
Object.defineProperty(FakeElement.prototype, "innerHTML", {
  get: function () { return ""; },
  set: function () { throw new Error("innerHTML must never be assigned: entry content is untrusted"); }
});
FakeElement.prototype.appendChild = function (child) { this.children.push(child); return child; };
FakeElement.prototype.setAttribute = function (name, value) { (this.attributes = this.attributes || {})[name] = String(value); };
FakeElement.prototype.getAttribute = function (name) { return (this.attributes || {})[name]; };
FakeElement.prototype.addEventListener = function (type, handler) {
  (this.listeners[type] = this.listeners[type] || []).push(handler);
};
FakeElement.prototype.fire = function (type) {
  (this.listeners[type] || []).forEach(function (handler) { handler({type: type}); });
};
FakeElement.prototype.find = function (predicate, out) {
  out = out || [];
  if (predicate(this)) { out.push(this); }
  this.children.forEach(function (child) { child.find(predicate, out); });
  return out;
};

var document = {
  createElement: function (tag) { return new FakeElement(tag); },
  getElementById: function (id) {
    if (!__elements[id]) { __elements[id] = new FakeElement("div"); }
    return __elements[id];
  }
};
document.getElementById("fewiki-data").textContent = __FEWIKI_DATA__;

/* The URL fragment. A test may preset it with a global __FEWIKI_HASH__ to load the page "from a link". */
var location = {hash: (typeof __FEWIKI_HASH__ === "string") ? __FEWIKI_HASH__ : ""};
var history = {replaceState: function (state, title, url) { location.hash = String(url); }};
