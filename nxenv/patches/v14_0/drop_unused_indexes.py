"""
This patch just drops some known indexes which aren't being used anymore or never were used.
"""

import click

import nxenv

UNUSED_INDEXES = [
	("Comment", ["link_doctype", "link_name"]),
	("Activity Log", ["link_doctype", "link_name"]),
]


def execute():
	if nxenv.db.db_type == "postgres":
		return

	db_tables = nxenv.db.get_tables(cached=False)

	# All parent indexes
	parent_doctypes = nxenv.get_all(
		"DocType",
		{"istable": 0, "is_virtual": 0, "issingle": 0},
		pluck="name",
	)
	db_tables = nxenv.db.get_tables(cached=False)

	for doctype in parent_doctypes:
		table = f"tab{doctype}"
		if table not in db_tables:
			continue
		drop_index_if_exists(table, "parent")

	# Unused composite indexes
	for doctype, index_fields in UNUSED_INDEXES:
		table = f"tab{doctype}"
		index_name = nxenv.db.get_index_name(index_fields)
		if table not in db_tables:
			continue
		drop_index_if_exists(table, index_name)


def drop_index_if_exists(table: str, index: str):
	if not nxenv.db.has_index(table, index):
		click.echo(f"- Skipped {index} index for {table} because it doesn't exist")
		return

	try:
		nxenv.db.sql_ddl(f"ALTER TABLE `{table}` DROP INDEX `{index}`")
	except Exception as e:
		nxenv.log_error("Failed to drop index")
		click.secho(f"x Failed to drop index {index} from {table}\n {e!s}", fg="red")
		return

	click.echo(f"✓ dropped {index} index from {table}")
