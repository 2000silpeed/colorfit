# Design System Artifacts

Place generated artifacts from `design-ontology-harness` in this directory.

Expected files:

- `system_spec.md`
- `token_schema.json`
- `component_inventory.json`
- `system_ontology.json`
- `components/component_specs.json` (optional, from build-components)
- `components/component_specs.md` (optional, human-readable version)

Important usage rule:

- treat these artifacts as alignment inputs, not a license for a full-shell rewrite
- preserve existing product features and entry points unless an explicit migration is requested
- validate supported themes and responsive states when applying visual refactors

Recommended sync source:

- a harness project output such as `build/system/blueprint/*`

Recommended mapping:

- `build/system/blueprint/system_spec.md` -> `design-system/system_spec.md`
- `build/system/blueprint/token_schema.json` -> `design-system/token_schema.json`
- `build/system/blueprint/component_inventory.json` -> `design-system/component_inventory.json`
- `build/system/blueprint/system_ontology.json` -> `design-system/system_ontology.json`
- `build/system/components/` -> `design-system/components/`
