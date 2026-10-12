# Deploy — status (2026-10-12)
NOT PUBLISHED YET. No CLI on this box is logged in (gh: not logged in; netlify/vercel/surge not installed or configured).
Tried: Netlify anonymous API (401), 0x0.st (uploads disabled), pagedrop.dev (approved, but the TLS connection was cut off by the box's network/proxy).

## Recommended path (needs a one-time login by Marcos)
1. `gh auth login` (Marcos's own GitHub account).
2. Publish:
   cd /workspace/anpd-estudo && git init -b main && git add index.html questoes.html && git commit -m "site"
   gh repo create anpd-estudo --public --source=. --push
   gh api -X POST repos/{owner}/anpd-estudo/pages -f "source[branch]=main" -f "source[path]=/"
   URL: https://<user>.github.io/anpd-estudo/ (no expiry)
3. Weekly redeploy: cd /workspace/anpd-estudo && git add -A && git commit -m "update $(date +%F)" && git push
4. Check: curl -s https://<user>.github.io/anpd-estudo/ | grep "Concurso ANPD 2026"; curl -s https://<user>.github.io/anpd-estudo/questoes.html | grep "Questões – Concurso ANPD"

## Questions page
questoes.html is GENERATED: edit build/q.py (questions) or build/tpl.html (layout), then run `cd build && python3 gen.py`. Publish index.html + questoes.html together (build/ need not be published).
