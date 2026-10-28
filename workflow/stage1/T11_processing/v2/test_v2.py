"""Offline regression checks for the VK additions and preserved corpus versions."""
import unittest
from collections import Counter
import build_corpus_v2 as v

class VKTests(unittest.TestCase):
    def raw(self, **kw):
        return dict(id='-12_3',source='search',owner_kind='person',author_hash='hashed',author_display='private',published_at='2026-10-28',_collected_at='2026-10-28T12:00:00Z',text='Электрозавод',**kw)
    def test_date_only_and_privacy(self):
        r=self.raw();out=v.vk_row(r,'post',r,b'test')
        self.assertIsNone(out['published_at']);self.assertEqual(out['date_precision'],'day')
        self.assertTrue(out['in_window']);self.assertIsNone(out['author_display'])
    def test_thread_context(self):
        p=self.raw();r=self.raw(parent_id='-12_3',thread_id='-12_3')
        r['text']='Спасибо';out=v.vk_row(r,'comment',p,b'test')
        self.assertTrue(out['relevant']);self.assertEqual(out['relevance_reason'],'thread_context')
        p['text']='Другой завод';self.assertFalse(v.vk_row(r,'comment',p,b'test')['relevant'])
    def test_counters(self):
        self.assertEqual(v.vk_number('1\u202f234'),1234)
        for value in ('1.2K','1,2 тыс.',None,''):self.assertIsNone(v.vk_number(value))
    def test_snapshot_dedup(self):
        a=self.raw();b=dict(a,_collected_at='2026-10-28T13:00:00Z',text='updated')
        stats=Counter();result=v.b.latest([a,b],lambda r:r['id'],stats,'vk_post')
        self.assertEqual(len(result),1);self.assertEqual(result[a['id']]['text'],'updated')
    def test_timestamp_normalization(self):
        r=self.raw();r['published_at']='2026-10-28T15:00:00+03:00'
        self.assertEqual(v.vk_row(r,'post',r,b'test')['published_at'],'2026-10-28T12:00:00Z')
if __name__=='__main__':unittest.main()
