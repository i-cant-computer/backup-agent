#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

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
    help="output log messages of this severity or above to stderr. (default: %(default)s)",
  )
  parser.add_argument(
    "-c",
    "--config",
    default="config.yaml",
    help="path to the configuration file. (default: %(default)s)",
  )
  return parser.parse_args()


def main() -> None:
  """Entry Point."""
  args = parse_args()

  with Path.open(args.config) as file:
    config_yaml = yaml.safe_load(file)
  config = SimpleNamespace(**config_yaml)

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
    podman_manager = PodmanExportManager(config.podman_user, Path(config.export_path))
    podman_manager.export_volumes(config.export_volumes, config.export_containers)

  policy = BackupPolicy(
    config.keep_daily,
    config.keep_weekly,
    config.keep_monthly,
    config.keep_quarterly,
  )
  borg_manager = BackupManager(
    Path(config.borg_repository), config.borg_password, policy
  )

  if args.backup:
    borg_manager.run_borg_backups([Path(p) for p in config.borg_backup_paths])

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
