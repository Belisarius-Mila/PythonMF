from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from app.science_news import ScienceNews, identity, public_url, archive_item
from app.science_news_sources import parse_feed, collect, SOURCES, reusable_full_text
from app.science_news_runner import tick, slot, grounded_items, PRAGUE
from app.cockpit_science_news import science_news_overview, science_news_decision_action, science_news_translate_action, translate
from app.science_news_model import call_model, policy, OneTurn


def item(**changes):
    return {"title": "Nový mechanismus", "abstract_cs": "Výsledky buněčného experimentu naznačují nový mechanismus.",
        "significance_cs": "Může otevřít novou možnost, zatím předklinickou.",
        "uncertainty_cs": "Nejde o doklad účinné léčby lidí.", "area": "Genetika", "category": "science",
        "published_at": "2026-01-02T12:00:00+00:00", "source_url": "https://www.nature.com/articles/test",
        "doi": "10.1234/test", **changes}


def packet():
    return {"candidates": [{"candidate_id": "src_test", "title": "Original title", "source_url": "https://www.nature.com/articles/test",
        "published_at": "2026-01-02T12:00:00+00:00", "doi": "10.1234/test",
        "source_excerpt": "A sufficiently long exact quotation from the source describing a cell experiment."}],
        "source_health": [{"source_id": "fixture", "state": "ok"}]}


def answer():
    return {"items": [{k: v for k, v in item(candidate_id="src_test", topic_id="", evidence_quote=packet()["candidates"][0]["source_excerpt"]).items()
        if k not in ("published_at", "source_url", "doi")}]}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ScienceNews(self.root / "news", self.root / "archive")

    def publish(self, items=None, key="fixture"):
        self.store.publish(key, items or [item()], available_at="2026-01-02T12:00:00+00:00")
        return identity((items or [item()])[0])

    def test_read_does_not_create_private_data(self):
        self.assertEqual(self.store.overview()["pending_count"], 0)
        self.assertFalse(self.store.root.exists())

    def test_save_is_idempotent_and_follows(self):
        news = self.publish()
        first = self.store.decide(news, "save", "req1")
        self.assertEqual(first["archive_id"], self.store.decide(news, "save", "req1")["archive_id"])
        self.assertTrue(self.store.decide(news, "save", "req2")["replayed"])
        self.assertEqual(len(list((self.root / "archive/articles").iterdir())), 1)
        overview = self.store.overview()
        self.assertEqual(overview["pending_count"], 0)
        self.assertTrue(overview["follows"][0]["active"])
        from app.article_archive import list_articles, get_article
        self.assertEqual(len(list_articles(category="all", archive_root=self.store.archive_root)["items"]), 1)
        text = get_article(article_id=first["archive_id"], archive_root=self.store.archive_root)
        self.assertIn(item()["abstract_cs"], text["text"])

    def test_follow_and_dismiss_do_not_archive(self):
        for action in ("follow", "dismiss"):
            with self.subTest(action=action):
                store = ScienceNews(self.root / action, self.root / "archive")
                store.publish("one", [item()], available_at="2026-01-02T12:00:00+00:00")
                store.decide(identity(item()), action, action)
                self.assertEqual(len(store.overview()["follows"]), action == "follow")
                self.assertEqual(store.overview()["pending_count"], 0)
        self.assertFalse((self.root / "archive").exists())

    def test_doi_duplicate_never_resurrects_decision(self):
        news = self.publish()
        self.store.decide(news, "dismiss", "req")
        self.publish([item(source_url="https://www.nasa.gov/duplicate")], "second")
        self.assertEqual(self.store.overview()["pending_count"], 0)

    def test_cross_action_replay_and_request_collision_fail(self):
        news = self.publish()
        self.store.decide(news, "follow", "req")
        for request in ("req", "different"):
            with self.assertRaises(ValueError): self.store.decide(news, "dismiss", request)

    def test_interrupted_archive_stays_pending_and_same_request_reconciles(self):
        news = self.publish()
        real = archive_item
        def interrupted(item, root):
            real(item, root)
            raise OSError("lost response")
        with patch("app.science_news.archive_item", interrupted):
            self.assertFalse(science_news_decision_action({"item_id": news, "action": "save", "request_id": "one"}, store=self.store)["ok"])
        self.assertEqual(self.store.overview()["pending_count"], 1)
        with self.assertRaises(ValueError): self.store.decide(news, "dismiss", "another")
        self.store.decide(news, "save", "one")
        self.assertEqual(len(list((self.root / "archive/articles").iterdir())), 1)
        self.assertEqual(self.store.overview()["pending_count"], 0)

    def test_reconciliation_preserves_manual_article_edits(self):
        news = self.publish()
        real = archive_item
        def interrupted(item, root):
            result = real(item, root)
            (root / "articles" / result / "article.txt").write_text("Moje pozdější poznámka")
            raise OSError()
        with patch("app.science_news.archive_item", interrupted):
            with self.assertRaises(OSError): self.store.decide(news, "save", "one")
        result = self.store.decide(news, "save", "one")
        self.assertEqual((self.store.archive_root / "articles" / result["archive_id"] / "article.txt").read_text(), "Moje pozdější poznámka")

    def test_parallel_identical_save_has_one_article(self):
        news = self.publish()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.store.decide(news, "save", "same"), range(4)))
        self.assertTrue(all(x["ok"] for x in results))
        self.assertEqual(len(list((self.root / "archive/articles").iterdir())), 1)

    def test_corrupt_store_is_unknown_not_empty(self):
        self.publish()
        self.store.path.write_text("{broken")
        self.assertFalse(science_news_overview(store=self.store)["ok"])

    def test_unfollow_is_persistent(self):
        news = self.publish()
        self.store.decide(news, "follow", "one")
        self.store.unfollow(news)
        self.assertFalse(ScienceNews(self.store.root).overview()["follows"][0]["active"])

    def test_new_revision_of_followed_paper_is_new_event_not_resurrection(self):
        news=self.publish()
        self.store.decide(news,'follow','first')
        updated=packet();updated['candidates'][0]['published_at']='2026-02-03T09:00:00+00:00'
        selected=answer();selected['items'][0]['topic_id']=news
        revisions=grounded_items(selected,updated,self.store.overview()['follows'])
        self.assertNotEqual(revisions[0]['id'],news)
        self.store.publish('followup',revisions,available_at='2026-02-03T09:00:00+00:00')
        self.assertEqual(self.store.overview()['pending_count'],1)
        self.store.decide(revisions[0]['id'],'follow','second')
        self.assertEqual(len(self.store.overview()['follows']),1)
        self.assertEqual(self.store.overview()['pending_count'],0)

    def test_partial_article_creation_can_reconcile_without_new_card(self):
        news=self.publish()
        from app.science_news import atomic_create_text
        def fail_metadata(path,*args,**kwargs):
            if path.name=='metadata.json':raise OSError('interrupted before metadata')
            return atomic_create_text(path,*args,**kwargs)
        with patch('app.science_news.atomic_create_text',side_effect=fail_metadata):
            with self.assertRaises(OSError):self.store.decide(news,'save','one')
        self.assertEqual(self.store.overview()['pending_count'],1)
        self.store.decide(news,'save','one')
        self.assertEqual(len(list((self.store.archive_root/'articles').iterdir())),1)

    def test_save_waits_for_translation_and_then_archives_same_text(self):
        news=self.publish()
        with self.store.transaction() as state:
            state['jobs']['translation_'+news]={'state':'running'}
        with self.assertRaises(ValueError):self.store.decide(news,'save','one')
        with self.store.transaction() as state:
            state['items'][news]['translation']='Dokončený český překlad.'
            state['jobs']['translation_'+news]['state']='completed'
        result=self.store.decide(news,'save','one')
        text=(self.store.archive_root/'articles'/result['archive_id']/'article.txt').read_text()
        self.assertIn('Dokončený český překlad.',text)

    def test_publish_idempotency_and_limits(self):
        self.publish()
        self.assertTrue(self.store.publish("fixture", [item()], available_at="2026-01-02T12:00:00+00:00")["replayed"])
        with self.assertRaises(ValueError): self.publish([item(title="changed")])
        with self.assertRaises(ValueError): self.publish([item()] * 6, "large")
        with self.assertRaises(ValueError): self.publish([item()] * 2, "duplicate")

    def test_unsafe_links_and_symlinks_rejected(self):
        for url in ("javascript:alert(1)", "http://localhost/x", "https://127.0.0.1/x", "https://host.local/x", "https://u:p@example.org/"):
            with self.subTest(url=url), self.assertRaises(ValueError): public_url(url)
        self.store.root.symlink_to(self.root / "target")
        with self.assertRaises(ValueError): self.store.overview()

    def test_unknown_item_and_bad_action_do_not_mutate(self):
        self.publish()
        before = self.store.path.read_bytes()
        for values in (("unknown", "save", "req"), (identity(item()), "invalid", "req")):
            with self.assertRaises(ValueError): self.store.decide(*values)
        self.assertEqual(before, self.store.path.read_bytes())

    def test_translation_requires_full_reusable_text_and_activation(self):
        news = self.publish()
        result = science_news_translate_action({"item_id": news}, store=self.store)
        self.assertFalse(result["ok"])
        self.assertEqual(self.store.overview()["pending_count"], 1)
        self.assertEqual(self.store._read()["jobs"], {})

    def test_translation_is_separate_from_decision(self):
        news = self.publish([item(source_text="A sufficiently long complete source message for the fixture.", translation_permission="user-provided")])
        model = Mock(return_value={"translation": "Dostatečně dlouhý úplný český překlad této zkušební zdrojové zprávy.", "complete": True})
        translate(self.store, self.store.item(news), model=model)
        self.assertEqual(model.call_count, 1)
        self.assertEqual(self.store.overview()["pending_count"], 1)
        self.assertTrue(self.store.item(news)["translation"])
        self.assertFalse(self.store.overview()["follows"])

    def test_incomplete_translation_does_not_become_full_translation(self):
        news = self.publish([item(source_text="Original full message" * 10)])
        with self.assertRaises(ValueError): translate(self.store, self.store.item(news), model=Mock(return_value={"complete": False, "translation": "krátce"}))
        self.assertNotIn("translation", self.store.item(news))

    def test_absent_activation_never_constructs_client(self):
        client = Mock()
        with self.assertRaises(ValueError): call_model(self.store, "one", {}, "instructions", {}, client_factory=client)
        client.assert_not_called()
        self.assertFalse(self.store.root.exists())

    def test_missing_central_role_blocks_even_with_private_activation(self):
        self.store.root.mkdir()
        (self.store.root/'activation.json').write_text(json.dumps({'enabled':True,'approval_ref':'test-approval',
            'max_job_credits':15,'max_month_credits':100,'activated_at':'2026-11-09T09:00:00+01:00'}))
        from app.communication.agent_roles import AgentRoleError
        client=Mock()
        with patch('app.science_news_model.agent_roles.load_role',side_effect=AgentRoleError('missing approval')):
            with self.assertRaises(ValueError):call_model(self.store,'one',{},'instructions',{},client_factory=client)
        client.assert_not_called()
        self.assertFalse(self.store.path.exists())

    def test_weekly_prepare_then_publish_and_restart(self):
        when = datetime(2026, 11, 13, 8, 0, tzinfo=PRAGUE)
        reviewer, collector = Mock(return_value=answer()), Mock(return_value=packet())
        first = tick(self.store, when, reviewer=reviewer, collector=collector, activated_at=when-timedelta(days=2))
        self.assertEqual(first["state"], "prepared")
        self.assertEqual(self.store.overview()["pending_count"], 0)
        second = tick(self.store, when+timedelta(hours=1), reviewer=reviewer, collector=collector)
        self.assertEqual(second["state"], "published")
        self.assertEqual(self.store.overview()["pending_count"], 1)
        self.assertEqual(reviewer.call_count, 1)
        self.assertEqual(tick(self.store, when+timedelta(hours=2), reviewer=reviewer, collector=collector)["state"], "already_published")

    def test_unknown_weekly_attempt_never_retries_even_next_week(self):
        reviewer, collector = Mock(side_effect=TimeoutError()), Mock(return_value=packet())
        when = datetime(2026,11,13,9,tzinfo=PRAGUE)
        for current in (when, when+timedelta(minutes=15), when+timedelta(days=7)):
            self.assertEqual(tick(self.store,current,reviewer=reviewer,collector=collector)["state"], "attention")
        self.assertEqual(reviewer.call_count, 1)

    def test_before_activation_due_does_not_run(self):
        when=datetime(2026,11,9,9,tzinfo=PRAGUE)
        reviewer=Mock()
        self.assertEqual(tick(self.store,when,reviewer=reviewer,activated_at=when)["state"], "not_due")
        reviewer.assert_not_called()
        self.assertFalse(self.store.root.exists())

    def test_all_failed_sources_do_not_publish_empty_success(self):
        reviewer=Mock()
        result=tick(self.store,datetime(2026,11,13,9,tzinfo=PRAGUE),reviewer=reviewer,
            collector=Mock(return_value={"candidates":[],"source_health":[{"state":"unavailable"}]}))
        self.assertEqual(result["state"],"attention")
        reviewer.assert_not_called()

    def test_empty_or_already_seen_batch_never_calls_model(self):
        self.publish()
        reviewer=Mock()
        when=datetime(2026,11,13,9,tzinfo=PRAGUE)
        result=tick(self.store,when,reviewer=reviewer,collector=Mock(return_value=packet()))
        self.assertEqual(result['state'],'published');self.assertEqual(result['item_count'],0)
        reviewer.assert_not_called()


class ContractTests(unittest.TestCase):
    def test_full_translation_source_needs_explicit_derivative_friendly_licence(self):
        body='<article><h1>Source</h1><p>'+('A complete scientific source paragraph. '*20)+'</p></article>'
        for licence in ('', '<link rel="license" href="https://creativecommons.org/licenses/by-nd/4.0/">'):
            with self.assertRaises(ValueError):reusable_full_text(item(),fetch=Mock(return_value=(licence+body).encode()))
        text,permission=reusable_full_text(item(),fetch=Mock(return_value=('<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">'+body).encode()))
        self.assertEqual(permission,'cc-by');self.assertIn('complete scientific',text)

    def test_grounding_projects_source_identity_and_disallows_inventions(self):
        result=grounded_items(answer(),packet(),[])
        self.assertEqual(result[0]["source_url"],packet()["candidates"][0]["source_url"])
        for field,value in (("evidence_quote","invented quote"),("candidate_id","invented"),("topic_id","unknown")):
            modified=answer();modified["items"][0][field]=value
            with self.assertRaises(ValueError): grounded_items(modified,packet(),[])
        modified=answer();modified["items"][0]["source_text"]="untrusted license claim"
        with self.assertRaises(ValueError): grounded_items(modified,packet(),[])

    def test_follow_up_needs_active_known_topic(self):
        modified=answer();modified["items"][0]["topic_id"]="known"
        self.assertEqual(grounded_items(modified,packet(),[{"topic_id":"known","active":True}])[0]["topic_id"],"known")
        with self.assertRaises(ValueError):grounded_items(modified,packet(),[{"topic_id":"known","active":False}])

    def test_dst_keeps_friday_nine(self):
        for date,offset in (((2026,3,27),1),((2026,4,3),2),((2026,10,23),2),((2026,10,30),1)):
            due=slot(datetime(*date,9,tzinfo=PRAGUE))
            self.assertEqual((due.weekday(),due.hour),(4,9))
            self.assertEqual(due.utcoffset().total_seconds(),offset*3600)

    def test_rss_atom_rdf_dates_links_and_xml_safety(self):
        rss=b'<rss><channel><item><title>Science</title><link>https://www.nature.com/test</link><description>A sufficiently long description.</description><pubDate>Fri, 13 Nov 2026 08:00:00 GMT</pubDate></item></channel></rss>'
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Science</title><link rel="self" href="https://example.org/self"/><link rel="alternate" href="https://www.nature.com/test"/><summary>Text</summary><published>2026-11-13T08:00:00Z</published></entry></feed>'
        self.assertEqual(parse_feed(rss,"test")[0]["source_url"],parse_feed(atom,"test")[0]["source_url"])
        for raw in (b'<!DOCTYPE x><rss/>',b'<html/>',b'<broken'):
            with self.assertRaises(Exception):parse_feed(raw,"test")

    def test_collection_reports_failures_and_filters_old_dates(self):
        rss=b'<rss><channel><item><title>Science</title><link>https://www.nature.com/test</link><description>Text</description><pubDate>Fri, 13 Nov 2026 08:00:00 GMT</pubDate></item></channel></rss>'
        def fetch(url):
            if url==SOURCES['nature_physics']:raise OSError()
            return rss
        result=collect(datetime(2026,11,13,9,tzinfo=PRAGUE),fetch=fetch)
        self.assertFalse(result['complete'])
        self.assertEqual(len(result['candidates']),1)
        self.assertEqual(collect(datetime(2026,12,13,9,tzinfo=PRAGUE),fetch=fetch)['candidates'],[])


if __name__ == '__main__':unittest.main()
