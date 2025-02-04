import os
import re


def get_versions():
    nxenv_version = os.getenv("NXENV_VERSION")
    erpnext_version = os.getenv("ERPNEXT_VERSION")
    assert nxenv_version, "No Nxenv version set"
    assert erpnext_version, "No ERPNext version set"
    return nxenv_version, erpnext_version


def update_pwd(nxenv_version: str, erpnext_version: str):
    with open("pwd.yml", "r+") as f:
        content = f.read()
        content = re.sub(
            rf"nxenv/erpnext:.*", f"nxenv/erpnext:{erpnext_version}", content
        )
        f.seek(0)
        f.truncate()
        f.write(content)


def main() -> int:
    update_pwd(*get_versions())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
