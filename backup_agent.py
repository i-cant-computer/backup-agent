#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

import backup_config
from borg_backup_manager import BackupManager, BackupPolicy
from podman_export_manager import PodmanExportManager


def parse_args() -> argparse.Namespace:
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(
    description="Backup agent for Podman volumes and Borg."
  )
  parser.add_argument(
    "-b",
    "--backup",
    action="store_true",
    help="run Borg backups.",
  )
  parser.add_argument(
    "-e",
    "--export-volumes",
    action="store_true",
    help="export named volumes.",
  )
  parser.add_argument(
    "-m",
    "--maintenance",
    action="store_true",
    help="perform Borg repository maintenance (prune and compact).",
  )
  parser.add_argument(
    "-l",
    "--log-level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="Output log messages of this severity or above to stderr. (default: %(default)s)",
  )
  return parser.parse_args()


def main() -> None:
  """Entry Point."""
  args = parse_args()
  log_format = (
    "%(levelname)s:%(name)s:%(funcName)s:%(message)s"
    if args.log_level == "DEBUG"
    else logging.BASIC_FORMAT
  )
  logging.basicConfig(
    level=args.log_level,
    format=log_format,
  )

  if args.export_volumes:
    podman_manager = PodmanExportManager(
      backup_config.PODMAN_SVC, Path(backup_config.EXPORT_PATH)
    )
    podman_manager.export_volumes(
      backup_config.EXPORT_VOLUMES, backup_config.EXPORT_CONTAINERS
    )

  policy = BackupPolicy(
    backup_config.DAILY,
    backup_config.WEEKLY,
    backup_config.MONTHLY,
    backup_config.QUARTERLY,
  )
  borg_manager = BackupManager(
    Path(backup_config.BORG_REPOSITORY), backup_config.BORG_PASSWORD, policy
  )

  if args.backup:
    borg_manager.run_borg_backups([Path(p) for p in backup_config.BORG_BACKUP_PATHS])

  if args.maintenance:
    borg_manager.perform_backup_maintenance()


if __name__ == "__main__":
  try:
    main()
  except Exception as error:
    log = logging.getLogger(__name__)
    msg = f"unexpected error: {error}"
    log.critical(msg, exc_info=True, stack_info=True)
    sys.exit(1)
