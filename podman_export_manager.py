import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pid.decorator import pidfile

PODMAN_EXPORT = ["/usr/bin/podman", "volume", "export"]
SYSTEMCTL = "/usr/bin/systemctl"
SUDO = "/bin/sudo"


@dataclass
class PodmanExportManager:
  user: str
  export_path: Path

  def __post_init__(self) -> None:
    """Complete initialisation of PodmanExportManager."""
    self._systemctl = [SYSTEMCTL, "--user", "--machine", f"{self.user}@.host"]
    self._sudo = [SUDO, "-i", "-u", self.user]
    self.log = logging.getLogger(self.__class__.__name__)
    self.log.debug("%s initialised for user %s", self.__class__.__name__, self.user)

  @pidfile("podman_export")
  def export_volumes(self, volumes: list[str], containers: list[str]) -> None:
    """Export named volumes, restarting containers afterwards."""
    start_time = datetime.now().astimezone()
    self.log.info("volume export started at %s", start_time)

    self._systemctl_stop_services(containers)
    for c in containers:
      if self._systemctl_is_active(c):
        msg = f"service {c} did not shut down, aborting export"
        self.log.critical(msg)
        raise OSError(msg)

    error_encountered = False
    self.log.info("exporting named volumes %s", " ".join(volumes))
    for v in volumes:
      error_encountered = (
        not self._podman_export_volume(v, self.export_path) or error_encountered
      )

    for c in containers:
      self._systemctl_start(c)
    for c in containers:
      if not self._systemctl_is_active(c):
        msg = f"service {c} did not start"
        self.log.error(msg)
        error_encountered = True

    export_duration = datetime.now().astimezone() - start_time
    if error_encountered:
      self.log.critical("volume export completed in %s with errors", export_duration)
      raise OSError
    self.log.info("volume export completed in %s", export_duration)

  def _podman_export_volume(self, volume: str, path: Path) -> bool:
    """Export a named volume to the supplied path using ``podman volume export``.

    Returns: True if the export succeeded.
    """
    full_path = Path(path) / (volume + ".tar")
    args = [
      *self._sudo,
      *PODMAN_EXPORT,
      "--output",
      f"{full_path}",
      volume,
    ]
    self.log.debug("exporting named volume %s to %s", volume, full_path)
    cmd = subprocess.run(  # noqa: S603
      args,
      check=False,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.PIPE,
    )
    if cmd.returncode != 0:
      self.log.error(
        "export of volume %s failed - %s", volume, cmd.stderr.decode().strip()
      )
    return cmd.returncode == 0

  def _systemctl_is_active(self, service: str) -> bool:
    """Confirm whether a service is active.

    Returns: True if the service is active.
    """
    args = [*self._systemctl, "is-active", service]
    cmd = subprocess.run(  # noqa: S603
      args,
      capture_output=True,
      check=False,
      text=True,
    )
    status = cmd.stdout.strip()
    self.log.debug("%s is %s", service, status)
    return status == "active"

  def _systemctl_start(self, service: str) -> None:
    """Start a service if it is not already running."""
    if not self._systemctl_is_active(service):
      self.log.info("starting service %s", service)
      args = [*self._systemctl, "start", service]
      subprocess.run(args, check=False)  # noqa: S603

  def _systemctl_stop_services(self, services: list[str]) -> None:
    """Stop a set of services."""
    self.log.info("stopping services %s", " ".join(services))
    args = [*self._systemctl, "stop", *services]
    subprocess.run(args, check=False)  # noqa: S603
