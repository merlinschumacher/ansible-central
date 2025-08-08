#!/bin/bash
#
# Ansible Vault Management Script
# Provides convenient commands for managing encrypted secrets
#

SECRETS_FILE="host_vars/central/secrets.yaml"

show_help() {
    cat << EOF
Usage: $0 [COMMAND] [FILE]

Commands:
    edit        Edit encrypted secrets file
    view        View encrypted secrets file
    encrypt     Encrypt a file with ansible-vault
    decrypt     Decrypt a file with ansible-vault
    rekey       Change vault password for secrets file
    create      Create new encrypted file
    help        Show this help message

Examples:
    $0 edit                          # Edit main secrets file
    $0 view                          # View main secrets file
    $0 encrypt host_vars/new.yaml    # Encrypt specific file
    $0 decrypt host_vars/old.yaml    # Decrypt specific file
    $0 rekey                         # Change vault password
    $0 create host_vars/new.yaml     # Create new encrypted file

Default file: $SECRETS_FILE

EOF
}

case "$1" in
    edit)
        FILE="${2:-$SECRETS_FILE}"
        echo "🔐 Editing encrypted file: $FILE"
        ansible-vault edit "$FILE"
        ;;
    view)
        FILE="${2:-$SECRETS_FILE}"
        echo "👀 Viewing encrypted file: $FILE"
        ansible-vault view "$FILE"
        ;;
    encrypt)
        if [ -z "$2" ]; then
            echo "❌ Please specify a file to encrypt"
            echo "Usage: $0 encrypt <file>"
            exit 1
        fi
        echo "🔐 Encrypting file: $2"
        ansible-vault encrypt "$2"
        ;;
    decrypt)
        if [ -z "$2" ]; then
            echo "❌ Please specify a file to decrypt"
            echo "Usage: $0 decrypt <file>"
            exit 1
        fi
        echo "🔓 Decrypting file: $2"
        ansible-vault decrypt "$2"
        ;;
    rekey)
        FILE="${2:-$SECRETS_FILE}"
        echo "🔑 Changing vault password for: $FILE"
        ansible-vault rekey "$FILE"
        ;;
    create)
        if [ -z "$2" ]; then
            echo "❌ Please specify a file to create"
            echo "Usage: $0 create <file>"
            exit 1
        fi
        echo "📝 Creating new encrypted file: $2"
        ansible-vault create "$2"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run '$0 help' for usage information."
        exit 1
        ;;
esac
