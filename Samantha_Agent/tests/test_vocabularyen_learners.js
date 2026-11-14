const test=require('node:test');
const assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
const L=require('../../docs/vocabulary-en/learners.js');
function memory(){const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),map};}
test('independent learner lists persist without changing shared items or themes',()=>{
  const storage=memory(),repo=L.store(()=>storage),before=repo.read(),next=L.empty();
  next.profiles.A.selected=['ven-0001','ven-0020'];next.profiles.A.hard=['ven-0020'];next.profiles.B.selected=['ven-0024'];
  repo.write(next,before.raw);const loaded=L.store(()=>storage).read();
  const items=[{uid:'ven-0001',primaryGroup:'topic-04'},{uid:'ven-0020',primaryGroup:'topic-06'},{uid:'ven-0024',primaryGroup:'topic-06'}],original=JSON.stringify(items);
  assert.deepEqual(L.selection(items,loaded.value,'A').map(i=>i.uid),['ven-0001','ven-0020']);
  assert.deepEqual(L.selection(items,loaded.value,'A',true).map(i=>i.uid),['ven-0020']);
  assert.deepEqual(L.selection(items,loaded.value,'B').map(i=>i.uid),['ven-0024']);assert.equal(L.selection(items,loaded.value,'C').length,0);
  assert.equal(L.selection(items,loaded.value,'all'),items);assert.equal(JSON.stringify(items),original);
});
test('PIN has a random salt, verifies correctly and never enters the transferable backup',async()=>{
  const pin=await L.makePin('1234',webcrypto),other=await L.makePin('1234',webcrypto);
  assert.notEqual(pin.salt,other.salt);assert.equal(await L.verifyPin('1234',pin,webcrypto),true);assert.equal(await L.verifyPin('4321',pin,webcrypto),false);
  await assert.rejects(L.makePin('12',webcrypto),/4 až 8/);
  const data=L.empty();data.profiles.A.pin=pin;data.profiles.A.selected=['ven-0001'];
  const text=JSON.stringify(L.backup(data));assert.ok(!text.includes(pin.hash)&&!text.includes(pin.salt)&&!text.includes('1234'));
  assert.deepEqual(L.parseBackup(text).profiles.A,{selected:['ven-0001'],hard:[]});
});
test('bad or oversized backups and invalid hard subsets do not change existing storage',()=>{
  const storage=memory(),repo=L.store(()=>storage),saved=repo.write(L.empty(),null),before=storage.getItem(L.KEY);
  for(const text of ['{','{}','x'.repeat(1000001),JSON.stringify({...L.backup(saved.value),schema:99})])assert.throws(()=>L.parseBackup(text));
  const invalid=L.backup(saved.value);invalid.profiles.A.hard=['ven-0001'];assert.throws(()=>L.parseBackup(JSON.stringify(invalid)),/Obtížná/);
  const malicious=L.backup(saved.value);malicious.profiles.A.selected=['<script>'];assert.throws(()=>L.parseBackup(JSON.stringify(malicious)));
  assert.equal(storage.getItem(L.KEY),before);
});
test('stale tabs and failed storage writes cannot report success or overwrite a newer profile',()=>{
  const storage=memory(),repo=L.store(()=>storage),first=repo.read(),second=repo.read(),a=L.empty();a.profiles.A.selected=['ven-0001'];repo.write(a,first.raw);
  assert.throws(()=>repo.write(L.empty(),second.raw),/jiném okně/);assert.deepEqual(repo.read().value.profiles.A.selected,['ven-0001']);
  const full={getItem:()=>null,setItem:()=>{throw Error('QuotaExceededError');}};assert.throws(()=>L.store(()=>full).write(L.empty(),null),/nepodařilo uložit/);
  assert.throws(()=>L.store(()=>({getItem:()=>null,setItem:()=>{}})).write(L.empty(),null),/nelze potvrdit/);
});
test('corrupt or blocked storage is preserved; unknown valid word IDs survive a backup for later vocabulary versions',()=>{
  const storage=memory();storage.setItem(L.KEY,'corrupt');assert.throws(()=>L.store(()=>storage).read(),/nelze načíst/);assert.equal(storage.getItem(L.KEY),'corrupt');
  assert.throws(()=>L.store(()=>{throw Error('blocked');}).read(),/nelze načíst/);
  const data=L.empty();data.profiles.D.selected=['ven-future-word'];assert.deepEqual(L.parseBackup(JSON.stringify(L.backup(data))).profiles.D.selected,['ven-future-word']);
});
