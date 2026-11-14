(function (root) {
  "use strict";
  const MISSING = "__unassigned__";
  const SUBJECTS = ["Antropologie, etnografie", "Biologické vědy", "Divadlo, film, tanec", "Ekonomické vědy, obchod", "Filozofie a náboženství", "Fyzika a příbuzné vědy", "Geografie. Geologie", "Historie. Biografie", "Hudba", "Chemie. Mineralogie", "Lingvistika. Literární věda", "Všeobecnosti. Informatika", "Matematika", "Lékařství", "Politické vědy", "Právo", "Psychologie", "Sociologie", "Technika, technologie", "Sport. Rekreace", "Umění, architektura", "Výchova a vzdělávání", "Výpočetní technika", "Zemědělství", "Beletrie", "Literatura pro děti a mládež"];
  const keys = ["subjects", "groups", "genres", "topics", "languages", "author", "location"];
  let groupOptions = [];
  const groupText = group => `${group.subject} → ${group.label}`;
  function groupsFor(item) {
    const subjects = Array.isArray(item.book_subjects) ? item.book_subjects : (item.book_classification || {}).subjects || [];
    return (item.book_groups || (item.book_classification || {}).groups || []).filter(group => subjects.includes(group.subject));
  }
  const folded = text => String(text).normalize("NFC").toLocaleLowerCase("cs");
  function values(item, key, subjects = []) {
    let found;
    if (key === "groups") found = groupsFor(item).filter(group => !subjects.length || subjects.includes(group.subject)).map(group => group.code);
    else if (key === "author" || key === "location") found = [item["book_" + key] || ""];
    else if (key === "subjects" && Array.isArray(item.book_subjects)) found = item.book_subjects;
    else found = (item.book_classification || {})[key] || [];
    const unique = new Map();
    found.forEach(value => { const text = String(value).trim(); if (text) unique.set(folded(text), text); });
    return unique.size ? [...unique.values()] : [MISSING];
  }
  function matches(item, selections, except = "") {
    return keys.every(key => key === except || !(selections[key] || []).length ||
      selections[key].some(selected => values(item, key, except === "subjects" ? [] : selections.subjects || []).some(value => folded(value) === folded(selected))));
  }
  function facets(items, selections, key) {
    const counts = new Map();
    items.filter(item => matches(item, selections, key)).forEach(item => values(item, key, selections.subjects || []).forEach(value => {
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
  function describe(value, manual = null, manualGroups = null) {
    if (!value && manual === null && manualGroups === null) return "Obor zatím není přiřazený. Vyber jej z nabídky.";
    value = value || {};
    const subjects = manual === null ? value.subjects || [] : manual;
    const groups = (manualGroups === null ? value.groups || [] : manualGroups).filter(group => subjects.includes(group.subject));
    return [[manual === null ? "Obor" : "Obor (ručně)", subjects], [manualGroups === null ? "Skupina" : "Skupina (ručně)", groups.map(groupText)], ["Žánr / forma", value.genres], ["Témata", value.topics], ["Jazyk", value.languages]]
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
  function setGroupOptions(options) { groupOptions = Array.isArray(options) ? options : []; }
  function fillGroups(select, subjects, selected, catalog, doc) {
    const choices = new Map(groupOptions.map(group => [group.code, group]));
    // A catalogue may use a valid code absent from the manual names table.
    (catalog || []).forEach(group => { if (!choices.has(group.code)) choices.set(group.code, group); });
    select.replaceChildren();
    [...choices.values()].filter(group => (subjects || []).includes(group.subject))
      .sort((a,b) => groupText(a).localeCompare(groupText(b), "cs")).forEach(group => {
        const option = doc.createElement("option"); option.value = group.code;
        option.textContent = `${group.label} (${group.code})`; option.dataset.subject = group.subject;
        option.disabled = !groupOptions.some(entry => entry.code === group.code);
        option.selected = (selected || []).includes(group.code); select.append(option);
      });
  }
  function selectedGroups(select) {
    return Array.from(select.selectedOptions).filter(option => !option.disabled).map(option => option.value).filter(Boolean);
  }
  function manualGroupEntries(codes) { return groupOptions.filter(group => codes.includes(group.code)); }
  function groupLabel(code, items) {
    const group = (items || []).flatMap(groupsFor).find(entry => entry.code === code);
    return group ? groupText(group) : code;
  }
  function describeItem(item) {
    const value = {...(item.book_classification || {}),
      subjects: Array.isArray(item.book_subjects) ? item.book_subjects : (item.book_classification || {}).subjects,
      groups: groupsFor(item)};
    return describe(value, item.book_subjects_origin === "manual" ? item.book_subjects : null,
      item.book_groups_origin === "manual" ? item.book_groups || [] : null);
  }
  const api = {MISSING, SUBJECTS, keys, values, matches, facets, describe, describeItem, fillSubjects, selectedSubjects,
    setGroupOptions, fillGroups, selectedGroups, manualGroupEntries, groupsFor, groupText, groupLabel};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.LibraryBookFacets = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
