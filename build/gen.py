# Gera ../questoes.html a partir de q.py + tpl.html.
# Edite as questões em q.py e o layout em tpl.html, depois rode: python3 gen.py
import json, collections, html as h

exec(open("q.py", encoding="utf-8").read())

BAS = {"Direito Constitucional", "Direito Administrativo"}

def fmt(s):
    s = h.escape(s or "", quote=False)
    return s.replace("[[pre]]", "<pre class='log'>").replace("[[/pre]]", "</pre>")

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
    out.append({
        "id": i + 1, "m": fmt(m), "t": fmt(t), "e": fmt(e), "c": c, "k": fmt(k),
        "g": gid, "bl": "Básicos" if m in BAS else "Específicos",
    })

cont_m = collections.Counter(q["m"] for q in out)
cont_c = collections.Counter(q["c"] for q in out)
cont_b = collections.Counter(q["bl"] for q in out)
print(f"{len(out)} itens · {gid} textos")
for m, n in cont_m.most_common():
    print(f"  {m}: {n}")
print(f"blocos: {dict(cont_b)}")
print(f"gabarito C={cont_c['C']} E={cont_c['E']}")
assert len(out) >= 120
assert abs(cont_c["C"] - cont_c["E"]) <= 4, "proporcao C/E deve ficar perto de 50/50"

data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
html = open("tpl.html", encoding="utf-8").read().replace("__DATA__", data)
open("../questoes.html", "w", encoding="utf-8").write(html)
print("gerado: ../questoes.html")
