#!/bin/bash
#
# Central Server Deployment Script
# This script provides convenient commands to deploy different parts of the infrastructure
#

PLAYBOOK="playbook.yaml"
INVENTORY="production.yaml"

show_help() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    system      Deploy system configuration (Docker, networking, etc.)
    infra       Deploy infrastructure services (Traefik, Authentik, CrowdSec)
    backup      Deploy backup services (BorgWarehouse, Borg)
    apps        Deploy application services (Media, Monitoring)
    all         Deploy all services
    check       Run playbook in check mode
    help        Show this help message

Options:
    --limit HOST         Limit execution to specific host
    --tags TAGS          Run only specific tags
    --skip-tags TAGS     Skip specific tags
    --check              Run in check mode (dry run)
    --diff               Show diffs when files are changed
    --ask-vault-pass     Prompt for ansible vault password

Examples:
    $0 system --ask-vault-pass   # Deploy system configuration with vault password
    $0 infra --check            # Check infrastructure deployment
    $0 apps --limit central     # Deploy apps to central host only
    $0 all --skip-tags security # Deploy all except security services
    $0 check --ask-vault-pass   # Check deployment with vault access

Note: Most deployments require vault password to access encrypted secrets.

EOF
}

# Default ansible options
ANSIBLE_OPTS="-i $INVENTORY"

# Check if --ask-vault-pass is passed as an argument
for arg in "$@"; do
    if [[ "$arg" == "--ask-vault-pass" ]]; then
        ANSIBLE_OPTS="$ANSIBLE_OPTS --ask-vault-pass"
        break
    fi
done

case "$1" in
    system)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK --tags "system-configuration" -e "configure_system=true" "$@"
        ;;
    infra)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK --tags "infrastructure" "$@"
        ;;
    backup)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK --tags "backup" "$@"
        ;;
    apps)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK --tags "applications" "$@"
        ;;
    all)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK -e "configure_system=true" "$@"
        ;;
    check)
        shift
        ansible-playbook $ANSIBLE_OPTS $PLAYBOOK --check --diff "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo "Run '$0 help' for usage information."
        exit 1
        ;;
esac
