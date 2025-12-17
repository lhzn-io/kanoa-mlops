# Upgrading from Source

Since `kanoa-mlops` is currently in active development and not yet on PyPI, you may need to upgrade your project to use the latest changes from the `main` branch.

## Workflow

If you have a project (e.g., `chatty-buoy`) that depends on a local checkout of `kanoa-mlops`, follow these steps to upgrade:

### 1. Update the Source

Navigate to your local `kanoa-mlops` repository and pull the latest changes:

```bash
cd /path/to/kanoa-mlops
git pull origin main
```

### 2. Reinstall the Package

Activate your project's environment and reinstall `kanoa-mlops`. Using editable mode (`-e`) is recommended for development.

```bash
cd /path/to/your-project
conda activate your-project-env
pip install -e /path/to/kanoa-mlops
```

### 3. Update Infrastructure Templates

The core value of `kanoa-mlops` is the curated set of Docker templates. When these templates change upstream (e.g., bug fixes, new models), you must regenerate them in your project.

Run the `init` command with the `--force` flag to overwrite existing files in your `docker/` directory:

```bash
kanoa mlops init mlops --dir . --force
```

> ⚠️ **Warning**: This will overwrite any manual changes you've made to files in `docker/`. If you have customized your compose files, verify the changes with `git diff` before committing.

### 4. Restart Services

After updating the configurations, restart your services to apply the changes:

```bash
kanoa stop
kanoa serve
```
