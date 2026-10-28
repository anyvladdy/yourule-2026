"""Independent exploratory Russian NLP; no supervised stance claims and no external requests.

Reads corpus_v2.parquet, writes aggregate tables and local row annotations to v2/out.
Manual/validated stance labels are absent: stance is deliberately not estimated.
"""
import argparse,csv,hashlib,json,re,sys,warnings
from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pymorphy3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'out'
sys.path.insert(0,str(HERE));import build_corpus_v2 as c
SEED=20261028
STOP=set('и в во на с со к ко из за у о об по до от для при под над не ни но а или да же бы был быть есть это этот тот такой весь вся ещё уже только также как что чтобы кто где когда почему потому поэтому если то ли вот тут там здесь так надо нужно можно мочь будет будут нет да свой наш ваш мой твой его её их они мы вы он она оно я ты меня мне нам вам себя себе самый каждый другой один два три очень просто вообще действительно сейчас сегодня тогда потом всегда никогда много мало больше менее такой таки уж ну даже ведь без про между после перед около через иза изза который поскольку хотя зачем либо какой весь всем всё все ещё еще например действительно иметь стать хотеть сказать говорить знать думать смотреть видеть человек люди раз год день время дело место http https www com ru org user email phone youtube telegram vk электрозавод электрический завод московский москва канал видео комментарий пост автор подписаться ссылка читать подробный новость смотреть далее текст'.split())
STOP.update('сам ничего пока однако теперь видимо именно действительно должный нужный'.split())
THEMES={
 'heritage':('Историческая ценность',r'\b(?:истори\w*|наслед\w*|памятник\w*|архитектур\w*|старин\w*)'),
 'demolition':('Снос и утрата',r'\b(?:снос\w*|снес\w*|снест\w*|уничтож\w*|ломать\w*|разруш\w*)'),
 'preservation':('Фасады и подлинность',r'\b(?:фасад\w*|новодел\w*|подлин\w*|воссозда\w*|входн\w*\s+групп\w*|муляж\w*)'),
 'development':('Новая застройка',r'\b(?:застрой\w*|жиль\w*|жилищ\w*|квартир\w*|небоскр[её]б\w*|человейник\w*|коммерц\w*)'),
 'governance':('Город и принятие решений',r'\b(?:власт\w*|мэри\w*|собянин\w*|чиновник\w*|коррупц\w*|сговор\w*|девелопер\w*)'),
 'transparency':('Документы и объяснения',r'\b(?:схем\w*|документ\w*|планиров\w*|проект\w*|скрыва\w*|прозрачн\w*)'),
 'participation':('Участие в обсуждении',r'\b(?:слушани\w*|обсуждени\w*|петиц\w*|подпис\w*|спросил\w*|спросит\w*)'),
 'cultural_use':('Арендаторы и культура',r'\b(?:арендатор\w*|мастерск\w*|студи\w*|галере\w*|театр\w*|творческ\w*|культурн\w*\s+пространств\w*)'),
 'local_impacts':('Бытовые последствия',r'\b(?:пробк\w*|транспорт\w*|парков\w*|шум\w*|пыл\w*|набережн\w*|доступ\w*)'),
}
RX={key:re.compile(pattern,re.I) for key,(_,pattern) in THEMES.items()}
MORPH=pymorphy3.MorphAnalyzer()

@lru_cache(maxsize=100000)
def lemma(word):
    p=MORPH.parse(word)[0]
    if any(t in p.tag for t in ('Name','Surn','Patr')):return ''
    if p.tag.POS in ('NPRO','PREP','CONJ','PRCL','INTJ','NUMR'):return ''
    return p.normal_form

def normalize(text):
    text=re.sub(r'https?://\S+|\[[^\]]+\]',' ',text.lower().replace('ё','е'))
    words=[]
    for token in re.findall(r'\b[а-я]{3,}\b',text):
        if token in STOP:continue
        item=lemma(token)
        if item and item not in STOP and len(item)>2:words.append(item)
    return ' '.join(words)

def save_csv(name,rows,fields=None):
    if fields is None:fields=list(rows[0]) if rows else []
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def author_ngrams(eligible, limit=40):
    """One vote per (platform, author hash, phrase); unknown authors excluded.

    No phrase may cross a message boundary. Authors on different platforms are
    distinct accounts, not assumed to be distinct people.
    """
    authors=defaultdict(lambda: {2:set(),3:set()});unknown=0
    for row,doc in eligible:
        if not row.get('author_id_hash'):
            unknown+=1;continue
        phrases=authors[(row['platform'],row['author_id_hash'])]
        words=doc.split()
        for n in (2,3):
            phrases[n].update(' '.join(words[i:i+n]) for i in range(len(words)-n+1))
    result=[]
    for n in (2,3):
        counts=Counter()
        for phrases in authors.values():counts.update(phrases[n])
        for phrase,count in sorted(counts.items(),key=lambda x:(-x[1],x[0]))[:limit]:
            result.append(dict(n=n,lemma_phrase=phrase,unique_author_count=count,
                               denominator=len(authors)))
    return result,len(authors),unknown

def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    path=ROOT/'data/processed/corpus_v2.parquet';data=pq.read_table(path).to_pylist()
    lookup={(r['platform'],r['id']):r for r in data}
    direct_threads={(r['source_id'],r['thread_id']) for r in data if r['platform']=='youtube' and r['row_type'] in ('comment','reply') and c.SITE.search(r['text'])}
    for r in data:
        strict=r['relevant']
        if r['platform']=='youtube' and r['source_kind']=='digest' and r['row_type'] in ('comment','reply'):
            strict=(r['source_id'],r['thread_id']) in direct_threads
        r['_strict']=strict
    broad=[r for r in data if r['row_type'] in ('comment','reply') and r['in_window'] and r['relevant']]
    mainrows=[r for r in broad if r['_strict'] and r['context_complete']]
    coverage=[]
    for platform in ('youtube','telegram','vk'):
        group=[r for r in data if r['platform']==platform]
        candidates=[r for r in broad if r['platform']==platform]
        eligible=[r for r in mainrows if r['platform']==platform]
        coverage.append(dict(platform=platform,all_rows=len(group),publications=sum(r['row_type'] in ('video','post') for r in group),
            reactions=sum(r['row_type'] in ('comment','reply') for r in group),
            broad_p3=len(candidates),strict_complete_p3=len(eligible),
            strict_context_excluded=sum(r['_strict'] and not r['context_complete'] for r in candidates),
            unique_authors=len({r['author_id_hash'] for r in eligible if r['author_id_hash']}),
            unknown_author_rows=sum(not r['author_id_hash'] for r in eligible),
            day_precision=sum(r['date_precision']=='day' for r in group)))
    save_csv('coverage.csv',coverage)
    terms=[]
    for platform in ('youtube','telegram','vk'):
        rs=[r for r in mainrows if r['platform']==platform]
        for key,(title,_) in THEMES.items():
            matched=[r for r in rs if RX[key].search(r['text'])]
            terms.append(dict(platform=platform,theme=key,title=title,matches=len(matched),denominator=len(rs),
                              percent=round(100*len(matched)/len(rs),2) if rs else None))
    save_csv('theme_mentions.csv',terms)
    periods=[]
    for platform in ('youtube','telegram','vk'):
        for period in ('P0','P1','P2','P3','after_cut','unknown'):
            rs=[r for r in data if r['platform']==platform and r['period']==period and r['relevant']]
            periods.append(dict(platform=platform,period=period,publications=sum(r['row_type'] in ('video','post') for r in rs),reactions=sum(r['row_type'] in ('comment','reply') for r in rs)))
    save_csv('period_coverage.csv',periods)
    weeks=Counter()
    from datetime import date,timedelta
    for r in mainrows:
        day=date.fromisoformat(r['published_date']);week=day-timedelta(days=day.weekday())
        weeks[(r['platform'],week.isoformat())]+=1
    save_csv('weekly_reactions.csv',[dict(platform=p,week=w,messages=n) for (p,w),n in sorted(weeks.items())])
    # Root publication, not the top-level comment, for concentration.
    def publication(r):
        if r['platform']=='youtube':return r['source_id']
        if r['platform']=='telegram':return r['thread_id']
        current=r;seen=set()
        while current['row_type']!='post' and current.get('parent_id') and current['id'] not in seen:
            seen.add(current['id']);nxt=lookup.get(('vk',current['parent_id']))
            if nxt is None:return r['thread_id']
            current=nxt
        return current['id']
    concentration=[];sensitivity=[]
    for platform in ('youtube','telegram','vk'):
        rs=[r for r in mainrows if r['platform']==platform];counts=Counter(publication(r) for r in rs)
        largest,count=counts.most_common(1)[0] if counts else (None,0)
        concentration.append(dict(platform=platform,largest_publication_messages=count,denominator=len(rs),
                                  largest_percent=round(100*count/len(rs),2) if rs else 0,publications_with_reactions=len(counts)))
        trimmed=[r for r in rs if publication(r)!=largest]
        for key,(title,_) in THEMES.items():
            baseline=sum(bool(RX[key].search(r['text'])) for r in rs)/len(rs) if rs else 0
            reduced=sum(bool(RX[key].search(r['text'])) for r in trimmed)/len(trimmed) if trimmed else 0
            sensitivity.append(dict(platform=platform,theme=key,all_n=len(rs),without_largest_n=len(trimmed),
                all_percent=round(100*baseline,2),without_largest_percent=round(100*reduced,2),delta_pp=round(100*(reduced-baseline),2)))
    save_csv('source_concentration.csv',concentration);save_csv('sensitivity.csv',sensitivity)
    normal={}; eligible=[]
    for r in mainrows:
        doc=normalize(r['text']);normal[(r['platform'],r['id'])]=doc
        if len(doc.split())>=4 and r['lang']=='ru':eligible.append((r,doc))
    unique=sorted({doc for _,doc in eligible})
    vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=4,max_df=.7,max_features=15000,sublinear_tf=True)
    X=vectorizer.fit_transform(unique)
    initial_unique_count=len(unique)
    nonzero=np.asarray(X.getnnz(axis=1)).ravel()>0
    unique=[doc for doc,keep in zip(unique,nonzero) if keep]
    X=X[nonzero]
    eligible=[(r,doc) for r,doc in eligible if doc in set(unique)]
    n_topics=min(8,X.shape[0]-1,X.shape[1]-1)
    model=NMF(n_components=n_topics,init='nndsvda',random_state=SEED,max_iter=500)
    W=model.fit_transform(X);names=vectorizer.get_feature_names_out()
    top=[]
    for k,weights in enumerate(model.components_):
        chosen=np.argsort(weights)[::-1][:12]
        top.append(dict(topic=k+1,terms='; '.join(names[i] for i in chosen),unique_documents=int(sum(np.argmax(W,axis=1)==k))))
    save_csv('nmf_topics.csv',top)
    mapped={doc:(int(np.argmax(weights))+1,float(np.max(weights)/sum(weights)) if sum(weights)>0 else 0)
            for doc,weights in zip(unique,W)}
    annotations=[]
    for r in data:
        key=(r['platform'],r['id']);doc=normal.get(key);topic,strength=mapped.get(doc,(None,None))
        annotations.append(dict(platform=r['platform'],id=r['id'],analysis_eligible=key in normal,
            topic_id=topic,topic_weight_share=strength,theme_mentions=[k for k in THEMES if RX[k].search(r['text'])],
            stance=None,stance_status='not_estimated_no_validated_labels'))
    pq.write_table(pa.Table.from_pylist(annotations),OUT/'nlp_annotations.parquet',compression='zstd')
    topic_counts=Counter(mapped[doc][0] for _,doc in eligible if doc in mapped)
    save_csv('nmf_topic_counts.csv',[dict(topic=k,documents=n,denominator=len(eligible)) for k,n in sorted(topic_counts.items())])
    grams,gram_authors,gram_unknown=author_ngrams(eligible)
    save_csv('ngrams.csv',grams)
    meta={'version':'v2','revision':'R2_C1_C3','seed':SEED,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'broad_reactions_p3':len(broad),'strict_complete_reactions_p3':len(mainrows),
          'nlp_eligible_messages':len(eligible),'nlp_unique_documents':len(unique),'zero_vector_documents_excluded':initial_unique_count-len(unique),'tfidf_shape':list(X.shape),
          'ngram_count_unit':'distinct (platform, author_id_hash) per phrase; no cross-message phrases',
          'ngram_unique_authors':gram_authors,'ngram_unknown_author_messages_excluded':gram_unknown,
          'nmf_topics':n_topics,'nmf_iterations':model.n_iter_,'nmf_reconstruction_error':float(model.reconstruction_err_),
          'normalization':'pymorphy3, Russian tokens >=3 letters; stopwords; person-name tags removed',
          'scope':'P3 reactions only; explicit-site threads for YouTube digests; complete parent context',
          'stance':'not estimated: no validated labels or local Ollama server; no fabricated agreement/accuracy',
          'theme_mentions':'lexical mentions, NOT classified criticism, stance or causality',
          'sentiment':'not estimated; no validated/pretrained local model used'}
    (OUT/'nlp_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    assert sum(r['strict_complete_p3'] for r in coverage)==len(mainrows)
    assert len(annotations)==len(data)
    assert all(0<=r['matches']<=r['denominator'] for r in terms)
    assert sum(topic_counts.values())==len(eligible)
    print(json.dumps(meta,ensure_ascii=False,indent=2));print('PASS aggregate reconciliations; one annotation per row; no stance asserted')

if __name__=='__main__':main()
