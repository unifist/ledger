"""
Handles everything for the Zoom Origin
"""

# pylint: disable=unsupported-membership-test

import time
import datetime

import json
import base64
import requests

import service
import ledger

WHO = "zoom"

def init(daemon):
    """
    Intialize the daemon for this Origin
    """

    if (
        not daemon.redis.exists("ledger/origin/zoom/witness") or
        "daemon" not in [group["name"] for group in daemon.redis.xinfo_groups("ledger/origin/zoom/witness")]
    ):
        daemon.redis.xgroup_create("ledger/origin/zoom/witness", "daemon", mkstream=True)


def origin(daemon, instance):
    """
    Handles this Origin
    """

    for witness in ledger.Witness.many(origin_id=instance["id"]):

        daemon.logger.info("witness", extra={"witness": witness.export()})
        service.WITNESSES.observe(1)

        daemon.redis.xadd("ledger/origin/zoom/witness", fields={"witness": json.dumps(witness.export())})


def process(daemon):
    """
    Processes this Origin
    """

    message = daemon.redis.xreadgroup("daemon", daemon.name, {"ledger/origin/zoom/witness": ">"}, count=1, block=1000*daemon.sleep)

    if not message or "witness" not in message[0][1][0][1]:
        return

    witness = json.loads(message[0][1][0][1]["witness"])
    daemon.logger.info("witness", extra={"witness": witness})
    service.WITNESSES.observe(1)

    Client(daemon, witness["entity_id"]).witness(witness)

    daemon.redis.xack("ledger/origin/zoom/witness", "daemon", message[0][1][0][0])


class Client:
    """
    Class for interacting with Zoom's API
    """

    WITNESS_BACK = 15*24*60*60 # 15 days back

    daemon = None
    session = None

    def __init__(self, daemon, entity_id):

        self.daemon = daemon

        with open(f"/opt/service/secret/zoom-{entity_id}.json", "r") as creds_file:
            creds = json.load(creds_file)

        base64_creds = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()
        headers = {
            "Authorization": f"Basic {base64_creds}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "account_credentials", "account_id": creds["account_id"]}

        response = requests.post("https://zoom.us/oauth/token", headers=headers, data=data)
        response.raise_for_status()
        access_token = response.json()["access_token"]

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })

    def meeting_summaries(self):
        """
        Iterates through all the summaries for this account (sans details)
        """

        response = self.session.get("https://api.zoom.us/v2/meetings/meeting_summaries").json()

        while response:

            for summary in response["summaries"]:
                yield summary

            if response.get("next_page_token"):
                response = self.session.get(
                    "https://api.zoom.us/v2/meetings/meeting_summaries",
                    json={"next_page_token": response["next_page_token"]}
                ).json()
            else:
                response = None

    def meeting_summary(self, summary):
        """
        Gets all the details for a summary
        """

        return self.session.get(f"https://api.zoom.us/v2/meetings/{summary['meeting_uuid']}/meeting_summary").json()

    def witness(self, witness):
        """
        Processes a witness, syncing all the meetings
        """

        facts = ledger.Fact.many(witness_id=witness["id"], when__gt=time.time()-self.WITNESS_BACK)["who"]

        for summary in self.meeting_summaries():

            who = f"meeting_summary:{summary['meeting_uuid']}"

            if who in facts or ledger.Fact.many(witness_id=witness["id"], who=who).count():
                continue

            self.daemon.fact(
                witness_id=witness["id"],
                who=who,
                when=time.mktime(datetime.datetime.strptime(summary["summary_end_time"], "%Y-%m-%dT%H:%M:%SZ").timetuple()),
                what=self.meeting_summary(summary)
            )
