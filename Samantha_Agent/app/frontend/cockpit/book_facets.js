(function (root) {
  "use strict";
  const MISSING = "__unassigned__";
  const SUBJECTS = ["Antropologie, etnografie", "Biologické vědy", "Divadlo, film, tanec", "Ekonomické vědy, obchod", "Filozofie a náboženství", "Fyzika a příbuzné vědy", "Geografie. Geologie", "Historie. Biografie", "Hudba", "Chemie. Mineralogie", "Lingvistika. Literární věda", "Všeobecnosti. Informatika", "Matematika", "Lékařství", "Politické vědy", "Právo", "Psychologie", "Sociologie", "Technika, technologie", "Sport. Rekreace", "Umění, architektura", "Výchova a vzdělávání", "Výpočetní technika", "Zemědělství", "Beletrie", "Literatura pro děti a mládež"];
  const keys = ["subjects", "genres", "topics", "languages", "author", "location"];
  const folded = text => String(text).normalize("NFC").toLocaleLowerCase("cs");
  function values(item, key) {
    let found;
    if (key === "author" || key === "location") found = [item["book_" + key] || ""];
    else if (key === "subjects" && Array.isArray(item.book_subjects)) found = item.book_subjects;
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
  function describe(value, manual = null) {
    if (!value && manual === null) return "Obor zatím není přiřazený. Vyber jej z nabídky.";
    value = value || {};
    return [[manual === null ? "Obor" : "Obor (ručně)", manual === null ? value.subjects : manual], ["Žánr / forma", value.genres], ["Témata", value.topics], ["Jazyk", value.languages]]
      .filter(([name, entries]) => name.startsWith("Obor") || (entries || []).length)
      .map(([name, entries]) => name + ": " + ((entries || []).join("; ") || "Bez zařazení")).join(" · ");
  }
  function fillSubjects(select, selected, doc) {
    select.replaceChildren();
    [...SUBJECTS].sort((a,b) => a.localeCompare(b,"cs")).forEach(value => {
      const option = doc.createElement("option"); option.value = value; option.textContent = value;
      option.selected = (selected || []).includes(value); select.append(option);
    });
  }
  function selectedSubjects(select) {
    return Array.from(select.selectedOptions).map(option => option.value).filter(Boolean);
  }
  function describeItem(item) { return describe(item.book_classification, item.book_subjects_origin === "manual" ? item.book_subjects : null); }
  const api = {MISSING, SUBJECTS, keys, values, matches, facets, describe, describeItem, fillSubjects, selectedSubjects};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.LibraryBookFacets = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
