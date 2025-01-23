# Releasing Nxenv ERPNext

- Make a new nxcli dedicated for releasing

```
nxcli init release-nxcli --nxenv-path git@github.com:nxenv/nxenv.git
```

- Get ERPNext in the release nxcli

```
nxcli get-app erpnext git@github.com:nxenv/erpnext.git
```

- Configure as release nxcli. Add this to the common_site_config.json

```
"release_nxcli": true,
```

- Add branches to update in common_site_config.json

```
"branches_to_update": {
    "staging": ["develop", "hotfix"],
    "hotfix": ["develop", "staging"]
}
```

- Use the release commands to release

```
Usage: nxcli release [OPTIONS] APP BUMP_TYPE
```

- Arguments :
  - _APP_ App name e.g [nxenv|erpnext|yourapp]
  - _BUMP_TYPE_ [major|minor|patch|stable|prerelease]
- Options:
  - --from-branch git develop branch, default is develop
  - --to-branch git master branch, default is master
  - --remote git remote, default is upstream
  - --owner git owner, default is nxenv
  - --repo-name git repo name if different from app name
- When updating major version, update `develop_version` in hooks.py, e.g. `9.x.x-develop`
