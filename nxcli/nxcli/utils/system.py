# imports - standard imports
import grp
import os
import pwd
import shutil
import sys

# imports - module imports
import nxcli
from nxcli.utils import (
	exec_cmd,
	get_process_manager,
	log,
	run_nxenv_cmd,
	sudoers_file,
	which,
	is_valid_nxenv_branch,
)
from nxcli.utils.nxcli import build_assets, clone_apps_from
from nxcli.utils.render import job


@job(title="Initializing Nxcli {path}", success="Nxcli {path} initialized")
def init(
	path,
	apps_path=None,
	no_procfile=False,
	no_backups=False,
	nxenv_path=None,
	nxenv_branch=None,
	verbose=False,
	clone_from=None,
	skip_redis_config_generation=False,
	clone_without_update=False,
	skip_assets=False,
	python="python3",
	install_app=None,
	dev=False,
):
	"""Initialize a new nxcli directory

	* create a nxcli directory in the given path
	* setup logging for the nxcli
	* setup env for the nxcli
	* setup config (dir/pids/redis/procfile) for the nxcli
	* setup patches.txt for nxcli
	* clone & install nxenv
	        * install python & node dependencies
	        * build assets
	* setup backups crontab
	"""

	# Use print("\033c", end="") to clear entire screen after each step and re-render each list
	# another way => https://stackoverflow.com/a/44591228/10309266

	import nxcli.cli
	from nxcli.app import get_app, install_apps_from_path
	from nxcli.nxcli import Nxcli

	verbose = nxcli.cli.verbose or verbose

	nxcli = Nxcli(path)

	nxcli.setup.dirs()
	nxcli.setup.logging()
	nxcli.setup.env(python=python)
	config = {}
	if dev:
		config["developer_mode"] = 1
	nxcli.setup.config(
		redis=not skip_redis_config_generation,
		procfile=not no_procfile,
		additional_config=config,
	)
	nxcli.setup.patches()

	# local apps
	if clone_from:
		clone_apps_from(
			nxcli_path=path, clone_from=clone_from, update_app=not clone_without_update
		)

	# remote apps
	else:
		nxenv_path = nxenv_path or "https://github.com/nxenv/nxenv.git"
		is_valid_nxenv_branch(nxenv_path=nxenv_path, nxenv_branch=nxenv_branch)
		get_app(
			nxenv_path,
			branch=nxenv_branch,
			nxcli_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

		# fetch remote apps using config file - deprecate this!
		if apps_path:
			install_apps_from_path(apps_path, nxcli_path=path)

	# getting app on nxcli init using --install-app
	if install_app:
		get_app(
			install_app,
			branch=nxenv_branch,
			nxcli_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

	if not skip_assets:
		build_assets(nxcli_path=path)

	if not no_backups:
		nxcli.setup.backups()


def setup_sudoers(user):
	from nxcli.config.lets_encrypt import get_certbot_path

	if not os.path.exists("/etc/sudoers.d"):
		os.makedirs("/etc/sudoers.d")

		set_permissions = not os.path.exists("/etc/sudoers")
		with open("/etc/sudoers", "a") as f:
			f.write("\n#includedir /etc/sudoers.d\n")

		if set_permissions:
			os.chmod("/etc/sudoers", 0o440)

	template = nxcli.config.env().get_template("nxenv_sudoers")
	nxenv_sudoers = template.render(
		**{
			"user": user,
			"service": which("service"),
			"systemctl": which("systemctl"),
			"nginx": which("nginx"),
			"certbot": get_certbot_path(),
		}
	)

	with open(sudoers_file, "w") as f:
		f.write(nxenv_sudoers)

	os.chmod(sudoers_file, 0o440)
	log(f"Sudoers was set up for user {user}", level=1)


def start(no_dev=False, concurrency=None, procfile=None, no_prefix=False, procman=None):
	program = which(procman) if procman else get_process_manager()
	if not program:
		raise Exception("No process manager found")

	os.environ["PYTHONUNBUFFERED"] = "true"
	if not no_dev:
		os.environ["DEV_SERVER"] = "true"

	command = [program, "start"]
	if concurrency:
		command.extend(["-c", concurrency])

	if procfile:
		command.extend(["-f", procfile])

	if no_prefix:
		command.extend(["--no-prefix"])

	os.execv(program, command)


def migrate_site(site, nxcli_path="."):
	run_nxenv_cmd("--site", site, "migrate", nxcli_path=nxcli_path)


def backup_site(site, nxcli_path="."):
	run_nxenv_cmd("--site", site, "backup", nxcli_path=nxcli_path)


def backup_all_sites(nxcli_path="."):
	from nxcli.nxcli import Nxcli

	for site in Nxcli(nxcli_path).sites:
		backup_site(site, nxcli_path=nxcli_path)


def fix_prod_setup_perms(nxcli_path=".", nxenv_user=None):
	from glob import glob
	from nxcli.nxcli import Nxcli

	nxenv_user = nxenv_user or Nxcli(nxcli_path).conf.get("nxenv_user")

	if not nxenv_user:
		print("nxenv user not set")
		sys.exit(1)

	globs = ["logs/*", "config/*"]
	for glob_name in globs:
		for path in glob(glob_name):
			uid = pwd.getpwnam(nxenv_user).pw_uid
			gid = grp.getgrnam(nxenv_user).gr_gid
			os.chown(path, uid, gid)


def setup_fonts():
	fonts_path = os.path.join("/tmp", "fonts")

	if os.path.exists("/etc/fonts_backup"):
		return

	exec_cmd("git clone https://github.com/nxenv/fonts.git", cwd="/tmp")
	os.rename("/etc/fonts", "/etc/fonts_backup")
	os.rename("/usr/share/fonts", "/usr/share/fonts_backup")
	os.rename(os.path.join(fonts_path, "etc_fonts"), "/etc/fonts")
	os.rename(os.path.join(fonts_path, "usr_share_fonts"), "/usr/share/fonts")
	shutil.rmtree(fonts_path)
	exec_cmd("fc-cache -fv")
