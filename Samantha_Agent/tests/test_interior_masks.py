from __future__ import annotations

import copy
import hashlib
import io
import json
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

from app import cockpit
from app.interior_masks import MODES, SIZE, composite, png, rasterize, sample_image
from app.interior_mask_store import InteriorMaskStore, MaskConflict, interior_mask_action


def layer(mode="EDITABLE", points=None):
    return {"id":uuid.uuid4().hex, "name":"Povrch", "mode":mode, "visible":True, "strokes":[
        {"tool":"rect","erase":False,"width":10,"points":points or [[10,10],[50,50]]}]}


class MaskTests(unittest.TestCase):
    def test_priority_all_modes_and_hidden_protection(self):
        for mode in ("PIXEL_LOCK","CONTEXT_ONLY","GEOMETRY_LOCK"):
            protection=layer(mode)
            protection["visible"]=False
            for edit in ("EDITABLE","FREE_DESIGN"):
                mask, conflict, _=rasterize([layer(edit),protection],(64,64))
                self.assertEqual(mask.getbbox(),None)
                self.assertIsNotNone(conflict.getbbox())
                other,_,_=rasterize([protection,layer(edit)],(64,64))
                self.assertEqual(mask.tobytes(),other.tobytes())

    def test_default_protected_feather_roundtrip_rgb_and_alpha(self):
        for mode in ("RGB","RGBA"):
            color=(20,30,40,23) if mode=="RGBA" else (20,30,40)
            base=png(Image.new(mode,(64,64),color))
            candidate=png(Image.new(mode,(64,64),"red"))
            for feather in (0,5,20):
                output,report=composite(base,candidate,[layer()],feather)
                self.assertEqual(report["protected_changed_pixels"],0)
                self.assertEqual(report["geometry"],"unverified")
                with Image.open(io.BytesIO(output)) as decoded:
                    self.assertEqual(decoded.getpixel((0,0)),color)
                    self.assertNotEqual(decoded.getpixel((25,25)),color)
            output,_=composite(base,candidate,[])
            with Image.open(io.BytesIO(output)) as decoded:
                self.assertEqual(decoded.tobytes(),Image.new(mode,(64,64),color).tobytes())

    def test_size_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            composite(sample_image(),png(Image.new("RGB",(600,400))),[])

    def test_polygon_brush_and_erase_are_native_and_ordered(self):
        item=layer()
        item["strokes"]=[
            {"tool":"polygon","erase":False,"width":1,"points":[[5,5],[60,5],[60,60],[5,60]]},
            {"tool":"brush","erase":True,"width":10,"points":[[20,20],[40,20]]}]
        mask,_,_=rasterize([item],(64,64))
        self.assertEqual(mask.getpixel((30,20)),0)
        self.assertEqual(mask.getpixel((30,40)),255)
        item["strokes"].append({"tool":"brush","erase":False,"width":2,"points":[[30,20]]})
        self.assertEqual(rasterize([item],(64,64))[0].getpixel((30,20)),255)

    def test_invalid_coordinates_and_versions(self):
        for value in (-1,float("nan"),True,64):
            item=layer(points=[[value,5],[20,20]])
            with self.assertRaises(ValueError):
                rasterize([item],(64,64))
        item=layer();item["mode"]="unknown"
        with self.assertRaises(ValueError):
            rasterize([item],(64,64))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"private"/"pilot.sqlite3"
        self.store=InteriorMaskStore(self.path)

    def payload(self,**values):
        return {"action":"save","request_id":uuid.uuid4().hex,"expected_revision":0,
                "base_sha256":hashlib.sha256(sample_image()).hexdigest(),"layers":[layer()],
                "title":"Nová varianta","color":"#128045","feather":3,**values}

    def test_reads_do_not_create_files(self):
        self.assertEqual(self.store.state()["revision"],0)
        self.assertTrue(self.store.image())
        self.assertFalse(self.path.parent.exists())

    def test_save_reopen_variant_and_replay(self):
        payload=self.payload(action="variant")
        result=self.store.execute(payload)
        self.assertEqual(self.store.execute(payload),result)
        reopened=InteriorMaskStore(self.path)
        self.assertEqual(reopened.state()["layers"],payload["layers"])
        self.assertEqual(len(reopened.state()["variants"]),1)
        raw=reopened.image(str(result["variant_id"]))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result["report"]["result_sha256"])
        self.assertEqual(reopened.state()["revision"],1)

    def test_stored_original_survives_sample_renderer_change(self):
        original=self.store.image()
        self.store.execute(self.payload())
        with patch("app.interior_mask_store.sample_image",return_value=b"changed-renderer"):
            self.assertEqual(self.store.image(),original)
            self.assertEqual(self.store.state()["base_sha256"],hashlib.sha256(original).hexdigest())

    def test_stale_revision_and_changed_operation_conflict(self):
        payload=self.payload();self.store.execute(payload)
        for other in (self.payload(),{**payload,"title":"Jiné"}):
            with self.assertRaises(MaskConflict):
                self.store.execute(other)
        self.assertEqual(self.store.state()["revision"],1)

    def test_parallel_save_has_single_winner(self):
        def save(_):
            return interior_mask_action(self.payload(),store=self.store)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(save,range(2)))
        self.assertEqual(sum(x["ok"] for x in outcomes),1)
        self.assertEqual(self.store.state()["revision"],1)

    def test_conflict_copy_preserves_server_draft(self):
        server=self.payload()
        self.store.execute(server)
        copy_payload=self.payload(action="copy",expected_revision=1,layers=[layer("PIXEL_LOCK")])
        result=self.store.execute(copy_payload)
        self.assertEqual(self.store.state()["layers"],server["layers"])
        self.assertEqual(self.store.state()["revision"],2)
        self.assertIn("variant_id",result)
        self.assertEqual(self.store.execute(copy_payload),result)

    def test_failure_mid_operation_rolls_back_draft_and_variant(self):
        self.store.execute(self.payload())
        with patch("app.interior_mask_store.composite",side_effect=ValueError("failure")):
            result=interior_mask_action(self.payload(action="variant",expected_revision=1),store=self.store)
        self.assertFalse(result["ok"])
        self.assertEqual(self.store.state()["revision"],1)
        self.assertEqual(self.store.state()["variants"],[])

    def test_wrong_base_unknown_adapter_and_malformed_payload_never_write(self):
        for payload in (self.payload(base_sha256="bad"),self.payload(action="paid"),self.payload(feather=True),
                        self.payload(color=[]),{**self.payload(),"provider":"remote"}):
            self.assertFalse(interior_mask_action(payload,store=self.store)["ok"])
        self.assertFalse(self.path.exists())


class MaskHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=InteriorMaskStore(Path(self.temp.name)/"mask.sqlite3")
        patcher=patch("app.cockpit_interior.InteriorMaskStore",return_value=self.store)
        patcher.start();self.addCleanup(patcher.stop)
        action_patcher=patch("app.cockpit.interior_mask_action",side_effect=lambda data:interior_mask_action(data,store=self.store))
        action_patcher.start();self.addCleanup(action_patcher.stop)
        self.server=ThreadingHTTPServer(("127.0.0.1",0),cockpit.CockpitServer().make_handler())
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        def shutdown():
            self.server.shutdown();self.server.server_close();thread.join()
        self.addCleanup(shutdown)
        self.base=f"http://127.0.0.1:{self.server.server_port}"

    def request(self,path,payload=None,origin=None):
        headers={"Origin":origin or self.base,"Content-Type":"application/json"}
        data=None if payload is None else json.dumps(payload).encode()
        try: response=urlopen(Request(self.base+path,data=data,headers=headers),timeout=5)
        except HTTPError as error: response=error
        with response:return response.status,response.read()

    def test_registered_page_read_save_and_image_roundtrip(self):
        code,raw=self.request("/interior/masks/")
        self.assertEqual(code,200)
        self.assertIn("Zkušební místnost",raw.decode())
        self.assertNotIn("{{SAMANTHA",raw.decode())
        self.assertFalse(self.store.path.exists())
        code,raw=self.request("/api/interior/masks/state")
        state=json.loads(raw)
        payload={"action":"variant","request_id":uuid.uuid4().hex,"expected_revision":0,"base_sha256":state["base_sha256"],
                 "layers":[layer()],"title":"Povrch","color":"#123456","feather":5}
        code,raw=self.request("/api/interior/masks/action",payload)
        self.assertEqual(code,200,raw)
        result=json.loads(raw)
        code,raw=self.request("/api/interior/masks/image?variant="+str(result["variant_id"]))
        self.assertEqual(code,200)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result["report"]["result_sha256"])
        self.assertEqual(self.request("/api/interior/masks/action",{**payload,"request_id":uuid.uuid4().hex})[0],409)

    def test_origin_and_query_guards(self):
        self.assertEqual(self.request("/api/interior/masks/action",{},origin="https://invalid.example")[0],403)
        for path in ("/api/interior/masks/state?variant=1","/api/interior/masks/image?variant=1&variant=2",
                     "/api/interior/masks/image?variant=../","/interior/masks/?other=1"):
            self.assertEqual(self.request(path)[0],400)
        self.assertFalse(self.store.path.exists())
