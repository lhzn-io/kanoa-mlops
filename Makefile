# kanoa-mlops Makefile
# Infrastructure and development commands

.PHONY: help setup setup-user setup-dev lint format test clean docs
.PHONY: deploy destroy status ssh logs stop start list switch my-ip cost

# =============================================================================
# Help
# =============================================================================

help:
	@echo "kanoa-mlops Commands"
	@echo "===================="
	@echo ""
	@echo "Infrastructure (GCP GPU):"
	@echo "  make infra-setup        - First-time Terraform setup"
	@echo "  make deploy-molmo       - Deploy vLLM with Molmo-7B (~\$$0.70/hr)"
	@echo "  make deploy-gemma3-4b   - Deploy vLLM with Gemma 3 4B"
	@echo "  make deploy-gemma3-12b  - Deploy vLLM with Gemma 3 12B"
	@echo "  make deploy-gemma3-27b  - Deploy vLLM with Gemma 3 27B"
	@echo "  make deploy-llama3-8b   - Deploy vLLM with Llama 3 8B"
	@echo "  make destroy            - Destroy current deployment"
	@echo "  make status             - Show deployment status"
	@echo "  make stop               - Stop instance (save costs)"
	@echo "  make start              - Start stopped instance"
	@echo "  make clean-infra        - Destroy ALL deployments"
	@echo ""
	@echo "Local Services:"
	@echo "  Use the 'kanoa' CLI for local services:"
	@echo "    kanoa serve ollama"
	@echo "    kanoa serve monitoring"
	@echo "    kanoa serve vllm-gemma"
	@echo "    kanoa stop"
	@echo ""
	@echo "Development:"
	@echo "  make setup-user         - Install user dependencies (pip)"
	@echo "  make setup-dev          - Install dev environment (conda + tools)"
	@echo "  make setup              - Alias for setup-dev"
	@echo "  make lint               - Run linting checks (ruff, mypy, shellcheck)"
	@echo "  make format             - Auto-format code with ruff"
	@echo "  make test               - Run smoke tests"
	@echo "  make test-ollama        - Run Ollama integration tests"
	@echo "  make gpu-probe          - Probe GPU and display metadata"
	@echo "  make clean              - Remove temp files"
	@echo ""
	@echo "Utilities:"
	@echo "  make my-ip              - Show your IP for firewall config"
	@echo "  make cost               - Show cost estimates"
	@echo "  make list               - List all deployments"

# =============================================================================
# Variables
# =============================================================================

TF_DIR := infrastructure/gcp
PRESETS_DIR := $(TF_DIR)/presets

# =============================================================================
# Development Commands
# =============================================================================

setup-user:
	@echo "Installing user dependencies..."
	pip install -r requirements.txt
	@echo ""
	@echo "Done! You can now run the example notebooks."
	@echo "For GCP deployment, also install:"
	@echo "  - terraform: https://developer.hashicorp.com/terraform/install"
	@echo "  - gcloud:    https://cloud.google.com/sdk/docs/install"

setup-dev:
	@echo "Creating/updating conda environment..."
	micromamba create -f environment.yml || micromamba update -f environment.yml --prune
	@echo ""
	@echo "Done! Activate with: micromamba activate kanoa-mlops"

setup: setup-dev

lint:
	@echo "Running ruff check..."
	ruff check .
	@echo ""
	@echo "Running ruff format check..."
	ruff format --check .
	@echo ""
	@echo "Running mypy..."
	mypy kanoa_mlops tests
	@echo ""
	@echo "Running shell linting (if installed)..."
	-shellcheck scripts/*.sh
	@echo ""
	@echo "Validating notebook JSON..."
	@python3 -c "import json; json.load(open('examples/quickstart-molmo-gcp.ipynb'))" && echo "  quickstart-molmo-gcp.ipynb: OK"
	@python3 -c "import json; json.load(open('examples/quickstart-gemma3-gcp.ipynb'))" && echo "  quickstart-gemma3-gcp.ipynb: OK"
	@python3 -c "import json; json.load(open('examples/demo-molmo-7b-egpu.ipynb'))" && echo "  demo-molmo-7b-egpu.ipynb: OK"
	@python3 -c "import json; json.load(open('examples/demo-gemma-3-12b-egpu.ipynb'))" && echo "  demo-gemma-3-12b-egpu.ipynb: OK"

format:
	@echo "Running ruff check with auto-fix..."
	ruff check --fix .
	@echo ""
	@echo "Running ruff format..."
	ruff format .

test:
	@echo "Running infrastructure validation..."
	@if command -v terraform >/dev/null 2>&1; then \
		cd infrastructure/gcp && terraform validate; \
	else \
		echo "  terraform not found - skipping"; \
	fi
	@echo "Running unit tests..."
	@micromamba run -n kanoa-mlops pytest tests/unit -v

gpu-probe:
	@echo "Probing for NVIDIA GPUs..."
	@nvidia-smi

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf docs/_build

docs:
	@echo "Building documentation..."
	sphinx-build -b html docs docs/_build/html
	@echo "Docs built in docs/_build/html"

# =============================================================================
# Infrastructure Setup
# =============================================================================

infra-setup:
	@echo "Setting up kanoa-mlops infrastructure..."
	@if [ ! -f $(TF_DIR)/terraform.tfvars ]; then \
		cp $(TF_DIR)/terraform.tfvars.example $(TF_DIR)/terraform.tfvars; \
		echo ""; \
		echo "Created terraform.tfvars - please edit with your values:"; \
		echo "  - project_id: your GCP project ID"; \
		echo "  - allowed_source_ranges: your IP (run 'make my-ip')"; \
		echo ""; \
		echo "Then run: make deploy-molmo (or other model)"; \
	else \
		echo "terraform.tfvars already exists"; \
	fi
	@cd $(TF_DIR) && terraform init -upgrade

# =============================================================================
# Deploy Commands (Model Presets)
# =============================================================================

deploy-molmo:
	@$(MAKE) _deploy WORKSPACE=molmo PRESET=molmo-7b

test-ollama:
	@echo "Running Ollama integration tests..."
	@python3 tests/integration/test_ollama_gemma3.py


deploy-gemma3-4b:
	@$(MAKE) _deploy WORKSPACE=gemma3-4b PRESET=gemma3-4b

deploy-gemma3-12b:
	@$(MAKE) _deploy WORKSPACE=gemma3-12b PRESET=gemma3-12b

deploy-gemma3-27b:
	@$(MAKE) _deploy WORKSPACE=gemma3-27b PRESET=gemma3-27b

deploy-llama3-8b:
	@$(MAKE) _deploy WORKSPACE=llama3-8b PRESET=llama3-8b

# Internal: Generic deploy with workspace isolation
_deploy:
	@if [ ! -f $(TF_DIR)/terraform.tfvars ]; then \
		echo "Error: terraform.tfvars not found. Run 'make infra-setup' first."; \
		exit 1; \
	fi
	@echo "Deploying $(WORKSPACE)..."
	@cd $(TF_DIR) && terraform workspace select $(WORKSPACE) 2>/dev/null || terraform workspace new $(WORKSPACE)
	@cd $(TF_DIR) && terraform apply -var-file=terraform.tfvars -var-file=presets/$(PRESET).tfvars -auto-approve
	@echo ""
	@echo "=========================================="
	@echo "Deployment complete! Use these endpoints:"
	@echo "=========================================="
	@cd $(TF_DIR) && terraform output -raw vllm_api_endpoint 2>/dev/null && echo ""
	@echo ""
	@echo "Auto-shutdown enabled: 30 min idle timeout"
	@echo "Run 'make destroy' when done to avoid charges."

# =============================================================================
# Destroy Commands
# =============================================================================

destroy:
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" = "default" ] || [ -z "$$WORKSPACE" ]; then \
		echo "No active deployment. Use 'make list' to see deployments."; \
		exit 1; \
	fi; \
	echo "Destroying $$WORKSPACE..."; \
	cd $(TF_DIR) && terraform destroy -var-file=terraform.tfvars -var-file=presets/$${WORKSPACE}.tfvars -auto-approve; \
	cd $(TF_DIR) && terraform workspace select default; \
	cd $(TF_DIR) && terraform workspace delete $$WORKSPACE 2>/dev/null || true
	@echo "Destroyed. No more charges for this deployment."

clean-infra:
	@echo "Destroying ALL deployments..."
	@cd $(TF_DIR) && for ws in $$(terraform workspace list | grep -v default | tr -d '* '); do \
		if [ -n "$$ws" ]; then \
			echo "Destroying workspace: $$ws"; \
			terraform workspace select $$ws; \
			terraform destroy -var-file=terraform.tfvars -var-file=presets/$${ws}.tfvars -auto-approve 2>/dev/null || true; \
			terraform workspace select default; \
			terraform workspace delete $$ws 2>/dev/null || true; \
		fi \
	done
	@echo "All deployments destroyed."

# =============================================================================
# Instance Management
# =============================================================================

status:
	@echo "kanoa-mlops Deployment Status"
	@echo "=============================="
	@cd $(TF_DIR) && terraform workspace list 2>/dev/null || echo "Terraform not initialized"
	@echo ""
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" != "default" ] && [ -n "$$WORKSPACE" ]; then \
		echo "Current: $$WORKSPACE"; \
		cd $(TF_DIR) && terraform output 2>/dev/null || echo "Not deployed"; \
	else \
		echo "No deployment selected. Run 'make deploy-<model>'"; \
	fi

list:
	@echo "Active deployments (workspaces):"
	@cd $(TF_DIR) && terraform workspace list 2>/dev/null | grep -v "default" || echo "  None"
	@echo ""
	@echo "GCP instances:"
	@gcloud compute instances list --filter="labels.project=kanoa-mlops" \
		--format="table(name,zone,status,networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null \
		|| echo "  (gcloud not configured or no instances)"

ssh:
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" = "default" ] || [ -z "$$WORKSPACE" ]; then \
		echo "No active deployment."; \
		exit 1; \
	fi; \
	cd $(TF_DIR) && eval $$(terraform output -raw ssh_command)

logs:
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" = "default" ] || [ -z "$$WORKSPACE" ]; then \
		echo "No active deployment."; \
		exit 1; \
	fi; \
	cd $(TF_DIR) && eval $$(terraform output -raw logs_command)

stop:
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" = "default" ] || [ -z "$$WORKSPACE" ]; then \
		echo "No active deployment."; \
		exit 1; \
	fi; \
	echo "Stopping instance (disk preserved)..."; \
	cd $(TF_DIR) && eval $$(terraform output -raw stop_command)
	@echo "Stopped. Charges: ~\$$0.15/hr (disk only). Run 'make start' to resume."

start:
	@WORKSPACE=$$(cd $(TF_DIR) && terraform workspace show 2>/dev/null); \
	if [ "$$WORKSPACE" = "default" ] || [ -z "$$WORKSPACE" ]; then \
		echo "No active deployment."; \
		exit 1; \
	fi; \
	echo "Starting instance..."; \
	cd $(TF_DIR) && eval $$(terraform output -raw start_command)
	@echo "Starting. Wait 2-5 min for vLLM to load model."

# =============================================================================
# Utilities
# =============================================================================

my-ip:
	@echo "Your IP: $$(curl -s ifconfig.me)/32"
	@echo ""
	@echo "Add to terraform.tfvars:"
	@echo '  allowed_source_ranges = ["'$$(curl -s ifconfig.me)'/32"]'

cost:
	@echo "Cost Estimates (L4 GPU, us-central1)"
	@echo "====================================="
	@echo ""
	@echo "Per Hour:"
	@echo "  Running:  ~\$$0.70/hr (compute + GPU)"
	@echo "  Stopped:  ~\$$0.05/hr (200GB SSD disk)"
	@echo "  Deleted:  \$$0"
	@echo ""
	@echo "Typical Usage:"
	@echo "  2-hr session:     ~\$$1.40"
	@echo "  Daily (2 hrs):    ~\$$28/month"
	@echo "  With auto-stop:   ~\$$15-20/month"
	@echo ""
	@echo "Auto-shutdown is enabled (30 min idle)."
	@echo "Run 'make destroy' after sessions to avoid disk charges."

switch:
	@echo "Available deployments:"
	@cd $(TF_DIR) && terraform workspace list 2>/dev/null
	@echo ""
	@read -p "Enter workspace name: " ws; \
	cd $(TF_DIR) && terraform workspace select $$ws
	@$(MAKE) status
