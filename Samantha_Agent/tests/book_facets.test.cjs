const assert = require("node:assert/strict");
const {MISSING, values, matches, facets, describe} = require("../app/frontend/cockpit/book_facets.js");
const book = (id, subjects, genres, topics = []) => ({id, book_classification: {subjects, genres, topics}, book_author: "Autor", book_location: "obývák"});
const items = [book("a", ["Beletrie", "Beletrie"], ["romány"], ["historie"]),
  book("b", ["Beletrie", "Literatura pro děti a mládež"], ["pohádky"]),
  book("c", ["Matematika"], ["učebnice"]), {id: "old", tags: ["fantasy", "obalka", "ma-obrazek"]}];
assert.deepEqual(values(items[0], "subjects"), ["Beletrie"]);
assert.deepEqual(values(items[3], "subjects"), [MISSING]);
assert.equal(require("../app/frontend/cockpit/book_facets.js").keys.includes("legacy"), false);
assert.deepEqual(facets(items, {}, "subjects").find(x => x.value === "Beletrie"), {value: "Beletrie", count: 2});
let query = {subjects: ["Beletrie", "Matematika"], genres: ["učebnice", "romány"]};
assert.deepEqual(items.filter(item => matches(item, query)).map(x => x.id), ["a", "c"], "OR inside a group; AND between groups");
query = {subjects: ["Beletrie"], genres: ["romány"], topics: ["historie"]};
assert.deepEqual(items.filter(item => matches(item, query)).map(x => x.id), ["a"]);
assert.deepEqual(facets(items, {subjects: ["Beletrie"]}, "genres").map(x => x.value), ["pohádky", "romány"]);
assert.deepEqual(facets(items, {subjects: ["Matematika"], genres: ["romány"]}, "genres"), [{value: "romány", count: 0}, {value: "učebnice", count: 1}]);
assert.deepEqual(items.filter(item => matches(item, {subjects: [MISSING]})).map(x => x.id), ["old"]);
assert.equal(facets([...items, book("d", ["Fyzika a příbuzné vědy"], [])], {}, "subjects").length, 5, "new saved subjects appear immediately");
assert.equal(facets(items, {}, "subjects").some(x => x.value === "Fyzika a příbuzné vědy"), false);
assert.match(describe({subjects: [], topics: ["téma"], languages: []}), /Obor: Bez zařazení · Témata: téma/);
console.log("Book facets: counts, dependent options, OR/AND, missing and legacy values passed.");
const manual={...items[0],book_subjects:["Matematika"],book_subjects_origin:"manual"};
assert.deepEqual(values(manual,"subjects"),["Matematika"]);
assert.match(require("../app/frontend/cockpit/book_facets.js").describeItem(manual),/Obor \(ručně\): Matematika/);
assert.equal(manual.book_classification.subjects[0],"Beletrie");
