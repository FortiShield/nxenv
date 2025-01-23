Add the following configuration to `launch.json` `configurations` array to start nxcli console and use debugger. Replace `development.localhost` with appropriate site. Also replace `nxenv-nxcli` with name of the nxcli directory.

```json
{
  "name": "Nxcli Console",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/nxenv-nxcli/apps/nxenv/nxenv/utils/nxcli_helper.py",
  "args": ["nxenv", "--site", "development.localhost", "console"],
  "pythonPath": "${workspaceFolder}/nxenv-nxcli/env/bin/python",
  "cwd": "${workspaceFolder}/nxenv-nxcli/sites",
  "env": {
    "DEV_SERVER": "1"
  }
}
```
