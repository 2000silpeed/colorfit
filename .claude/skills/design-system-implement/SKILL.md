---
name: design-system-implement
description: Implement or refactor UI code to match the project's design-system artifacts. Use when building tokens, components, styles, or screens based on the generated design-system outputs.
allowed-tools: Read Glob Grep Bash Edit Write
paths:
  - "design-system/**"
  - "src/**"
  - "app/**"
  - "components/**"
  - "styles/**"
---

Before making changes:

1. Read `design-system/system_spec.md`.
2. Read `design-system/token_schema.json`.
3. Read `design-system/component_inventory.json`.

Implementation rules:

- Treat the design-system artifacts as the source of truth.
- Keep implementation aligned with the product's brand keywords and anti-keywords.
- Implement high-priority component families before medium-priority families.
- Reuse or extend primitives before adding net-new components.
- Preserve existing features, navigation entry points, and data flows unless removal is explicitly requested.
- Keep supported themes, breakpoints, and critical interaction states working while refactoring.
- Prefer semantic tokens over one-off hardcoded colors so theme support survives future changes.
- Default to the smallest viable surface refactor; do not rewrite the whole shell unless the task explicitly calls for it.
- If `token_schema.json` includes a curated color reference or palette roles, align color decisions to that input before inventing a new palette.
- Update nearby documentation or tests when implementation meaningfully changes.
- NEVER change layout properties (display, flex-direction, grid-template, position, width, height).
- NEVER change font-size or line-height to "fit the token scale." Existing sizes are tuned to the layout. Only replace when the token resolves to the exact same px. If no match, keep original + TODO.
- NEVER round spacing values to the nearest token — if no exact match, leave as-is with a TODO.

When finishing:

- State which artifact files guided the implementation.
- Mention any gaps between the requested UI and the current system artifacts.
- Mention any feature, theme, or layout risks that still need manual verification.
