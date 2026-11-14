(function (root) {
  "use strict";
  const MISSING = "__unassigned__";
  const keys = ["subjects", "genres", "topics", "languages", "legacy", "author", "location"];
  const folded = text => String(text).normalize("NFC").toLocaleLowerCase("cs");
  function values(item, key) {
    let found;
    if (key === "author" || key === "location") found = [item["book_" + key] || ""];
    else if (key === "legacy") found = (item.tags || []).filter(x => !["obalka", "ma-obrazek"].includes(folded(x)));
    else found = (item.book_classification || {})[key] || [];
    const unique = new Map();
    found.forEach(value => { const text = String(value).trim(); if (text) unique.set(folded(text), text); });
    return unique.size ? [...unique.values()] : [MISSING];
  }
  function matches(item, selections, except = "") {
    return keys.every(key => key === except || !(selections[key] || []).length ||
      selections[key].some(selected => values(item, key).some(value => folded(value) === folded(selected))));
  }
  function facets(items, selections, key) {
    const counts = new Map();
    items.filter(item => matches(item, selections, key)).forEach(item => values(item, key).forEach(value => {
      const id = folded(value), entry = counts.get(id) || {value, count: 0}; entry.count++; counts.set(id, entry);
    }));
    // Keep a chosen zero-count value visible; never silently broaden a query.
    (selections[key] || []).forEach(value => {
      const entry = counts.get(folded(value));
      if (entry) entry.value = value;
      else counts.set(folded(value), {value, count: 0});
    });
    return [...counts.values()].sort((a, b) => a.value.localeCompare(b.value, "cs", {sensitivity: "base"}));
  }
  function describe(value) {
    if (!value) return "Katalogové třídění zatím není doplněné.";
    return [["Obor", value.subjects], ["Žánr / forma", value.genres], ["Témata", value.topics], ["Jazyk", value.languages]]
      .filter(([name, entries]) => name === "Obor" || (entries || []).length)
      .map(([name, entries]) => name + ": " + ((entries || []).join("; ") || "Bez zařazení")).join(" · ");
  }
  const api = {MISSING, keys, values, matches, facets, describe};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.LibraryBookFacets = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
