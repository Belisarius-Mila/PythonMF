import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { makeDeck, sentenceParts, Playback } from '../web/core.mjs';

const data = JSON.parse(await readFile(new URL('../web/data.json', import.meta.url)));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

class FakeAudio {
  constructor() { this.playCount = 0; this.pauseCount = 0; this.currentTime = 0; this.volume = 1; }
  pause() { this.pauseCount++; }
  play() { this.playCount++; return Promise.resolve(); }
}

test('all 24 visible constructions match the exact statement/question MP3 text', () => {
  for (const row of data.verbs) {
    for (const question of [false, true]) {
      const text = sentenceParts(row, question).map(p => p.text).join(' ').replace(/ ([.?])$/, '$1');
      const field = question ? 'question' : 'statement';
      assert.equal(text, row[field]);
      assert.equal(text, data.audio[row.audio[field]].text);
    }
  }
});

test('question transformations preserve token identity, replace has/goes and retain capital I', () => {
  const be = sentenceParts(data.verbs[0], true);
  assert.deepEqual(be.slice(0, 2), [{ key: 'verb', text: 'Am' }, { key: 'pronoun', text: 'I' }]);
  const have = sentenceParts(data.verbs.find(r => r.verb === 'has'), true);
  assert.equal(have[0].text, 'Does'); assert.equal(have[2].text, 'have');
  const go = sentenceParts(data.verbs.find(r => r.verb === 'goes'), true);
  assert.equal(go[0].text, 'Does'); assert.equal(go[2].text, 'go');
});

test('shuffle visits every item once, leaves source order intact and avoids boundary repeat', () => {
  const items = data.sentences.filter(r => r.lesson === 'have');
  const ids = items.map(r => r.id);
  for (let pass = 0; pass < 40; pass++) {
    const deck = makeDeck(items, true, Math.random, items[0].id);
    assert.notEqual(deck[0].id, items[0].id);
    assert.deepEqual(deck.map(r => r.id).sort(), [...ids].sort());
  }
  assert.deepEqual(items.map(r => r.id), ids);
});

test('stop cancels playing MP3, pending delays and animations', async () => {
  const audio = new FakeAudio(); const player = new Playback(audio);
  const speaking = player.play('one.mp3', player.token);
  const delay = player.wait(5000, player.token);
  let cancelled = 0;
  player.animations.add({ cancel() { cancelled++; } });
  player.stop();
  assert.equal(await speaking, false); assert.equal(await delay, false);
  assert.equal(cancelled, 1); assert.equal(audio.currentTime, 0);
});

test('late rejection from old audio cannot stop or finish a newer MP3', async () => {
  const audio = new FakeAudio(); let rejectOld;
  audio.play = () => new Promise((resolve, reject) => { rejectOld = reject; });
  const player = new Playback(audio); const old = player.play('old.mp3', player.token);
  player.stop(); assert.equal(await old, false);
  audio.play = () => Promise.resolve();
  const newer = player.play('new.mp3', player.token);
  const pauseCount = audio.pauseCount;
  rejectOld(new Error('late old promise rejection'));
  await sleep(0);
  assert.equal(audio.pauseCount, pauseCount);
  assert.equal(typeof audio.onended, 'function');
  audio.onended(); assert.equal(await newer, true);
});

test('pause freezes teaching delay and resumes it without creating a new generation', async () => {
  const player = new Playback(new FakeAudio());
  const token = player.token;
  player.togglePause();
  let done = false; const waiting = player.wait(60, token).then(value => { done = true; return value; });
  await sleep(120); assert.equal(done, false);
  player.togglePause(); assert.equal(await waiting, true);
  assert.equal(player.token, token);
});

test('pause/resume owns the same MP3 and animation', async () => {
  const audio = new FakeAudio(); const player = new Playback(audio);
  let paused = 0; let resumed = 0;
  player.animations.add({ pause() { paused++; }, play() { resumed++; } });
  const speaking = player.play('one.mp3', player.token);
  assert.equal(player.togglePause(), true); assert.equal(audio.pauseCount, 1);
  assert.equal(player.togglePause(), false); assert.equal(audio.playCount, 2);
  assert.equal(paused, 1); assert.equal(resumed, 1);
  audio.onended(); assert.equal(await speaking, true);
});

test('missing or blocked audio reports the error and ends the teaching step', async () => {
  const audio = new FakeAudio(); const messages = [];
  audio.play = () => Promise.reject(new Error('NotAllowedError'));
  const player = new Playback(audio, message => messages.push(message));
  assert.equal(await player.play('missing.mp3', player.token), false);
  assert.equal(messages.length, 1); assert.equal(player.finishAudio, null);
});

test('a stale unlock promise cannot pause a newer sentence', async () => {
  const audio = new FakeAudio(); let unlock;
  audio.play = () => new Promise(resolve => { unlock = resolve; });
  const player = new Playback(audio);
  const priming = player.prime('old.mp3'); player.stop();
  audio.play = () => Promise.resolve();
  const speaking = player.play('new.mp3', player.token);
  const pauseCount = audio.pauseCount; unlock(); await priming;
  assert.equal(audio.pauseCount, pauseCount); assert.equal(audio.volume, 1);
  audio.onended(); assert.equal(await speaking, true);
});
