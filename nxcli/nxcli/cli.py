# imports - standard imports
import atexit
from contextlib import contextmanager
from logging import Logger
import os
import pwd
import sys

# imports - third party imports
import click

# imports - module imports
import nxcli
from nxcli.nxcli import Nxcli
from nxcli.commands import nxcli_command
from nxcli.config.common_site_config import get_config
from nxcli.utils import (
	check_latest_version,
	drop_privileges,
	find_parent_nxcli,
	get_env_nxenv_commands,
	get_cmd_output,
	is_nxcli_directory,
	is_dist_editable,
	is_root,
	log,
	setup_logging,
	get_cmd_from_sysargv,
)
from nxcli.utils.nxcli import get_env_cmd
from importlib.util import find_spec


# these variables are used to show dynamic outputs on the terminal
dynamic_feed = False
verbose = False
is_envvar_warn_set = None
from_command_line = False  # set when commands are executed via the CLI
nxcli.LOG_BUFFER = []

change_uid_msg = "You should not run this command as root"
src = os.path.dirname(__file__)
SKIP_MODULE_TRACEBACK = ("click",)


@contextmanager
def execute_cmd(check_for_update=True, command: str = None, logger: Logger = None):
	if check_for_update:
		atexit.register(check_latest_version)

	try:
		yield
	except BaseException as e:
		return_code = getattr(e, "code", 1)

		if isinstance(e, Exception):
			click.secho(f"ERROR: {e}", fg="red")

		if return_code:
			logger.warning(f"{command} executed with exit code {return_code}")

		raise e


def cli():
	setup_clear_cache()
	global from_command_line, nxcli_config, is_envvar_warn_set, verbose

	from_command_line = True
	command = " ".join(sys.argv)
	argv = set(sys.argv)
	is_envvar_warn_set = not (os.environ.get("NXCLI_DEVELOPER") or os.environ.get("CI"))
	is_cli_command = len(sys.argv) > 1 and not argv.intersection({"src", "--version"})
	cmd_from_sys = get_cmd_from_sysargv()

	if "--verbose" in argv:
		verbose = True

	change_working_directory()
	logger = setup_logging()
	logger.info(command)

	nxcli_config = get_config(".")

	if is_cli_command:
		check_uid()
		change_uid()
		change_dir()

	if (
		is_envvar_warn_set
		and is_cli_command
		and not nxcli_config.get("developer_mode")
		and is_dist_editable(nxcli.PROJECT_NAME)
	):
		log(
			"nxcli is installed in editable mode!\n\nThis is not the recommended mode"
			" of installation for production. Instead, install the package from PyPI"
			" with: `pip install nxenv-nxcli`\n",
			level=3,
		)

	in_nxcli = is_nxcli_directory()

	if (
		not in_nxcli
		and len(sys.argv) > 1
		and not argv.intersection(
			{"init", "find", "src", "drop", "get", "get-app", "--version"}
		)
		and not cmd_requires_root()
	):
		log("Command not being executed in nxcli directory", level=3)

	if len(sys.argv) == 1 or sys.argv[1] == "--help":
		print(click.Context(nxcli_command).get_help())
		if in_nxcli:
			print(get_nxenv_help())
		return

	_opts = [x.opts + x.secondary_opts for x in nxcli_command.params]
	opts = {item for sublist in _opts for item in sublist}

	setup_exception_handler()

	# handle usages like `--use-feature='feat-x'` and `--use-feature 'feat-x'`
	if cmd_from_sys and cmd_from_sys.split("=", 1)[0].strip() in opts:
		nxcli_command()

	if cmd_from_sys in nxcli_command.commands:
		with execute_cmd(check_for_update=is_cli_command, command=command, logger=logger):
			nxcli_command()

	if in_nxcli:
		nxenv_cmd()

	nxcli_command()


def check_uid():
	if cmd_requires_root() and not is_root():
		log("superuser privileges required for this command", level=3)
		sys.exit(1)


def cmd_requires_root():
	if len(sys.argv) > 2 and sys.argv[2] in (
		"production",
		"sudoers",
		"lets-encrypt",
		"fonts",
		"print",
		"firewall",
		"ssh-port",
		"role",
		"fail2ban",
		"wildcard-ssl",
	):
		return True
	if len(sys.argv) >= 2 and sys.argv[1] in (
		"patch",
		"renew-lets-encrypt",
		"disable-production",
	):
		return True
	if len(sys.argv) > 2 and sys.argv[1] in ("install"):
		return True


def change_dir():
	if os.path.exists("config.json") or "init" in sys.argv:
		return
	dir_path_file = "/etc/nxenv_nxcli_dir"
	if os.path.exists(dir_path_file):
		with open(dir_path_file) as f:
			dir_path = f.read().strip()
		if os.path.exists(dir_path):
			os.chdir(dir_path)


def change_uid():
	if is_root() and not cmd_requires_root():
		nxenv_user = nxcli_config.get("nxenv_user")
		if nxenv_user:
			drop_privileges(uid_name=nxenv_user, gid_name=nxenv_user)
			os.environ["HOME"] = pwd.getpwnam(nxenv_user).pw_dir
		else:
			log(change_uid_msg, level=3)
			sys.exit(1)


def app_cmd(nxcli_path="."):
	f = get_env_cmd("python", nxcli_path=nxcli_path)
	os.chdir(os.path.join(nxcli_path, "sites"))
	os.execv(f, [f] + ["-m", "nxenv.utils.nxcli_helper"] + sys.argv[1:])


def nxenv_cmd(nxcli_path="."):
	f = get_env_cmd("python", nxcli_path=nxcli_path)
	os.chdir(os.path.join(nxcli_path, "sites"))
	os.execv(f, [f] + ["-m", "nxenv.utils.nxcli_helper", "nxenv"] + sys.argv[1:])


def get_nxenv_commands():
	if not is_nxcli_directory():
		return set()

	return set(get_env_nxenv_commands())


def get_nxenv_help(nxcli_path="."):
	python = get_env_cmd("python", nxcli_path=nxcli_path)
	sites_path = os.path.join(nxcli_path, "sites")
	try:
		out = get_cmd_output(
			f"{python} -m nxenv.utils.nxcli_helper get-nxenv-help", cwd=sites_path
		)
		return "\n\nFramework commands:\n" + out.split("Commands:")[1]
	except Exception:
		return ""


def change_working_directory():
	"""Allows nxcli commands to be run from anywhere inside a nxcli directory"""
	cur_dir = os.path.abspath(".")
	nxcli_path = find_parent_nxcli(cur_dir)
	nxcli.current_path = os.getcwd()
	nxcli.updated_path = nxcli_path

	if nxcli_path:
		os.chdir(nxcli_path)


def setup_clear_cache():
	from copy import copy

	f = copy(os.chdir)

	def _chdir(*args, **kwargs):
		Nxcli.cache_clear()
		get_env_cmd.cache_clear()
		return f(*args, **kwargs)

	os.chdir = _chdir


def setup_exception_handler():
	from traceback import format_exception
	from nxcli.exceptions import CommandFailedError

	def handle_exception(exc_type, exc_info, tb):
		if exc_type == CommandFailedError:
			print("".join(generate_exc(exc_type, exc_info, tb)))
		else:
			sys.__excepthook__(exc_type, exc_info, tb)

	def generate_exc(exc_type, exc_info, tb):
		TB_SKIP = [
			os.path.dirname(find_spec(module).origin) for module in SKIP_MODULE_TRACEBACK
		]

		for tb_line in format_exception(exc_type, exc_info, tb):
			for skip_module in TB_SKIP:
				if skip_module not in tb_line:
					yield tb_line

	sys.excepthook = handle_exception
