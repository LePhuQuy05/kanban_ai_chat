# Scripts Notes

Scripts in this folder manage local Docker startup/shutdown:

- Windows PowerShell:
  - `start.ps1`
  - `stop.ps1`
- Windows CMD:
  - `start.bat`
  - `stop.bat`
- macOS/Linux:
  - `start.sh`
  - `stop.sh`

All scripts call `docker compose` from repository root conventions.