#!/usr/bin/env python3
"""
Docker Image Version Updater
Automatically checks for newer Docker image versions using semantic versioning
Only updates minor and patch versions, skips major version updates by default
"""

import argparse
import logging
import sys
import yaml
import docker
import semver
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("docker-update.log")],
)
logger = logging.getLogger(__name__)


class SemanticVersion:
    """Handle semantic version parsing and comparison using semver library"""

    def __init__(self, version_string: str):
        self.original = version_string
        self.version_string = version_string.lstrip("v")

        if not semver.VersionInfo.isvalid(self.version_string):
            raise ValueError(f"Invalid semantic version: {version_string}")

        self.version_info = semver.VersionInfo.parse(self.version_string)

    def __str__(self):
        return self.original

    def __repr__(self):
        return f"SemanticVersion('{self.original}')"

    def __eq__(self, other):
        return self.version_info == other.version_info

    def __lt__(self, other):
        return self.version_info < other.version_info

    def __le__(self, other):
        return self.version_info <= other.version_info

    def __gt__(self, other):
        return self.version_info > other.version_info

    def __ge__(self, other):
        return self.version_info >= other.version_info

    def is_compatible_update(self, other, allow_major: bool = False):
        """Check if other version is a compatible update"""
        if other.version_info <= self.version_info:
            return False

        if other.version_info.major > self.version_info.major:
            return allow_major

        return True  # Same major, higher minor/patch is allowed


class DockerRegistry:
    """Handle Docker registry API interactions using Docker SDK"""

    def __init__(self):
        self.client = docker.APIClient()

    def get_registry_tags(self, image: str) -> List[str]:
        """Get tags from Docker registry using Docker SDK"""
        try:
            repository, _ = image.split(":")
            tags = self.client.tags(repository)
            return tags
        except docker.errors.APIError as e:
            logger.warning(f"Failed to fetch tags for {image}: {e}")
            return []


class DockerImageUpdater:
    """Main class for updating Docker image versions"""

    def __init__(
        self, vars_file: Path, dry_run: bool = False, allow_major: bool = False
    ):
        self.vars_file = vars_file
        self.dry_run = dry_run
        self.allow_major = allow_major
        self.registry = DockerRegistry()

        # Patterns to skip (typically latest tags or non-semantic versions)
        self.skip_patterns = [
            "latest",
            "stable",
            "main",
            "master",
            "edge",
            "develop",
            "nightly",
            "alpha",
            "beta",
            "rc",
        ]

        self.updates_found = []
        self.errors = []

    def _should_skip_tag(self, tag: str) -> bool:
        """Check if tag should be skipped based on patterns"""
        return any(pattern in tag.lower() for pattern in self.skip_patterns)

    def _load_yaml(self) -> dict:
        """Load YAML configuration file"""
        try:
            with open(self.vars_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {self.vars_file}: {e}")
            raise

    def _save_yaml(self, data: dict) -> None:
        """Save YAML configuration file"""
        try:
            with open(self.vars_file, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {self.vars_file}: {e}")
            raise

    def _create_backup(self) -> Path:
        """Create backup of the variables file"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = (
            self.vars_file.parent / f"{self.vars_file.name}.backup.{timestamp}"
        )

        try:
            backup_path.write_text(self.vars_file.read_text())
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def _flatten_docker_images(
        self, docker_images: dict, prefix: str = ""
    ) -> Dict[str, str]:
        """Flatten nested docker_images dictionary"""
        flattened = {}

        for key, value in docker_images.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(self._flatten_docker_images(value, full_key))
            elif isinstance(value, str) and ":" in value:
                flattened[full_key] = value

        return flattened

    def _update_nested_dict(self, data: dict, key_path: str, new_value: str) -> None:
        """Update nested dictionary value using dot notation key path"""
        keys = key_path.split(".")
        current = data["docker_images"]

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = new_value

    def _find_latest_compatible_version(
        self, current_version: str, available_tags: List[str]
    ) -> Optional[SemanticVersion]:
        """Find the latest compatible version from available tags"""
        try:
            current_semver = SemanticVersion(current_version)
        except ValueError:
            logger.warning(f"Current version is not semantic: {current_version}")
            return None

        latest_compatible = None

        for tag in available_tags:
            if self._should_skip_tag(tag):
                continue

            try:
                tag_semver = SemanticVersion(tag)

                if tag_semver.is_compatible_update(current_semver, self.allow_major):
                    if latest_compatible is None or tag_semver > latest_compatible:
                        latest_compatible = tag_semver
            except ValueError:
                continue  # Skip invalid semantic versions

        return latest_compatible

    def check_image_updates(
        self, image_key: str, image_full: str
    ) -> Optional[Tuple[str, str]]:
        """Check for updates for a single image"""
        if ":" not in image_full:
            logger.warning(f"Image {image_key} has no tag specified: {image_full}")
            return None

        repository, current_tag = image_full.rsplit(":", 1)

        if self._should_skip_tag(current_tag):
            logger.info(
                f"Skipping {image_key} - tag '{current_tag}' matches skip pattern"
            )
            return None

        logger.info(f"Checking {image_key}: {image_full}")

        # Get available tags from registry
        available_tags = self.registry.get_registry_tags(repository)

        if not available_tags:
            logger.warning(f"No tags found for {repository}")
            return None

        # Find latest compatible version
        latest_version = self._find_latest_compatible_version(
            current_tag, available_tags
        )

        if latest_version and str(latest_version) != current_tag:
            logger.info(
                f"Update available for {image_key}: {current_tag} -> {latest_version}"
            )
            return (current_tag, str(latest_version))

        return None

    def update_all_images(self) -> Dict[str, object]:
        """Check and update all Docker images"""
        logger.info("Starting Docker image update check...")

        # Load current configuration
        data = self._load_yaml()
        docker_images = data.get("docker_images", {})

        if not docker_images:
            logger.warning("No docker_images section found in configuration")
            return {"updates": 0, "errors": 0}

        # Create backup if not dry run
        if not self.dry_run:
            self._create_backup()

        # Flatten nested structure
        flattened_images = self._flatten_docker_images(docker_images)

        logger.info(f"Found {len(flattened_images)} Docker images to check")

        updates_made = 0

        for image_key, image_full in flattened_images.items():
            try:
                update_info = self.check_image_updates(image_key, image_full)

                if update_info:
                    old_version, new_version = update_info

                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] Would update {image_key}: {old_version} -> {new_version}"
                        )
                    else:
                        # Update the nested structure
                        repository = image_full.rsplit(":", 1)[0]
                        new_image = f"{repository}:{new_version}"
                        self._update_nested_dict(data, image_key, new_image)
                        logger.info(
                            f"Updated {image_key}: {old_version} -> {new_version}"
                        )

                    self.updates_found.append(
                        {
                            "key": image_key,
                            "old_version": old_version,
                            "new_version": new_version,
                            "image": image_full,
                        }
                    )
                    updates_made += 1

            except Exception as e:
                logger.error(f"Error checking {image_key}: {e}")
                self.errors.append(f"{image_key}: {e}")

        # Save updated configuration
        if updates_made > 0 and not self.dry_run:
            self._save_yaml(data)
            logger.info(f"Configuration updated with {updates_made} image updates")

        return {
            "updates": updates_made,
            "errors": len(self.errors),
            "checked": len(flattened_images),
        }

    def print_summary(self, results: Dict[str, object]) -> None:
        """Print summary of update results"""
        print("\n" + "=" * 60)
        print("Docker Image Update Summary")
        print("=" * 60)

        print(f"Images checked: {results['checked']}")
        print(f"Updates {'found' if self.dry_run else 'applied'}: {results['updates']}")
        print(f"Errors: {results['errors']}")

        if self.updates_found:
            print(f"\n{'Available updates:' if self.dry_run else 'Applied updates:'}")
            for update in self.updates_found:
                print(
                    f"  • {update['key']}: {update['old_version']} -> {update['new_version']}"
                )

        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  • {error}")

        if results["updates"] > 0:
            if self.dry_run:
                print("\nRun without --dry-run to apply these updates")
            else:
                print(
                    "\nReview changes and run 'make deploy-all' to deploy updated images"
                )
        else:
            print("\nAll images are up to date!")


def main():
    parser = argparse.ArgumentParser(
        description=("Check and update Docker image versions using semantic versioning")
    )
    parser.add_argument(
        "--vars-file",
        type=Path,
        default=Path("group_vars/myhosts.yaml"),
        help="Path to the variables file (default: group_vars/myhosts.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument(
        "--allow-major",
        action="store_true",
        help="Allow major version updates (potentially breaking)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create backup without checking updates",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate vars file exists
    if not args.vars_file.exists():
        logger.error(f"Variables file not found: {args.vars_file}")
        sys.exit(1)

    # Handle backup-only mode
    if args.backup_only:
        updater = DockerImageUpdater(args.vars_file)
        backup_path = updater._create_backup()
        print(f"Backup created: {backup_path}")
        sys.exit(0)

    # Create updater and run
    vars_file = args.vars_file
    updater = DockerImageUpdater(
        vars_file=vars_file, dry_run=args.dry_run, allow_major=args.allow_major
    )

    try:
        results = updater.update_all_images()
        updater.print_summary(results)

        # Exit with error code if there were errors
        if results["errors"] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Update check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Update check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
