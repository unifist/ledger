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

import origin.zoom

PROCESS = prometheus_client.Gauge("process_seconds", "Time to complete a processing task")
ORIGINS = prometheus_client.Summary("origins_processed", "Origins processed")
WITNESSES = prometheus_client.Summary("witnesses_processed", "Witnesses processed")
FACTS = prometheus_client.Summary("facts_created", "Facts created")

class Daemon: # pylint: disable=too-few-public-methods
    """
    Daemon class
    """

    ORIGINS = [
        origin.zoom
    ]

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

        for handler in self.ORIGINS:
            if hasattr(handler, "init"):
                handler.init(self)

    @PROCESS.time()
    def process(self):
        """
        Reads people off the queue and logs them
        """

        message = self.redis.xreadgroup("daemon", self.name, {"ledger/origin": ">"}, count=1, block=1000*self.sleep)

        if not message or "origin" not in message[0][1][0][1]:
            return

        instance = json.loads(message[0][1][0][1]["origin"])
        self.logger.info("origin", extra={"origin": instance})
        ORIGINS.observe(1)

        for handler in self.ORIGINS:
            if handler.WHO == instance["who"] and hasattr(handler, "origin"):
                handler.origin(self, instance)

        self.redis.xack("ledger/origin", "daemon", message[0][1][0][0])

    def run(self):
        """
        Main loop with sleep
        """

        prometheus_client.start_http_server(80)

        while True:

            self.process()

            for handler in self.ORIGINS:
                if hasattr(handler, "process"):
                    handler.process(self)
