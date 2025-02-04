"""
Deprecate archived_sites folder for consistency. This change is
only for Nxenv v14 nxclies. If not a v14 nxcli yet, skip this
patch and try again later.

1. Rename folder `./archived_sites` to `./archived/sites`
2. Create a symlink `./archived_sites` => `./archived/sites`

Corresponding changes in nxenv/nxenv via https://github.com/nxenv/nxenv/pull/15060
"""
import os
from pathlib import Path

import click
from nxcli.utils.app import get_current_version
from semantic_version import Version


def execute(nxcli_path):
	nxenv_version = Version(get_current_version("nxenv"))

	if nxenv_version.major < 14 or os.name != "posix":
		# Returning False means patch has been skipped
		return False

	pre_patch_dir = os.getcwd()
	old_directory = Path(nxcli_path, "archived_sites")
	new_directory = Path(nxcli_path, "archived", "sites")

	if not old_directory.exists():
		return False

	if old_directory.is_symlink():
		return True

	os.chdir(nxcli_path)

	if not os.path.exists(new_directory):
		os.makedirs(new_directory)

	old_directory.rename(new_directory)

	click.secho(f"Archived sites are now stored under {new_directory}")

	if not os.listdir(old_directory):
		os.rmdir(old_directory)

	os.symlink(new_directory, old_directory)

	click.secho(f"Symlink {old_directory} that points to {new_directory}")

	os.chdir(pre_patch_dir)
