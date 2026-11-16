# Gera ../questoes.html a partir de q.py + tpl.html.
# Edite as questões em q.py e o layout em tpl.html, depois rode: python3 gen.py
import json, collections, html as h

exec(open("q.py", encoding="utf-8").read())

def esc(s):
    return h.escape(s or "", quote=False)

out, gid, prev = [], 0, object()
assert Q, "q.py precisa definir a lista Q"
for i, item in enumerate(Q):
    assert len(item) == 5, f"item {i+1} deve ser (materia, texto, enunciado, C|E, comentario)"
    m, t, e, c, k = item
    assert c in ("C", "E"), f"item {i+1}: gabarito deve ser C ou E, veio {c!r}"
    assert m and e and k, f"item {i+1}: materia, enunciado e comentario sao obrigatorios"
    if t != prev:
        gid += 1
        prev = t
    out.append({"id": i + 1, "m": esc(m), "t": esc(t), "e": esc(e), "c": c, "k": esc(k), "g": gid})

cont_m = collections.Counter(q["m"] for q in out)
cont_c = collections.Counter(q["c"] for q in out)
print(f"{len(out)} itens")
for m, n in cont_m.most_common():
    print(f"  {m}: {n}")
print(f"gabarito C={cont_c['C']} E={cont_c['E']}")

data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
html = open("tpl.html", encoding="utf-8").read().replace("__DATA__", data)
open("../questoes.html", "w", encoding="utf-8").write(html)
print("gerado: ../questoes.html")
