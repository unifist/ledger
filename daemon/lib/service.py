"""
Module for the Daemon
"""

# pylint: disable=no-self-use

import os
import micro_logger
import json
import redis

import relations_rest

import prometheus_client

PROCESS = prometheus_client.Gauge("process_seconds", "Time to complete a processing task")
ORIGINS = prometheus_client.Summary("origins_processed", "Origins processed")

class Daemon: # pylint: disable=too-few-public-methods
    """
    Daemon class
    """

    def __init__(self):

        self.name = os.environ["K8S_POD"]

        self.sleep = int(os.environ.get("SLEEP", 5))

        self.logger = micro_logger.getLogger("ledger-daemon")

        self.source = relations_rest.Source("ledger", url="http://api.ledger")

        self.redis = redis.Redis(host='redis.ledger', encoding="utf-8", decode_responses=True)

        if (
            not self.redis.exists("ledger/origin") or
            "daemon" not in [group["name"] for group in self.redis.xinfo_groups("ledger/origin")]
        ):
            self.redis.xgroup_create("ledger/origin", "daemon", mkstream=True)

    @PROCESS.time()
    def process(self):
        """
        Reads people off the queue and logs them
        """

        message = self.redis.xreadgroup("daemon", self.name, {"ledger/origin": ">"}, count=1, block=1000*self.sleep)

        if not message or "origin" not in message[0][1][0][1]:
            return

        origin = json.loads(message[0][1][0][1]["origin"])
        self.logger.info("origin", extra={"origin": origin})
        ORIGINS.observe(1)
        self.redis.xack("ledger/origin", "daemon", message[0][1][0][0])

    def run(self):
        """
        Main loop with sleep
        """

        prometheus_client.start_http_server(80)

        while True:
            self.process()
