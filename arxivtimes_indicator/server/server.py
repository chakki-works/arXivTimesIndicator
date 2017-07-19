import os
import json
import tornado.web
import requests
import pandas as pd
from arxivtimes_indicator.server.__dummy_data import DummyData


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        posts = {}
        stat = {}

        if DummyData.is_dummy_request(self):
            dd = DummyData()
            recent = dd.get_recent()
            popular = dd.get_popular()
            posts = {
                "recent": recent,
                "popular": popular
            }
            posts = json.dumps(posts)
            stat = json.dumps(dd.aggregate_per_month())
        else:
            # todo: extract data from url
            pass
        
        self.render("index.html", posts=posts, stat=stat)


class UserHandler(tornado.web.RequestHandler):

    def get(self, user_id):
        profile = {
            "user_id": user_id,
            "avatar_url": self.static_url("images/GitHub-Mark-64px.png"),
            "url": "",
            "name": user_id,
            "belongs": "",
            "blog": "",
            "total_score": 0,
            "post_count": 0
        }

        url = "https://api.github.com/users/{}".format(user_id)
        try:
            r = requests.get(url)
            if r.ok:
                p = r.json()
                profile["avatar_url"] = p["avatar_url"]
                profile["url"] = p["html_url"]
                profile["name"] = p["name"]
                if p["company"] or p["location"]:
                    if p["company"] and p["location"]:
                        profile["belongs"] = "at " + p["company"] + "," + p["location"]
                    elif p["company"]:
                        profile["belongs"] = "at " + p["company"]
                    elif p["location"]:
                        profile["belongs"] = "in " + p["location"]

                profile["blog"] = p["blog"]
                profile["location"] = p["location"]
        except Exception as ex:
            print(ex)
        
        posts = {"recent":[], "popular":[]}
        stats = {"monthly":{}, "kinds": {}}

        if DummyData.is_dummy_request(self):
            dd = DummyData()
            profile["total_score"] = dd.get_user_total_score(user_id)
            profile["post_count"] = dd.get_user_post_count(user_id)
            recent = dd.get_recent(user_id=user_id)[:10]
            popular = dd.get_popular(user_id=user_id)[:10]
            posts["recent"] = recent
            posts["popular"] = popular

            monthly = dd.aggregate_per_month(user_id)
            kinds = dd.aggregate_kinds(user_id)
            stats["monthly"] = monthly
            stats["kinds"] = kinds
            stats = json.dumps(stats)

        self.render("user.html", profile=profile, posts=posts, stats=stats)


class StatisticsHandler(tornado.web.RequestHandler):

    def get(self, user_id): 
        self.render("statistics.html")


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/user/([^/]+)", UserHandler),
            (r"/statistics", StatisticsHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret=os.environ.get("SECRET_TOKEN", "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"),
            xsrf_cookies=True,
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)