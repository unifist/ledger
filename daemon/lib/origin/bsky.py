"""
Handles everything for the BlueSky Origin
"""

import time
import datetime

import json
import atproto

import service
import ledger

WHO = "bsky"

def init(daemon):
    """
    Intialize the daemon for this Origin
    """

    if (
        not daemon.redis.exists("ledger/origin/bsky") or
        "daemon" not in [group["name"] for group in daemon.redis.xinfo_groups("ledger/origin/bsky")]
    ):
        daemon.redis.xgroup_create("ledger/origin/bsky", "daemon", mkstream=True)


def origin(daemon, instance):
    """
    Handles this Origin
    """

    daemon.redis.xadd("ledger/origin/bsky", fields={"posts": "posts"})
    daemon.logger.info("likes", extra={"posts": "posts"})

    for witness in ledger.Witness.many(origin_id=instance["id"]):

        daemon.logger.info("witness", extra={"witness": witness.export()})
        service.WITNESSES.observe(1)

        daemon.redis.xadd("ledger/origin/bsky", fields={"witness": json.dumps(witness.export())})

def process(daemon):
    """
    Reads witnesses off the list, for posts and likes
    """

    client = Client(daemon)

    message = daemon.redis.xreadgroup("daemon", daemon.name, {
        "ledger/origin/bsky": ">",
    }, count=1, block=100*daemon.sleep)

    if not message:
        return

    print(message)

    if "posts" in message[0][1][0][1]:
        client.posts()

    if "witness" in message[0][1][0][1]:
        client.witness(json.loads(message[0][1][0][1]["witness"]))

    daemon.redis.xack("ledger/origin/bsky", "daemon", message[0][1][0][0])

class Client:
    """
    Class for interacting with BlueSky's API
    """

    BACK = 10  # Cache DB back 100 facts
    FINDS = 3   # Crawl back through history until you find 3 already existing

    daemon = None
    client = None
    profile = None
    handles = None
    witness_ids = None

    def __init__(self, daemon):

        self.daemon = daemon

        with open("/opt/service/secret/bsky.json", "r") as creds_file:
            creds = json.load(creds_file)

        self.client = atproto.Client(creds["url"])
        self.profile = self.client.login(creds["handle"], creds["password"])
        self.handles = []
        self.witness_ids = {}

        for witness in ledger.Witness.many(origin__who=WHO):
            handle = witness.who
            self.handles.append(handle)
            self.witness_ids[handle] = witness.id

    @staticmethod
    def make_time(at):
        """
        Makes a timestamp from a string
        """

        return time.mktime(
            datetime.datetime.strptime(
                at.rsplit(".", 1)[0], "%Y-%m-%dT%H:%M:%S"
            ).timetuple()
        )

    def post_handles(self, post):
        """
        Extra all valie handles following us
        """

        if post.author.handle not in self.handles and post.author.handle != self.profile.handle:
            return

        if post.author.handle in self.handles:
            yield post.author.handle

    def like_handles(self, likes):
        """
        Extra all valie handles following us
        """

        for like in likes:
            if like.author in self.handles:
                yield like.author

    @staticmethod
    def post_to_dict(post):
        """
        Converts a post to dict
        """

        value = {
            "cid": post.cid,
            "author": post.author.handle,
            "created_at": post.record.created_at,
            "text": post.record.text
        }

        return value

    def like_to_dict(self, handle, post):
        """
        Converts a like to dict
        """

        value = {
            "actor": handle,
            "post": self.post_to_dict(post)
        }

        return value

    def reply_to_dict(self, reply, parent):
        """
        Converts a reply to dict
        """

        value = {
            "reply": self.post_to_dict(reply.post),
            "post": self.post_to_dict(parent)
        }

        return value

    def witness_posts(self, witness):
        """
        Synchronizes posts
        """

        facts = ledger.Fact.many(witness_id=witness["id"], who__start="post:").limit(self.BACK).who
        finds = 0

        cursor = None

        while True:

            response = self.client.app.bsky.feed.get_author_feed(params={
                "actor": witness["who"],
                "limit": self.BACK,
                "cursor": cursor,
                "filter": "posts_with_replies"
            })

            for view in response.feed:

                if witness["who"] in self.post_handles(view.post):

                    who = f"post:{view.post.uri}"

                    self.post_likes(view.post)

                    if who in facts or ledger.Fact.many(witness_id=witness["id"], who=who).count():

                        finds += 1

                        if finds == self.FINDS:
                            return

                        continue

                    self.daemon.fact(
                        witness_id=witness["id"],
                        who=who,
                        when=self.make_time(view.post.record.created_at),
                        what=self.post_to_dict(view.post)
                    )

            cursor = response.cursor

            if not cursor:
                break

    def post_likes(self, post):
        """
        Synchronizes likes on followers posts
        """

        facts = ledger.Fact.many(witness__origin__who=WHO, who__start="like:").limit(self.BACK).who
        finds = 0

        cursor = None

        while True:

            response = self.client.get_likes(
                uri=post.uri,
                limit=self.BACK,
                cursor=cursor
            )

            for like in response.likes:

                if like.actor.handle not in self.handles:
                    continue

                who = f"like:{post.uri}:{like.actor.handle}"

                if who in facts or ledger.Fact.many(witness_id=self.witness_ids[like.actor.handle], who=who).count():

                    finds += 1

                    if finds == self.FINDS:
                        return

                    continue

                self.daemon.fact(
                    witness_id=self.witness_ids[like.actor.handle],
                    who=who,
                    when=self.make_time(like.created_at),
                    what=self.like_to_dict(like.actor.handle, post)
                )

            cursor = response.cursor

            if not cursor:
                break

    def post_replies(self, post):
        """
        Synchronizes likes on followers posts
        """

        facts = ledger.Fact.many(witness__origin__who=WHO, who__start="reply:").limit(self.BACK).who
        finds = 0

        response = self.client.get_post_thread(
            uri=post.uri
        )

        for reply in response.thread.replies:

            if reply.post.author.handle not in self.handles:
                continue

            who = f"reply:{post.uri}:{reply.post.uri}"

            if who in facts or ledger.Fact.many(witness_id=self.witness_ids[reply.post.author.handle], who=who).count():

                finds += 1

                if finds == self.FINDS:
                    return

                continue

            self.daemon.fact(
                witness_id=self.witness_ids[reply.post.author.handle],
                who=who,
                when=self.make_time(reply.post.record.created_at),
                what=self.reply_to_dict(reply, post)
            )

    def posts(self):
        """
        Synchronizes likes on our post
        """

        cursor = None

        while True:

            response = self.client.app.bsky.feed.get_author_feed(params={
                "actor": self.profile.handle,
                "limit": self.BACK,
                "cursor": cursor,
                "filter": "posts_with_replies"
            })

            for view in response.feed:
                self.post_likes(view.post)
                self.post_replies(view.post)

            cursor = response.cursor

            if not cursor:
                break

    def witness(self, witness):
        """
        Processes a witness, syncing all the feeds
        """

        if witness["who"] not in self.handles:
            self.daemon.logger.error(f"witness {witness['who']} not following", extra={"witness": witness["who"]})

        #self.witness_posts(witness)
