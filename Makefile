# Central Server Infrastructure - Makefile
# Provides convenient commands for deployment and management

.PHONY: help install validate check deploy-all deploy-system deploy-infra deploy-backup deploy-apps clean

# Ansible vault options
VAULT_OPTS = --ask-vault-pass

# Default target
help: ## Show this help message
	@echo "Central Server Infrastructure - Available Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Examples:"
	@echo "  make install        # Install dependencies"
	@echo "  make validate       # Validate configuration"
	@echo "  make deploy-infra   # Deploy infrastructure services"
	@echo "  make deploy-all     # Full deployment"
	@echo "  make edit-secrets   # Edit encrypted secrets"
	@echo "  make view-secrets   # View encrypted secrets"
	@echo
	@echo "Note: Commands that access encrypted secrets will prompt for vault password"

install: ## Install Ansible dependencies
	@echo "📦 Installing Ansible dependencies..."
	pip install ansible
	ansible-galaxy install -r requirements.yaml
	@echo "✅ Dependencies installed"

validate: ## Validate configuration and connectivity
	@echo "🔍 Validating configuration..."
	./validate.sh

check: ## Run playbook in check mode (dry run)
	@echo "🧪 Running deployment check..."
	./deploy.sh check $(VAULT_OPTS)

deploy-system: ## Deploy system configuration
	@echo "🔧 Deploying system configuration..."
	./deploy.sh system $(VAULT_OPTS)

deploy-infra: ## Deploy infrastructure services
	@echo "🏗️ Deploying infrastructure services..."
	./deploy.sh infra $(VAULT_OPTS)

deploy-backup: ## Deploy backup services
	@echo "💾 Deploying backup services..."
	./deploy.sh backup $(VAULT_OPTS)

deploy-apps: ## Deploy application services
	@echo "📱 Deploying application services..."
	./deploy.sh apps $(VAULT_OPTS)

deploy-all: ## Deploy all services (full deployment)
	@echo "🚀 Running full deployment..."
	./deploy.sh all $(VAULT_OPTS)

update: ## Update service versions and redeploy
	@echo "🔄 Updating services..."
	git pull
	ansible-galaxy install -r requirements.yaml --force
	./deploy.sh check $(VAULT_OPTS)
	./deploy.sh all $(VAULT_OPTS)

status: ## Show service status
	@echo "📊 Service Status:"
	@ansible all -i production.yaml -m shell -a "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" -b $(VAULT_OPTS)

logs: ## Show recent logs for all services
	@echo "📋 Recent service logs:"
	@ansible all -i production.yaml -m shell -a "find /docker -name 'compose.yaml' -exec dirname {} \; | head -5 | xargs -I {} docker compose -f {}/compose.yaml logs --tail=10" -b $(VAULT_OPTS)

clean: ## Clean up temporary files
	@echo "🧹 Cleaning temporary files..."
	find . -name "*.retry" -delete
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

restart-service: ## Restart a specific service (usage: make restart-service SERVICE=traefik)
	@if [ -z "$(SERVICE)" ]; then \
		echo "❌ Please specify SERVICE (e.g., make restart-service SERVICE=traefik)"; \
		exit 1; \
	fi
	@echo "🔄 Restarting $(SERVICE)..."
	@ansible all -i production.yaml -m shell -a "cd /docker/$(SERVICE) && docker compose restart" -b $(VAULT_OPTS)

backup-config: ## Backup current configuration
	@echo "💾 Backing up configuration..."
	@BACKUP_DIR="backup-$$(date +%Y%m%d-%H%M%S)"; \
	mkdir -p "$$BACKUP_DIR"; \
	cp -r group_vars host_vars *.yaml "$$BACKUP_DIR/"; \
	echo "✅ Configuration backed up to $$BACKUP_DIR"

# Vault Management Commands
edit-secrets: ## Edit encrypted secrets file
	@echo "🔐 Editing secrets file..."
	./vault.sh edit

view-secrets: ## View encrypted secrets file
	@echo "👀 Viewing secrets file..."
	./vault.sh view

encrypt-file: ## Encrypt a file with ansible-vault (usage: make encrypt-file FILE=path/to/file)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify FILE (e.g., make encrypt-file FILE=secrets.yaml)"; \
		exit 1; \
	fi
	@echo "🔐 Encrypting $(FILE)..."
	./vault.sh encrypt $(FILE)

decrypt-file: ## Decrypt a file with ansible-vault (usage: make decrypt-file FILE=path/to/file)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify FILE (e.g., make decrypt-file FILE=secrets.yaml)"; \
		exit 1; \
	fi
	@echo "🔓 Decrypting $(FILE)..."
	./vault.sh decrypt $(FILE)

rekey-vault: ## Change vault password
	@echo "🔑 Changing vault password..."
	./vault.sh rekey
