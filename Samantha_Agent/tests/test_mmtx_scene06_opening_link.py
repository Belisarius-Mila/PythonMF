from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[2]


class CompletionLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_banner = False
        self.banner_hidden = False
        self.links = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id") == "completeBanner":
            self.in_banner = True
            self.banner_hidden = "hidden" in attrs.get("class", "").split()
        if self.in_banner and tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if self.in_banner and tag == "div":
            self.in_banner = False


class Scene06OpeningLinkTests(unittest.TestCase):
    def test_scene_five_completion_leads_to_the_real_new_scene(self):
        for relative in ("docs", "MatysekANJ/web_mmtx"):
            scene = REPO / relative / "scene05_log_bridge"
            parser = CompletionLinks()
            parser.feed((scene / "index.html").read_text())
            self.assertTrue(parser.banner_hidden)
            self.assertEqual(parser.links, ["../scene06_lake_arrival/index.html"])
            target = (scene / parser.links[0]).resolve()
            self.assertTrue(target.is_file())
            self.assertIn("arrival_side_view_benji_v2.webp", target.read_text())
            # Removed invisible early shortcut stays removed; only completed bridge leads on.
            self.assertNotIn('class="scene-quick-skip"', (scene / "index.html").read_text())

    def test_entry_markup_and_styles_match_in_both_mirrors(self):
        for name in ("index.html", "interaction.css", "script.js"):
            self.assertEqual((REPO / "docs/scene05_log_bridge" / name).read_bytes(),
                             (REPO / "MatysekANJ/web_mmtx/scene05_log_bridge" / name).read_bytes())

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_secret_corner_only_opens_on_finished_final_picture(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const nodes=new Map();
function node(id){
 if(!nodes.has(id)){
  const classes=new Set(id==='dictionaryPanel'?['hidden']:[]);
  nodes.set(id,{hidden:true,disabled:false,dataset:{},style:{},listeners:{},
   classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x),
    toggle(x,on){if(on===undefined)on=!classes.has(x);if(on)classes.add(x);else classes.delete(x);}},
   setAttribute(){},addEventListener(k,f){this.listeners[k]=f;},querySelectorAll(){return[];},
   append(){},appendChild(){},replaceChildren(){}});
 }
 return nodes.get(id);
}
const context=vm.createContext({document:{getElementById:node,querySelectorAll:()=>[],createElement:()=>node(Symbol())},
 localStorage:{getItem:()=>null,setItem(){}},window:{}});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),context);
const run=s=>vm.runInContext(s,context);
assert.equal(node('lakeShortcut').hidden,true);
run(`scene.dataset.sceneState='friends-farewell';state.stage='finish-dialogue';updateControls();`);
assert.equal(node('lakeShortcut').hidden,true);
run(`state.stage='complete';updateControls();`);assert.equal(node('lakeShortcut').hidden,false);
run(`toggleDictionary();`);assert.equal(node('lakeShortcut').hidden,true);
run(`toggleDictionary();`);assert.equal(node('lakeShortcut').hidden,false);
run(`state.isPlaying=true;updateControls();`);assert.equal(node('lakeShortcut').hidden,true);
run(`state.isPlaying=false;state.isAnimating=true;updateControls();`);assert.equal(node('lakeShortcut').hidden,true);
run(`state.isAnimating=false;scene.dataset.sceneState='lamp-rescued';updateControls();`);
assert.equal(node('lakeShortcut').hidden,true);
'''
        scene = REPO / "docs/scene05_log_bridge"
        html = (scene / "index.html").read_text()
        self.assertIn('id="lakeShortcut" href="../scene06_lake_arrival/index.html"', html)
        self.assertIn('aria-label="Pokračovat k jezeru — scéna 6" hidden></a>', html)
        result = subprocess.run([shutil.which("node"), "-e", script, str(scene / "script.js")],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
