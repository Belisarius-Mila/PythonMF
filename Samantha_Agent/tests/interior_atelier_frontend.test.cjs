const test = require("node:test");
const assert = require("node:assert/strict");
const {emptyDraft, escape, scopeKey, gate, paths, restoreDraft, pruneDraftSources} = require("../app/frontend/interior/app.js");

test("late server response cannot replace a newer project or variant context", () => {
  const clock = gate();
  const first = clock.begin(), second = clock.begin();
  assert.equal(clock.current(first), false);
  assert.equal(clock.current(second), true);
  clock.begin();
  assert.equal(clock.current(second), false);
});
test("browser draft keys distinguish project, room and variant", () => {
  const base = {project: "A", room: "room", base: "base"};
  assert.notEqual(scopeKey(base), scopeKey({...base, project:"B"}));
  assert.notEqual(scopeKey(base), scopeKey({...base, room:"other"}));
  assert.notEqual(scopeKey(base), scopeKey({...base, base:"variant"}));
});
test("latest saved server revision wins over clean browser snapshots", () => {
  const result = restoreDraft({...emptyDraft(), prompt:"New server", revision:5},
    {draft:{...emptyDraft(),prompt:"Old browser"},revision:1,dirty:false});
  assert.equal(result.draft.prompt,"New server");
  assert.equal(result.revision,5);
});
test("unfinished browser edits survive reload without upgrading their expected revision", () => {
  const draft = {...emptyDraft(),prompt:"My unfinished edit"};
  const result = restoreDraft({...emptyDraft(),revision:2},{draft,revision:2,dirty:true});
  assert.equal(result.draft.prompt,"My unfinished edit");
  assert.equal(result.dirty,true);
  assert.equal(result.conflict,false);
});
test("newer server draft does not get silently overwritten by recovered stale edits", () => {
  const result = restoreDraft({...emptyDraft(),prompt:"Remote change",revision:6},
    {draft:{...emptyDraft(),prompt:"Local change"},revision:2,dirty:true});
  assert.equal(result.conflict,true);
  assert.equal(result.revision,2,"Must send the original expectation, making the server reject a stale save");
  assert.equal(result.draft.prompt,"Local change");
});
test("malformed browser cache falls back to the server", () => {
  const result = restoreDraft({...emptyDraft(),revision:4},{draft:{prompt:null},dirty:true,revision:1});
  assert.equal(result.revision,4);
  assert.equal(result.dirty,false);
});
test("deleted source cannot return from an unfinished browser draft, while its text survives", () => {
  const cached = {draft:{...emptyDraft(),prompt:"My unfinished text",source_ids:["deleted","kept"],
    image_source_id:"deleted",annotations:[[[0,0],[1,1]]]},revision:2,dirty:true};
  const result = restoreDraft({...emptyDraft(),revision:3},cached,{kept:{}});
  assert.deepEqual(result.draft.source_ids,["kept"]);
  assert.equal(result.draft.image_source_id,"");
  assert.deepEqual(result.draft.annotations,[]);
  assert.equal(result.draft.prompt,"My unfinished text");
  assert.equal(result.conflict,true);
  assert.equal(cached.draft.image_source_id,"deleted","Do not mutate another cached snapshot");
});
test("removing a reference preserves the drawing over a different working image", () => {
  const drawing=[[[0,0],[1,1]]];
  const result=pruneDraftSources({...emptyDraft(),source_ids:["old","working"],image_source_id:"working",annotations:drawing},{working:{}});
  assert.deepEqual(result.source_ids,["working"]);
  assert.deepEqual(result.annotations,drawing);
});
test("private titles, prompts and filenames render as text", () => {
  const result = escape('<img src=x onerror="evil()"> & \'test\'');
  assert(!result.includes("<img"));
  assert(result.includes("&lt;img"));
  assert(result.includes("&quot;evil()&quot;"));
});
test("normalized drawing survives image resizing and rejects markup injection", () => {
  assert.equal(paths([[[0,0],[0.5,1]]]),'<path d="M0 0 L500 1000"/>');
  assert.equal(paths([[['0" onload="evil()',0],[1,1]]]),"");
  assert.equal(paths([[[0,0],[Infinity,1]]]),"");
  assert.equal(paths([[[0,0],[2,1]]]),"");
});
