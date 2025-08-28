"""Sample configuration file.

Rename to config.py and configure for your environment.
"""

# Account running podman containers
PODMAN_SVC = "podman"

# List of named volumes exported for the backup
EXPORT_VOLUMES = [
  "named-volume1",
  "named-volume2",
]
# List of containers that need to be stopped for the export
EXPORT_CONTAINERS = [
  "container1",
  "container2",
]
# Path where volumes are exported
EXPORT_PATH = "/path/to/named/volume/exports"

# Backup policy
DAILY = 7
WEEKLY = 4
MONTHLY = 3
QUARTERLY = 3

# Path to borg repository
BORG_REPOSITORY = "/path/to/borg/repository"
# Password for borg repository
BORG_PASSWORD = "BORG_REPOSITORY_PASSWORD"  # noqa: S105
# Paths included in borg backups
BORG_BACKUP_PATHS = [EXPORT_PATH, "/second/backup/folder/"]
