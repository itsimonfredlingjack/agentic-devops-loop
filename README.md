# 🚀 Mitt Flask-Projekt

Detta är ett skelett för att bygga en applikation med hjälp av AI.

---

## 📋 Mall för ny uppgift (Kopiera denna)

<details>
<summary><strong>👉 Klicka här för att hämta mallen</strong></summary>

### 1. Din Beskrivning (Fyll i detta på vanlig svenska)

**Vad ska vi bygga?**
> [T.ex: En app för att hålla koll på mina krukväxter.]

**Vad ska sparas i systemet?**
> [T.ex: Växtens namn, datum när jag vattnade senast, och en bildlänk.]

**Vad ska man kunna göra? (Funktioner)**
> 1. [T.ex: Jag vill kunna lägga till en ny växt.]
> 2. [T.ex: Listan ska visa vilka växter som behöver vattnas idag.]
> 3. [T.ex: Det ska inte gå att lägga in en växt utan namn.]

---

### 2. Instruktioner till AI (Rör ej dessa - detta garanterar godkänt)

**TO THE AI (CLAUDE CODE):**
You are an expert Python Architect. The user above has described an app idea in plain Swedish. Your job is to translate this simple request into a **strict enterprise-grade Flask application** according to the following non-negotiable constraints:

**Architecture (Locked):**
1.  **3-Layer Architecture:**
    * `app/data/`: Data models (Dataclasses) & Repositories.
    * `app/business/`: Pure Python Service classes (Business Logic). No Flask code here.
    * `app/presentation/`: Flask Blueprints, Routes, Templates.
2.  **TDD (Test Driven Development):**
    * You MUST write tests first.
    * Use `pytest` with `sqlite:///:memory:`.
3.  **Dependency Injection:**
    * Inject repositories into services, and services into routes.

**Process:**
1.  Analyze the user's "Vad ska sparas?" -> Create the Model.
2.  Analyze the "Vad ska man kunna göra?" -> Create Service methods and "Affärsregler" (Business Rules).
3.  Implement: Test -> Code -> Refactor.

**Definition of Done:**
- [ ] Project structure follows `app/data`, `app/business`, `app/presentation`.
- [ ] Unit tests cover the user's rules (Service layer).
- [ ] Integration tests cover the user's flows (Routes).
- [ ] Templates uses Swedish text for UI.

</details>
