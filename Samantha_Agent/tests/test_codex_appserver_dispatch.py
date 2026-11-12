from __future__ import annotations

import json
import queue
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from app.codex_appserver import (
    CodexAppServerClient, CodexVersion, StdioAppServerTransport, UnixSocketAppServerTransport,
    AppServerError, AppServerContractError, AppServerTimeout,
)
from app.codex_appserver_dispatch import (
    AppServerDispatcher, AppServerClosedError, AppServerOverflowError,
)
from scripts.codex_sdk_socket_fixture import SyntheticSocket


def event(method, **params):
    return {"method": method, "params": params}


def turn_event(method="turn/started", thread="thread-a", turn="turn-a", **changes):
    return event(method, threadId=thread, turn={"id": turn, **changes})


def usage(**changes):
    return dict(inputTokens=10, cachedInputTokens=2, outputTokens=4, reasoningOutputTokens=1, totalTokens=14) | changes


class MemoryTransport(StdioAppServerTransport):
    """Real request/receive dispatcher, only the wire is synthetic."""
    def __init__(self, on_send=None, timeout=.3):
        self._init_dispatcher(timeout=timeout)
        self.writes = []
        self.on_send = on_send

    @property
    def running(self):
        return self._dispatcher.running

    @property
    def process_id(self):
        return 0

    def _send(self, message):
        with self._send_lock:
            if not self.running:
                raise AppServerClosedError("synthetic wire closed")
            self.writes.append(deepcopy(message))
        if self.on_send:
            self.on_send(message)

    def feed(self, message):
        return self._dispatcher.feed(message, generation=self._dispatcher.generation)

    def close(self):
        self._dispatcher.close()


class DispatcherTests(unittest.TestCase):
    def make(self, **limits):
        dispatcher = AppServerDispatcher(**limits)
        self.addCleanup(dispatcher.close)
        return dispatcher

    def feed(self, dispatcher, message):
        return dispatcher.feed(message, generation=dispatcher.generation)

    def test_concurrent_rpc_out_of_order_events_are_never_stolen(self):
        transport = MemoryTransport(timeout=1)
        self.addCleanup(transport.close)
        both_written = threading.Barrier(3)
        transport.on_send = lambda _message: both_written.wait(timeout=1)
        sub = transport.subscribe(thread_id="thread-a")
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(transport.request, "config/read", {})
            second = pool.submit(transport.request, "model/list", {})
            both_written.wait(timeout=1)
            transport.feed(turn_event())
            for message in reversed(transport.writes):
                transport.feed({"id": message["id"], "result": {"owner": message["method"]}})
            self.assertEqual(first.result(1), {"owner": "config/read"})
            self.assertEqual(second.result(1), {"owner": "model/list"})
        self.assertEqual(sub.get(timeout=.1).kind, "turn_started")
        self.assertEqual(transport.receive(lambda m: m["method"] == "turn/started", description="proof")["params"]["turn"]["id"], "turn-a")
        self.assertEqual(transport.diagnostics()["pending_rpc"], 0)

    def test_plan_before_ack_is_resolved_only_by_exact_binding(self):
        d = self.make()
        current = d.subscribe(thread_id="thread-a", turn_id="turn-a", methods=("turn/plan/updated",))
        other = d.subscribe(thread_id="thread-b")
        self.feed(d, event("turn/plan/updated", turnId="turn-a", plan=[{"step":"Syntetický krok", "status":"inProgress"}]))
        with self.assertRaises(AppServerTimeout): current.get(timeout=.01)
        d.register(1, "turn/start", {"threadId":"thread-a", "input":[{"text":"PRIVATE"}]})
        self.feed(d, {"id":1,"result":{"turn":{"id":"turn-a"}}})
        self.assertEqual(d.wait(1, timeout=.1)["result"]["turn"]["id"], "turn-a")
        plan = current.get(timeout=.1)
        self.assertEqual((plan.kind,plan.thread_id,plan.turn_id), ("plan","thread-a","turn-a"))
        self.assertEqual(plan.compatibility, "compatible_turn_only")
        self.assertNotIn("threadId",plan.params, "scope metadata must not rewrite the original wire payload")
        with self.assertRaises(AppServerTimeout): other.get(timeout=.01)
        self.assertNotIn("PRIVATE", json.dumps(d.diagnostics()))

    def test_thread_only_usage_is_not_attributed_to_an_arbitrary_turn(self):
        d = self.make()
        whole_thread = d.subscribe(thread_id="thread-a", methods=("thread/tokenUsage/updated",))
        turn = d.subscribe(thread_id="thread-a", turn_id="turn-a")
        self.feed(d,event("thread/tokenUsage/updated",threadId="thread-a",tokenUsage={"total":usage()}))
        observation=whole_thread.get(timeout=.1)
        self.assertEqual(observation.kind,"thread_usage")
        self.assertIsNone(observation.turn_id)
        with self.assertRaises(AppServerTimeout): turn.get(timeout=.01)
        with self.assertRaises(AppServerTimeout): d.receive(lambda _m:True, timeout=.01)

    def test_explicit_scopes_foreign_turns_and_generation_do_not_cross(self):
        d = self.make()
        sub = d.subscribe(thread_id="thread-a",turn_id="turn-a")
        self.feed(d,turn_event(thread="foreign",turn="foreign-turn"))
        self.feed(d,turn_event(turn="other-turn"))
        d.feed(turn_event(),generation="previous-connection")
        self.assertEqual(d.diagnostics()["counters"]["stale_generations"],1)
        with self.assertRaises(AppServerTimeout): sub.get(timeout=.01)
        self.feed(d,turn_event())
        self.assertEqual(sub.get(timeout=.1).turn_id,"turn-a")
        fresh = self.make()
        self.assertNotEqual(fresh.generation,d.generation)
        fresh_sub=fresh.subscribe(thread_id="thread-a")
        fresh.feed(turn_event(),generation=d.generation)
        with self.assertRaises(AppServerTimeout):fresh_sub.get(timeout=.01)

    def test_slow_callback_never_blocks_rpc_and_overflow_is_local(self):
        d=self.make()
        entered,release=threading.Event(),threading.Event()
        seen=[]
        def callback(value):
            entered.set(); release.wait(1); seen.append(value.sequence)
        sub=d.subscribe(thread_id="thread-a",max_events=1,callback=callback)
        self.addCleanup(release.set)
        self.feed(d,turn_event())
        self.assertTrue(entered.wait(1))
        self.feed(d,turn_event(turn="turn-b"))
        self.feed(d,turn_event(turn="turn-c"))
        self.assertTrue(sub.diagnostics()["closed"])
        d.register(1,"config/read",{})
        self.feed(d,{"id":1,"result":{"ok":True}})
        self.assertTrue(d.wait(1,timeout=.1)["result"]["ok"])
        with self.assertRaises(AppServerOverflowError): sub.get(timeout=.01)
        release.set(); sub._worker.join(1)
        self.assertFalse(sub._worker.is_alive())
        self.assertEqual(len(seen),1)
        self.assertTrue(d.running)

    def test_callback_can_issue_rpc_without_reader_deadlock(self):
        t=MemoryTransport()
        self.addCleanup(t.close)
        t.on_send=lambda m:t.feed({"id":m["id"],"result":{"answer":42}})
        done=threading.Event(); answers=[]
        def callback(_event):
            answers.append(t.request("config/read",{})["answer"]);done.set()
        sub=t.subscribe(thread_id="thread-a",callback=callback)
        t.feed(turn_event())
        self.assertTrue(done.wait(1));self.assertEqual(answers,[42])
        sub.close();sub._worker.join(1)
        self.assertFalse(sub._worker.is_alive())

    def test_callback_exception_does_not_leak_or_close_connection(self):
        d=self.make();done=threading.Event()
        def callback(_event):
            done.set();raise ValueError("PRIVATE_CALLBACK")
        sub=d.subscribe(callback=callback)
        self.feed(d,turn_event());self.assertTrue(done.wait(1));sub._worker.join(1)
        self.assertTrue(d.running);self.assertTrue(sub.diagnostics()["closed"])
        self.assertEqual(d.diagnostics()["counters"]["callback_failures"],1)
        self.assertNotIn("PRIVATE",json.dumps(d.diagnostics()))

    def test_close_wakes_all_rpc_and_event_waiters_immediately(self):
        d=self.make();subs=[d.subscribe() for _ in range(2)]
        d.register(1,"config/read",{});d.register(2,"model/list",{})
        with ThreadPoolExecutor(4) as pool:
            futures=[pool.submit(d.wait,n,timeout=20) for n in (1,2)]
            futures += [pool.submit(s.get,timeout=20) for s in subs]
            d.close()
            for f in futures:
                with self.assertRaises(AppServerClosedError): f.result(1)
        self.assertEqual(d.diagnostics()["pending_rpc"],0)
        self.assertEqual(d.diagnostics()["subscriptions"],0)

    def test_queued_evidence_drains_on_eof_but_public_callbacks_do_not(self):
        d=self.make();sub=d.subscribe()
        d.register(1,"config/read",{})
        self.feed(d,{"id":1,"result":{"ok":True}});self.feed(d,turn_event())
        d.close(reason="eof")
        self.assertEqual(d.wait(1,timeout=.1)["result"],{"ok":True})
        self.assertEqual(d.receive(lambda _m:True,timeout=.1)["method"],"turn/started")
        with self.assertRaises(AppServerClosedError):sub.get(timeout=.1)
        with self.assertRaises(AppServerClosedError):d.receive(lambda _m:True,timeout=.1)

    def test_limits_pending_subscriptions_bytes_core_and_unresolved(self):
        d=self.make(max_pending=1,max_subscriptions=1,max_events=1)
        d.register(1,"config/read",{})
        with self.assertRaises(AppServerOverflowError):d.register(2,"model/list",{})
        d.subscribe()
        with self.assertRaises(AppServerOverflowError):d.subscribe()
        self.feed(d,turn_event());self.assertFalse(self.feed(d,turn_event(turn="turn-b")))
        with self.assertRaises(AppServerOverflowError):d.wait(1,timeout=.1)
        self.assertEqual(d.diagnostics()["legacy"]["bytes"],0)
        b=self.make(max_bytes=10);b.register(1,"config/read",{})
        self.assertFalse(self.feed(b,{"id":1,"result":{"value":"x"*100}}))
        with self.assertRaises(AppServerOverflowError):b.wait(1,timeout=.1)
        u=self.make(max_unresolved=1)
        self.feed(u,event("turn/plan/updated",turnId="unbound",plan=[]))
        self.assertFalse(self.feed(u,event("turn/plan/updated",turnId="other-unbound",plan=[])))
        self.assertEqual(u.diagnostics()["unresolved"],0)

    def test_binding_limit_retires_completed_not_active_turns(self):
        d=self.make(max_bindings=1)
        self.feed(d,turn_event("turn/completed",status="completed"))
        self.assertTrue(self.feed(d,turn_event(turn="turn-b")))
        self.assertEqual(d.diagnostics()["bindings"],1)
        self.assertFalse(self.feed(d,turn_event(turn="turn-c")))
        self.assertFalse(d.running)

    def test_streaming_deltas_do_not_accumulate_in_legacy_receipt_queue(self):
        d=self.make(max_events=1)
        for _ in range(1000):
            self.assertTrue(self.feed(d,event("item/agentMessage/delta",threadId="thread-a",turnId="turn-a",itemId="agent-a",delta="synthetic")))
        self.assertEqual(d.diagnostics()["legacy"]["queued"],0)
        self.assertTrue(self.feed(d,turn_event()))

    def test_latest_usage_coalesces_only_the_legacy_queue(self):
        d=self.make(max_events=1);sub=d.subscribe(methods=("thread/tokenUsage/updated",))
        for i in (10,20):
            self.feed(d,event("thread/tokenUsage/updated",threadId="thread-a",turnId="turn-a",tokenUsage={"total":usage(inputTokens=i,totalTokens=i+4)}))
        self.assertEqual(d.diagnostics()["legacy"]["queued"],1)
        self.assertEqual(d.receive(lambda _m:True,timeout=.1)["params"]["tokenUsage"]["total"]["inputTokens"],20)
        self.assertEqual(sub.get(timeout=.1).params["tokenUsage"]["total"]["inputTokens"],10)
        self.assertEqual(sub.get(timeout=.1).params["tokenUsage"]["total"]["inputTokens"],20)

    def test_consumer_and_predicate_cannot_mutate_other_receivers(self):
        d=self.make();one=d.subscribe();two=d.subscribe()
        original=turn_event();self.feed(d,original)
        a=one.get(timeout=.1);a._message["params"]["PRIVATE"]="changed"
        self.assertNotIn("PRIVATE",two.get(timeout=.1).params)
        def predicate(message):
            message["params"]["PRIVATE"]="changed";return True
        self.assertNotIn("PRIVATE",d.receive(predicate,timeout=.1)["params"])
        self.assertNotIn("thread-a",repr(a));self.assertNotIn("PRIVATE",repr(a))

    def test_slow_legacy_predicate_does_not_hold_the_dispatch_lock(self):
        d=self.make();self.feed(d,turn_event())
        entered,release=threading.Event(),threading.Event()
        def predicate(_message):
            entered.set();release.wait(1);return True
        with ThreadPoolExecutor(1) as pool:
            waiting=pool.submit(d.receive,predicate,timeout=2)
            self.assertTrue(entered.wait(1))
            d.register(1,"config/read",{});self.feed(d,{"id":1,"result":{"ok":True}})
            self.assertTrue(d.wait(1,timeout=.1)["result"]["ok"])
            release.set();waiting.result(1)

    def test_malformed_notifications_quarantine_unknown_is_opt_in(self):
        d=self.make();normal=d.subscribe();debug=d.subscribe(include_unknown=True)
        bad=[event("turn/plan/updated",turnId="turn-a",plan=[{"step":"x","status":"wrong"}]),
             event("item/agentMessage/delta",threadId="thread-a",turnId="turn-a",itemId="x",delta={})]
        for value in bad:self.assertTrue(self.feed(d,value))
        self.feed(d,event("future/method",threadId="thread-a",turnId="untrusted",value="PRIVATE"))
        with self.assertRaises(AppServerTimeout):normal.get(timeout=.01)
        observation=debug.get(timeout=.1)
        self.assertEqual(observation.kind,"unknown")
        self.assertEqual(d.diagnostics()["bindings"],0)
        self.assertEqual(d.diagnostics()["counters"]["invalid_notifications"],len(bad))
        self.assertNotIn("PRIVATE",json.dumps(d.diagnostics()))

    def test_server_requests_and_ambiguous_envelopes_never_authorize_actions(self):
        for value in [dict(id=True,result={}),dict(id=1,result={},error={}),[],
                      dict(id=1,error="PRIVATE"),dict(id=1,method="item/commandExecution/requestApproval",params={"command":"PRIVATE"})]:
            d=self.make();d.register(1,"turn/start",{"threadId":"thread-a"})
            self.assertFalse(self.feed(d,value))
            with self.assertRaises(AppServerContractError) as raised:d.wait(1,timeout=.1)
            self.assertNotIn("PRIVATE",str(raised.exception));self.assertNotIn("PRIVATE",repr(raised.exception))

    def test_conflicting_binding_or_response_is_not_accepted(self):
        d=self.make();self.feed(d,turn_event())
        self.assertFalse(self.feed(d,turn_event(thread="different")))
        r=self.make();r.register(1,"config/read",{})
        self.feed(r,{"id":1,"result":{"x":1}});self.feed(r,{"id":1,"result":{"x":1}})
        self.assertFalse(self.feed(r,{"id":1,"result":{"x":2}}))
        with self.assertRaises(AppServerContractError):r.wait(1,timeout=.1)

    def test_timeout_and_late_rpc_do_not_attach_to_next_request(self):
        d=self.make();d.register(1,"turn/start",{"threadId":"thread-a"})
        with self.assertRaises(AppServerTimeout):d.wait(1,timeout=.01)
        d.register(2,"config/read",{})
        self.feed(d,{"id":1,"result":{"turn":{"id":"late-turn"}}})
        self.feed(d,{"id":2,"result":{"ok":True}})
        self.assertEqual(d.wait(2,timeout=.1)["result"],{"ok":True})
        self.assertEqual(d.diagnostics()["bindings"],0)
        self.assertEqual(d.diagnostics()["counters"]["orphan_responses"],1)

    def test_nonpositive_limits_and_invalid_subscription_fail_before_use(self):
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):AppServerDispatcher(max_events=value)
        d=self.make()
        for kwargs in ({"methods":[]},{"methods":("bad\nmethod",)},{"thread_id":""},{"max_bytes":0},{"callback":3}):
            with self.assertRaises(ValueError):d.subscribe(**kwargs)

    def test_closed_blocked_callbacks_still_count_toward_worker_limit(self):
        d=self.make(max_subscriptions=1)
        entered,release=threading.Event(),threading.Event()
        def callback(_event):entered.set();release.wait(1)
        sub=d.subscribe(callback=callback);self.feed(d,turn_event())
        self.assertTrue(entered.wait(1));self.addCleanup(release.set);sub.close()
        with self.assertRaises(AppServerOverflowError):d.subscribe(callback=callback)
        self.assertEqual(d.diagnostics()['callback_workers'],1)
        release.set();sub._worker.join(1)
        self.assertEqual(d.diagnostics()['callback_workers'],0)
        next_sub=d.subscribe();next_sub.close()

    def test_subscription_budgets_and_failed_worker_reservation_are_released(self):
        d=self.make();large=d.subscribe(max_bytes=128*1024*1024)
        with self.assertRaises(AppServerOverflowError):d.subscribe(max_bytes=1)
        large.close()
        with patch('threading.Thread.start',side_effect=RuntimeError('PRIVATE')):
            with self.assertRaises(AppServerError) as raised:d.subscribe(callback=lambda _event:None)
        self.assertNotIn('PRIVATE',str(raised.exception))
        self.assertEqual(d.diagnostics()['subscriptions'],0)
        self.assertEqual(d.diagnostics()['callback_workers'],0)
        self.assertEqual(d.diagnostics()['subscription_reserved_bytes'],0)
        self.assertTrue(d.running)

    def test_wrong_field_types_quarantine_without_breaking_other_delivery(self):
        d=self.make();sub=d.subscribe()
        for bad in ([],{},False,12,None):
            values=[event('turn/plan/updated',turnId='turn-a',plan=[{'step':'x','status':bad}]),
                event('thread/status/changed',threadId='thread-a',status={'type':bad})]
            for value in values:self.assertTrue(self.feed(d,value))
        with self.assertRaises(AppServerTimeout):sub.get(timeout=.01)
        self.feed(d,turn_event());self.assertEqual(sub.get(timeout=.1).kind,'turn_started')
        self.assertTrue(d.running)

    def test_bad_declared_frame_size_never_changes_budget(self):
        for size in (0,-1,True,1.5,64*1024*1024+1):
            d=self.make();d.register(1,'config/read',{})
            self.assertFalse(d.feed({'id':1,'result':{}},generation=d.generation,size=size))
            with self.assertRaises(AppServerContractError):d.wait(1,timeout=.1)
            self.assertEqual(d.diagnostics()['pending_bytes'],0)

    def test_nonfinite_deadlines_fail_instead_of_busy_loop_or_wire_action(self):
        d=self.make();sub=d.subscribe();d.register(1,'config/read',{})
        for value in (float('nan'),float('inf'),-1,True,'bad'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):sub.get(timeout=value)
                with self.assertRaises(ValueError):d.wait(1,timeout=value)
                with patch('app.codex_appserver.subprocess.Popen') as start:
                    with self.assertRaises(ValueError):StdioAppServerTransport(timeout=value)
                    start.assert_not_called()
        d.forget(1)

    def test_deferred_plan_delivery_has_monotonic_sequence_and_original_wire_order(self):
        d=self.make();sub=d.subscribe(thread_id='thread-a')
        self.feed(d,event('turn/plan/updated',turnId='turn-a',plan=[]))
        self.feed(d,event('thread/tokenUsage/updated',threadId='thread-a',tokenUsage={'total':usage()}))
        d.register(1,'turn/start',{'threadId':'thread-a'})
        self.feed(d,{'id':1,'result':{'turn':{'id':'turn-a'}}});d.wait(1,timeout=.1)
        first,second=sub.get(timeout=.1),sub.get(timeout=.1)
        self.assertEqual([first.kind,second.kind],['thread_usage','plan'])
        self.assertEqual([first.sequence,second.sequence],[1,2])
        self.assertEqual([first.received_sequence,second.received_sequence],[2,1])

    def test_malformed_critical_proof_closes_instead_of_bypassing_a_guard(self):
        for bad in [event('turn/plan/updated',threadId='thread-a',turnId='turn-a',plan=[{'step':'x','status':'bad'}],item={'id':'tool-a','type':'commandExecution'}),
            turn_event('turn/completed',status='future'),
            event('item/completed',threadId='thread-a',turnId='turn-a',item={'type':'userMessage','id':'u','clientId':False}),
            event('item/started',threadId='thread-a',turnId='turn-a',item={'type':'commandExecution'}),
            event('item/completed',threadId='thread-a',turnId='turn-a',item={'type':'agentMessage','id':'a','text':'x','phase':{}})]:
            d=self.make();d.register(1,'config/read',{})
            self.assertFalse(self.feed(d,bad))
            with self.assertRaises(AppServerContractError):d.wait(1,timeout=.1)

    def test_existing_science_guard_sees_started_and_unknown_item_payloads(self):
        from app.science_news_model import OneTurn
        t=MemoryTransport();self.addCleanup(t.close)
        guard=OneTurn(t,Path.cwd(),{},'synthetic','synthetic',{})
        t.feed(event('item/started',threadId='thread-a',turnId='turn-a',item={'id':'user-a','type':'userMessage','clientId':None,'content':[]}))
        self.assertIsNone(guard.receive(lambda _m:True,description='synthetic guard')['params']['item']['clientId'])
        for method in ('item/started','future/item'):
            t=MemoryTransport();self.addCleanup(t.close)
            guard=OneTurn(t,Path.cwd(),{},'synthetic','synthetic',{})
            t.feed(event(method,threadId='thread-a',turnId='turn-a',item={'id':'tool-a','type':'commandExecution','command':'PRIVATE'}))
            with self.assertRaises(ValueError):guard.receive(lambda _m:True,description='synthetic guard')
            self.assertFalse(t.writes)


class ClientDispatcherTests(unittest.TestCase):
    def client(self, transport, *, peer="0.167.0"):
        original=transport.on_send
        def handler(message):
            if message.get("method")=="initialize":
                transport.feed({"id":message["id"],"result":{"userAgent":f"codex/{peer}"}})
            elif original:
                original(message)
        transport.on_send=handler
        with patch('app.codex_appserver.read_codex_version',return_value=CodexVersion.parse('codex-cli 0.167.0')):
            client=CodexAppServerClient(transport_factory=lambda **_kwargs:transport)
        self.addCleanup(client.close)
        return client

    def completed(self, transport, *, thread="thread-a", turn="turn-a", client="message-a", started=True, users=1):
        if started:transport.feed(turn_event(thread=thread,turn=turn))
        items=[{"type":"userMessage","id":f"user-{i}","clientId":client} for i in range(users)]
        items += [{"type":"agentMessage","id":"answer","phase":"final_answer","text":"Potvrzený výsledek"},
                  {"type":"agentMessage","id":"comment","phase":"commentary","text":"Pozdější komentář"}]
        for item in items:
            transport.feed(event("item/completed",threadId=thread,turnId=turn,item=item))
        transport.feed(turn_event("turn/completed",thread=thread,turn=turn,status="completed",items=items))

    def test_real_client_receipt_with_simultaneous_read_plan_and_thread_usage(self):
        t=MemoryTransport(timeout=1);started=threading.Event()
        def handler(m):
            if m.get("method")=="turn/start":
                t.feed(event("turn/plan/updated",turnId="turn-a",plan=[{"step":"První krok","status":"completed"}]))
                t.feed({"id":m["id"],"result":{"turn":{"id":"turn-a"}}})
                t.feed(turn_event());started.set()
            if m.get("method")=="config/read":
                t.feed(event("thread/tokenUsage/updated",threadId="thread-a",tokenUsage={"total":usage(inputTokens=100,totalTokens=104)}))
                t.feed({"id":m["id"],"result":{"config":{"safe":True}}})
                t.feed(event("thread/tokenUsage/updated",threadId="thread-a",turnId="turn-a",tokenUsage={"total":usage()}))
                t.feed(event("item/completed",threadId="foreign-thread",turnId="foreign-turn",item={"id":"foreign","type":"userMessage","clientId":"message-a"}))
                self.completed(t,started=False)
        t.on_send=handler;client=self.client(t)
        sub=client.subscribe_events(thread_id="thread-a",methods=("turn/plan/updated","thread/tokenUsage/updated"))
        with ThreadPoolExecutor(1) as pool:
            work=pool.submit(client.send_text,thread_id="thread-a",text="Syntetické zadání",client_message_id="message-a")
            self.assertTrue(started.wait(1))
            self.assertEqual(client.read_effective_config(cwd=Path.cwd()),{"safe":True})
            receipt=work.result(1)
        self.assertTrue(receipt.delivered);self.assertEqual(receipt.user_item_count,1)
        self.assertEqual(receipt.answer,"Potvrzený výsledek")
        self.assertEqual(receipt.thread_token_usage["total_tokens"],14)
        stream=[sub.get(timeout=.1) for _ in range(3)]
        self.assertEqual([e.kind for e in stream],["plan","thread_usage","thread_usage"])
        self.assertIsNone(stream[1].turn_id)
        self.assertEqual(sum(m.get('method')=='turn/start' for m in t.writes),1)
        self.assertEqual(len({m['id'] for m in t.writes if 'id' in m}),3)

    def test_bad_latest_usage_clears_old_measurement_without_breaking_delivery(self):
        t=MemoryTransport()
        def handler(message):
            if message.get('method')=='turn/start':
                t.feed({'id':message['id'],'result':{'turn':{'id':'turn-a'}}})
                t.feed(turn_event())
                for raw in ({'total':usage()},None):
                    t.feed(event('thread/tokenUsage/updated',threadId='thread-a',turnId='turn-a',tokenUsage=raw))
                self.completed(t,started=False)
        t.on_send=handler;client=self.client(t)
        sub=client.subscribe_events(thread_id='thread-a',methods=('thread/tokenUsage/updated',))
        receipt=client.send_text(thread_id='thread-a',text='synthetic',client_message_id='message-a')
        self.assertTrue(receipt.delivered);self.assertIsNone(receipt.thread_token_usage)
        self.assertEqual(sub.get(timeout=.1).kind,'thread_usage')
        self.assertEqual(sub.get(timeout=.1).kind,'telemetry_unavailable')
        self.assertEqual(t.diagnostics()['counters']['invalid_telemetry'],1)

    def test_unproven_delivery_is_rejected_with_real_dispatcher(self):
        for started,users in [(False,1),(True,0),(True,2)]:
            with self.subTest(started=started,users=users):
                t=MemoryTransport()
                def handler(m):
                    if m.get('method')=='turn/start':
                        t.feed({'id':m['id'],'result':{'turn':{'id':'turn-a'}}})
                        self.completed(t,started=started,users=users)
                t.on_send=handler;client=self.client(t)
                with self.assertRaises(AppServerContractError):
                    client.send_text(thread_id='thread-a',text='synthetic',client_message_id='message-a')
                self.assertEqual(sum(m.get('method')=='turn/start' for m in t.writes),1)

    def test_disconnect_before_and_after_ack_never_retries(self):
        for ack in [False,True]:
            with self.subTest(ack=ack):
                t=MemoryTransport()
                def handler(m):
                    if m.get('method')=='turn/start':
                        if ack:
                            t.feed({'id':m['id'],'result':{'turn':{'id':'turn-a'}}});t.feed(turn_event())
                            t.feed(event('error',threadId='thread-a',turnId='turn-a',willRetry=True,error={'message':'PRIVATE','codexErrorInfo':{'httpConnectionFailed':{'httpStatusCode':503}}}))
                        t._dispatcher.close(reason='eof')
                t.on_send=handler;client=self.client(t)
                with self.assertRaises(AppServerError) as raised:
                    client.send_text(thread_id='thread-a',text='synthetic',client_message_id='message-a')
                self.assertEqual(sum(m.get('method')=='turn/start' for m in t.writes),1)
                self.assertNotIn('PRIVATE',str(raised.exception))
                if ack:self.assertTrue(raised.exception.will_retry)
                self.assertEqual(t.diagnostics()['pending_rpc'],0)

    def test_hub_persists_unknown_and_blocks_duplicate_without_new_connection(self):
        from app.communication.session_hub import CanonicalSessionHub, SessionDeliveryUnknownError
        with tempfile.TemporaryDirectory() as directory:
            t=MemoryTransport()
            def handler(m):
                if m.get('method')=='thread/start':
                    t.feed({'id':m['id'],'result':{'thread':{'id':'thread-a'}}})
                if m.get('method')=='turn/start':
                    t._dispatcher.close(reason='eof')
            t.on_send=handler;client=self.client(t)
            factory_calls=[]
            def factory():factory_calls.append(True);return client
            hub=CanonicalSessionHub(state_path=Path(directory)/'state.json',workspace=Path(directory),client_factory=factory,
                developer_instructions='Synthetic test',sandbox='read-only',sandbox_policy={'type':'readOnly'},
                approval_policy='never',reasoning_effort='low')
            self.addCleanup(hub.close)
            hub.connect()
            before=hub.snapshot();before_bytes=hub.state_path.read_bytes();before_mtime=hub.state_path.stat().st_mtime_ns
            writes_before=len(t.writes)
            diagnostics=hub.protocol_diagnostics()
            self.assertEqual(len(t.writes),writes_before)
            self.assertTrue(diagnostics['available'])
            self.assertIn('0.167.0',diagnostics['details']['connected_server_version'])
            self.assertEqual(hub.snapshot(),before)
            self.assertEqual(hub.state_path.read_bytes(),before_bytes)
            self.assertEqual(hub.state_path.stat().st_mtime_ns,before_mtime)
            with self.assertRaises(AppServerError):hub.send(text='synthetic',client_message_id='message-unique-12345')
            state=hub.snapshot()
            self.assertEqual(state['messages'][-1]['status'],'delivery_unknown')
            with self.assertRaises(SessionDeliveryUnknownError):hub.send(text='synthetic',client_message_id='message-unique-12345')
            self.assertEqual(len(factory_calls),1)
            self.assertEqual(sum(m.get('method')=='turn/start' for m in t.writes),1)

    def test_version_diagnostics_distinguishes_peer_cli_and_schema_without_payloads(self):
        t=MemoryTransport();client=self.client(t,peer='0.168.0')
        diagnostic=client.protocol_diagnostics()
        self.assertTrue(diagnostic['server_newer_than_reference'])
        self.assertIn('0.168.0',diagnostic['connected_server_version'])
        self.assertIn('0.167.0',diagnostic['local_cli_version'])
        self.assertEqual(diagnostic['support_evidence'],'handshake_and_core_validation')
        self.assertEqual(diagnostic['dispatcher']['pending_rpc'],0)
        self.assertNotIn('params',json.dumps(diagnostic))

    def test_response_envelope_cannot_be_turn_started_evidence_in_adapter(self):
        self.assertFalse(CodexAppServerClient._belongs_to_turn({'id':1,'method':'turn/started','params':{'threadId':'thread-a','turnId':'turn-a'}},thread_id='thread-a',turn_id='turn-a'))


class TransportLifecycleTests(unittest.TestCase):
    def test_invalid_json_duplicate_keys_binary_and_nonfinite_frames_close_safely(self):
        for raw in ('not JSON PRIVATE', '[1,2]', '{"id":1,"id":2,"result":{}}', '{"id":1,"result":{"x":NaN}}', '['*1100+']'*1100, b'\xff'):
            with self.subTest(raw=raw):
                t=MemoryTransport();t._dispatcher.register(1,'config/read',{})
                self.assertFalse(t._accept_frame(raw,t._dispatcher.generation))
                with self.assertRaises(AppServerContractError) as raised:t._dispatcher.wait(1,timeout=.1)
                self.assertNotIn('PRIVATE',str(raised.exception))
                # CPython versions have different JSON nesting limits. If the
                # nested list decodes, routing still rejects its non-object root.
                # Both paths must close and wake the reserved RPC above.
                expected = {'protocol_error'} if raw == '[1,2]' else {'invalid_frame'}
                if raw == '['*1100+']'*1100:
                    expected.add('protocol_error')
                self.assertIn(t.diagnostics()['close_reason'], expected)

    def test_synthetic_stdio_peer_eof_wakes_unanswered_rpc(self):
        # Executable fixture reads one request and exits. It is not Codex.
        with tempfile.TemporaryDirectory() as directory:
            peer=Path(directory)/'synthetic-peer'
            import sys
            peer.write_text(f'#!{sys.executable}\nimport sys\nsys.stdin.readline()\n')
            peer.chmod(0o700)
            t=StdioAppServerTransport(codex_binary=str(peer),timeout=10)
            try:
                started=time.monotonic()
                with self.assertRaises(AppServerClosedError):t.request('config/read',{})
                self.assertLess(time.monotonic()-started,2)
            finally:t.close()
            self.assertFalse(t._reader.is_alive())
            self.assertIsNotNone(t._process.poll())
            self.assertTrue(t._process.stdout.closed);self.assertTrue(t._process.stdin.closed)

    def test_synthetic_stdio_reply_and_core_notifications_are_separated(self):
        with tempfile.TemporaryDirectory() as directory:
            import sys
            peer=Path(directory)/'synthetic-peer'
            peer.write_text(f'#!{sys.executable}\n'+'''import sys,json
m=json.loads(sys.stdin.readline())
print(json.dumps({'method':'turn/started','params':{'threadId':'thread-a','turn':{'id':'turn-a'}}}),flush=True)
print(json.dumps({'id':m['id'],'result':{'ok':True}}),flush=True)
sys.stdin.readline()
''')
            peer.chmod(0o700)
            t=StdioAppServerTransport(codex_binary=str(peer),timeout=1)
            try:
                sub=t.subscribe(thread_id='thread-a')
                self.assertEqual(t.request('config/read',{}),{'ok':True})
                self.assertEqual(sub.get(timeout=.2).kind,'turn_started')
                self.assertEqual(t.receive(lambda _m:True,description='fixture')['method'],'turn/started')
            finally:t.close()
            self.assertFalse(t._reader.is_alive())

    def test_unix_real_websocket_two_clients_reconnect_does_not_stop_fixture_server(self):
        with tempfile.TemporaryDirectory(prefix='ha03-',dir='/tmp') as directory:
            with SyntheticSocket(Path(directory),websocket=True) as peer:
                def connect():
                    t=UnixSocketAppServerTransport(socket_path=peer.path,timeout=.5)
                    t.request('initialize',{'clientInfo':{'name':'synthetic-ha03'}});t.notify('initialized')
                    t.request('thread/resume',{'threadId':'fixture-thread','cwd':str(Path(directory)),'model':'synthetic','modelProvider':'synthetic'})
                    return t
                a,b=connect(),connect()
                try:
                    a.close()
                    self.assertTrue(peer.thread.is_alive())
                    self.assertEqual(b.request('thread/read',{})['thread']['id'],'fixture-thread')
                    new_a=connect()
                    try:
                        self.assertNotEqual(a.diagnostics()['generation'],new_a.diagnostics()['generation'])
                        self.assertEqual(new_a.request('thread/read',{})['thread']['id'],'fixture-thread')
                        self.assertTrue(b.running)
                    finally:new_a.close()
                finally:a.close();b.close()
                self.assertNotIn('turn/start',[method for method,_params in peer.calls])
                self.assertNotIn('thread/start',[method for method,_params in peer.calls])
                self.assertFalse(peer.errors)

    def test_real_unix_remote_eof_before_and_after_ack_has_no_replay(self):
        class ClosingPeer(SyntheticSocket):
            def _websocket(self, connection):
                for raw in connection:
                    message=json.loads(raw)
                    if message.get('method')=='turn/start':
                        self.calls.append(('turn/start',message['params']))
                        if self.scenario=='after':
                            connection.send(json.dumps({'id':message['id'],'result':{'turn':{'id':'fixture-turn'}}}))
                            connection.send(json.dumps(turn_event(thread='fixture-thread',turn='fixture-turn')))
                        connection.close()
                        return
                    self._dispatch(message,lambda value:connection.send(json.dumps(value)))
        for scenario in ('before','after'):
            with self.subTest(scenario=scenario),tempfile.TemporaryDirectory(prefix='ha03-',dir='/tmp') as directory:
                with ClosingPeer(Path(directory),websocket=True,scenario=scenario) as peer:
                    with patch('app.codex_appserver.read_codex_version',return_value=CodexVersion.parse('codex-cli 0.167.0')):
                        client=CodexAppServerClient(transport_factory=lambda **_kwargs:UnixSocketAppServerTransport(socket_path=peer.path,timeout=5))
                    try:
                        started=time.monotonic()
                        with self.assertRaises(AppServerError):client.send_text(thread_id='fixture-thread',client_message_id='synthetic-message',text='synthetic')
                        self.assertLess(time.monotonic()-started,2)
                        self.assertEqual(sum(method=='turn/start' for method,_params in peer.calls),1)
                        self.assertTrue(peer.thread.is_alive())
                        self.assertEqual(client.protocol_diagnostics()['dispatcher']['pending_rpc'],0)
                    finally:client.close()
                    self.assertFalse(client.transport._reader.is_alive())

    def test_unix_peer_eof_wakes_request_before_deadline(self):
        # A server-owned request is deliberately rejected without replying/approval.
        with tempfile.TemporaryDirectory(prefix='ha03-',dir='/tmp') as directory:
            with SyntheticSocket(Path(directory),websocket=True) as peer:
                t=UnixSocketAppServerTransport(socket_path=peer.path,timeout=5)
                try:
                    t.request('initialize',{})
                    started=time.monotonic()
                    with self.assertRaises(AppServerContractError):t.request('fixture/approval',{'method':'item/commandExecution/requestApproval'})
                    self.assertLess(time.monotonic()-started,2)
                    self.assertFalse(peer.approvals)
                finally:t.close()
                self.assertFalse(t._reader.is_alive())

    def test_send_failure_wakes_other_waiter_and_releases_failed_slot(self):
        t=MemoryTransport(timeout=5)
        t._dispatcher.register(1,'model/list',{});t._next_request_id=2
        t.on_send=lambda _m:(_ for _ in ()).throw(AppServerError('synthetic write failure'))
        with ThreadPoolExecutor(1) as pool:
            waiting=pool.submit(t._dispatcher.wait,1,timeout=5)
            with self.assertRaises(AppServerError):t.request('config/read',{})
            with self.assertRaises(AppServerError):waiting.result(1)
        self.assertEqual(t.diagnostics()['pending_rpc'],0)
        self.assertEqual(len(t.writes),1)
