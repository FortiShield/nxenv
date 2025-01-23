# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from click import secho

import nxenv


def execute():
	if nxenv.get_hooks("jenv"):
		print()
		secho(
			'WARNING: The hook "jenv" is deprecated. Follow the migration guide to use the new "jinja" hook.',
			fg="yellow",
		)
		secho("https://github.com/nxenv/nxenv/wiki/Migrating-to-Version-13", fg="yellow")
		print()
