import random
import unittest
from datetime import datetime, timedelta
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import tests.models
from arxivtimes_indicator.models.model import *


class TestCreateTable(unittest.TestCase):

    def test_create_table(self):
        self.assertFalse(Issue.table_exists())
        self.assertFalse(Label.table_exists())
        create_tables()
        self.assertTrue(Issue.table_exists())
        self.assertTrue(Label.table_exists())
        drop_tables()


class TestIssue(unittest.TestCase):

    def setUp(self):
        create_tables()

    def test_create(self):
        title = 'test_title'
        url = 'https://github.com/arXivTimes/arXivTimes/issues/350'
        user_id = 'icoxfog417'
        avatar_url = 'https://avatars2.githubusercontent.com/u/544269?v=3'
        score = 55
        created_at = datetime.now()
        body = 'test_body'
        labels = [Label(name='ComputerVision'), Label(name='CNN')]
        issue = Issue(title=title,
                      url=url,
                      user_id=user_id,
                      avatar_url=avatar_url,
                      score=score,
                      created_at=created_at,
                      body=body,
                      labels=labels)
        self.assertEqual(issue.title, title)
        self.assertEqual(issue.url, url)
        self.assertEqual(issue.user_id, user_id)
        self.assertEqual(issue.avatar_url, avatar_url)
        self.assertEqual(issue.score, score)
        self.assertEqual(issue.created_at, created_at)
        self.assertEqual(issue.body, body)
        self.assertEqual(issue.labels, labels)

    def test_count(self):
        self.assertEqual(len(Issue.select()), 0)
        issue = Issue(title='title', url='url', user_id='user_id', avatar_url='avatar_url',
                      score=50, created_at=datetime.now(), body='body', labels=[])
        issue.save()
        self.assertEqual(len(Issue.select()), 1)

    def test_extract_headline(self):
        body = """## 一言でいうと

        End-to-Endの対話システムを構築するためのデータセットが公開。50万発話でが含まれ、ドメインはレストラン検索となっている。発話に対しては固有表現(slot)的なアノテーションもされている(「フレンチが食べたい。500円くらいで」なら、種別=フレンチ、予算=500円など)。

        ### 論文リンク

        https://arxiv.org/abs/1706.09254"""
        headline = Issue.extract_headline(body)
        result = '''End-to-Endの対話システムを構築するためのデータセットが公開。50万発話でが含まれ、ドメインはレストラン検索となっている。発話に対しては固有表現(slot)的なアノテーションもされている(「フレンチが食べたい。500円くらいで」なら、種別=フレンチ、予算=500円など)。'''
        self.assertEqual(headline, result)

    def tearDown(self):
        drop_tables()


class TestLabel(unittest.TestCase):

    def setUp(self):
        create_tables()

    def test_create(self):
        name = 'example'
        label = Label(name=name)
        self.assertEqual(label.name, name)

    def test_count(self):
        self.assertEqual(len(Label.select()), 0)
        label = Label(name='example')
        issue = Issue(title='title', url='url', user_id='user_id', avatar_url='avatar_url',
                      score=50, created_at=datetime.now(), body='body', labels=[label])
        issue.save()
        label.issue = issue
        label.save()
        self.assertEqual(len(Label.select()), 1)
        self.assertEqual(len(Issue.select()), 1)

    def tearDown(self):
        drop_tables()


class TestDataAPI(unittest.TestCase):

    max_count = 100

    def setUp(self):
        create_tables()
        self._insert_data(count=self.max_count)

    def tearDown(self):
        drop_tables()

    def _insert_data(self, count):
        for i in range(count):
            issue, labels = self.generate_data()
            issue.save()
            for label in labels:
                label.issue = issue
                label.save()

    def generate_data(self):
        LABELS = list(IndicatorApi.LABEL_TO_GENRE.keys())
        url = 'http://example.com'
        title = 'example'
        body = 'example'
        user_id = 'user_{}'.format(random.randint(0, 10))
        avatar_url = 'http://example.com'
        labels = [Label(name=name) for name in random.sample(LABELS, random.randint(1, 4))]
        score = random.randint(30, 80)
        now = datetime.now()
        delta = timedelta(weeks=random.randint(1, 25))
        created_at = '{}-{} 00:00:00+00:00'.format((now - delta).strftime("%Y-%m"), random.randint(1, 28))
        issue = Issue(title=title,
                      url=url,
                      user_id=user_id,
                      avatar_url=avatar_url,
                      score=score,
                      created_at=created_at,
                      body=body,
                      labels=labels)
        return issue, labels

    def test_get_recent(self):
        data_api = IndicatorApi()
        issues = data_api.get_recent(user_id='', limit=-1)
        self.assertEqual(len(issues), self.max_count)
        issues = data_api.get_recent(user_id='', limit=10)
        self.assertEqual(len(issues), 10)
        issues = data_api.get_recent(user_id='user_3', limit=-1)
        self.assertTrue(len(issues) < self.max_count)

    def test_get_qualified(self):
        data_api = IndicatorApi()
        issues = data_api.get_qualified(user_id='', limit=-1)
        self.assertEqual(len(issues), self.max_count)
        issues = data_api.get_qualified(user_id='', limit=10)
        self.assertEqual(len(issues), 10)
        issues = data_api.get_qualified(user_id='user_3', limit=-1)
        self.assertTrue(len(issues) < self.max_count)

    def test_aggregate_per_month(self):
        data_api = IndicatorApi()
        res = data_api.aggregate_per_month()
        print(res.keys())
        print(res.values())

    def test_aggregate_kinds(self):
        data_api = IndicatorApi()
        res = data_api.aggregate_kinds()
        print(res.keys())
        print(res.values())

    def test_get_user_total_score(self):
        data_api = IndicatorApi()
        score = data_api.get_user_total_score('user_3')
        self.assertTrue(isinstance(score, int))
        self.assertTrue(score > 0)        

    def test_get_user_post_count(self):
        data_api = IndicatorApi()
        count = data_api.get_user_post_count('user_3')
        self.assertTrue(isinstance(count, int))
        self.assertTrue(count > 0)        


if __name__ == "__main__":
    unittest.main()
