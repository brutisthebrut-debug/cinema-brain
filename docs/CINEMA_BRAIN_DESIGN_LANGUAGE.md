# Cinema Brain Design Language

## Design intent

Cinema Brain should feel cinematic, intimate, intelligent, and carefully curated.

The visual reference is not enterprise analytics software. The intended emotional territory sits between:

- Letterboxd's film literacy
- Obsidian's focused knowledge-work atmosphere
- A24's restraint and cultural confidence
- Criterion Collection booklets and archival film notes

The result should feel like entering a private screening room or film archive where meaning is being restored, not like opening an admin console.

## Core principles

### Dark, not noisy

Use deep charcoal and near-black surfaces with restrained contrast. Avoid excessive gradients, glowing effects, or dense widget grids.

### Editorial, not corporate

Favor strong film titles, thoughtful spacing, readable rationale, and clear hierarchy. The film and the evidence should dominate the screen.

### Focused work

One primary decision at a time. Progress should be visible, but the interface should not compete for attention.

### Quiet confidence

Use motion, color, and labels sparingly. Important states should be unmistakable without feeling loud.

### Evidence is beautiful

Rationales, confidence, sources, disagreement, and provenance are first-class interface material—not hidden technical metadata.

## Visual foundation

### Palette

- Background: near black or charcoal
- Elevated surfaces: subtle warm charcoal
- Primary text: warm off-white
- Secondary text: muted gray
- Accent: restrained amber or aged gold
- Approval: deep, muted green
- Edit or caution: ochre
- Rejection or conflict: dark red

Exact color tokens may evolve, but the relationship and restraint should remain consistent.

### Typography

- System or highly readable sans serif for application controls
- Optional editorial serif for selected headings or film-title moments only
- Strong title hierarchy
- Comfortable line height for rationales and evidence
- Avoid tiny metadata where the reviewer must strain

### Shape and depth

- Soft but not playful corner radii
- Thin borders rather than heavy shadows
- Layering should suggest archival cards, screening notes, or index records
- Avoid generic SaaS card walls

## Interaction language

### Primary decisions

Use direct verbs:

- Approve
- Edit
- Reject
- Promote
- Validate
- Review conflict

Do not hide irreversible or truth-changing actions behind vague labels such as “Continue.”

### Progress

Progress should communicate meaningful work:

- assignments reviewed
- films completed
- unresolved conflicts
- promotion readiness
- validation status

Avoid vanity metrics.

### Editing

When a reviewer edits a trait, show the candidate value beside the reviewed value. Preserve the original rationale and make the review note visible.

### Errors

Errors should explain the contract violation and how to resolve it. They should not erase entered review work.

## First implemented pattern

The canonical trait review UI establishes the initial pattern:

- single-film context
- one trait assignment per view
- candidate value and confidence
- visible source and rationale
- approve, edit, and reject actions
- guarded fields for edits and rejections
- progress indicator
- local autosave
- exact CSV contract export

Future Studio surfaces should reuse these patterns rather than introducing unrelated visual systems.

## Accessibility and mobile

- Mobile-first layouts for review tasks
- Large, reliable touch targets
- Visible focus states
- Sufficient contrast
- No meaning conveyed by color alone
- Clear labels for values and confidence
- Keyboard support when the interface becomes a regular desktop workflow

## What to avoid

- enterprise dashboard aesthetics
- excessive charts before the underlying metric is actionable
- gamification of review truth
- neon cyberpunk styling
- ornamental film-strip clichés
- dense sidebars with inactive future features
- public-social patterns inside the internal Studio
- animation that slows repetitive review work

## Design test

Before shipping a Studio screen, ask:

1. Is the film or intelligence task the visual focus?
2. Is the next decision obvious?
3. Can the reviewer inspect why the candidate exists?
4. Does the interface preserve uncertainty and disagreement?
5. Does it feel calm enough for repeated, careful work?
6. Does it reuse the existing review contract and interaction language?
