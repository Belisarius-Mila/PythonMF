"""Exercise the scene's actual browser state machine with a controlled DOM and audio."""
import asyncio
import importlib.util
import json
import subprocess
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / 'docs/scene06_lake_arrival'
MIRROR = ROOT / 'MatysekANJ/web_mmtx/scene06_lake_arrival'

class Scene06Tests(unittest.TestCase):
    def test_state_machine_and_audio_cancellation(self):
        harness = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const root=process.argv[1]; let played=[],hold=false, active=null;
class Classes{constructor(){this.s=new Set()}toggle(c,yes){if(yes)this.s.add(c);else this.s.delete(c)}contains(c){return this.s.has(c)}}
class Element{constructor(id){this.id=id;this.classList=new Classes();this.style={};this.attrs={};this.listeners={};this.children=[];this.disabled=false}setAttribute(k,v){this.attrs[k]=v}addEventListener(k,v){this.listeners[k]=v}appendChild(n){this.children.push(n)}click(){if(!this.disabled&&this.listeners.click)this.listeners.click()} }
const ids=['picture','back','language','repeat','speech','speaker','en','cz','notes','hotspot','next','song','gate'];const e=Object.fromEntries(ids.map(x=>[x,new Element(x)]));
const events={}, winEvents={};const document={hidden:false,getElementById:id=>e[id],createElement:()=>new Element('new'),addEventListener:(k,v)=>events[k]=v};
class Audio{constructor(path){this.path=path;this.listeners={};active=this}addEventListener(k,v){this.listeners[k]=v}play(){played.push(this.path);if(!hold)queueMicrotask(()=>this.listeners.ended());return Promise.resolve()}pause(){this.paused=true}}
const paths=Object.fromEntries(Array.from({length:100},(_,i)=>[String(i).padStart(3,'0'),'audio/en/'+String(i).padStart(3,'0')+'.mp3']));const window={SCENE06_AUDIO:{en:paths,cs:paths},SCENE06_STORY:JSON.parse(fs.readFileSync(root+'/story.json')),addEventListener:(k,v)=>winEvents[k]=v};
const c={window,document,Audio,localStorage:{getItem:()=>null,setItem(){}},setTimeout:(f,t)=>{if(t<1000)queueMicrotask(f);return 1},clearTimeout:()=>{},console};vm.runInNewContext(fs.readFileSync(root+'/script.js','utf8'),c);
const flush=()=>new Promise(r=>setImmediate(r));
(async()=>{
 assert(e.gate.listeners.click);assert(!e.back.disabled);assert(e.next.classList.contains('hidden'));
 e.gate.click();await flush();assert.equal(played.length,2);assert.equal(e.en.textContent,'Bye, Logan!');
 e.repeat.click();await flush();assert.equal(played.length,4);assert.equal(e.en.textContent,'Bye, Logan!');
 e.language.click();assert.equal(e.language.textContent,'EN');e.repeat.click();await flush();assert.equal(played.length,5);
 e.language.click();let count=0;
 while(e.en.textContent!=='Tap the light!'){e.next.click();await flush();if(++count>10)throw Error('light never reached')}
 assert(e.next.classList.contains('hidden'));let before=played.length;e.next.click();await flush();assert.equal(played.length,before);
 e.hotspot.click();await flush();await flush();assert.equal(e.en.textContent,'Look! My ears!');
 while(!e.song.classList.contains('hidden')===false && count<200){
   if(e.hotspot.classList.contains('hidden'))e.next.click();else e.hotspot.click();
   await flush();await flush();count++;
 }
 assert(count<200,'scene did not finish');assert.equal(e.notes.children.length,4);assert.equal(e.en.textContent,'See you!');assert(!e.song.classList.contains('hidden'));e.song.click();await flush();assert(!e.song.disabled);
 // Reinitialize and interrupt an English audio before it finishes; Czech must not start.
 const x=Object.fromEntries(ids.map(id=>[id,new Element(id)]));document.getElementById=id=>x[id];hold=true;played=[];vm.runInNewContext(fs.readFileSync(root+'/script.js','utf8'),c);x.gate.click();await flush();assert.equal(played.length,1);document.hidden=true;events.visibilitychange();await flush();assert.equal(played.length,1);assert(active.paused);assert(!x.repeat.disabled);
 document.hidden=false;x.repeat.click();await flush();active.listeners.error();await flush();active.listeners.error();await flush();assert(!x.repeat.disabled);assert(!x.next.disabled);
 console.log('state, interaction, EN/CZ, repeat, finish and interruption OK');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        result = subprocess.run(['node','-e',harness,str(SCENE)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)



    def test_audio_builder_prepares_directory_and_rejects_stale_input_offline(self):
        spec=importlib.util.spec_from_file_location('scene06_builder', ROOT/'MatysekANJ/build_scene06_audio.py')
        builder=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        row=['bunny','Bye, Logan!','Ahoj, Logane!','farewell']
        root=MagicMock();audio=root.__truediv__.return_value;lang=audio.__truediv__.return_value;path=lang.__truediv__.return_value
        path.is_file.return_value=False
        synth=AsyncMock(side_effect=RuntimeError('offline test'))
        with patch.object(builder,'ROOT',root):
            with self.assertRaisesRegex(RuntimeError,'zastaveno bez opakování'):
                asyncio.run(builder.generate_one(0,'en',row,{},'ffmpeg',synth=synth))
        path.parent.mkdir.assert_called_once_with(parents=True,exist_ok=True)
        synth.assert_awaited_once()
        path.is_file.return_value=True;path.read_bytes.return_value=b'existing'
        synth.reset_mock()
        wrong=builder.expected(row,'en',b'existing');wrong['text']='Different text'
        with patch.object(builder,'ROOT',root):
            with self.assertRaisesRegex(RuntimeError,'původní soubor zachován'):
                asyncio.run(builder.generate_one(0,'en',row,{'en/000':wrong},'ffmpeg',synth=synth))
        synth.assert_not_awaited()
        path.open.assert_not_called()

    def test_touch_geometry_at_phone_widths(self):
        # Conservative bounds for the image, HUD and speech bubble. A real
        # browser layout remains a separate manual check.
        spots = {"light": (70,35,18,20), "daisy": (42,47,19,36),
                 "drum": (69,68,19,28), "dotty": (8,26,22,25),
                 "shells": (55,53,12,20), "song": (28,70,40,18)}
        css = (SCENE/'styles.css').read_text()
        script = (SCENE/'script.js').read_text()
        self.assertNotIn('min-height:36px',css)
        for name, rect in spots.items():
            self.assertIn(name + ':[' + ','.join(map(str,rect)) + ',',script)
        for width in (390,844):
            height = width * 9 / 16
            for name,(x,y,w,h) in spots.items():
                target=(width*x/100,height*y/100,max(44,width*w/100),max(44,height*h/100))
                bubble=(width*(.55 if name=='dotty' else .03),height*.15,width*.42,60)
                def intersects(a,b):
                    return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
                self.assertFalse(intersects(target,bubble),f'{width} {name} bubble')
                self.assertGreaterEqual(target[1],48,f'{width} {name} HUD')
                self.assertGreaterEqual(target[2],44)
                self.assertGreaterEqual(target[3],44)

    def test_mirror_and_navigation(self):
        docs = {p.relative_to(SCENE):p.read_bytes() for p in SCENE.rglob('*') if p.is_file()}
        mirror = {p.relative_to(MIRROR):p.read_bytes() for p in MIRROR.rglob('*') if p.is_file()}
        self.assertEqual(docs,mirror)
        for base in (ROOT/'docs',ROOT/'MatysekANJ/web_mmtx'):
            html=(base/'scene05_log_bridge/index.html').read_text()
            self.assertIn('id="completeBanner" href="../scene06_lake_arrival/index.html"',html)
            self.assertIn('href="../scene05_log_bridge/index.html"', (base/'scene06_lake_arrival/index.html').read_text())
        story=json.loads((SCENE/'story.json').read_text())
        self.assertEqual([x[4] for x in story if len(x)>4],['light','daisy','drum','dotty','shells','song'])

if __name__=='__main__': unittest.main()
