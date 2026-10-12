import json,random
exec(open('q.py').read())
random.seed(2026); out=[]
for i,(m,e,c,w,k) in enumerate(Q):
    alts=[c]+w; random.shuffle(alts); out.append({"id":i+1,"m":m,"e":e,"a":alts,"c":alts.index(c),"k":k})
data=json.dumps(out,ensure_ascii=False)
html=open('tpl.html').read().replace('__DATA__',data)
open('../questoes.html','w').write(html)
import collections;print(collections.Counter('ABCDE'[q['c']] for q in out))
