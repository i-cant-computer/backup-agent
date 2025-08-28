# Backup Agent

A minimal backup tool to backup containers.

This agent:

- Stops containers safely during backup
- Exports specified named volumes with `podman volume export`
- Uses **BorgBackups** for versioned, deduplicated backups with a retention
  policy.

---

## 🔧 Configuration

All settings are provided in a `config.yaml` file in a configurable location. A
`sample_config.yaml` is provided with illustrative values. Rename it and tailor
it to your needs.

---

## ▶️ Usage

Run the backup agent from the command line with specific actions:

```bash
python3 backup_agent.py [OPTIONS]
```

**Options:**

```text
usage: backup_agent.py [-h] [-b] [-e] [-m] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-c CONFIG]

Backup agent for Podman volumes and Borg.

options:
  -h, --help            show this help message and exit
  -b, --backup          run Borg backups.
  -e, --export-volumes  export named volumes.
  -m, --maintenance     perform Borg repository maintenance (prune and compact).
  -l, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Output log messages of this severity or above to stderr.
                        (default: INFO)
  -c, --config CONFIG   Path to the configuration file. (default: config.yaml)
```

**Examples:**

- To export volumes and run backups with default logging:

  ```bash
  python3 backup_agent.py --export --backup
  ```

- To perform only maintenance with debug logging:

  ```bash
  python3 backup_agent.py -m -l DEBUG
  ```

- To see all available options:

  ```bash
  python3 backup_agent.py --help
  ```

---

## 🗂 Structure

```text
.
├── README.md                 # This file
├── LICENSE                   # Project license
├── pyproject.toml            # Python Project file
├── backup_agent.py           # Entry point for the backup agent
├── borg_backup_manager.py    # Runs backups using borg
├── podman_export_manager.py  # Exports volumes using podman
├── sample_config.yaml        # Sample user-defined configuration
```

---

## ⚠️ Warnings

- This tool **stops your containers** during volume export to ensure consistent
  backups
- The borg repository must be created prior to running the script
- Keep `config.yaml` protected from unauthorized access
- `backup_agent` assumes that required binaries are available under `/bin/` (for
  `sudo`) and `/usr/bin/` (for `borg` and `podman`)

---

## 📝 License

MIT License. See `LICENSE` for details.

---
