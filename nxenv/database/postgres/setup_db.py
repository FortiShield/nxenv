import os
import re

import nxenv
from nxenv.database.db_manager import DbManager
from nxenv.utils import cint


def setup_database():
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql("end")
	root_conn.sql(f'DROP DATABASE IF EXISTS "{nxenv.conf.db_name}"')

	# If user exists, just update password
	if root_conn.sql(f"SELECT 1 FROM pg_roles WHERE rolname='{nxenv.conf.db_user}'"):
		root_conn.sql(f"ALTER USER \"{nxenv.conf.db_user}\" WITH PASSWORD '{nxenv.conf.db_password}'")
	else:
		root_conn.sql(f"CREATE USER \"{nxenv.conf.db_user}\" WITH PASSWORD '{nxenv.conf.db_password}'")
	root_conn.sql(f'CREATE DATABASE "{nxenv.conf.db_name}"')
	root_conn.sql(f'GRANT ALL PRIVILEGES ON DATABASE "{nxenv.conf.db_name}" TO "{nxenv.conf.db_user}"')
	if psql_version := root_conn.sql("SHOW server_version_num", as_dict=True):
		semver_version_num = psql_version[0].get("server_version_num") or "140000"
		if cint(semver_version_num) > 150000:
			root_conn.sql(f'ALTER DATABASE "{nxenv.conf.db_name}" OWNER TO "{nxenv.conf.db_user}"')
	root_conn.close()


def bootstrap_database(verbose, source_sql=None):
	nxenv.connect()
	import_db_from_sql(source_sql, verbose)

	nxenv.connect()
	if "tabDefaultValue" not in nxenv.db.get_tables():
		import sys

		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"This happens when the backup fails to restore. Please check that the file is valid\n"
			"Do go through the above output to check the exact error message from MariaDB",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	if verbose:
		print("Starting database import...")
	db_name = nxenv.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_postgres.sql")
	DbManager(nxenv.local.db).restore_database(
		verbose, db_name, source_sql, nxenv.conf.db_user, nxenv.conf.db_password
	)
	if verbose:
		print("Imported from database {}".format(source_sql))


def get_root_connection():
	if not nxenv.local.flags.root_connection:
		import sys
		from getpass import getpass

		if not nxenv.flags.root_login:
			nxenv.flags.root_login = (
				nxenv.conf.get("postgres_root_login")
				or nxenv.conf.get("root_login")
				or (sys.__stdin__.isatty() and input("Enter postgres super user [postgres]: "))
				or "postgres"
			)

		if not nxenv.flags.root_password:
			nxenv.flags.root_password = (
				nxenv.conf.get("postgres_root_password")
				or nxenv.conf.get("root_password")
				or getpass("Postgres super user password: ")
			)

		nxenv.local.flags.root_connection = nxenv.database.get_db(
			socket=nxenv.conf.db_socket,
			host=nxenv.conf.db_host,
			port=nxenv.conf.db_port,
			user=nxenv.flags.root_login,
			password=nxenv.flags.root_password,
			cur_db_name=nxenv.flags.root_login,
		)

	return nxenv.local.flags.root_connection


def drop_user_and_database(db_name, db_user):
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql(
		"SELECT pg_terminate_backend (pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s",
		(db_name,),
	)
	root_conn.sql("end")
	root_conn.sql(f"DROP DATABASE IF EXISTS {db_name}")
	root_conn.sql(f"DROP USER IF EXISTS {db_user}")
