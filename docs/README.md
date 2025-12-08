# kanoa-mlops Documentation

This directory contains the documentation for the `kanoa-mlops` infrastructure.

## Structure

### `source/` (Sphinx Documentation)

The official documentation is built using Sphinx from the files in `source/`.
To build the documentation locally:

```bash
cd docs
make html
```

The built HTML files will be in `build/html/`.

### `planning/`

Living documents with checklists and roadmaps.

- **[Infrastructure_Spec.md](planning/Infrastructure_Spec.md)**: Core infrastructure specification and roadmap

### `analysis/` (Future)

Static, dated snapshots of architectural decisions and investigations.

## Documentation Philosophy

- **Planning docs**: Use `[✓]` for completed items, `[ ]` for planned items
- **Analysis docs**: Dated snapshots (e.g., `20251130-vllm-performance-analysis.md`)
- **Keep it concise**: Infrastructure docs should be scannable and actionable
