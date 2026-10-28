"""Regression checks for review C1 and C3; no corpus mutation."""
import unittest
from analyze_nlp_v2 import author_ngrams,RX

class ReviewTests(unittest.TestCase):
    def row(self,author='a',platform='telegram'):
        return {'platform':platform,'author_id_hash':author}
    def test_demolition_forms(self):
        for text in ('снос','снесли','снести','уничтожают','ломать','разрушение'):
            self.assertIsNotNone(RX['demolition'].search(text),text)
        self.assertIsNone(RX['demolition'].search('износ здания'))
    def test_repeated_author_votes_once(self):
        records=[(self.row(),'старый красивый дом сегодня')]*12
        records += [(self.row(),'старый красивый дом завтра'),(self.row('b'),'старый красивый дом')]
        grams,n,unknown=author_ngrams(records)
        phrase=next(r for r in grams if r['lemma_phrase']=='старый красивый')
        self.assertEqual(phrase['unique_author_count'],2);self.assertEqual(n,2)
        self.assertEqual(unknown,0)
    def test_platform_and_unknown(self):
        grams,n,unknown=author_ngrams([(self.row(),'старый дом'),(self.row(platform='vk'),'старый дом'),(self.row(None),'старый дом')])
        self.assertEqual(n,2);self.assertEqual(unknown,1)
        self.assertEqual(grams[0]['unique_author_count'],2)
    def test_no_boundary_phrases_and_determinism(self):
        rows=[(self.row(),'старый дом'),(self.row(),'красивый фасад')]
        a=author_ngrams(rows);self.assertEqual(a,author_ngrams(rows[::-1]))
        self.assertNotIn('дом красивый',{r['lemma_phrase'] for r in a[0]})
if __name__=='__main__':unittest.main()
