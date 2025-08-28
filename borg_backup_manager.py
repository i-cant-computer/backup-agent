import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pid.decorator import pidfile

BORG = "/usr/bin/borg"


@dataclass
class BackupPolicy:
  daily: int
  weekly: int
  monthly: int
  quarterly: int


@dataclass
class BackupManager:
  repository: Path
  password: str
  policy: BackupPolicy
  log: logging.Logger = field(init=False)

  def __post_init__(self) -> None:
    """Configure logging after initialisation."""
    self.log = logging.getLogger(self.__class__.__name__)
    self.log.debug("backup manager initialised with repository %s", self.repository)

  @pidfile("podman_export")
  @pidfile("borg_backups")
  def run_borg_backups(self, paths: list[Path]) -> None:
    """Backup supplied paths into a new archive inside the manager's repository."""
    start_time = datetime.now().astimezone()
    self.log.info("borg backup started at %s", start_time)
    cmd = subprocess.run(  # noqa: S603
      [
        BORG,
        "create",
        "-v",
        "--stats",
        f"{self.repository}::{datetime.now().astimezone()}",
        *paths,
      ],
      check=False,
      capture_output=True,
      env={"BORG_PASSPHRASE": self.password},
      text=True,
    )
    backup_completion = datetime.now().astimezone() - start_time
    if cmd.returncode != 0:
      self.log.critical("borg backup completed with errors in %s", backup_completion)
      self.log.critical(cmd.stderr.strip())
      # Should always raise an Exception
      cmd.check_returncode()
    self.log.info(cmd.stderr.strip())
    self.log.info("borg backup completed in %s", backup_completion)

  @pidfile("borg_backups")
  def perform_backup_maintenance(self) -> None:
    """Perform maintenance on the manager's repository (prune, compact)."""
    start_time = datetime.now().astimezone()
    self.log.info("repository maintenance started st %s", start_time)
    self._run_borg_prune()
    self._run_borg_compact()
    mainentance_completion = datetime.now().astimezone() - start_time
    self.log.info("repository maintenance completed in %s", mainentance_completion)

  def _run_borg_prune(self) -> None:
    """Run ``borg prune`` on the manager's repository."""
    cmd = subprocess.run(  # noqa: S603
      [
        BORG,
        "prune",
        "--stats",
        "--keep-daily",
        f"{self.policy.daily}",
        "--keep-weekly",
        f"{self.policy.weekly}",
        "--keep-monthly",
        f"{self.policy.monthly}",
        "--keep-13weekly",
        f"{self.policy.quarterly}",
        f"{self.repository}",
      ],
      check=False,
      capture_output=True,
      env={"BORG_PASSPHRASE": self.password},
      text=True,  # Added text=True for consistency
    )
    if cmd.returncode != 0:
      self.log.critical("error pruning repository")
      self.log.critical(cmd.stderr.strip())
      # Should always raise an Exception
      cmd.check_returncode()
    self.log.info("prune complete")
    self.log.info(cmd.stderr.strip())

  def _run_borg_compact(self) -> None:
    """Run ``borg compact`` on the manager's repository."""
    cmd = subprocess.run(  # noqa: S603
      [
        BORG,
        "--verbose",
        "compact",
        f"{self.repository}",
      ],
      check=False,
      capture_output=True,
      text=True,  # Added text=True for consistency
    )
    if cmd.returncode != 0:
      self.log.critical("error compacting repository")
      self.log.critical(cmd.stderr.strip())
      # Should always raise an Exception
      cmd.check_returncode()
    self.log.info("compacting complete")
    self.log.info(cmd.stderr.strip())
