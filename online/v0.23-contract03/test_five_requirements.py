"""Synthetic HTTP, concurrency, restart and failure acceptance tests; no network."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / 'candidate-contract03/source'
if not DEFAULT_SOURCE.exists():
    DEFAULT_SOURCE = HERE / 'source'
sys.path.insert(0, os.getenv('CHRONOTRACE_CANDIDATE_SOURCE', str(DEFAULT_SOURCE)))
import numpy as np
from fastapi.testclient import TestClient
from adaptive_evidence import chronotrace_api as api
from adaptive_evidence.aml_contract import Add, EnvelopeJournal
from adaptive_evidence.core import Config, MemoryStore as ExactStore
from adaptive_evidence.chronotrace_store import MemoryStore
from adaptive_evidence.remote_encoder import EmbeddingError

KEY = 'invented-test-only-key'
HEADERS = {'X-Api-Key': KEY}


class Encoder:
    identity = 'synthetic-contract02-fixed-vector'
    def __init__(self):
        self.documents = 0
        self.fail = False
        self.entered = threading.Event()
        self.release = None

    def encode(self, texts, *, query=False):
        if not query:
            self.documents += len(texts)
            self.entered.set()
            if self.release is not None and not self.release.wait(timeout=10):
                raise RuntimeError('synthetic_gate_timeout')
            if self.fail:
                raise EmbeddingError('synthetic_transient_failure')
        return np.array([[1., 0., 0.] for _ in texts], dtype=np.float32)


def payload(user='tenant-a', request='same-logical-write', session='session-one', content='Violet observatory belongs to tenant A.'):
    return dict(user_id=user, request_id=request, session_id=session,
                messages=[dict(role='user', content=content, timestamp=1700000000000)])


class Requirements(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.path = Path(self.temp.name) / 'raw.sqlite3'
        self.encoder = Encoder()
        self.store = MemoryStore(self.path, self.encoder, Config(context_chars=24000))
        self.env = patch.dict(os.environ, {'MEMORY_API_KEY': KEY, 'AE_MODE': 'query_document_evidence'})
        self.env.start()
        original_connect = socket.socket.connect
        def local_control_pipe(sock, address):
            # Windows asyncio constructs its internal wakeup socketpair using
            # loopback TCP. Preserve that OS mechanism; reject external sockets.
            if isinstance(address, tuple) and address[0] in {'127.0.0.1', '::1'}:
                return original_connect(sock, address)
            raise AssertionError('external_network_forbidden')
        self.network = patch('socket.socket.connect', new=local_control_pipe)
        self.network.start()
        api.app.dependency_overrides[api.get_store] = lambda: self.store
        self.client = TestClient(api.app)

    def tearDown(self):
        api.app.dependency_overrides.clear()
        self.network.stop()
        self.env.stop()
        self.temp.cleanup()

    def add(self, value):
        return self.client.post('/add', json=value, headers=HEADERS)

    def search(self, user='tenant-a', query='observatory', top_k=100, **extra):
        return self.client.post('/search', json=dict(user_id=user, query=query, top_k=top_k, **extra), headers=HEADERS)

    def counts(self):
        with closing(self.store.connect()) as db:
            return {table: db.execute('SELECT count(*) FROM '+table).fetchone()[0]
                    for table in ['sources', 'chunks', 'requests']}

    def test_user_boundary_same_request_id_and_cross_session(self):
        first = payload()
        other = payload(user='tenant-b', content='Orange observatory belongs to tenant B.')
        second = payload(request='second-write', session='session-two', content='Silver telescope is in tenant A observatory.')
        for value in [first, other, second]:
            self.assertEqual(self.add(value).status_code, 200)
        a = self.search().json()['data']
        b = self.search(user='tenant-b').json()['data']
        self.assertIn(first['messages'][0]['content'], '\n'.join(x['content'] for x in a))
        self.assertIn(second['messages'][0]['content'], '\n'.join(x['content'] for x in a))
        self.assertNotIn('tenant B', '\n'.join(x['content'] for x in a))
        self.assertNotIn('tenant A', '\n'.join(x['content'] for x in b))
        self.assertEqual(self.search(user='unseen-user').json(), {'data': []})
        self.assertEqual(self.search(session_id='session-one').status_code, 422)

    def test_no_200_before_embedding_and_commit_then_immediate_search(self):
        self.encoder.release = threading.Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.add, payload())
            self.assertTrue(self.encoder.entered.wait(timeout=5))
            self.assertFalse(future.done())
            self.assertEqual(self.counts(), dict(sources=0, chunks=0, requests=0))
            self.assertEqual(self.search().json(), {'data': []})
            self.encoder.release.set()
            response = future.result(timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), dict(success=True, user_id='tenant-a',
            request_id='same-logical-write', session_id='session-one'))
        self.assertTrue(self.search().json()['data'])
        reopened = MemoryStore(self.path, Encoder(), Config(context_chars=24000))
        self.assertTrue(reopened.search(user_id='tenant-a', query='observatory', top_k=100,
                                       mode='query_document_evidence'))

    def test_cached_search_sees_successive_write(self):
        self.add(payload())
        self.search()  # Populate prior index revision.
        text = 'New durable source from a different session.'
        self.assertEqual(self.add(payload(request='new-write', session='new-session', content=text)).status_code, 200)
        result = self.search(query='durable source').json()['data']
        self.assertIn(text, '\n'.join(x['content'] for x in result))

    def test_16_concurrent_logical_retries_one_source(self):
        value = payload()
        with ThreadPoolExecutor(max_workers=16) as pool:
            responses = list(pool.map(self.add, [value]*16))
        self.assertEqual([r.status_code for r in responses], [200]*16)
        self.assertEqual(self.counts(), dict(sources=1, chunks=1, requests=1))
        self.assertEqual(self.encoder.documents, 1)
        before = self.search().json()
        self.assertEqual(self.add(value).status_code, 200)
        self.assertEqual(self.search().json(), before)
        self.assertEqual(self.add(payload(content='Conflicting replacement.')).status_code, 409)
        self.assertEqual(self.add(payload(session='conflicting-session')).status_code, 409)
        self.assertEqual(self.search().json(), before)

    def test_legacy_write_conflict_cannot_poison_correct_retry(self):
        # Simulate an Add committed by release01 before the new ingress journal.
        self.store.add(**payload())
        self.assertEqual(self.add(payload(content='A conflicting body after upgrade.')).status_code, 409)
        self.assertEqual(self.add(payload()).status_code, 200)
        self.assertEqual(self.counts(), dict(sources=1, chunks=1, requests=1))

    def test_provider_failure_not_success_and_same_request_can_repair(self):
        self.encoder.fail = True
        self.assertEqual(self.add(payload()).status_code, 503)
        self.assertEqual(self.counts(), dict(sources=0, chunks=0, requests=0))
        self.assertEqual(self.search().json(), {'data': []})
        journal = EnvelopeJournal(self.path)
        with closing(journal.connect()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM completions').fetchone()[0], 0)
        self.encoder.fail = False
        self.assertEqual(self.add(payload()).status_code, 200)
        self.assertEqual(self.counts(), dict(sources=1, chunks=1, requests=1))
        self.assertTrue(self.search().json()['data'])

    def test_ordered_text_parts_original_envelope_and_retry_conflict(self):
        parts = [dict(type='text', text='First immutable part.'), dict(type='text', text='Second immutable part.')]
        value = payload(content=parts)
        self.assertEqual(self.add(value).status_code, 200)
        result = self.search(query=[dict(type='text', text='First'), dict(type='text', text='Second')]).json()['data']
        self.assertIn('First immutable part.\nSecond immutable part.', '\n'.join(x['content'] for x in result))
        with closing(EnvelopeJournal(self.path).connect()) as db:
            original = json.loads(db.execute('SELECT body FROM envelopes').fetchone()[0])
            self.assertEqual(original['messages'][0]['content'], parts)
            self.assertEqual(db.execute('SELECT count(*) FROM completions').fetchone()[0], 1)
        # Same flattened bytes do not authorize replacement of the original form.
        self.assertEqual(self.add(payload(content='First immutable part.\nSecond immutable part.')).status_code, 409)
        self.assertEqual(self.add(value).status_code, 200)

    def test_envelope_and_derivation_immutable(self):
        self.add(payload())
        with closing(EnvelopeJournal(self.path).connect()) as db:
            for query in ["UPDATE envelopes SET body='{}'", 'DELETE FROM envelopes', 'DELETE FROM completions']:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(query)
        with closing(self.store.derived.connect()) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM objects')

    def test_top_k_empty_response_required_fields_and_order(self):
        self.assertEqual(self.search().json(), {'data': []})
        for i in range(4):
            self.add(payload(request='different-'+str(i), content='Original source '+str(i)+' for telescope observatory.'))
        for limit in [1, 2, 100]:
            response = self.search(top_k=limit)
            self.assertEqual(response.status_code, 200)
            result = response.json()['data']
            self.assertLessEqual(len(result), limit)
            for record in result:
                self.assertIsInstance(record['id'], str)
                self.assertTrue(record['id'])
                self.assertTrue(record['content'])
            direct = self.store.search(user_id='tenant-a', query='observatory', top_k=limit,
                                       mode='query_document_evidence')
            self.assertEqual(result, direct)  # API preserves evidence priority.

    def test_no_answer_gold_option_letter_or_cross_user_fallback(self):
        self.add(payload(content='A sealed observatory contains a brass telescope.'))
        result = self.search(query='Which object is there?', options=['A. Microscope', 'B. Brass telescope']).json()['data']
        self.assertTrue(result)
        self.assertTrue(all('A sealed observatory contains a brass telescope.' in x['content'] for x in result))
        self.assertFalse(any(x['content'].strip() in {'B', 'B. Brass telescope'} for x in result))
        for extra in [dict(answer='B'), dict(gold='B'), dict(evidence=['external-label'])]:
            self.assertEqual(self.search(**extra).status_code, 422)
        self.assertEqual(self.search(user='foreign-user').json(), {'data': []})

    def test_textual_rejects_images_invalid_fields_without_echo(self):
        bad = payload(content=[dict(type='image_url', image_url=dict(url='data:image/png;base64,fixture'))])
        response = self.add(bad)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'detail':'Invalid request schema'})
        for bad in [payload(content=[]), payload(content=' '), payload(user=' '),
                    dict(payload(), messages=[dict(role='user', content='private-invalid-body', timestamp=True)])]:
            response = self.add(bad)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn('private-invalid-body', response.text)
        for limit in [0, 101, True, '100']:
            self.assertEqual(self.search(top_k=limit).status_code, 422)

    def test_authentication_and_no_partial_success_envelope(self):
        for headers in [{}, {'Authorization':'Bearer invalid'}, {'X-Api-Key':'invalid'}]:
            self.assertEqual(self.client.post('/add', json=payload(), headers=headers).status_code, 401)
        self.assertEqual(self.counts(), dict(sources=0, chunks=0, requests=0))
        for scheme in ['Bearer', 'Token']:
            self.assertEqual(self.client.post('/add', json=payload(),
                headers={'Authorization':scheme+' '+KEY}).status_code, 200)
        self.assertEqual(self.counts(), dict(sources=1, chunks=1, requests=1))

    def test_existing_string_payloads_preserve_exact_retrieval(self):
        values = [payload(content='A source sentence.\nAnother source sentence.'),
                  payload(request='second', session='another', content='A different original source about a telescope.')]
        for value in values:
            parsed = Add.model_validate(value)
            self.assertEqual(parsed.retrieval_payload(), value)
            self.add(value)
        baseline = ExactStore(self.path, Encoder(), Config(context_chars=24000))
        for query in ['source', 'telescope', 'Which object?']:
            for limit in [1, 2, 100]:
                expected = baseline.search(user_id='tenant-a', query=query, top_k=limit, mode='query_document_evidence')
                self.assertEqual(self.search(query=query, top_k=limit).json()['data'], expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
