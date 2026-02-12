# AGENTIC DEVOPS LOOP — OPERATIV DOKUMENTATION

> Single source of truth för grupp-ett-github (SEJFA).
> Senast verifierad: 2026-02-11 mot faktisk repo-audit.
> Alla påståenden i detta dokument är verifierade mot repots faktiska innehåll om inte markerade med ⚠️.

---

## 1. SYSTEMÖVERSIKT

### Vad det ÄR

En Flask-applikation ("SEJFA") med en agentic DevOps-loop byggd ovanpå Claude Code. Hela idén är att automatisera flödet från Jira-ticket till deploy utan manuell intervention.

### Vad som BORDE hända

```
Jira ticket (GE-xxx)
    → /start-task hämtar ticket, skapar branch, sätter upp CURRENT_TASK.md
    → Ralph Loop (TDD: red → green → refactor, repeat)
    → finish-task körs AUTOMATISKT som del av loopen (verify, commit, push, PR, merge, Jira)
    → CI kör (lint + test)
    → Jules AI reviewar PR
    → gh pr merge --squash (direkt efter CI passerar)
    → deploy.yml bygger Docker → ACR → Azure Container Apps
    → post_deploy_verify.yml hälsokontroll (5 retries × 10s)
    → OK? → Jira-kommentar "✅ Deployed & Verified"
    → FAIL? → Rollback till föregående revision + Jira-kommentar "❌ Rolled back"
    → Live (verified)
```

### Vad som FAKTISKT händer

```
Jira ticket (GE-xxx)
    → /start-task ✅ funkar (med reservation, se CURRENT_TASK.md-problemet)
    → Ralph Loop ✅ funkar (stop-hook är fail-closed och solid)
    → finish-task ✅ FIXAT — körs automatiskt som del av start-task loopen (ingen separat /finish-task)
    → CI kör ✅ funkar (ci.yml + ci_branch.yml)
    → Jules AI reviewar ❓ OVERIFIERAT — alla 4 Jules-workflows beror på en action-referens som kan vara ogiltig
    → Merge ✅ FIXAT — finish-task kör gh pr checks --watch + gh pr merge --squash
    → deploy.yml ✅ triggas av merge till main
    → post_deploy_verify.yml ✅ NY — hälsokontroll + rollback + Jira-uppdatering
    → Monitor-dashboard ❌ DÖD — trasiga imports, får inga uppdateringar
```

---

## 2. DETALJERAD STATUSRAPPORT

### ✅ VAD SOM FUNKAR

#### Ralph Loop (stop-hook)
Filen: `.claude/hooks/stop-hook.py`

Stop-hooken är **fail-closed** och väldesignad:
- Tre persistence-mekanismer: `.ralph_loop_active`, `ralph-state.json`, `.git/info/ralph-loop-active.json`
- Återskapar borttagna flaggfiler mitt i loopen (förhindrar bypass)
- Enforcar på Jira-style branches (`feature/GE-*`) även utan explicit loop-flagga
- Max 25 iterationer med auto-WIP-commit + draft PR som säkerhetsventil
- Ogiltig JSON / tom input medan loop är aktiv = blockerar (förhindrar bypass)
- Exit code 2 = "fortsätt jobba" när loop är aktiv

#### CI Pipeline
Filer: `.github/workflows/ci.yml`, `.github/workflows/ci_branch.yml`

- `ci.yml`: Triggas på push till `main` och PRs mot `main`. Kör ruff lint + pytest på Python 3.10-3.13. Coverage gate 70%.
- `ci_branch.yml`: Samma sak men för non-main branches.
- Fungerar som förväntat.

#### Deploy Pipeline
Fil: `.github/workflows/deploy.yml`

- Triggas på push till `main`
- Bygger Docker image → pushar till Azure Container Registry → deployer till Azure Container Apps
- Fungerar — MEN triggas bara om något mergas till main, vilket inte sker automatiskt.

#### Branch Cleanup
Fil: `.github/workflows/cleanup-branches.yml`

- **OBS: Inte daglig automatik.** Manuell `workflow_dispatch` med krav på att skriva "DELETE ALL BRANCHES" som confirmation. En nuke-knapp, inte schemalagd städning.
- Har dry-run-läge och `production` environment gate.

#### Applikationsarkitektur
Tre-lager Flask-app med ren separation:
- `src/sejfa/newsflash/` — data/business/presentation (SQLAlchemy)
- `src/expense_tracker/` — data/business/presentation (in-memory)
- `src/sejfa/core/` — admin auth, subscriber service (legacy)
- `src/sejfa/monitor/` — monitor service + routes (server-sidan finns men hooks skickar inget)

243 tester. SQLAlchemy + Flask-Migrate. Gunicorn.

---

### ❌ VAD SOM INTE FUNKAR

#### Problem 1: Claude avslutar innan /finish-task körs

**Symptom:** Claude Code tycker den är klar (tester passerar, kod skriven) och avslutar sessionen. Stop-hooken fångar inte upp detta. Ingen PR skapas.

**Status:** ✅ LÖST (2026-02-11). Grundorsaken var att finish-task existerade som separat skill — agenten tolkade implementation och delivery som två separata steg med human-in-the-loop. Fix: start-task SKILL.md uppdaterad med explicit instruktion att finish-task steg 1-11 körs automatiskt som del av Ralph Loop. finish-task SKILL.md markerad som referensdokument (ska aldrig triggas manuellt).

#### Problem 2: PRs mergas aldrig automatiskt

**Symptom:** Även om finish-task lyckas skapa en PR, stannar flödet. Ingen merge sker.

**Status:** ✅ LÖST (2026-02-11). Grundorsaken var att `gh pr merge --auto --squash` kräver branch protection på main (repot har ingen). Kommandot failade tyst. Fix: Ersatt med `gh pr checks --watch` (väntar på CI) + `gh pr merge --squash` (mergar direkt). Om merge failar (t.ex. review krävs) loggas varning men Jira-uppdatering fortsätter.

#### Problem 3: Monitor-dashboard är död

**Symptom:** Dashboarden på `gruppett.fredlingautomation.dev/static/monitor.html` visar inget.

**Analys:**
Två hooks ska skicka uppdateringar till dashboarden:
- `.claude/hooks/monitor_hook.py` (PreToolUse) — ska skicka tool-use events
- `.claude/hooks/stop-hook.py` — ska skicka status vid stopp

Båda importerar från `monitor_client.py` som ligger i samma mapp. ~~Men **Python hittar inte filen** pga trasig import-path.~~ ✅ Import-path fixad (2026-02-11): Båda hooks har nu `sys.path.insert(0, str(HOOKS_DIR))` innan importen.

**Kvarvarande problem:** `monitor_client.py` pratar med `http://localhost:5000` — fungerar bara om Flask-appen körs på samma maskin som Claude Code. I Cowork-sandbox eller CI-kontext nås servern aldrig. Fail-silent dock (try/except), så det skadar inget.

#### Problem 4: Jules-integration är overifierad

**Symptom:** Oklart om Jules AI-review fungerar överhuvudtaget.

**Analys:**
4 workflows beror på `google-labs-code/jules-action@v1.0.0`:
- `jules_review.yml` — AI code review på PRs
- `jules_health_check.yml` — daglig health ping
- `self_healing.yml` — auto-fix vid CI-fail
- `self_heal_pr.yml` — manuell self-heal

Problem:
1. **Action-referensen kan vara ogiltig** — `google-labs-code/jules-action@v1.0.0` kanske inte existerar eller har bytt namn. Om den inte finns failar ALLA Jules-workflows.
2. ~~**`scripts/preflight.sh` SAKNAS**~~ ✅ LÖST — filen finns nu (`scripts/preflight.sh`, 225 rader). CI-aware: skippar Jira/GitHub auth i CI-kontext.
3. **Säkerhetsrisk i `self_healing.yml`** — har `contents: write` permissions + checkout av `head_sha` från potentiella forks = RCE-risk.
4. ~~**`jules_review.yml` saknade `statuses: write`** — "Set Jules review status" fick 403 vid commit status API-anrop.~~ ✅ LÖST (2026-02-11): `statuses: write` tillagd i permissions.
5. ~~**Jules recursive loop** — Jules reviewar PR → skapar findings-PR → triggar sig själv → oändlig kedja (#320→#324→#325→...→#330).~~ ✅ LÖST (2026-02-11): Lagt till `if`-guard som skippar PRs från `jules-*` branches och `google-labs-jules[bot]` actor.

**Status:** ⚠️ Kräver verifiering. Kolla GitHub Actions run-historik för att se om Jules-workflows faktiskt har körts framgångsrikt. Commit status-permission och recursion-guard är fixade.

#### Problem 5: CURRENT_TASK.md-inkonsistens

**Symptom:** Hooks och skills pekar på olika filer.

**Analys:**
- `start-task` SKILL.md populerar `CURRENT_TASK.md`
- `prevent-push.py` hook läser `CURRENT_TASK.md` (rot-mappen)
- Det fanns TVÅ filer: `CURRENT_TASK.md` (GE-49) och en gammal kopia i `docs/` (GE-40)
- De beskriver OLIKA tasks

**Fix:** Bestäm EN plats. Uppdatera alla skills och hooks att peka på samma fil.

---

### ⚠️ SÄKERHETSPROBLEM

1. **Hardcoded credentials** — `src/sejfa/core/admin_auth.py` har default admin/admin123
2. **`self_healing.yml` RCE-risk** — `contents: write` + checkout av untrusted code
3. **Flask secret key** — troligen hardcoded i `app.py` (ej verifierat i audit men flaggat tidigare)

---

## 3. FILKARTA

### Workflows (8 st)
| Fil | Status | Funktion |
|-----|--------|----------|
| `ci.yml` | ✅ | Lint + test på PRs/push till main |
| `ci_branch.yml` | ✅ | Lint + test på feature branches |
| `deploy.yml` | ✅ (men triggas aldrig pga ingen merge) | Docker → ACR → Azure |
| `post_deploy_verify.yml` | ✅ NY | Hälsokontroll → rollback vid fail → Jira-uppdatering |
| `cleanup-branches.yml` | ✅ | Städar mergade branches dagligen |
| `jules_review.yml` | ❓ Overifierad (✅ statuses: write fixad, ✅ recursion guard tillagd) | AI code review på PRs |
| `jules_health_check.yml` | ❓ Overifierad (✅ preflight.sh finns nu) | Daglig Jules health ping |
| `self_healing.yml` | ❓ Overifierad + säkerhetsrisk | Auto-fix vid CI-fail |
| `self_heal_pr.yml` | ❓ Overifierad | Manuell self-heal per PR |

### Hooks (4 st)
| Fil | Status | Funktion |
|-----|--------|----------|
| `stop-hook.py` | ✅ Logiken funkar, ✅ monitor-import fixad | Ralph Loop enforcer |
| `monitor_hook.py` | ✅ Import fixad, ❌ server onåbar i sandbox/CI | Ska skicka tool-use events till dashboard |
| `monitor_client.py` | ✅ Hittas av hooks (sys.path fix), ❌ localhost:5000 onåbar | HTTP-klient för monitor API |
| `prevent-push.py` | ⚠️ Läser fel CURRENT_TASK.md | Blockerar push vid no-push markers |

### Skills (2 st)
| Fil | Status | Funktion |
|-----|--------|----------|
| `start-task/SKILL.md` | ✅ Entry point för hela loopen | Hämtar Jira ticket, skapar branch, startar Ralph Loop inkl. finish-task |
| `finish-task/SKILL.md` | ✅ Referensdokument (triggas aldrig manuellt) | Verifierar kvalitet, skapar PR, väntar CI, mergar, uppdaterar Jira |

### Scripts (3 st)
| Fil | Status | Funktion |
|-----|--------|----------|
| `scripts/ci_check.sh` | ✅ | Lokal CI-simulering |
| `scripts/classify_failure.py` | ✅ (kod ok, beroende på Jules) | Klassificerar CI-fel |
| `scripts/jules_payload.py` | ✅ (kod ok, beroende på Jules) | Bygger Jules-payload |
| `scripts/preflight.sh` | ✅ Finns (CI-aware) | Refereras av jules_health_check.yml |

### Docs (viktigast)
| Fil | Status | Beskrivning |
|-----|--------|-------------|
| `docs/AGENTIC_DEVOPS_LOOP.md` | 📌 DENNA FIL | Single source of truth |
| `docs/jules-playbook.md` | ❓ Overifierad mot workflows | Jules drifthandbok |
| `docs/DEPLOYMENT.md` | ⚠️ Cloudflare Tunnel-specifik | Deploy-guide |
| `CURRENT_TASK.md` (rot) | ⚠️ Inkonsistent med docs/ | Aktiv task (GE-49) |
| Tidigare `docs/`-kopia | ✅ Borttagen | Tidigare dubblett av task-fil |

---

## 4. INSTRUKTIONER FÖR AI-AGENTER

### För Claude Code (implementation)
1. Läs DENNA fil först — den beskriver verkligheten
2. `.claude/CLAUDE.md` har kodstil och arkitekturregler
3. Skills finns i `.claude/skills/` — `/start-task` är entry point, finish-task körs automatiskt som del av loopen
4. Stop-hooken fungerar — lita på den, finish-task körs automatiskt (trigga ALDRIG `/finish-task` manuellt)
5. Monitor-hooks skickar INGET just nu — ignorera monitor-uppdateringar tills import-fixen är på plats

### För Jules (code review)
1. `docs/jules-playbook.md` finns men är ⚠️ OVERIFIERAD
2. Payload byggs av `scripts/jules_payload.py`
3. Fel klassificeras av `scripts/classify_failure.py`
4. Om `google-labs-code/jules-action@v1.0.0` inte fungerar — inget av detta spelar roll

### För Cockpit-Claude (orchestration)
1. Lita BARA på denna fil för systembeskrivning
2. Repot finns på: `https://github.com/itsimonfredlingjack/grupp-ett-github.git`
3. Förväxla INTE med Simons privata repo: `https://github.com/itsimonfredlingjack/agentic-dev-loop-w-claude-code-and-github-actions.git`
4. Deploy sker via Cloudflare Tunnel → `gruppett.fredlingautomation.dev`

---

## 5. PRIORITERAD FIX-LISTA

| # | Problem | Svårighetsgrad | Impact |
|---|---------|---------------|--------|
| 1 | ~~Auto-merge saknas~~ | ✅ LÖST | finish-task kör `gh pr checks --watch` + `gh pr merge --squash` |
| 2 | ~~Monitor imports trasiga~~ | ✅ LÖST (sys.path fix redan applicerad) | Dashboard nås ej i sandbox/CI men imports funkar |
| 3 | CURRENT_TASK.md inkonsistens | Enkel (bestäm en plats) | Skills och hooks tittar på olika filer |
| 4 | ~~preflight.sh saknas~~ | ✅ LÖST (filen finns, CI-aware) | Jules health check borde fungera |
| 5 | Verifiera Jules action-referens | Kolla Actions-historik | Om ogiltig funkar inget Jules-relaterat |
| 6 | ~~Claude avslutar innan finish-task~~ | ✅ LÖST | finish-task inlinad i start-task loopen |
| 7 | self_healing.yml säkerhetsrisk | Medium (ta bort contents: write) | RCE-risk |
| 8 | Hardcoded credentials | Medium | Säkerhetsrisk |
| 9 | ~~Jules 403 vid commit status~~ | ✅ LÖST | `statuses: write` tillagd i jules_review.yml |
| 10 | ~~Post-deploy verification saknas~~ | ✅ LÖST | `post_deploy_verify.yml` — hälsokontroll + rollback + Jira |
| 11 | ~~Jules skapar PRs istf kommentarer~~ | ✅ LÖST | jules-action ersatt med direkt Jules API (session utan automationMode) |

---

## 6. CHANGELOG

| Datum | Ändring |
|-------|---------|
| 2026-02-11 | Skapad baserat på fullständig repo-audit. Ersätter alla tidigare fragmenterade docs som operativ referens. |
| 2026-02-11 | Fix #1: finish-task merge — `--auto` ersatt med `pr checks --watch` + direkt `--squash` merge. |
| 2026-02-11 | Fix #6: finish-task inlinad i start-task — ingen human-in-the-loop mellan implementation och delivery. |
| 2026-02-11 | Fix #9: jules_review.yml — `statuses: write` tillagd för commit status API. |
| 2026-02-11 | Fix #10: jules_review.yml — recursion guard: skippa `jules-*` branches och `google-labs-jules[bot]` actor. |
| 2026-02-12 | Fix #11: jules-action ersatt med direkt Jules API-anrop. 30 spam-PRs stängda. |
| 2026-02-12 | Fix #10: post_deploy_verify.yml — closed-loop deploy verification med hälsokontroll, rollback och Jira-uppdatering. |
