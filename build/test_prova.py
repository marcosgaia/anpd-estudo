#!/usr/bin/env python3
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8766/questoes.html"
IDX = "http://127.0.0.1:8766/index.html"
CHROME = "/usr/bin/google-chrome"
errs = []

def ok(name, cond, detail=""):
    status = "OK" if cond else "FALHOU"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        errs.append(name + (": " + detail if detail else ""))

def listen(page):
    page.on("pageerror", lambda e: errs.append(f"JS: {e}") or print("  [JS]", e))
    def on_console(msg):
        if msg.type == "error":
            t = msg.text
            if "favicon" in t.lower() or "404" in t:
                return
            errs.append(f"console: {t}")
            print("  [console]", t)
    page.on("console", on_console)
    page.on("dialog", lambda d: d.accept())

def sw(page):
    return page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox","--disable-gpu"])
        context = browser.new_context()
        page = context.new_page()
        listen(page)

        print("1) Carrega e não tem erro de JS")
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function("() => typeof Q !== 'undefined' && Q.length===120")
        n = page.evaluate("() => Q.length")
        mats = page.evaluate("() => {const c={};Q.forEach(q=>c[q.m]=(c[q.m]||0)+1);return c}")
        ce = page.evaluate("() => {let C=0,E=0;Q.forEach(q=>q.c==='C'?C++:E++);return [C,E]}")
        bl = page.evaluate("() => {const c={};Q.forEach(q=>c[q.bl]=(c[q.bl]||0)+1);return c}")
        ok("120 itens", n==120, str(n))
        ok("matérias", mats.get("LGPD")==36 and mats.get("Segurança da Informação")==30 and mats.get("ANPD e Regulação")==22 and mats.get("Direito Constitucional")==16 and mats.get("Direito Administrativo")==16, str(mats))
        ok("C/E ~50/50", abs(ce[0]-ce[1])<=4, str(ce))
        ok("blocos 32+88", bl.get("Básicos")==32 and bl.get("Específicos")==88, str(bl))
        ok("UI Prova real", page.get_by_role("button", name="Iniciar Prova real").count()==1)

        print("2) Nota líquida (função de correção)")
        r = page.evaluate("""() => {
          const cases = {};
          function run(n, fn){
            modo='Simulado'; locked=false; cur=Q.slice(0,n); resp={}; fn();
            return stats().t;
          }
          cases.sete_menos_dois = run(10, () => {
            cur.forEach((q,i)=>{
              if(i<7) resp[q.id]=q.c;
              else if(i<9) resp[q.id]=(q.c==='C'?'E':'C');
            });
          });
          cases.tudo_branco = run(10, () => {});
          cases.cinco_erradas = run(5, () => {
            cur.forEach(q => { resp[q.id] = q.c==='C'?'E':'C'; });
          });
          cases.um_a_um = run(2, () => {
            resp[cur[0].id]=cur[0].c;
            resp[cur[1].id]=cur[1].c==='C'?'E':'C';
          });
          // blocos: 32 básicos certos, 2 específicos errados, resto branco
          modo='Prova real'; locked=false; cur=Q.slice(); resp={};
          Q.filter(q=>q.bl==='Básicos').forEach(q=>{resp[q.id]=q.c});
          const esp=Q.filter(q=>q.bl==='Específicos');
          resp[esp[0].id]=esp[0].c==='C'?'E':'C';
          resp[esp[1].id]=esp[1].c==='C'?'E':'C';
          cases.blocos=stats();
          return cases;
        }""")
        ok("7C-2E+1branco = 5", r["sete_menos_dois"]["liq"]==5 and r["sete_menos_dois"]["a"]==7 and r["sete_menos_dois"]["e"]==2 and r["sete_menos_dois"]["b"]==1, str(r["sete_menos_dois"]))
        ok("tudo em branco = 0", r["tudo_branco"]["liq"]==0 and r["tudo_branco"]["b"]==10, str(r["tudo_branco"]))
        ok("5 erradas = -5", r["cinco_erradas"]["liq"]==-5 and r["cinco_erradas"]["e"]==5, str(r["cinco_erradas"]))
        ok("1C-1E = 0", r["um_a_um"]["liq"]==0 and r["um_a_um"]["a"]==1 and r["um_a_um"]["e"]==1, str(r["um_a_um"]))
        B,E = r["blocos"]["B"], r["blocos"]["E"]
        ok("bloco Básicos 32", B["liq"]==32 and B["a"]==32 and B["tot"]==32, str(B))
        ok("bloco Específicos -2", E["liq"]==-2 and E["e"]==2 and E["b"]==86 and E["tot"]==88, str(E))
        ok("total 30", r["blocos"]["t"]["liq"]==30, str(r["blocos"]["t"]))

        print("3) Histórico antigo continua visível")
        page.evaluate("""() => {
          const old=[{d:'01/01/2026, 10:00:00',modo:'Simulado',mat:'Todas',a:8,n:10,tot:10}];
          const mid=[{d:'10/11/2026, 10:00:00',modo:'Simulado',mat:'LGPD',a:5,n:8,tot:10,e:3,b:2,liq:2,s:{}}];
          localStorage.setItem('anpdHist', JSON.stringify(old.concat(mid)));
        }""")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => typeof Q !== 'undefined' && Q.length===120")
        html = page.inner_text("#hist")
        ok("formato anterior", "formato anterior" in html and "8/10" in html, html[:200])
        ok("histórico com líquida", "2 (5C − 3E, 2 em branco)" in html, html[:400])

        print("4) Prova real: caderno, folha, correção só no final")
        page.get_by_role("button", name="Iniciar Prova real").click()
        page.wait_for_selector(".caderno")
        cad = page.inner_text(".caderno")
        ok("instruções do caderno", "Folha de Respostas" in cad and "CERTO" in cad and "ERRADO" in cad)
        ok("seção Básicos", "Conhecimentos Básicos" in cad)
        ok("seção Específicos", "Conhecimentos Específicos" in cad)
        ok("textos-base", "Texto 1" in cad and "Texto 21" in cad)
        ok("sem gabarito no início", "Gabarito:" not in cad and page.locator(".caderno .com").count()==0)
        ok("placar sem nota ainda", "nota líquida" not in page.inner_text("#placar").lower() or "aparece ao finalizar" in page.inner_text("#placar"))
        # mark via API then check folha paint before end
        page.evaluate("""() => {
          const q=cur[0];
          resp[q.id]=q.c;
          const w=cur[1];
          resp[w.id]=(w.c==='C'?'E':'C');
        }""")
        page.get_by_role("button", name="Folha de respostas").click()
        page.wait_for_selector(".folha")
        ok("folha com 120 linhas", page.locator(".frow").count()==120, str(page.locator(".frow").count()))
        ok("ainda sem correção na folha", page.locator(".bub.ok").count()==0 and page.locator(".bub.no").count()==0)
        page.get_by_role("button", name="Encerrar prova").click()
        page.wait_for_timeout(400)
        pl = page.inner_text("#placar")
        ok("nota no final", "nota líquida 0" in pl or "nota líquida 0" in pl.lower() or "líquida 0" in pl, pl)
        # 1C-1E + 118 blank = 0, with block scores
        ok("nota por bloco", "Conhecimentos Básicos" in pl and "Conhecimentos Específicos" in pl, pl)
        page.get_by_role("button", name="Caderno de prova").click()
        page.wait_for_selector(".caderno .com")
        ok("comentários no caderno após o fim", page.locator(".caderno .com").count()>=2, str(page.locator(".caderno .com").count()))
        hist = page.inner_text("#hist")
        ok("histórico Prova real", "Prova real" in hist and "Básicos" in hist, hist[:300])

        print("5) Layout 390px")
        for label, target, extra in [
            ("index", IDX, None),
            ("questoes estudo", URL, "estudo"),
            ("prova caderno", URL, "caderno"),
            ("prova folha", URL, "folha"),
        ]:
            pg = context.new_page()
            listen(pg)
            pg.set_viewport_size({"width":390,"height":844})
            if extra in ("caderno","folha"):
                pg.goto(URL, wait_until="domcontentloaded")
                pg.wait_for_function("() => typeof Q !== 'undefined'")
                pg.get_by_role("button", name="Iniciar Prova real").click()
                pg.wait_for_selector(".caderno")
                if extra=="folha":
                    pg.get_by_role("button", name="Folha de respostas").click()
                    pg.wait_for_selector(".folha")
            elif extra=="estudo":
                pg.goto(URL, wait_until="domcontentloaded")
                pg.wait_for_function("() => typeof Q !== 'undefined'")
                pg.get_by_role("button", name="Modo estudo").click()
                pg.wait_for_selector(".item")
            else:
                pg.goto(target, wait_until="domcontentloaded")
            m = sw(pg)
            ok(f"390 {label}", m["sw"] <= m["cw"]+1, str(m))
            pg.close()

        browser.close()

    print("\nResumo:", "PASSOU" if not errs else f"{len(errs)} falha(s)")
    for e in errs:
        print(" -", e)
    return 0 if not errs else 1

if __name__ == "__main__":
    raise SystemExit(main())
