# CURRENT TASK: GE-98

## Ticket Info
- **Jira ID:** GE-98
- **Branch:** feature/GE-98-green-organic
- **Type:** Task
- **Priority:** Medium
- **Status:** In Progress

## Summary
Green & Organic - "Botanical Garden / Organic Zen" Theme

## Description

<ticket>
This is the "Wow factor" theme. It shows the AI understands texture and mood. It should feel like a digital greenhouse.

**Maximal Change Title:** Reskin to "Botanical Garden / Organic Zen" theme

**Description:** Transform the interface into a lush, organic environment. It should feel less like software and more like a living terrarium.

- **Background:** A soft, pale sage green (#F1F8E9). Overlay a subtle "dappled sunlight" shadow effect (as if light is filtering through leaves).
- **Style/Feel:** Biophilic Design. Soft, natural, and tactile. Avoid sharp digital edges.
- **Colors:** A palette of deep forest greens (#2E7D32) for text, earthy terracotta (#D84315) for alerts, and soft fern green for success states.
- **Fonts:** Serif for headers (e.g., Merriweather or Playfair Display) to give an elegant, editorial look. Clean, rounded Sans-Serif for data.
- **Cards & Panels:** Cards should look like high-quality, thick paper or cardstock. Use soft, diffused drop shadows to lift them off the background. Rounded corners (20px radius).
- **Layout:** Connecting lines should be organic curves (bezier curves), resembling vines or stems. Use small leaf icons 🍃 instead of standard dots for nodes.
</ticket>

## Acceptance Criteria
- [ ] Background: soft pale sage green (#F1F8E9) with dappled sunlight shadow overlay effect
- [ ] Colors: deep forest green (#2E7D32) for text, terracotta (#D84315) for alerts, fern green for success
- [ ] Fonts: Serif (Merriweather/Playfair Display) for headers, rounded sans-serif for data
- [ ] Cards: paper/cardstock feel, soft diffused shadows, 20px border-radius
- [ ] Layout: bezier curve organic connecting lines, leaf 🍃 icons instead of dots for nodes
- [ ] Biophilic aesthetic: feels like a living terrarium/digital greenhouse
- [ ] All tests pass
- [ ] Linting passes

## Progress Log

| Iteration | Date | Action | Result |
|-----------|------|--------|--------|
| 1 | 2026-02-17 | Branch created, ticket fetched | ✅ |

## Files to Modify
- `src/sejfa/newsflash/presentation/templates/base.html` (main app base)
- `src/expense_tracker/templates/expense_tracker/base.html` (expense tracker base)

## Notes
- This is a theme/UI ticket - modifying Flask templates
- Similar pattern to GE-86 (cyber-glitch), GE-91 (claymorphism), GE-93 (napkin sketch)
