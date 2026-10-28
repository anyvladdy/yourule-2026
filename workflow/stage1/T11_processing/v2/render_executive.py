"""Render exportable executive figures and an offline presentation page from v2 aggregates."""
import argparse,csv,html,json,os,textwrap,zipfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parent/'out/.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.dates as mdates
import numpy as np
from datetime import date,timedelta

HERE=Path(__file__).resolve().parent;OUT=HERE/'out';FIG=OUT/'figures'
BG='#F5F1E9';INK='#172E36';MUTED='#59686B';GRID='#DADBD3';ACCENT='#B24D36'
PLAT={'youtube':('YouTube','#B24D36'),'telegram':('Telegram','#2E6B78'),'vk':('VK','#697755')}
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,
 'xtick.color':MUTED,'ytick.color':INK,'axes.edgecolor':GRID,'axes.facecolor':BG,
 'figure.facecolor':BG,'savefig.facecolor':BG,'font.size':16,'svg.fonttype':'none'})

def read(name):return list(csv.DictReader((OUT/name).open()))
def nfmt(n):return f'{int(n):,}'.replace(',',' ')
def base(title,subtitle,page):
 fig=plt.figure(figsize=(16,9))
 fig.text(.055,.94,'ЭЛЕКТРОЗАВОД  /  ПУБЛИЧНАЯ ДИСКУССИЯ',size=12,color=MUTED,weight='bold')
 fig.text(.055,.855,title,size=31,weight='bold',va='top')
 fig.text(.055,.785,subtitle,size=14,color=MUTED,va='top')
 fig.text(.055,.045,'01.06–28.10.2026  •  Выборка публичных реакций  •  Аналитическая версия v2',size=11,color=MUTED)
 fig.text(.945,.045,f'{page:02}',ha='right',size=12,color=MUTED)
 return fig

def clean(ax):
 for spine in ax.spines.values():spine.set_visible(False)
 ax.tick_params(length=0,pad=9)
 ax.set_axisbelow(True)

def save(fig,name,foot):
 fig.text(.055,.095,foot,size=12,color=MUTED)
 fig.savefig(FIG/(name+'.png'),dpi=150)
 fig.savefig(FIG/(name+'.svg'))
 plt.close(fig)

def render():
 argparse.ArgumentParser(description=__doc__).parse_args();FIG.mkdir(exist_ok=True)
 coverage=read('coverage.csv');themes=read('theme_mentions.csv');concentration=read('source_concentration.csv')
 meta=json.loads((OUT/'nlp_manifest.json').read_text()); build=json.loads((OUT/'build_manifest.json').read_text())
 fig=base('4 919 реакций для предметного разбора','Общий корпус: 14 340 записей. Уточнены контекст сообщений и связи ответов.',1)
 ax=fig.add_axes([.16,.24,.72,.43]);clean(ax)
 for i,r in enumerate(coverage):
  p=r['platform'];broad=int(r['broad_p3']);strict=int(r['strict_complete_p3'])
  ax.barh(i,broad,color=GRID,height=.52)
  ax.barh(i,strict,color=PLAT[p][1],height=.52)
  ax.text(strict/2,i,nfmt(strict),color='white',ha='center',va='center',weight='bold',size=22)
  ax.text(broad+55,i,'из '+nfmt(broad),va='center',size=15,color=MUTED)
 ax.set_yticks(range(3),[PLAT[r['platform']][0] for r in coverage],fontsize=20);ax.invert_yaxis()
 ax.set_xlim(0,3500);ax.set_xticks([0,1000,2000,3000],['0','1 000','2 000','3 000']);ax.grid(axis='x',color=GRID,lw=.6)
 ax.set_xlabel('Комментарии и ответы, сообщений',labelpad=14)
 save(fig,'01_corpus','Цвет — строгий срез; серый — исходный отбор. Исключены 522 реакции дайджестов и 17 записей с неполным контекстом.')

 fig=base('Слова о проекте: девять тем обсуждения','Доли сообщений со словами каждого словаря; ширина словарей различается, ранжирование не применяется.',2)
 ax=fig.add_axes([.30,.22,.60,.48]);clean(ax)
 keys=list(dict.fromkeys(r['theme'] for r in themes));titles={r['theme']:r['title'] for r in themes}
 matrix=np.array([[float(next(r['percent'] for r in themes if r['theme']==k and r['platform']==p)) for p in PLAT] for k in keys])
 cmap=colors.LinearSegmentedColormap.from_list('signal',[BG,'#C8DAD7','#3C736D'])
 ax.imshow(matrix,aspect='auto',cmap=cmap,vmin=0,vmax=max(matrix.max(),1),interpolation='nearest')
 ax.set_yticks(range(len(keys)),[titles[k] for k in keys],fontsize=14)
 ax.set_xticks(range(3),[PLAT[r['platform']][0]+'\nn = '+nfmt(r['strict_complete_p3']) for r in coverage],fontsize=16)
 for i in range(len(keys)):
  for j in range(3):ax.text(j,i,f'{matrix[i,j]:.1f}%'.replace('.',','),ha='center',va='center',color='white' if matrix[i,j]>matrix.max()*.68 else INK,size=17,weight='bold')
 save(fig,'02_themes','Доля реакций со словами темы. Темы пересекаются; это не доли критиков и не оценка отношения к проекту.')

 fig=base('Один материал даёт 27–31% реакций площадки','Проверять выводы нужно и без крупнейшей публикации.',3)
 ax=fig.add_axes([.16,.26,.75,.41]);clean(ax)
 for i,r in enumerate(concentration):
  p=r['platform'];pct=float(r['largest_percent'])
  ax.barh(i,100,color=GRID,height=.48);ax.barh(i,pct,color=PLAT[p][1],height=.48)
  ax.text(pct/2,i,f'{pct:.1f}%'.replace('.',','),ha='center',va='center',color='white',weight='bold',size=23)
  ax.text(pct+2,i,f"{nfmt(r['largest_publication_messages'])} из {nfmt(r['denominator'])}",va='center',size=16)
 ax.set_yticks(range(3),[PLAT[r['platform']][0] for r in concentration],fontsize=20);ax.invert_yaxis()
 ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%'])
 ax.set_xlabel('Доля сообщений в строгом срезе площадки',labelpad=15)
 save(fig,'03_concentration','После исключения крупнейшего материала доля словаря исторической ценности меняется не более чем на 1,3 п. п.')

 fig=base('Реакции распределены по времени неравномерно','Даты публикации комментариев в собранной выборке; причины всплесков этим графиком не установлены.',4)
 weekly=read('weekly_reactions.csv');start=date(2026,6,1);weeks=[start+timedelta(days=7*i) for i in range(22)]
 for i,p in enumerate(PLAT):
  ax=fig.add_axes([.13,.57-i*.18,.77,.125]);clean(ax)
  counts={r['week']:int(r['messages']) for r in weekly if r['platform']==p}
  vals=[counts.get(w.isoformat(),0) for w in weeks]
  ax.plot(weeks,vals,color=PLAT[p][1],lw=2.4);ax.fill_between(weeks,vals,color=PLAT[p][1],alpha=.14)
  ax.set_ylabel(PLAT[p][0]+'\nсообщений',fontsize=12,labelpad=14)
  ax.set_ylim(bottom=0);ax.grid(axis='y',color=GRID,lw=.6)
  ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
  ax.tick_params(labelsize=11)
  if i<2:ax.set_xticklabels([])
 save(fig,'04_timeline','Сбор ретроспективный и неполный. Нулевое значение не доказывает отсутствия обсуждения на платформе.')

 fig=base('Словарь наследия устойчив к исключению лидера','Сравнение частоты темы с крупнейшей публикацией и без неё — внутри каждой площадки.',5)
 ax=fig.add_axes([.17,.26,.70,.42]);clean(ax)
 sens=[r for r in read('sensitivity.csv') if r['theme']=='heritage']
 for i,r in enumerate(sens):
  p=r['platform'];a=float(r['all_percent']);b=float(r['without_largest_percent'])
  ax.plot([a,b],[i,i],color=PLAT[p][1],lw=3)
  ax.scatter([a],[i],s=160,c=PLAT[p][1]);ax.scatter([b],[i],s=160,facecolor=BG,edgecolor=PLAT[p][1],linewidth=2.3)
  ax.text(min(a,b)-.35,i+.18,f'{a:.1f}% → {b:.1f}%'.replace('.',','),size=16)
 ax.set_yticks(range(3),[PLAT[r['platform']][0] for r in sens],fontsize=20);ax.invert_yaxis()
 ax.set_ylim(2.55,-.35);ax.set_xlim(0,20);ax.set_xticks([0,5,10,15,20],['0%','5%','10%','15%','20%']);ax.grid(axis='x',color=GRID,lw=.6)
 ax.set_xlabel('Реакции со словами исторической ценности',labelpad=15)
 save(fig,'05_sensitivity','Закрашенная точка — полный строгий срез; контур — без лидера. Это проверка частоты словаря, не устойчивости всех выводов.')

 topicrows=read('nmf_topics.csv');topiccounts={int(r['topic']):int(r['documents']) for r in read('nmf_topic_counts.csv')}
 labels={1:'Повседневные реплики без единой темы',2:'Снос и сравнения с другими объектами',3:'Облик и сохранность зданий',4:'Снос памятников и новое строительство',5:'Охранный статус и культурное наследие',6:'История и утрата памяти',7:'Будущая застройка и функции',8:'Образ города и городская идентичность'}
 fig=base('Восемь направлений для чтения дискуссии','Автоматическая тематическая модель; названия групп — интерпретация для навигации по текстам.',6)
 ax=fig.add_axes([.42,.23,.47,.47]);clean(ax)
 ordered=sorted(topiccounts,key=topiccounts.get,reverse=True)
 vals=[topiccounts[k] for k in ordered]
 ax.barh(range(len(vals)),vals,color='#3C736D',height=.58)
 ax.set_yticks(range(len(vals)),[labels[k] for k in ordered],fontsize=12);ax.invert_yaxis()
 for i,v in enumerate(vals):ax.text(v+12,i,nfmt(v),va='center',fontsize=14)
 ax.set_xlim(0,max(vals)*1.12);ax.grid(axis='x',color=GRID,lw=.6);ax.set_xlabel('Сообщений с преобладающей модельной темой',labelpad=12,fontsize=13)
 save(fig,'06_nlp_topics',f"Модель охватывает {nfmt(meta['nlp_eligible_messages'])} из 4 919 реакций. Единица — сообщение; повторения одного автора могут влиять на группы.")

 for r in topicrows:r['editorial_label']=labels[int(r['topic'])]
 with (OUT/'topic_interpretation.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(topicrows[0]));w.writeheader();w.writerows(topicrows)
 slides=[('01_corpus','Объём и отбор'),('02_themes','Темы'),('03_concentration','Концентрация'),('04_timeline','Хронология'),('05_sensitivity','Проверка устойчивости'),('06_nlp_topics','NLP-карта')]
 # Portable page uses embedded SVGs: no network, external fonts, datasets or personal text.
 svgslides=[]
 for stem,title in slides:
  svg=(FIG/(stem+'.svg')).read_text();svg=svg[svg.index('<svg'):]
  svgslides.append(f'<section class="slide" aria-label="{html.escape(title)}">{svg}</section>')
 page='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Электрозавод — аналитика публичной дискуссии</title><style>
*{box-sizing:border-box}body{margin:0;background:#172e36;font-family:Arial,sans-serif;color:#f5f1e9}header{display:flex;justify-content:space-between;align-items:center;padding:18px 4vw;gap:20px}header p{margin:0;font-size:14px}nav{display:flex;gap:8px}button{background:transparent;border:1px solid #879495;color:inherit;padding:10px 18px;border-radius:3px;font-size:14px;cursor:pointer}button:hover,button:focus{background:#406b70}.slide{display:none;max-width:1600px;margin:auto}.slide.active{display:block}.slide svg{display:block;width:100%;height:auto}.help{margin:12px 4vw;color:#c6d0cc;font-size:12px}@media print{body{background:white}header,.help{display:none}.slide{display:block;break-after:page}}@page{size:landscape;margin:0}
</style></head><body><header><p>Электрозавод · Для обсуждения · Аналитическая версия v2</p><nav><button id="prev" aria-label="Предыдущая страница">← Назад</button><button id="next" aria-label="Следующая страница">Далее →</button><button id="full">На весь экран</button></nav></header>'''+''.join(svgslides)+'''<p class="help"><span id="counter"></span> · Стрелки клавиатуры переключают страницы. Доли относятся к собранным сообщениям, а не к населению Москвы.</p><script>
const slides=[...document.querySelectorAll('.slide')];let index=0;function show(){slides.forEach((s,i)=>s.classList.toggle('active',i===index));document.getElementById('counter').textContent=(index+1)+' / '+slides.length;document.getElementById('prev').disabled=index===0;document.getElementById('next').disabled=index===slides.length-1;}document.getElementById('prev').onclick=()=>{index=Math.max(0,index-1);show()};document.getElementById('next').onclick=()=>{index=Math.min(slides.length-1,index+1);show()};document.getElementById('full').onclick=()=>document.documentElement.requestFullscreen?.();document.onkeydown=e=>{if(e.key==='ArrowRight')document.getElementById('next').click();if(e.key==='ArrowLeft')document.getElementById('prev').click()};show();</script></body></html>'''
 (OUT/'executive_brief.html').write_text(page)
 print('Rendered 6 PNG + 6 SVG and standalone executive_brief.html')

if __name__=='__main__':render()
