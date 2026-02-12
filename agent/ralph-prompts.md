# Ralph Loop Prompts - Mallar

Samling av beprövade prompts för olika typer av uppgifter.

## Standard Implementation Prompt

Används för nya features och generella implementationsuppgifter.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du implementerar en uppgift från Jira. Följ TDD:

1. LÄS kraven i CURRENT_TASK.md
2. SKRIV ett failing test
3. KÖR pytest -xvs - verifiera att testet FAILS
4. IMPLEMENTERA minimal kod för att passera
5. KÖR pytest -xvs - verifiera att testet PASSERAR
6. UPPDATERA CURRENT_TASK.md med framsteg

EFTER VARJE ITERATION:
- Logga i framstegstabellen
- Kryssa i avklarade acceptanskriterier

NÄR ALLA ACCEPTANSKRITERIER ÄR UPPFYLLDA:
1. git push -u origin HEAD
2. gh pr create --title '[JIRA-ID] Beskrivning' --body 'PR body'
3. Output: DONE

VIKTIGT: Ljug ALDRIG om completion!
" --completion-promise "DONE" --max-iterations 25
```

## Buggfix Prompt

Används för att fixa buggar med regression test.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du fixar en bugg. Följ denna process:

1. REPRODUCERA buggen (skriv ett test som demonstrerar den)
2. KÖR pytest - VERIFIERA att testet FAILS (bevisar buggen)
3. FIXA buggen med minimal kodändring
4. KÖR pytest - VERIFIERA att testet nu PASSERAR
5. KÖR hela testsuiten: pytest -xvs
6. UPPDATERA CURRENT_TASK.md

NÄR KLART:
- Alla tester passerar (inkl regression test)
- Buggen är reproducerbar via test
- Push + PR
- Output: FIXED
" --completion-promise "FIXED" --max-iterations 15
```

## Refactoring Prompt

Används för refaktorering utan nya features.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du refaktorerar kod. VIKTIGT: Ingen ny funktionalitet!

PROCESS:
1. KÖR pytest -xvs - alla tester MÅSTE passera INNAN du börjar
2. GÖR en LITEN refaktorering (en åt gången)
3. KÖR pytest -xvs - alla tester MÅSTE fortfarande passera
4. COMMITTA med tydligt meddelande
5. UPPDATERA CURRENT_TASK.md
6. REPETERA

TILLÅTNA REFAKTORERINGAR (välj EN per iteration):
- Extrahera funktion
- Byt namn för tydlighet
- Ta bort duplicering (DRY)
- Förenkla villkor
- Flytta kod till rätt modul

FÖRBJUDET:
- Lägga till nya features
- Ändra beteende
- Optimera i förtid

NÄR ALLA PUNKTER I CURRENT_TASK.md ÄR KLARA:
Output: REFACTORED
" --completion-promise "REFACTORED" --max-iterations 20
```

## Test-Only Prompt

Används för att öka testtäckning.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du ska skriva tester för befintlig kod. SKRIV INTE ny produktionskod!

PROCESS:
1. IDENTIFIERA otestade delar (kör coverage)
2. SKRIV test för EN funktion/metod
3. KÖR pytest -xvs - verifiera testet passerar
4. UPPDATERA coverage
5. UPPDATERA CURRENT_TASK.md

TEST-TYPER ATT INKLUDERA:
- Happy path (normalt flöde)
- Edge cases (gränsvärden)
- Error cases (felhantering)
- Integration (samverkan mellan moduler)

NÄR COVERAGE-MÅL UPPNÅTT:
Output: TESTED
" --completion-promise "TESTED" --max-iterations 15
```

## Documentation Prompt

Används för dokumentationsuppgifter.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du ska skriva/uppdatera dokumentation.

PROCESS:
1. LÄS befintlig kod och förstå den
2. SKRIV/UPPDATERA dokumentation enligt lista i CURRENT_TASK.md
3. VERIFIERA att dokumentationen är korrekt
4. COMMITTA med beskrivande meddelande

DOKUMENTATIONSTYPER:
- README: Översikt, installation, användning
- Docstrings: Google-stil för Python
- API docs: Endpoints, parametrar, responses
- Architecture: System design, dataflöde

KVALITETSKRAV:
- Tydlig och koncis
- Korrekt och uppdaterad
- Inkluderar exempel
- Läsbar för målgruppen

NÄR ALLA DOCS I CURRENT_TASK.md ÄR KLARA:
Output: DOCUMENTED
" --completion-promise "DOCUMENTED" --max-iterations 10
```

## API Endpoint Prompt

Används för att skapa nya API-endpoints.

```
/ralph-loop "
LÄS CURRENT_TASK.md FÖRST.

Du skapar en ny API-endpoint. Följ TDD:

1. SKRIV integrationstester för endpointen
   - Test för success case
   - Test för validation errors
   - Test för auth (om relevant)
2. KÖR pytest - verifiera FAILS
3. IMPLEMENTERA endpoint i Flask
4. KÖR pytest - verifiera PASSERAR
5. UPPDATERA CURRENT_TASK.md

ENDPOINT-KRAV:
- Input validation
- Proper HTTP status codes
- JSON response format
- Error handling
- Docstring med API doc

NÄR ALLA TESTER PASSERAR OCH ENDPOINT FUNGERAR:
Output: ENDPOINT_DONE
" --completion-promise "ENDPOINT_DONE" --max-iterations 20
```

## Tips för effektiva Ralph Loops

### 1. Sätt alltid --max-iterations
Förhindrar oändliga loopar vid problem.

### 2. Var specifik med completion promise
Exakt strängmatchning - `"DONE"` matchar inte `"Done"` eller `"done"`.

### 3. Uppdatera CURRENT_TASK.md konsekvent
Det är agentens minne mellan iterationer.

### 4. TDD är inte valfritt
Skriv ALLTID tester först - det fångar problem tidigt.

### 5. En sak åt gången
Bryt ner stora uppgifter i mindre steg.

### 6. Verifiera innan completion
Kör alltid tester innan du skriver `DONE`.

## Felsökning

### Loop avslutas för tidigt
- Kontrollera att completion promise inte finns i annan output
- Använd unika promises som `TASK_XYZ_DONE`

### Loop avslutas aldrig
- Kontrollera att promise outputtas korrekt
- Kolla att --max-iterations är satt
- Verifiera att uppgiften faktiskt är möjlig att slutföra

### Agent gör fel saker
- Gör prompten mer specifik
- Lägg till explicit FÖRBJUDET-sektion
- Dela upp i mindre uppgifter
