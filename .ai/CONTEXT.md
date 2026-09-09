# AI Context Route

```yaml
schema_version: 1
context_repo: https://github.com/madebycli/master-context
project_id: helium-nix
source_repo: https://github.com/madebycli/helium-nix
context_root: projects/helium-nix/
entrypoint: projects/helium-nix/INDEX.md
```

## Mandatory AI behavior

Use this exact route. Validate against `REGISTRY.yaml`, read the declared entrypoint first, do not scan sibling project folders, reconcile durable context with verified repository reality before declaring work complete, and archive reusable prompts/plans/handoffs under `prompts/helium-nix/` when possible.
