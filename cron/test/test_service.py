import unittest
import unittest.mock
import micro_logger_unittest
import relations.unittest

import json

import service
import ledger

class MockRedis:

    host = None
    queue = None

    def __init__(self, host, **kwargs):

        self.host = host
        self.queue = {}

    def xadd(self, stream, fields):

        self.queue.setdefault(stream, [])
        self.queue[stream].append({"fields": fields})

class TestCron(micro_logger_unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("micro_logger.getLogger", micro_logger_unittest.MockLogger)
    @unittest.mock.patch('relations_restx.Source', relations.unittest.MockSource)
    @unittest.mock.patch('redis.Redis', MockRedis)
    def setUp(self):

        self.cron = service.Cron()

    @unittest.mock.patch.dict('os.environ', {"LOG_LEVEL": "INFO"})
    @unittest.mock.patch("micro_logger.getLogger", micro_logger_unittest.MockLogger)
    @unittest.mock.patch('relations_restx.Source', relations.unittest.MockSource)
    @unittest.mock.patch('redis.Redis', MockRedis)
    def test___init__(self):

        cron = service.Cron()

        self.assertEqual(cron.logger.name, "ledger-cron")

        self.assertIsInstance(relations.source("ledger"), relations.unittest.MockSource)

        self.assertEqual(cron.redis.host, "redis.ledger")

    def test_process(self):

        person = ledger.Person("Tom").create()

        self.cron.process()

        self.assertLogged(self.cron.logger, "info", "person", extra={"person": person.export()})

        self.assertEqual(len(self.cron.redis.queue['ledger/person']), 1)
        self.assertEqual(json.loads(self.cron.redis.queue['ledger/person'][0]["fields"]["person"]), person.export())

    @unittest.mock.patch('prometheus_client.push_to_gateway')
    def test_run(self, mock_push):

        self.cron.run()

        mock_push.assert_called_once_with("push.prometheus:9091", "ledger/cron", registry=service.REGISTRY)
