# Central Server Infrastructure

This Ansible playbook deploys a complete Docker-based service stack on a central server, including reverse proxy, authentication, security, media services, backup, and monitoring.

## 🏗️ Architecture

The deployment consists of four main service layers:

1. **System Configuration** - Base system setup (Docker, networking, time sync)
2. **Infrastructure Services** - Core services (Traefik, Authentik, CrowdSec)
3. **Backup Services** - Data protection (BorgWarehouse, Borg)
4. **Application Services** - End-user applications (Media stack, Monitoring)

## 🚀 Quick Start

### Prerequisites

```bash
# Install Ansible and required collections
pip install ansible
ansible-galaxy install -r requirements.yaml
```

### Basic Deployment

```bash
# Deploy everything (first time setup) - will prompt for vault password
./deploy.sh all --ask-vault-pass

# Deploy only infrastructure services
./deploy.sh infra --ask-vault-pass

# Check what would change without applying
./deploy.sh check --ask-vault-pass
```

### Using Make Commands (Recommended)

```bash
# Install dependencies
make install

# Edit encrypted secrets (prompts for vault password)
make edit-secrets

# Deploy all services (prompts for vault password automatically)
make deploy-all

# Deploy specific service groups
make deploy-infra
make deploy-backup
make deploy-apps

# View service status
make status

# Show available commands
make help
```

## 📦 Services Included

### Infrastructure

- **Traefik** - Reverse proxy with automatic HTTPS
- **Authentik** - Authentication and SSO
- **CrowdSec** - Security and intrusion prevention

### Backup

- **BorgWarehouse** - Backup repository server
- **Borg** - Backup client configuration

### Applications

- **Media Stack** - Jellyfin, Jellyseer, Jellyplex-watched
- **Monitoring** - UptimeKuma, WUD (What's Up Docker)

## 🎯 Deployment Commands

The `deploy.sh` script provides convenient deployment commands:

| Command  | Description               | Example                            |
| -------- | ------------------------- | ---------------------------------- |
| `system` | System configuration only | `./deploy.sh system`               |
| `infra`  | Infrastructure services   | `./deploy.sh infra --check`        |
| `backup` | Backup services           | `./deploy.sh backup`               |
| `apps`   | Application services      | `./deploy.sh apps --limit central` |
| `all`    | Complete deployment       | `./deploy.sh all --diff`           |
| `check`  | Dry run mode              | `./deploy.sh check`                |

### Advanced Usage

```bash
# Deploy with specific tags
ansible-playbook -i production.yaml playbook.yaml --tags "traefik,authentik"

# Skip certain services
ansible-playbook -i production.yaml playbook.yaml --skip-tags "media"

# Deploy to specific host
ansible-playbook -i production.yaml playbook.yaml --limit central

# Check mode with diff output
ansible-playbook -i production.yaml playbook.yaml --check --diff
```

## 📁 Project Structure

```
├── playbook.yaml              # Main deployment playbook
├── production.yaml            # Inventory file
├── deploy.sh                  # Deployment convenience script
├── requirements.yaml          # Ansible dependencies
├── group_vars/
│   └── myhosts.yaml          # Global variables
├── host_vars/central/
│   ├── main.yaml             # Host-specific variables
│   └── secrets.yaml          # Encrypted secrets
└── roles/                    # Service-specific roles
    ├── authentik/
    ├── borgwarehouse/
    ├── crowdsec/
    ├── media/
    ├── traefik/
    ├── uptimekuma/
    └── wud/
```

## ⚙️ Configuration

### Global Settings

Edit `group_vars/myhosts.yaml` to configure:

- Deployment control flags
- Docker configuration
- Service versions
- Common settings

### Host-Specific Settings

Edit `host_vars/central/main.yaml` for:

- Network configuration
- Domain settings
- Service-specific overrides

### Secrets Management

This repository uses Ansible Vault to encrypt sensitive data like passwords, API keys, and certificates. All secrets are stored in the encrypted file `host_vars/central/secrets.yaml`.

#### Vault Operations

**Using Make commands (recommended):**

```bash
# Edit encrypted secrets (prompts for password)
make edit-secrets

# View encrypted secrets (prompts for password)
make view-secrets

# Change vault password
make rekey-vault
```

**Using the vault script:**

```bash
# Show all vault commands
./vault.sh help

# Edit main secrets file
./vault.sh edit

# View main secrets file
./vault.sh view

# Encrypt a new file
./vault.sh encrypt path/to/newfile.yaml

# Change vault password
./vault.sh rekey
```

**Direct Ansible Vault commands:**

```bash
# Edit encrypted file
ansible-vault edit host_vars/central/secrets.yaml

# View encrypted file
ansible-vault view host_vars/central/secrets.yaml

# Encrypt a new file
ansible-vault encrypt path/to/file.yaml
```

#### Deployment with Vault

All deployment commands automatically prompt for the vault password:

```bash
# Make commands (vault password prompted automatically)
make deploy-all
make deploy-infra
make status

# Direct script usage (must specify --ask-vault-pass)
./deploy.sh all --ask-vault-pass
./deploy.sh infra --ask-vault-pass
```

## 🏷️ Tags Reference

### Service Groups

- `system-configuration` - Base system setup
- `infrastructure` - Core infrastructure services
- `backup` - Backup and recovery services
- `applications` - End-user applications

### Individual Services

- `docker`, `networking`, `traefik`, `authentik`
- `crowdsec`, `borgwarehouse`, `borg`
- `media`, `uptimekuma`, `wud`

### Special Tags

- `verification` - Post-deployment checks
- `packages` - System package management
- `directories` - Directory creation

## 🔒 Security Features

- Automatic HTTPS with Traefik and Let's Encrypt
- CrowdSec intrusion prevention
- Authentik SSO integration
- Network segmentation with Docker networks
- Regular security updates via unattended-upgrades

## 📊 Monitoring

After deployment, services are available at:

- **Traefik Dashboard**: `https://your-domain/dashboard/`
- **Authentik**: `https://your-domain/auth/`
- **UptimeKuma**: `https://your-domain/uptime/`
- **Media Services**: `https://your-domain/media/`

## 🛠️ Troubleshooting

### Check Service Status

```bash
# View running containers
docker ps

# Check service logs
docker compose -f /docker/SERVICE/compose.yaml logs -f
```

### Validate Configuration

```bash
# Test playbook syntax
ansible-playbook --syntax-check playbook.yaml

# Run in check mode
./deploy.sh check
```

### Common Issues

- Ensure DNS records point to your server
- Check firewall rules for required ports
- Verify Docker daemon is running
- Check available disk space in `/docker`

## 🔄 Updates

To update service versions:

1. Edit service tags in `group_vars/myhosts.yaml`
2. Run deployment: `./deploy.sh apps`

To update the playbook:

```bash
git pull
ansible-galaxy install -r requirements.yaml --force
./deploy.sh check  # Verify changes
./deploy.sh all    # Apply updates
```

## 📝 Contributing

When adding new services:

1. Create a new role in `roles/`
2. Add the role to the appropriate block in `playbook.yaml`
3. Add appropriate tags for selective deployment
4. Update this README with service information
