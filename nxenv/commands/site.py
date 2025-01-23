# imports - standard imports
import os
import shutil
import sys
import traceback

# imports - third party imports
import click

# imports - module imports
import nxenv
from nxenv.commands import get_site, pass_context
from nxenv.exceptions import SiteNotSpecifiedError
from nxenv.utils import CallbackManager
from nxenv.utils.nxcli_helper import CliCtxObj


@click.command("new-site")
@click.argument("site")
@click.option("--db-name", help="Database name")
@click.option("--db-password", help="Database password")
@click.option(
	"--db-type",
	default="mariadb",
	type=click.Choice(["mariadb", "postgres"]),
	help='Optional "postgres" or "mariadb". Default is "mariadb"',
)
@click.option("--db-host", help="Database Host")
@click.option("--db-port", type=int, help="Database Port")
@click.option(
	"--db-root-username",
	"--mariadb-root-username",
	help='Root username for MariaDB or PostgreSQL, Default is "root"',
)
@click.option("--db-root-password", "--mariadb-root-password", help="Root password for MariaDB or PostgreSQL")
@click.option(
	"--db-socket",
	"--mariadb-db-socket",
	envvar="MYSQL_UNIX_PORT",
	help="Database socket for MariaDB or folder containing database socket for PostgreSQL",
)
@click.option(
	"--no-mariadb-socket",
	is_flag=True,
	default=False,
	help="DEPRECATED: Set MariaDB host to % and use TCP/IP Socket instead of using the UNIX Socket",
)
@click.option(
	"--mariadb-user-host-login-scope",
	help=(
		"Set the mariadb host for the user login scope if you don't want to use the current host as login "
		"scope which typically is ''@'localhost' - may be used when initializing a user on a remote host. "
		"See the mariadb docs on account names for more info."
	),
)
@click.option("--admin-password", help="Administrator password for new site", default=None)
@click.option("--verbose", is_flag=True, default=False, help="Verbose")
@click.option("--force", help="Force restore if site/database already exists", is_flag=True, default=False)
@click.option("--source-sql", "--source_sql", help="Initiate database with a SQL file")
@click.option("--install-app", multiple=True, help="Install app after installation")
@click.option("--set-default", is_flag=True, default=False, help="Set the new site as default site")
@click.option(
	"--setup-db/--no-setup-db",
	default=True,
	help="Create user and database in mariadb/postgres; only bootstrap if false",
)
@click.option("--db-user", help="Database user if you already have one")
def new_site(
	site,
	db_root_username=None,
	db_root_password=None,
	admin_password=None,
	verbose=False,
	source_sql=None,
	force=None,
	no_mariadb_socket=False,
	mariadb_user_host_login_scope=False,
	install_app=None,
	db_name=None,
	db_password=None,
	db_type=None,
	db_socket=None,
	db_host=None,
	db_port=None,
	db_user=None,
	set_default=False,
	setup_db=True,
):
	"Create a new site"
	from nxenv.installer import _new_site

	nxenv.init(site, new_site=True)

	if site in nxenv.get_all_apps():
		click.secho(
			f"Your nxcli has an app called {site}, please choose another name for the site.", fg="red"
		)
		sys.exit(1)

	if no_mariadb_socket:
		click.secho(
			"--no-mariadb-socket is DEPRECATED; "
			"use --mariadb-user-host-login-scope='%' (wildcard) or --mariadb-user-host-login-scope=<myhostscope>, instead. "
			"The name of this option was misleading: it had nothing to do with sockets.",
			fg="yellow",
		)
		mariadb_user_host_login_scope = "%"

	rollback_callback = CallbackManager()

	try:
		_new_site(
			db_name,
			site,
			db_root_username=db_root_username,
			db_root_password=db_root_password,
			admin_password=admin_password,
			verbose=verbose,
			install_apps=install_app,
			source_sql=source_sql,
			force=force,
			db_password=db_password,
			db_type=db_type,
			db_socket=db_socket,
			db_host=db_host,
			db_port=db_port,
			db_user=db_user,
			setup_db=setup_db,
			rollback_callback=rollback_callback,
			mariadb_user_host_login_scope=mariadb_user_host_login_scope,
		)

		if set_default:
			use(site)

	except Exception:
		traceback.print_exc()
		if sys.__stdin__.isatty() and click.confirm(
			"Site creation failed, do you want to rollback the site?", abort=True
		):
			rollback_callback.run()
		sys.exit(1)


@click.command("restore")
@click.argument("sql-file-path")
@click.option(
	"--db-root-username",
	"--mariadb-root-username",
	help='Root username for MariaDB or PostgreSQL, Default is "root"',
)
@click.option("--db-root-password", "--mariadb-root-password", help="Root password for MariaDB or PostgreSQL")
@click.option("--db-name", help="Database name for site in case it is a new one")
@click.option("--admin-password", help="Administrator password for new site")
@click.option("--install-app", multiple=True, help="Install app after installation")
@click.option("--with-public-files", help="Restores the public files of the site, given path to its tar file")
@click.option(
	"--with-private-files",
	help="Restores the private files of the site, given path to its tar file",
)
@click.option(
	"--force",
	is_flag=True,
	default=False,
	help="Ignore the validations and downgrade warnings. This action is not recommended",
)
@click.option("--encryption-key", help="Backup encryption key")
@pass_context
def restore(
	context: CliCtxObj,
	sql_file_path,
	encryption_key=None,
	db_root_username=None,
	db_root_password=None,
	db_name=None,
	verbose=None,
	install_app=None,
	admin_password=None,
	force=None,
	with_public_files=None,
	with_private_files=None,
):
	"Restore site database from an sql file"

	from nxenv.utils.synchronization import filelock

	site = get_site(context)
	nxenv.init(site)

	with filelock("site_restore", timeout=1):
		_restore(
			site=site,
			sql_file_path=sql_file_path,
			encryption_key=encryption_key,
			db_root_username=db_root_username,
			db_root_password=db_root_password,
			verbose=context.verbose or verbose,
			install_app=install_app,
			admin_password=admin_password,
			force=context.force or force,
			with_public_files=with_public_files,
			with_private_files=with_private_files,
		)


def _restore(
	*,
	site=None,
	sql_file_path=None,
	encryption_key=None,
	db_root_username=None,
	db_root_password=None,
	verbose=None,
	install_app=None,
	admin_password=None,
	force=None,
	with_public_files=None,
	with_private_files=None,
):
	from nxenv.installer import extract_files
	from nxenv.utils.backups import decrypt_backup, get_or_generate_backup_encryption_key

	err, out = nxenv.utils.execute_in_shell(f"file {sql_file_path}", check_exit_code=True)
	if err:
		click.secho("Failed to detect type of backup file", fg="red")
		sys.exit(1)

	if "cipher" in out.decode().split(":")[-1].strip():
		if encryption_key:
			click.secho("Encrypted backup file detected. Decrypting using provided key.", fg="yellow")

		else:
			click.secho("Encrypted backup file detected. Decrypting using site config.", fg="yellow")
			encryption_key = get_or_generate_backup_encryption_key()

		with decrypt_backup(sql_file_path, encryption_key):
			# Rollback on unsuccessful decryption
			if not os.path.exists(sql_file_path):
				click.secho("Decryption failed. Please provide a valid key and try again.", fg="red")
				sys.exit(1)

			restore_backup(
				sql_file_path,
				site,
				db_root_username,
				db_root_password,
				verbose,
				install_app,
				admin_password,
				force,
			)
	else:
		restore_backup(
			sql_file_path,
			site,
			db_root_username,
			db_root_password,
			verbose,
			install_app,
			admin_password,
			force,
		)

	# Extract public and/or private files to the restored site, if user has given the path
	if with_public_files:
		# Decrypt data if there is a Key
		if encryption_key:
			with decrypt_backup(with_public_files, encryption_key):
				public = extract_files(site, with_public_files)
		else:
			public = extract_files(site, with_public_files)

		# Removing temporarily created file
		os.remove(public)

	if with_private_files:
		# Decrypt data if there is a Key
		if encryption_key:
			with decrypt_backup(with_private_files, encryption_key):
				private = extract_files(site, with_private_files)
		else:
			private = extract_files(site, with_private_files)

		# Removing temporarily created file
		os.remove(private)

	success_message = "Site {} has been restored{}".format(
		site, " with files" if (with_public_files or with_private_files) else ""
	)
	click.secho(success_message, fg="green")


def restore_backup(
	sql_file_path: str,
	site,
	db_root_username,
	db_root_password,
	verbose,
	install_app,
	admin_password,
	force,
):
	from pathlib import Path

	from nxenv.installer import _new_site, is_downgrade, is_partial, validate_database_sql

	# Check for the backup file in the backup directory, as well as the main nxcli directory
	dirs = (f"{site}/private/backups", "..")

	# Try to resolve path to the file if we can't find it directly
	if not Path(sql_file_path).exists():
		click.secho(
			f"File {sql_file_path} not found. Trying to check in alternative directories.", fg="yellow"
		)
		for dir in dirs:
			potential_path = Path(dir) / Path(sql_file_path)
			if potential_path.exists():
				sql_file_path = str(potential_path.resolve())
				click.secho(f"File {sql_file_path} found.", fg="green")
				break
		else:
			click.secho(f"File {sql_file_path} not found.", fg="red")
			sys.exit(1)

	if is_partial(sql_file_path):
		click.secho(
			"Partial Backup file detected. You cannot use a partial file to restore a Nxenv site.",
			fg="red",
		)
		click.secho(
			"Use `nxcli partial-restore` to restore a partial backup to an existing site.",
			fg="yellow",
		)
		sys.exit(1)

	# Check if the backup is of an older version of nxenv and the user hasn't specified force
	if is_downgrade(sql_file_path, verbose=True) and not force:
		warn_message = (
			"This is not recommended and may lead to unexpected behaviour. " "Do you want to continue anyway?"
		)
		click.confirm(warn_message, abort=True)

	# Validate the sql file
	validate_database_sql(sql_file_path, _raise=not force)

	try:
		_new_site(
			nxenv.conf.db_name,
			site,
			db_root_username=db_root_username,
			db_root_password=db_root_password,
			admin_password=admin_password,
			verbose=verbose,
			install_apps=install_app,
			source_sql=sql_file_path,
			force=True,
			db_type=nxenv.conf.db_type,
		)

	except Exception as err:
		print(err)
		sys.exit(1)


@click.command("partial-restore")
@click.argument("sql-file-path")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--encryption-key", help="Backup encryption key")
@pass_context
def partial_restore(context: CliCtxObj, sql_file_path, verbose, encryption_key=None):
	from nxenv.installer import is_partial, partial_restore
	from nxenv.utils.backups import decrypt_backup, get_or_generate_backup_encryption_key

	if not os.path.exists(sql_file_path):
		print("Invalid path", sql_file_path)
		sys.exit(1)

	site = get_site(context)
	verbose = context.verbose or verbose
	nxenv.init(site)
	nxenv.connect()
	err, out = nxenv.utils.execute_in_shell(f"file {sql_file_path}", check_exit_code=True)
	if err:
		click.secho("Failed to detect type of backup file", fg="red")
		sys.exit(1)

	if "cipher" in out.decode().split(":")[-1].strip():
		if encryption_key:
			click.secho("Encrypted backup file detected. Decrypting using provided key.", fg="yellow")
			key = encryption_key

		else:
			click.secho("Encrypted backup file detected. Decrypting using site config.", fg="yellow")
			key = get_or_generate_backup_encryption_key()

		with decrypt_backup(sql_file_path, key):
			if not is_partial(sql_file_path):
				click.secho(
					"Full backup file detected. Use `nxcli restore` to restore a Nxenv Site.",
					fg="red",
				)
				sys.exit(1)

			partial_restore(sql_file_path, verbose)

		# Rollback on unsuccessful decryption
		if not os.path.exists(sql_file_path):
			click.secho("Decryption failed. Please provide a valid key and try again.", fg="red")
			sys.exit(1)

	else:
		if not is_partial(sql_file_path):
			click.secho(
				"Full backup file detected. Use `nxcli restore` to restore a Nxenv Site.",
				fg="red",
			)
			sys.exit(1)

		partial_restore(sql_file_path, verbose)
	nxenv.destroy()


@click.command("reinstall")
@click.option("--admin-password", help="Administrator Password for reinstalled site")
@click.option(
	"--db-root-username",
	"--mariadb-root-username",
	help='Root username for MariaDB or PostgreSQL, Default is "root"',
)
@click.option("--db-root-password", "--mariadb-root-password", help="Root password for MariaDB or PostgreSQL")
@click.option("--yes", is_flag=True, default=False, help="Pass --yes to skip confirmation")
@pass_context
def reinstall(
	context: CliCtxObj, admin_password=None, db_root_username=None, db_root_password=None, yes=False
):
	"Reinstall site ie. wipe all data and start over"
	site = get_site(context)
	_reinstall(site, admin_password, db_root_username, db_root_password, yes, verbose=context.verbose)


def _reinstall(
	site,
	admin_password=None,
	db_root_username=None,
	db_root_password=None,
	yes=False,
	verbose=False,
):
	from nxenv.installer import _new_site

	if not yes:
		click.confirm("This will wipe your database. Are you sure you want to reinstall?", abort=True)
	try:
		nxenv.init(site)
		nxenv.connect()
		nxenv.clear_cache()
		installed = nxenv.get_installed_apps()
		nxenv.clear_cache()
	except Exception:
		installed = []
	finally:
		if nxenv.db:
			nxenv.db.close()
		nxenv.destroy()

	nxenv.init(site)

	_new_site(
		nxenv.conf.db_name,
		site,
		verbose=verbose,
		force=True,
		install_apps=installed,
		db_root_username=db_root_username,
		db_root_password=db_root_password,
		admin_password=admin_password,
	)


@click.command("install-app")
@click.argument("apps", nargs=-1)
@click.option("--force", is_flag=True, default=False)
@pass_context
def install_app(context: CliCtxObj, apps, force=False):
	"Install a new app to site, supports multiple apps"
	from nxenv.installer import install_app as _install_app
	from nxenv.utils.synchronization import filelock

	exit_code = 0

	if not context.sites:
		raise SiteNotSpecifiedError

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()

		with filelock("install_app", timeout=1):
			for app in apps:
				try:
					_install_app(app, verbose=context.verbose, force=force)
				except nxenv.IncompatibleApp as err:
					err_msg = f":\n{err}" if str(err) else ""
					print(f"App {app} is Incompatible with Site {site}{err_msg}")
					exit_code = 1
				except Exception as err:
					err_msg = f": {err!s}\n{nxenv.get_traceback(with_context=True)}"
					print(f"An error occurred while installing {app}{err_msg}")
					exit_code = 1

			if not exit_code:
				nxenv.db.commit()

		nxenv.destroy()

	sys.exit(exit_code)


@click.command("list-apps")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
@pass_context
def list_apps(context: CliCtxObj, format):
	"""
	List apps in site.
	"""

	summary_dict = {}

	def format_app(app):
		name_len = max(len(app.app_name) for app in apps)
		ver_len = max(len(app.app_version) for app in apps)
		template = f"{{0:{name_len}}} {{1:{ver_len}}} {{2}}"
		return template.format(app.app_name, app.app_version, app.git_branch)

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()
		site_title = click.style(f"{site}", fg="green") if len(context.sites) > 1 else ""
		installed_apps_info = []

		apps = nxenv.get_single("Installed Applications").installed_applications
		if apps:
			installed_apps_info.extend(format_app(app) for app in apps)
		else:
			installed_apps_info.extend(nxenv.get_installed_apps())

		installed_apps_info_str = "\n".join(installed_apps_info)
		summary = f"{site_title}\n{installed_apps_info_str}\n"
		summary_dict[site] = [app.app_name for app in apps]

		if format == "text" and installed_apps_info and summary:
			print(summary)

		nxenv.destroy()

	if format == "json":
		click.echo(nxenv.as_json(summary_dict))


@click.command("add-database-index")
@click.option("--doctype", help="DocType on which index needs to be added")
@click.option(
	"--column",
	multiple=True,
	help="Column to index. Multiple columns will create multi-column index in given order. To create a multiple, single column index, execute the command multiple times.",
)
@pass_context
def add_db_index(context: CliCtxObj, doctype, column):
	"Adds a new DB index and creates a property setter to persist it."
	from nxenv.custom.doctype.property_setter.property_setter import make_property_setter

	columns = column  # correct naming
	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()
		try:
			nxenv.db.add_index(doctype, columns)
			if len(columns) == 1:
				make_property_setter(
					doctype,
					columns[0],
					property="search_index",
					value="1",
					property_type="Check",
					for_doctype=False,  # Applied on docfield
				)
			nxenv.db.commit()
		finally:
			nxenv.destroy()

	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("describe-database-table")
@click.option("--doctype", help="DocType to describe")
@click.option(
	"--column",
	multiple=True,
	help="Explicitly fetch accurate cardinality from table data. This can be quite slow on large tables.",
)
@pass_context
def describe_database_table(context, doctype, column):
	"""Describes various statistics about the table.
	This is useful to build integration like
	This includes:
	1. Schema
	2. Indexes
	3. stats - total count of records
	4. if column is specified then extra stats are generated for column:
	        Distinct values count in column
	"""
	if doctype is None:
		raise click.UsageError("--doctype <doctype> is required")
	import json

	from nxenv.core.doctype.recorder.recorder import _fetch_table_stats

	for site in context.sites:
		nxenv.init(site=site)
		nxenv.connect()
		try:
			data = _fetch_table_stats(doctype, column)
			# NOTE: Do not print anything else in this to avoid clobbering the output.
			print(json.dumps(data, indent=2))
		finally:
			nxenv.destroy()

	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("add-system-manager")
@click.argument("email")
@click.option("--first-name")
@click.option("--last-name")
@click.option("--password")
@click.option("--send-welcome-email", default=False, is_flag=True)
@pass_context
def add_system_manager(context: CliCtxObj, email, first_name, last_name, send_welcome_email, password):
	"Add a new system manager to a site"
	import nxenv.utils.user

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()
		try:
			nxenv.utils.user.add_system_manager(email, first_name, last_name, send_welcome_email, password)
			nxenv.db.commit()
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("add-user")
@click.argument("email")
@click.option("--first-name")
@click.option("--last-name")
@click.option("--password")
@click.option("--user-type")
@click.option("--add-role", multiple=True)
@click.option("--send-welcome-email", default=False, is_flag=True)
@pass_context
def add_user_for_sites(
	context: CliCtxObj, email, first_name, last_name, user_type, send_welcome_email, password, add_role
):
	"Add user to a site"
	import nxenv.utils.user

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()
		try:
			add_new_user(email, first_name, last_name, user_type, send_welcome_email, password, add_role)
			nxenv.db.commit()
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("disable-user")
@click.argument("email")
@pass_context
def disable_user(context: CliCtxObj, email):
	"""Disable a user account on site."""
	site = get_site(context)
	with nxenv.init_site(site):
		nxenv.connect()
		user = nxenv.get_doc("User", email)
		user.enabled = 0
		user.save(ignore_permissions=True)
		nxenv.db.commit()


@click.command("migrate")
@click.option("--skip-failing", is_flag=True, help="Skip patches that fail to run")
@click.option("--skip-search-index", is_flag=True, help="Skip search indexing for web documents")
@pass_context
def migrate(context: CliCtxObj, skip_failing=False, skip_search_index=False):
	"Run patches, sync schema and rebuild files/translations"

	from nxenv.migrate import SiteMigration

	for site in context.sites:
		click.secho(f"Migrating {site}", fg="green")
		try:
			SiteMigration(
				skip_failing=skip_failing,
				skip_search_index=skip_search_index,
			).run(site=site)
		finally:
			print()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("migrate-to")
def migrate_to():
	"Migrates site to the specified provider"
	from nxenv.integrations.nxenv_providers import migrate_to

	migrate_to()


@click.command("run-patch")
@click.argument("module")
@click.option("--force", is_flag=True)
@pass_context
def run_patch(context: CliCtxObj, module, force):
	"Run a particular patch"
	import nxenv.modules.patch_handler

	for site in context.sites:
		nxenv.init(site)
		try:
			nxenv.connect()
			nxenv.modules.patch_handler.run_single(module, force=force or context.force)
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("reload-doc")
@click.argument("module")
@click.argument("doctype")
@click.argument("docname")
@pass_context
def reload_doc(context: CliCtxObj, module, doctype, docname):
	"Reload schema for a DocType"
	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			nxenv.reload_doc(module, doctype, docname, force=context.force)
			nxenv.db.commit()
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("reload-doctype")
@click.argument("doctype")
@pass_context
def reload_doctype(context: CliCtxObj, doctype):
	"Reload schema for a DocType"
	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			nxenv.reload_doctype(doctype, force=context.force)
			nxenv.db.commit()
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("add-to-hosts")
@pass_context
def add_to_hosts(context: CliCtxObj):
	"Add site to hosts"
	for site in context.sites:
		nxenv.commands.popen(f"echo '127.0.0.1\t{site}\n::1\t{site}' | sudo tee -a /etc/hosts")
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("use")
@click.argument("site")
def _use(site, sites_path="."):
	"Set a default site"
	use(site, sites_path=sites_path)


def use(site, sites_path="."):
	from nxenv.installer import update_site_config

	if os.path.exists(os.path.join(sites_path, site)):
		sites_path = os.getcwd()
		conifg = os.path.join(sites_path, "common_site_config.json")
		update_site_config("default_site", site, validate=False, site_config_path=conifg)
		print(f"Current Site set to {site}")
	else:
		print(f"Site {site} does not exist")


@click.command("backup")
@click.option("--with-files", default=False, is_flag=True, help="Take backup with files")
@click.option(
	"--include",
	"--only",
	"-i",
	default="",
	type=str,
	help="Specify the DocTypes to backup seperated by commas",
)
@click.option(
	"--exclude",
	"-e",
	default="",
	type=str,
	help="Specify the DocTypes to not backup seperated by commas",
)
@click.option("--backup-path", default=None, help="Set path for saving all the files in this operation")
@click.option("--backup-path-db", default=None, help="Set path for saving database file")
@click.option("--backup-path-files", default=None, help="Set path for saving public file")
@click.option("--backup-path-private-files", default=None, help="Set path for saving private file")
@click.option("--backup-path-conf", default=None, help="Set path for saving config file")
@click.option(
	"--ignore-backup-conf",
	default=False,
	is_flag=True,
	help="Ignore excludes/includes set in config",
)
@click.option("--verbose", default=False, is_flag=True, help="Add verbosity")
@click.option("--compress", default=False, is_flag=True, help="Compress private and public files")
@click.option("--old-backup-metadata", default=False, is_flag=True, help="Use older backup metadata")
@pass_context
def backup(
	context: CliCtxObj,
	with_files=False,
	backup_path=None,
	backup_path_db=None,
	backup_path_files=None,
	backup_path_private_files=None,
	backup_path_conf=None,
	ignore_backup_conf=False,
	verbose=False,
	compress=False,
	include="",
	exclude="",
	old_backup_metadata=False,
):
	"Backup"

	from nxenv.utils.backups import scheduled_backup

	verbose = verbose or context.verbose
	exit_code = 0
	rollback_callback = None

	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			rollback_callback = CallbackManager()
			odb = scheduled_backup(
				ignore_files=not with_files,
				backup_path=backup_path,
				backup_path_db=backup_path_db,
				backup_path_files=backup_path_files,
				backup_path_private_files=backup_path_private_files,
				backup_path_conf=backup_path_conf,
				ignore_conf=ignore_backup_conf,
				include_doctypes=include,
				exclude_doctypes=exclude,
				compress=compress,
				verbose=verbose,
				force=True,
				old_backup_metadata=old_backup_metadata,
				rollback_callback=rollback_callback,
			)
		except Exception:
			click.secho(
				f"Backup failed for Site {site}. Database or site_config.json may be corrupted",
				fg="red",
			)
			if rollback_callback:
				rollback_callback.run()
				rollback_callback = None
			if verbose:
				print(nxenv.get_traceback(with_context=True))
			exit_code = 1
			continue
		if nxenv.get_system_settings("encrypt_backup") and nxenv.get_site_config().encryption_key:
			click.secho(
				"Backup encryption is turned on. Please note the backup encryption key.",
				fg="yellow",
			)

		odb.print_summary()
		click.secho(
			"Backup for Site {} has been successfully completed{}".format(
				site, " with files" if with_files else ""
			),
			fg="green",
		)
		nxenv.destroy()

	if not context.sites:
		raise SiteNotSpecifiedError

	sys.exit(exit_code)


@click.command("remove-from-installed-apps")
@click.argument("app")
@pass_context
def remove_from_installed_apps(context: CliCtxObj, app):
	"Remove app from site's installed-apps list"
	ensure_app_not_nxenv(app)
	from nxenv.installer import remove_from_installed_apps

	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			remove_from_installed_apps(app)
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("uninstall-app")
@click.argument("app")
@click.option(
	"--yes",
	"-y",
	help="To bypass confirmation prompt for uninstalling the app",
	is_flag=True,
	default=False,
)
@click.option("--dry-run", help="List all doctypes that will be deleted", is_flag=True, default=False)
@click.option("--no-backup", help="Do not backup the site", is_flag=True, default=False)
@click.option("--force", help="Force remove app from site", is_flag=True, default=False)
@pass_context
def uninstall(context: CliCtxObj, app, dry_run, yes, no_backup, force):
	"Remove app and linked modules from site"
	ensure_app_not_nxenv(app)
	from nxenv.installer import remove_app
	from nxenv.utils.synchronization import filelock

	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			with filelock("uninstall_app"):
				remove_app(app_name=app, dry_run=dry_run, yes=yes, no_backup=no_backup, force=force)
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("drop-site")
@click.argument("site")
@click.option(
	"--db-root-username",
	"--mariadb-root-username",
	"--root-login",
	help='Root username for MariaDB or PostgreSQL, Default is "root"',
)
@click.option(
	"--db-root-password",
	"--mariadb-root-password",
	"--root-password",
	help="Root password for MariaDB or PostgreSQL",
)
@click.option("--archived-sites-path")
@click.option("--no-backup", is_flag=True, default=False)
@click.option("--force", help="Force drop-site even if an error is encountered", is_flag=True, default=False)
def drop_site(
	site,
	db_root_username="root",
	db_root_password=None,
	archived_sites_path=None,
	force=False,
	no_backup=False,
):
	"""Remove a site from database and filesystem."""
	_drop_site(site, db_root_username, db_root_password, archived_sites_path, force, no_backup)


def _drop_site(
	site,
	db_root_username=None,
	db_root_password=None,
	archived_sites_path=None,
	force=False,
	no_backup=False,
):
	from nxenv.database import drop_user_and_database
	from nxenv.utils.backups import scheduled_backup

	nxenv.init(site)
	nxenv.connect()

	try:
		if not no_backup:
			click.secho(f"Taking backup of {site}", fg="green")
			odb = scheduled_backup(ignore_files=False, ignore_conf=True, force=True, verbose=True)
			odb.print_summary()
	except Exception as err:
		if force:
			pass
		else:
			messages = [
				"=" * 80,
				f"Error: The operation has stopped because backup of {site}'s database failed.",
				f"Reason: {err!s}\n",
				"Fix the issue and try again.",
				f"Hint: Use 'nxcli drop-site {site} --force' to force the removal of {site}",
			]
			click.echo("\n".join(messages))
			sys.exit(1)

	click.secho("Dropping site database and user", fg="green")

	nxenv.flags.root_login = db_root_username
	nxenv.flags.root_password = db_root_password

	drop_user_and_database(nxenv.conf.db_name, nxenv.conf.db_user)

	archived_sites_path = archived_sites_path or os.path.join(
		nxenv.utils.get_nxcli_path(), "archived", "sites"
	)
	archived_sites_path = os.path.realpath(archived_sites_path)

	click.secho(f"Moving site to archive under {archived_sites_path}", fg="green")
	os.makedirs(archived_sites_path, exist_ok=True)
	move(archived_sites_path, site)


def move(dest_dir, site):
	if not os.path.isdir(dest_dir):
		raise Exception("destination is not a directory or does not exist")

	nxenv.init(site)
	old_path = nxenv.utils.get_site_path()
	new_path = os.path.join(dest_dir, site)

	# check if site dump of same name already exists
	site_dump_exists = True
	count = 0
	while site_dump_exists:
		final_new_path = new_path + str(count or "")
		site_dump_exists = os.path.exists(final_new_path)
		count += 1

	shutil.move(old_path, final_new_path)
	nxenv.destroy()
	return final_new_path


@click.command("set-password")
@click.argument("user")
@click.argument("password", required=False)
@click.option("--logout-all-sessions", help="Log out from all sessions", is_flag=True, default=False)
@pass_context
def set_password(context: CliCtxObj, user, password=None, logout_all_sessions=False):
	"Set password for a user on a site"
	if not context.sites:
		raise SiteNotSpecifiedError

	for site in context.sites:
		set_user_password(site, user, password, logout_all_sessions)


@click.command("set-admin-password")
@click.argument("admin-password", required=False)
@click.option("--logout-all-sessions", help="Log out from all sessions", is_flag=True, default=False)
@pass_context
def set_admin_password(context: CliCtxObj, admin_password=None, logout_all_sessions=False):
	"Set Administrator password for a site"
	if not context.sites:
		raise SiteNotSpecifiedError

	for site in context.sites:
		set_user_password(site, "Administrator", admin_password, logout_all_sessions)


def set_user_password(site, user, password, logout_all_sessions=False):
	import getpass

	from nxenv.utils.password import update_password

	try:
		nxenv.init(site)

		while not password:
			password = getpass.getpass(f"{user}'s password for {site}: ")

		nxenv.connect()
		if not nxenv.db.exists("User", user):
			print(f"User {user} does not exist")
			sys.exit(1)

		update_password(user=user, pwd=password, logout_all_sessions=logout_all_sessions)
		nxenv.db.commit()
	finally:
		nxenv.destroy()


@click.command("set-last-active-for-user")
@click.option("--user", help="Setup last active date for user")
@pass_context
def set_last_active_for_user(context: CliCtxObj, user=None):
	"Set users last active date to current datetime"
	from nxenv.core.doctype.user.user import get_system_users
	from nxenv.utils import now_datetime

	site = get_site(context)

	with nxenv.init_site(site):
		nxenv.connect()
		if not user:
			user = get_system_users(limit=1)
			if len(user) > 0:
				user = user[0]
			else:
				return

		nxenv.db.set_value("User", user, "last_active", now_datetime())
		nxenv.db.commit()


@click.command("publish-realtime")
@click.argument("event")
@click.option("--message")
@click.option("--room")
@click.option("--user")
@click.option("--doctype")
@click.option("--docname")
@click.option("--after-commit")
@pass_context
def publish_realtime(context: CliCtxObj, event, message, room, user, doctype, docname, after_commit):
	"Publish realtime event from nxcli"
	from nxenv import publish_realtime

	for site in context.sites:
		try:
			nxenv.init(site)
			nxenv.connect()
			publish_realtime(
				event,
				message=message,
				room=room,
				user=user,
				doctype=doctype,
				docname=docname,
				after_commit=after_commit,
			)
			nxenv.db.commit()
		finally:
			nxenv.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("browse")
@click.argument("site", required=False)
@click.option("--user", required=False, help="Login as user")
@pass_context
def browse(context: CliCtxObj, site, user=None):
	"""Opens the site on web browser"""
	from nxenv.auth import CookieManager, LoginManager

	site = get_site(context, raise_err=False) or site

	if not site:
		raise SiteNotSpecifiedError

	if site not in nxenv.utils.get_sites():
		click.echo(f"\nSite named {click.style(site, bold=True)} doesn't exist\n", err=True)
		sys.exit(1)

	nxenv.init(site)
	nxenv.connect()

	sid = ""
	if user:
		if not nxenv.db.exists("User", user):
			click.echo(f"User {user} does not exist")
			sys.exit(1)

		if nxenv.conf.developer_mode or user == "Administrator":
			nxenv.utils.set_request(path="/")
			nxenv.local.cookie_manager = CookieManager()
			nxenv.local.login_manager = LoginManager()
			nxenv.local.login_manager.login_as(user)
			sid = f"/app?sid={nxenv.session.sid}"
		else:
			click.echo("Please enable developer mode to login as a user")

	url = f"{nxenv.utils.get_site_url(site)}{sid}"

	if user == "Administrator":
		click.echo(f"Login URL: {url}")

	click.launch(url)


@click.command("start-recording")
@pass_context
def start_recording(context: CliCtxObj):
	"""Start Nxenv Recorder."""
	import nxenv.recorder

	for site in context.sites:
		nxenv.init(site)
		nxenv.set_user("Administrator")
		nxenv.recorder.start()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("stop-recording")
@pass_context
def stop_recording(context: CliCtxObj):
	"""Stop Nxenv Recorder."""
	import nxenv.recorder

	for site in context.sites:
		nxenv.init(site)
		nxenv.set_user("Administrator")
		nxenv.recorder.stop()
	if not context.sites:
		raise SiteNotSpecifiedError


@click.command("ngrok")
@click.option("--bind-tls", is_flag=True, default=False, help="Returns a reference to the https tunnel.")
@click.option(
	"--use-default-authtoken",
	is_flag=True,
	default=False,
	help="Use the auth token present in ngrok's config.",
)
@pass_context
def start_ngrok(context: CliCtxObj, bind_tls, use_default_authtoken):
	"""Start a ngrok tunnel to your local development server."""
	from pyngrok import ngrok

	site = get_site(context)
	nxenv.init(site)

	ngrok_authtoken = nxenv.conf.ngrok_authtoken
	if not use_default_authtoken:
		if not ngrok_authtoken:
			click.echo(
				f"\n{click.style('ngrok_authtoken', fg='yellow')} not found in site config.\n"
				"Please register for a free ngrok account at: https://dashboard.ngrok.com/signup and place the obtained authtoken in the site config.",
			)
			sys.exit(1)

		ngrok.set_auth_token(ngrok_authtoken)

	port = nxenv.conf.http_port
	if not port and nxenv.conf.developer_mode:
		port = nxenv.conf.webserver_port

	tunnel = ngrok.connect(addr=str(port), host_header=site, bind_tls=bind_tls)
	print(f"Public URL: {tunnel.public_url}")
	print("Inspect logs at http://127.0.0.1:4040")

	ngrok_process = ngrok.get_ngrok_process()
	try:
		# Block until CTRL-C or some other terminating event
		ngrok_process.proc.wait()
	except KeyboardInterrupt:
		print("Shutting down server...")
		nxenv.destroy()
		ngrok.kill()


@click.command("build-search-index")
@pass_context
def build_search_index(context):
	"""Rebuild search index used by global search."""
	from nxenv.search.website_search import build_index_for_all_routes

	site = get_site(context)
	if not site:
		raise SiteNotSpecifiedError

	print(f"Building search index for {site}")
	nxenv.init(site)
	nxenv.connect()
	try:
		build_index_for_all_routes()
	finally:
		nxenv.destroy()


@click.command("clear-log-table")
@click.option("--doctype", required=True, type=str, help="Log DocType")
@click.option("--days", type=int, help="Keep records for days")
@click.option("--no-backup", is_flag=True, default=False, help="Do not backup the table")
@pass_context
def clear_log_table(context: CliCtxObj, doctype, days, no_backup):
	"""If any logtype table grows too large then clearing it with DELETE query
	is not feasible in reasonable time. This command copies recent data to new
	table and replaces current table with new smaller table.


	ref: https://mariadb.com/kb/en/big-deletes/#deleting-more-than-half-a-table
	"""
	from nxenv.core.doctype.log_settings.log_settings import LOG_DOCTYPES
	from nxenv.core.doctype.log_settings.log_settings import clear_log_table as clear_logs
	from nxenv.utils.backups import scheduled_backup

	if not context.sites:
		raise SiteNotSpecifiedError

	if doctype not in LOG_DOCTYPES:
		raise nxenv.ValidationError(f"Unsupported logging DocType: {doctype}")

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()

		if not no_backup:
			scheduled_backup(
				ignore_conf=False,
				include_doctypes=doctype,
				ignore_files=True,
				force=True,
			)
			click.echo(f"Backed up {doctype}")

		try:
			click.echo(f"Copying {doctype} records from last {days} days to temporary table.")
			clear_logs(doctype, days=days)
		except Exception as e:
			click.echo(f"Log cleanup for {doctype} failed:\n{e}")
			sys.exit(1)
		else:
			click.secho(f"Cleared {doctype} records older than {days} days", fg="green")


@click.command("trim-database")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be deleted")
@click.option("--format", "-f", default="text", type=click.Choice(["json", "text"]), help="Output format")
@click.option("--no-backup", is_flag=True, default=False, help="Do not backup the site")
@click.option(
	"--yes",
	"-y",
	help="To bypass confirmation prompt.",
	is_flag=True,
	default=False,
)
@pass_context
def trim_database(context: CliCtxObj, dry_run, format, no_backup, yes=False):
	"""Remove database tables for deleted DocTypes."""
	if not context.sites:
		raise SiteNotSpecifiedError

	from nxenv.utils.backups import scheduled_backup

	ALL_DATA = {}

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()

		TABLES_TO_DROP = []
		STANDARD_TABLES = get_standard_tables()
		information_schema = nxenv.qb.Schema("information_schema")
		table_name = nxenv.qb.Field("table_name").as_("name")

		database_tables: list[str] = (
			nxenv.qb.from_(information_schema.tables)
			.select(table_name)
			.where(information_schema.tables.table_schema == nxenv.conf.db_name)
			.where(information_schema.tables.table_type == "BASE TABLE")
			.run(pluck=True)
		)
		doctype_tables = nxenv.get_all("DocType", pluck="name")

		for table_name in database_tables:
			if not table_name.startswith("tab"):
				continue
			if table_name.replace("tab", "", 1) not in doctype_tables and table_name not in STANDARD_TABLES:
				TABLES_TO_DROP.append(table_name)

		if not TABLES_TO_DROP:
			if format == "text":
				click.secho(f"{site}: No ghost tables", fg="green")
		else:
			if format == "text":
				print(f"{site}: Following tables will be dropped:")
				print("\n".join(f"* {dt}" for dt in TABLES_TO_DROP))

			if dry_run:
				continue

			if not yes:
				click.confirm("Do you want to continue?", abort=True)

			if not no_backup:
				if format == "text":
					print(f"Backing Up Tables: {', '.join(TABLES_TO_DROP)}")

				odb = scheduled_backup(
					ignore_conf=False,
					include_doctypes=",".join(x.replace("tab", "", 1) for x in TABLES_TO_DROP),
					ignore_files=True,
					force=True,
				)
				if format == "text":
					odb.print_summary()
					print("\nTrimming Database")

			for table in TABLES_TO_DROP:
				if format == "text":
					print(f"* Dropping Table '{table}'...")
				nxenv.db.sql_ddl(f"drop table `{table}`")

			ALL_DATA[nxenv.local.site] = TABLES_TO_DROP
		nxenv.destroy()

	if format == "json":
		import json

		print(json.dumps(ALL_DATA, indent=1))


def get_standard_tables():
	import re

	tables = []
	sql_file = os.path.join(
		"..",
		"apps",
		"nxenv",
		"nxenv",
		"database",
		nxenv.conf.db_type,
		f"framework_{nxenv.conf.db_type}.sql",
	)
	content = open(sql_file).read().splitlines()

	for line in content:
		table_found = re.search(r"""CREATE TABLE ("|`)(.*)?("|`) \(""", line)
		if table_found:
			tables.append(table_found.group(2))

	return tables


@click.command("trim-tables")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be deleted")
@click.option("--format", "-f", default="table", type=click.Choice(["json", "table"]), help="Output format")
@click.option("--no-backup", is_flag=True, default=False, help="Do not backup the site")
@pass_context
def trim_tables(context: CliCtxObj, dry_run, format, no_backup):
	"""Remove columns from tables where fields are deleted from doctypes."""
	if not context.sites:
		raise SiteNotSpecifiedError

	from nxenv.model.meta import trim_tables
	from nxenv.utils.backups import scheduled_backup

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()

		if not (no_backup or dry_run):
			click.secho(f"Taking backup for {nxenv.local.site}", fg="green")
			odb = scheduled_backup(ignore_files=False, force=True)
			odb.print_summary()

		try:
			trimmed_data = trim_tables(dry_run=dry_run, quiet=format == "json")

			if format == "table" and not dry_run:
				click.secho(f"The following data have been removed from {nxenv.local.site}", fg="green")

			handle_data(trimmed_data, format=format)
		finally:
			nxenv.destroy()


def handle_data(data: dict, format="json"):
	if format == "json":
		import json

		print(json.dumps({nxenv.local.site: data}, indent=1, sort_keys=True))
	else:
		from nxenv.utils.commands import render_table

		data = [["DocType", "Fields"]] + [[table, ", ".join(columns)] for table, columns in data.items()]
		render_table(data)


def add_new_user(
	email,
	first_name=None,
	last_name=None,
	user_type="System User",
	send_welcome_email=False,
	password=None,
	role=None,
):
	user = nxenv.new_doc("User")
	user.update(
		{
			"name": email,
			"email": email,
			"enabled": 1,
			"first_name": first_name or email,
			"last_name": last_name,
			"user_type": user_type,
			"send_welcome_email": 1 if send_welcome_email else 0,
		}
	)
	user.insert()
	user.add_roles(*role)
	if password:
		from nxenv.utils.password import update_password

		update_password(user=user.name, pwd=password)


def ensure_app_not_nxenv(app: str) -> None:
	"""
	Ensure that the app name passed is not 'nxenv'

	:param app: Name of the app
	:return: Nothing
	"""
	if app == "nxenv":
		click.secho("You cannot remove or uninstall the app `nxenv`", fg="red")
		sys.exit(1)


@click.command("bypass-patch")
@click.argument("patch_name")
@click.option("--yes", "-y", is_flag=True, default=False, help="Pass --yes to skip confirmation")
@pass_context
def bypass_patch(context: CliCtxObj, patch_name: str, yes: bool):
	"""Bypass a patch permanently instead of migrating using the --skip-failing flag."""
	from nxenv.modules.patch_handler import update_patch_log

	if not context.sites:
		raise SiteNotSpecifiedError

	if not yes:
		click.confirm(
			f"This will bypass the patch {patch_name!r} forever and register it as successful.\nAre you sure you want to continue?",
			abort=True,
		)

	for site in context.sites:
		nxenv.init(site)
		nxenv.connect()
		try:
			update_patch_log(patch_name)
			nxenv.db.commit()
		finally:
			nxenv.destroy()


commands = [
	add_system_manager,
	add_user_for_sites,
	add_db_index,
	describe_database_table,
	backup,
	drop_site,
	install_app,
	list_apps,
	migrate,
	migrate_to,
	new_site,
	reinstall,
	reload_doc,
	reload_doctype,
	remove_from_installed_apps,
	restore,
	run_patch,
	set_password,
	set_admin_password,
	uninstall,
	disable_user,
	_use,
	set_last_active_for_user,
	publish_realtime,
	browse,
	start_recording,
	stop_recording,
	add_to_hosts,
	start_ngrok,
	build_search_index,
	partial_restore,
	trim_tables,
	trim_database,
	clear_log_table,
	bypass_patch,
]
