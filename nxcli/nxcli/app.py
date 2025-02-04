# imports - standard imports
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid
import tarfile
import typing
from collections import OrderedDict
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# imports - third party imports
import click
import git
import semantic_version as sv

# imports - module imports
import nxcli
from nxcli.utils import (
	UNSET_ARG,
	fetch_details_from_tag,
	get_app_cache_extract_filter,
	get_available_folder_name,
	get_nxcli_cache_path,
	is_nxcli_directory,
	is_git_url,
	is_valid_nxenv_branch,
	log,
	run_nxenv_cmd,
	get_file_md5,
)
from nxcli.utils.nxcli import build_assets, install_python_dev_dependencies
from nxcli.utils.render import step

if typing.TYPE_CHECKING:
	from nxcli.nxcli import Nxcli


logger = logging.getLogger(nxcli.PROJECT_NAME)


class AppMeta:
	def __init__(self, name: str, branch: str = None, to_clone: bool = True):
		"""
		name (str): This could look something like
		        1. https://github.com/nxenv/healthcare.git
		        2. git@github.com:nxenv/healthcare.git
		        3. nxenv/healthcare@develop
		        4. healthcare
		        5. healthcare@develop, healthcare@v13.12.1

		References for Version Identifiers:
		 * https://www.python.org/dev/peps/pep-0440/#version-specifiers
		 * https://docs.npmjs.com/about-semantic-versioning

		class Healthcare(AppConfig):
		        dependencies = [{"nxenv/erpnext": "~13.17.0"}]
		"""
		self.name = name.rstrip("/")
		self.remote_server = "github.com"
		self.to_clone = to_clone
		self.on_disk = False
		self.use_ssh = False
		self.from_apps = False
		self.is_url = False
		self.branch = branch
		self.app_name = None
		self.git_repo = None
		self.is_repo = (
			is_git_repo(app_path=get_repo_dir(self.name))
			if os.path.exists(get_repo_dir(self.name))
			else True
		)
		self.mount_path = os.path.abspath(
			os.path.join(urlparse(self.name).netloc, urlparse(self.name).path)
		)
		self.setup_details()

	def setup_details(self):
		# support for --no-git
		if not self.is_repo:
			self.repo = self.app_name = self.name
			return
		# fetch meta from installed apps
		if self.nxcli and os.path.exists(os.path.join(self.nxcli.name, "apps", self.name)):
			self.mount_path = os.path.join(self.nxcli.name, "apps", self.name)
			self.from_apps = True
			self._setup_details_from_mounted_disk()

		# fetch meta for repo on mounted disk
		elif os.path.exists(self.mount_path):
			self.on_disk = True
			self._setup_details_from_mounted_disk()

		# fetch meta for repo from remote git server - traditional get-app url
		elif is_git_url(self.name):
			self.is_url = True
			self.__setup_details_from_git()

		# fetch meta from new styled name tags & first party apps on github
		else:
			self._setup_details_from_name_tag()

		if self.git_repo:
			self.app_name = os.path.basename(os.path.normpath(self.git_repo.working_tree_dir))
		else:
			self.app_name = self.repo

	def _setup_details_from_mounted_disk(self):
		# If app is a git repo
		self.git_repo = git.Repo(self.mount_path)
		try:
			self.__setup_details_from_git(self.git_repo.remotes[0].url)
			if not (self.branch or self.tag):
				self.tag = self.branch = self.git_repo.active_branch.name
		except IndexError:
			self.org, self.repo, self.tag = os.path.split(self.mount_path)[-2:] + (self.branch,)
		except TypeError:
			# faced a "a detached symbolic reference as it points" in case you're in the middle of
			# some git shenanigans
			self.tag = self.branch = None

	def _setup_details_from_name_tag(self):
		using_cached = bool(self.cache_key)
		self.org, self.repo, self.tag = fetch_details_from_tag(self.name, using_cached)
		self.tag = self.tag or self.branch

	def __setup_details_from_git(self, url=None):
		name = url if url else self.name
		if name.startswith("git@") or name.startswith("ssh://"):
			self.use_ssh = True
			_first_part, _second_part = name.rsplit(":", 1)
			self.remote_server = _first_part.split("@")[-1]
			self.org, _repo = _second_part.rsplit("/", 1)
		else:
			protocal = "https://" if "https://" in name else "http://"
			self.remote_server, self.org, _repo = name.replace(protocal, "").rsplit("/", 2)

		self.tag = self.branch
		self.repo = _repo.split(".")[0]

	@property
	def url(self):
		if self.is_url or self.from_apps or self.on_disk:
			return self.name

		if self.use_ssh:
			return self.get_ssh_url()

		return self.get_http_url()

	def get_http_url(self):
		return f"https://{self.remote_server}/{self.org}/{self.repo}.git"

	def get_ssh_url(self):
		return f"git@{self.remote_server}:{self.org}/{self.repo}.git"


@lru_cache(maxsize=None)
class App(AppMeta):
	def __init__(
		self,
		name: str,
		branch: str = None,
		nxcli: "Nxcli" = None,
		soft_link: bool = False,
		cache_key=None,
		*args,
		**kwargs,
	):
		self.nxcli = nxcli
		self.soft_link = soft_link
		self.required_by = None
		self.local_resolution = []
		self.cache_key = cache_key
		self.pyproject = None
		super().__init__(name, branch, *args, **kwargs)

	@step(title="Fetching App {repo}", success="App {repo} Fetched")
	def get(self):
		branch = f"--branch {self.tag}" if self.tag else ""
		shallow = "--depth 1" if self.nxcli.shallow_clone else ""

		if not self.soft_link:
			cmd = "git clone"
			args = f"{self.url} {branch} {shallow} --origin upstream"
		else:
			cmd = "ln -s"
			args = f"{self.name}"

		fetch_txt = f"Getting {self.repo}"
		click.secho(fetch_txt, fg="yellow")
		logger.log(fetch_txt)

		self.nxcli.run(
			f"{cmd} {args}",
			cwd=os.path.join(self.nxcli.name, "apps"),
		)

	@step(title="Archiving App {repo}", success="App {repo} Archived")
	def remove(self, no_backup: bool = False):
		active_app_path = os.path.join("apps", self.app_name)

		if no_backup:
			if not os.path.islink(active_app_path):
				shutil.rmtree(active_app_path)
			else:
				os.remove(active_app_path)
			log(f"App deleted from {active_app_path}")
		else:
			archived_path = os.path.join("archived", "apps")
			archived_name = get_available_folder_name(
				f"{self.app_name}-{date.today()}", archived_path
			)
			archived_app_path = os.path.join(archived_path, archived_name)

			shutil.move(active_app_path, archived_app_path)
			log(f"App moved from {active_app_path} to {archived_app_path}")

		self.from_apps = False
		self.on_disk = False

	@step(title="Installing App {repo}", success="App {repo} Installed")
	def install(
		self,
		skip_assets=False,
		verbose=False,
		resolved=False,
		restart_nxcli=True,
		ignore_resolution=False,
		using_cached=False,
	):
		import nxcli.cli
		from nxcli.utils.app import get_app_name

		self.validate_app_dependencies()

		verbose = nxcli.cli.verbose or verbose
		app_name = get_app_name(self.nxcli.name, self.app_name)
		if not resolved and self.app_name != "nxenv" and not ignore_resolution:
			click.secho(
				f"Ignoring dependencies of {self.name}. To install dependencies use --resolve-deps",
				fg="yellow",
			)

		install_app(
			app=app_name,
			tag=self.tag,
			nxcli_path=self.nxcli.name,
			verbose=verbose,
			skip_assets=skip_assets,
			restart_nxcli=restart_nxcli,
			resolution=self.local_resolution,
			using_cached=using_cached,
		)

	@step(title="Cloning and installing {repo}", success="App {repo} Installed")
	def install_resolved_apps(self, *args, **kwargs):
		self.get()
		self.install(*args, **kwargs, resolved=True)

	@step(title="Uninstalling App {repo}", success="App {repo} Uninstalled")
	def uninstall(self):
		self.nxcli.run(f"{self.nxcli.python} -m pip uninstall -y {self.name}")

	def _get_dependencies(self):
		from nxcli.utils.app import get_required_deps, required_apps_from_hooks

		if self.on_disk:
			required_deps = os.path.join(self.mount_path, self.app_name, "hooks.py")
			try:
				return required_apps_from_hooks(required_deps, local=True)
			except IndexError:
				return []
		try:
			required_deps = get_required_deps(self.org, self.repo, self.tag or self.branch)
			return required_apps_from_hooks(required_deps)
		except Exception:
			return []

	def update_app_state(self):
		from nxcli.nxcli import Nxcli

		nxcli = Nxcli(self.nxcli.name)
		nxcli.apps.sync(
			app_dir=self.app_name,
			app_name=self.name,
			branch=self.tag,
			required=self.local_resolution,
		)

	def get_pyproject(self) -> Optional[dict]:
		from nxcli.utils.app import get_pyproject

		if self.pyproject:
			return self.pyproject

		apps_path = os.path.join(os.path.abspath(self.nxcli.name), "apps")
		pyproject_path = os.path.join(apps_path, self.app_name, "pyproject.toml")
		self.pyproject = get_pyproject(pyproject_path)
		return self.pyproject

	def validate_app_dependencies(self, throw=False) -> None:
		pyproject = self.get_pyproject() or {}
		deps: Optional[dict] = (
			pyproject.get("tool", {}).get("nxcli", {}).get("nxenv-dependencies")
		)
		if not deps:
			return

		for dep, version in deps.items():
			validate_dependency(self, dep, version, throw=throw)

	"""
	Get App Cache

	Since get-app affects only the `apps`, `env`, and `sites`
	nxcli sub directories. If we assume deterministic builds
	when get-app is called, the `apps/app_name` sub dir can be
	cached.

	In subsequent builds this would save time by not having to:
	- clone repository
	- install frontend dependencies
	- building frontend assets
	as all of this is contained in the `apps/app_name` sub dir.

	Code that updates the `env` and `sites` subdirs still need
	to be run.
	"""

	def get_app_path(self) -> Path:
		return Path(self.nxcli.name) / "apps" / self.app_name

	def get_app_cache_temp_path(self, is_compressed=False) -> Path:
		cache_path = get_nxcli_cache_path("apps")
		ext = "tgz" if is_compressed else "tar"
		tarfile_name = f"{self.app_name}.{uuid.uuid4().hex}.{ext}"
		return cache_path / tarfile_name

	def get_app_cache_hashed_path(self, temp_path: Path) -> Path:
		assert self.cache_key is not None

		ext = temp_path.suffix[1:]
		md5 = get_file_md5(temp_path)
		tarfile_name = f"{self.app_name}.{self.cache_key}.md5-{md5}.{ext}"

		return temp_path.with_name(tarfile_name)

	def get_cached(self) -> bool:
		if not self.cache_key:
			return False

		if not (cache_path := validate_cache_and_get_path(self.app_name, self.cache_key)):
			return False

		app_path = self.get_app_path()
		if app_path.is_dir():
			shutil.rmtree(app_path)

		click.secho(
			f"Nxcli app-cache: extracting {self.app_name} from {cache_path.as_posix()}",
		)

		mode = "r:gz" if cache_path.suffix.endswith(".tgz") else "r"
		with tarfile.open(cache_path, mode) as tar:
			extraction_filter = get_app_cache_extract_filter(count_threshold=150_000)
			try:
				tar.extractall(app_path.parent, filter=extraction_filter)
				click.secho(
					f"Nxcli app-cache: extraction succeeded for {self.app_name}",
					fg="green",
				)
			except Exception:
				message = f"Nxcli app-cache: extraction failed for {self.app_name}"
				click.secho(
					message,
					fg="yellow",
				)
				logger.exception(message)
				shutil.rmtree(app_path)
				return False

		return True

	def set_cache(self, compress_artifacts=False) -> bool:
		if not self.cache_key:
			return False

		app_path = self.get_app_path()
		if not app_path.is_dir():
			return False

		cwd = os.getcwd()
		cache_path = self.get_app_cache_temp_path(compress_artifacts)
		mode = "w:gz" if compress_artifacts else "w"

		message = f"Nxcli app-cache: caching {self.app_name}"
		if compress_artifacts:
			message += " (compressed)"
		click.secho(message)

		self.prune_app_directory()

		success = False
		os.chdir(app_path.parent)
		try:
			with tarfile.open(cache_path, mode) as tar:
				tar.add(app_path.name)

			hashed_path = self.get_app_cache_hashed_path(cache_path)
			unlink_no_throw(hashed_path)

			cache_path.rename(hashed_path)
			click.secho(
				f"Nxcli app-cache: caching succeeded for {self.app_name} as {hashed_path.as_posix()}",
				fg="green",
			)

			success = True
		except Exception as exc:
			log(f"Nxcli app-cache: caching failed for {self.app_name} {exc}", level=3)
			success = False
		finally:
			os.chdir(cwd)
		return success

	def prune_app_directory(self):
		app_path = self.get_app_path()
		if can_nxenv_use_cached(self):
			remove_unused_node_modules(app_path)


def coerce_url_to_name_if_possible(git_url: str, cache_key: str) -> str:
	app_name = os.path.basename(git_url)
	if can_get_cached(app_name, cache_key):
		return app_name
	return git_url


def can_get_cached(app_name: str, cache_key: str) -> bool:
	"""
	Used before App is initialized if passed `git_url` is a
	file URL as opposed to the app name.

	If True then `git_url` can be coerced into the `app_name` and
	checking local remote and fetching can be skipped while keeping
	get-app command params the same.
	"""

	if cache_path := get_app_cache_path(app_name, cache_key):
		return cache_path.exists()

	return False


def can_nxenv_use_cached(app: App) -> bool:
	min_nxenv = get_required_nxenv_version(app)
	if not min_nxenv:
		return False

	try:
		return sv.Version(min_nxenv) in sv.SimpleSpec(">=15.12.0")
	except ValueError:
		# Passed value is not a version string, it's an expression
		pass

	try:
		"""
		15.12.0 is the first version to support USING_CACHED,
		but there is no way to check the last version without
		support. So it's not possible to have a ">" filter.

		Hence this excludes the first supported version.
		"""
		return sv.Version("15.12.0") not in sv.SimpleSpec(min_nxenv)
	except ValueError:
		click.secho(
			f"Nxcli app-cache: invalid value found for nxenv version '{min_nxenv}'",
			fg="yellow",
		)
		# Invalid expression
		return False


def validate_dependency(app: App, dep: str, req_version: str, throw=False) -> None:
	dep_path = Path(app.nxcli.name) / "apps" / dep
	if not dep_path.is_dir():
		click.secho(f"Required nxenv-dependency '{dep}' not found.", fg="yellow")
		if throw:
			sys.exit(1)
		return

	dep_version = get_dep_version(dep, dep_path)
	if not dep_version:
		return

	if sv.Version(dep_version) not in sv.SimpleSpec(req_version):
		click.secho(
			f"Installed nxenv-dependency '{dep}' version '{dep_version}' "
			f"does not satisfy required version '{req_version}'. "
			f"App '{app.name}' might not work as expected.",
			fg="yellow",
		)
		if throw:
			click.secho(f"Please install '{dep}{req_version}' first and retry", fg="red")
			sys.exit(1)


def get_dep_version(dep: str, dep_path: Path) -> Optional[str]:
	from nxcli.utils.app import get_pyproject

	dep_pp = get_pyproject(str(dep_path / "pyproject.toml"))
	version = dep_pp.get("project", {}).get("version")
	if version:
		return version

	dinit_path = dep_path / dep / "__init__.py"
	if not dinit_path.is_file():
		return None

	with dinit_path.open("r", encoding="utf-8") as dinit:
		for line in dinit:
			if not line.startswith("__version__ =") and not line.startswith("VERSION ="):
				continue

			version = line.split("=")[1].strip().strip("\"'")
			if version:
				return version
			else:
				break

	return None


def get_required_nxenv_version(app: App) -> Optional[str]:
	pyproject = app.get_pyproject() or {}

	# Reference: https://github.com/nxenv/nxcli/issues/1524
	req_nxenv = (
		pyproject.get("tool", {})
		.get("nxcli", {})
		.get("nxenv-dependencies", {})
		.get("nxenv")
	)

	if not req_nxenv:
		click.secho(
			"Required nxenv version not set in pyproject.toml, "
			"please refer: https://github.com/nxenv/nxcli/issues/1524",
			fg="yellow",
		)

	return req_nxenv


def remove_unused_node_modules(app_path: Path) -> None:
	"""
	Erring a bit the side of caution; since there is no explicit way
	to check if node_modules are utilized, this function checks if Vite
	is being used to build the frontend code.

	Since most popular Nxenv apps use Vite to build their frontends,
	this method should suffice.

	Note: root package.json is ignored cause those usually belong to
	apps that do not have a build step and so their node_modules are
	utilized during runtime.
	"""

	for p in app_path.iterdir():
		if not p.is_dir():
			continue

		package_json = p / "package.json"
		if not package_json.is_file():
			continue

		node_modules = p / "node_modules"
		if not node_modules.is_dir():
			continue

		can_delete = False
		with package_json.open("r", encoding="utf-8") as f:
			package_json = json.loads(f.read())
			build_script = package_json.get("scripts", {}).get("build", "")
			can_delete = "vite build" in build_script

		if can_delete:
			click.secho(
				f"Nxcli app-cache: removing {node_modules.as_posix()}",
				fg="yellow",
			)
			shutil.rmtree(node_modules)


def make_resolution_plan(app: App, nxcli: "Nxcli"):
	"""
	decide what apps and versions to install and in what order
	"""
	resolution = OrderedDict()
	resolution[app.app_name] = app

	for app_name in app._get_dependencies():
		dep_app = App(app_name, nxcli=nxcli)
		is_valid_nxenv_branch(dep_app.url, dep_app.branch)
		dep_app.required_by = app.name
		if dep_app.app_name in resolution:
			click.secho(f"{dep_app.app_name} is already resolved skipping", fg="yellow")
			continue
		resolution[dep_app.app_name] = dep_app
		resolution.update(make_resolution_plan(dep_app, nxcli))
		app.local_resolution = [repo_name for repo_name, _ in reversed(resolution.items())]
	return resolution


def get_excluded_apps(nxcli_path="."):
	try:
		with open(os.path.join(nxcli_path, "sites", "excluded_apps.txt")) as f:
			return f.read().strip().split("\n")
	except OSError:
		return []


def add_to_excluded_apps_txt(app, nxcli_path="."):
	if app == "nxenv":
		raise ValueError("Nxenv app cannot be excluded from update")
	if app not in os.listdir("apps"):
		raise ValueError(f"The app {app} does not exist")
	apps = get_excluded_apps(nxcli_path=nxcli_path)
	if app not in apps:
		apps.append(app)
		return write_excluded_apps_txt(apps, nxcli_path=nxcli_path)


def write_excluded_apps_txt(apps, nxcli_path="."):
	with open(os.path.join(nxcli_path, "sites", "excluded_apps.txt"), "w") as f:
		return f.write("\n".join(apps))


def remove_from_excluded_apps_txt(app, nxcli_path="."):
	apps = get_excluded_apps(nxcli_path=nxcli_path)
	if app in apps:
		apps.remove(app)
		return write_excluded_apps_txt(apps, nxcli_path=nxcli_path)


def get_app(
	git_url,
	branch=None,
	nxcli_path=".",
	skip_assets=False,
	verbose=False,
	overwrite=False,
	soft_link=False,
	init_nxcli=False,
	resolve_deps=False,
	cache_key=None,
	compress_artifacts=False,
):
	"""nxcli get-app clones a Nxenv App from remote (GitHub or any other git server),
	and installs it on the current nxcli. This also resolves dependencies based on the
	apps' required_apps defined in the hooks.py file.

	If the nxcli_path is not a nxcli directory, a new nxcli is created named using the
	git_url parameter.
	"""
	import nxcli as _nxcli
	import nxcli.cli as nxcli_cli
	from nxcli.nxcli import Nxcli
	from nxcli.utils.app import check_existing_dir

	if urlparse(git_url).scheme == "file" and cache_key:
		git_url = coerce_url_to_name_if_possible(git_url, cache_key)

	nxcli = Nxcli(nxcli_path)
	app = App(
		git_url, branch=branch, nxcli=nxcli, soft_link=soft_link, cache_key=cache_key
	)
	git_url = app.url
	repo_name = app.repo
	branch = app.tag
	nxcli_setup = False
	restart_nxcli = not init_nxcli
	nxenv_path, nxenv_branch = None, None

	if resolve_deps:
		resolution = make_resolution_plan(app, nxcli)
		click.secho("Following apps will be installed", fg="bright_blue")
		for idx, app in enumerate(reversed(resolution.values()), start=1):
			print(
				f"{idx}. {app.name} {f'(required by {app.required_by})' if app.required_by else ''}"
			)

		if "nxenv" in resolution:
			# Todo: Make nxenv a terminal dependency for all nxenv apps.
			nxenv_path, nxenv_branch = resolution["nxenv"].url, resolution["nxenv"].tag

	if not is_nxcli_directory(nxcli_path):
		if not init_nxcli:
			click.secho(
				f"{os.path.realpath(nxcli_path)} is not a valid nxcli directory. "
				"Run with --init-nxcli if you'd like to create a Nxcli too.",
				fg="red",
			)
			sys.exit(1)

		from nxcli.utils.system import init

		nxcli_path = get_available_folder_name(f"{app.repo}-nxcli", nxcli_path)
		init(
			path=nxcli_path,
			nxenv_path=nxenv_path,
			nxenv_branch=nxenv_branch or branch,
		)
		os.chdir(nxcli_path)
		nxcli_setup = True

	if nxcli_setup and nxcli_cli.from_command_line and nxcli_cli.dynamic_feed:
		_nxcli.LOG_BUFFER.append(
			{
				"message": f"Fetching App {repo_name}",
				"prefix": click.style("⏼", fg="bright_yellow"),
				"is_parent": True,
				"color": None,
			}
		)

	if resolve_deps:
		install_resolved_deps(
			nxcli,
			resolution,
			nxcli_path=nxcli_path,
			skip_assets=skip_assets,
			verbose=verbose,
		)
		return

	if app.get_cached():
		app.install(
			verbose=verbose,
			skip_assets=skip_assets,
			restart_nxcli=restart_nxcli,
			using_cached=True,
		)
		return

	dir_already_exists, cloned_path = check_existing_dir(nxcli_path, repo_name)
	to_clone = not dir_already_exists

	# application directory already exists
	# prompt user to overwrite it
	if dir_already_exists and (
		overwrite
		or click.confirm(
			f"A directory for the application '{repo_name}' already exists. "
			"Do you want to continue and overwrite it?"
		)
	):
		app.remove()
		to_clone = True

	if to_clone:
		app.get()

	if (
		to_clone
		or overwrite
		or click.confirm("Do you want to reinstall the existing application?")
	):
		app.install(verbose=verbose, skip_assets=skip_assets, restart_nxcli=restart_nxcli)

	app.set_cache(compress_artifacts)


def install_resolved_deps(
	nxcli,
	resolution,
	nxcli_path=".",
	skip_assets=False,
	verbose=False,
):
	from nxcli.utils.app import check_existing_dir

	if "nxenv" in resolution:
		# Terminal dependency
		del resolution["nxenv"]

	for repo_name, app in reversed(resolution.items()):
		existing_dir, path_to_app = check_existing_dir(nxcli_path, repo_name)
		if existing_dir:
			is_compatible = False

			try:
				installed_branch = nxcli.apps.states[repo_name]["resolution"]["branch"].strip()
			except Exception:
				installed_branch = (
					subprocess.check_output(
						"git rev-parse --abbrev-ref HEAD", shell=True, cwd=path_to_app
					)
					.decode("utf-8")
					.rstrip()
				)
			try:
				if app.tag is None:
					current_remote = (
						subprocess.check_output(
							f"git config branch.{installed_branch}.remote", shell=True, cwd=path_to_app
						)
						.decode("utf-8")
						.rstrip()
					)

					default_branch = (
						subprocess.check_output(
							f"git symbolic-ref refs/remotes/{current_remote}/HEAD",
							shell=True,
							cwd=path_to_app,
						)
						.decode("utf-8")
						.rsplit("/")[-1]
						.strip()
					)
					is_compatible = default_branch == installed_branch
				else:
					is_compatible = installed_branch == app.tag
			except Exception:
				is_compatible = False

			prefix = "C" if is_compatible else "Inc"
			click.secho(
				f"{prefix}ompatible version of {repo_name} is already installed",
				fg="green" if is_compatible else "red",
			)
			app.update_app_state()
			if click.confirm(
				f"Do you wish to clone and install the already installed {prefix}ompatible app"
			):
				click.secho(f"Removing installed app {app.name}", fg="yellow")
				shutil.rmtree(path_to_app)
			else:
				continue
		app.install_resolved_apps(skip_assets=skip_assets, verbose=verbose)


def new_app(app, no_git=None, nxcli_path="."):
	if nxcli.NXENV_VERSION in (0, None):
		click.secho(
			f"{os.path.realpath(nxcli_path)} is not a valid nxcli directory.",
			fg="red",
		)
		sys.exit(1)

	# For backwards compatibility
	app = app.lower().replace(" ", "_").replace("-", "_")
	if app[0].isdigit() or "." in app:
		click.secho(
			"App names cannot start with numbers(digits) or have dot(.) in them", fg="red"
		)
		return

	apps = os.path.abspath(os.path.join(nxcli_path, "apps"))
	args = ["make-app", apps, app]
	if no_git:
		if nxcli.NXENV_VERSION < 14:
			click.secho("Nxenv v14 or greater is needed for '--no-git' flag", fg="red")
			return
		args.append(no_git)

	logger.log(f"creating new app {app}")
	run_nxenv_cmd(*args, nxcli_path=nxcli_path)
	install_app(app, nxcli_path=nxcli_path)


def install_app(
	app,
	tag=None,
	nxcli_path=".",
	verbose=False,
	no_cache=False,
	restart_nxcli=True,
	skip_assets=False,
	resolution=UNSET_ARG,
	using_cached=False,
):
	import nxcli.cli as nxcli_cli
	from nxcli.nxcli import Nxcli

	install_text = f"Installing {app}"
	click.secho(install_text, fg="yellow")
	logger.log(install_text)

	if resolution == UNSET_ARG:
		resolution = []

	nxcli = Nxcli(nxcli_path)
	conf = nxcli.conf

	verbose = nxcli_cli.verbose or verbose
	quiet_flag = "" if verbose else "--quiet"
	cache_flag = "--no-cache-dir" if no_cache else ""

	app_path = os.path.realpath(os.path.join(nxcli_path, "apps", app))

	nxcli.run(
		f"{nxcli.python} -m pip install {quiet_flag} --upgrade -e {app_path} {cache_flag}"
	)

	if conf.get("developer_mode"):
		install_python_dev_dependencies(apps=app, nxcli_path=nxcli_path, verbose=verbose)

	if not using_cached and os.path.exists(os.path.join(app_path, "package.json")):
		yarn_install = "yarn install --check-files"
		if verbose:
			yarn_install += " --verbose"
		nxcli.run(yarn_install, cwd=app_path)

	nxcli.apps.sync(app_name=app, required=resolution, branch=tag, app_dir=app_path)

	if not skip_assets:
		build_assets(nxcli_path=nxcli_path, app=app, using_cached=using_cached)

	if restart_nxcli:
		# Avoiding exceptions here as production might not be set-up
		# OR we might just be generating docker images.
		nxcli.reload(_raise=False)


def pull_apps(apps=None, nxcli_path=".", reset=False):
	"""Check all apps if there no local changes, pull"""
	from nxcli.nxcli import Nxcli
	from nxcli.utils.app import get_current_branch, get_remote

	nxcli = Nxcli(nxcli_path)
	rebase = "--rebase" if nxcli.conf.get("rebase_on_pull") else ""
	apps = apps or nxcli.apps
	excluded_apps = nxcli.excluded_apps

	# check for local changes
	if not reset:
		for app in apps:
			if app in excluded_apps:
				print(f"Skipping reset for app {app}")
				continue
			app_dir = get_repo_dir(app, nxcli_path=nxcli_path)
			if os.path.exists(os.path.join(app_dir, ".git")):
				out = subprocess.check_output("git status", shell=True, cwd=app_dir)
				out = out.decode("utf-8")
				if not re.search(r"nothing to commit, working (directory|tree) clean", out):
					print(
						f"""

Cannot proceed with update: You have local changes in app "{app}" that are not committed.

Here are your choices:

1. Merge the {app} app manually with "git pull" / "git pull --rebase" and fix conflicts.
2. Temporarily remove your changes with "git stash" or discard them completely
	with "nxcli update --reset" or for individual repositries "git reset --hard"
3. If your changes are helpful for others, send in a pull request via GitHub and
	wait for them to be merged in the core."""
					)
					sys.exit(1)

	for app in apps:
		if app in excluded_apps:
			print(f"Skipping pull for app {app}")
			continue
		app_dir = get_repo_dir(app, nxcli_path=nxcli_path)
		if os.path.exists(os.path.join(app_dir, ".git")):
			remote = get_remote(app)
			if not remote:
				# remote is False, i.e. remote doesn't exist, add the app to excluded_apps.txt
				add_to_excluded_apps_txt(app, nxcli_path=nxcli_path)
				print(
					f"Skipping pull for app {app}, since remote doesn't exist, and"
					" adding it to excluded apps"
				)
				continue

			if not nxcli.conf.get("shallow_clone") or not reset:
				is_shallow = os.path.exists(os.path.join(app_dir, ".git", "shallow"))
				if is_shallow:
					s = " to safely pull remote changes." if not reset else ""
					print(f"Unshallowing {app}{s}")
					nxcli.run(f"git fetch {remote} --unshallow", cwd=app_dir)

			branch = get_current_branch(app, nxcli_path=nxcli_path)
			logger.log(f"pulling {app}")
			if reset:
				reset_cmd = f"git reset --hard {remote}/{branch}"
				if nxcli.conf.get("shallow_clone"):
					nxcli.run(f"git fetch --depth=1 --no-tags {remote} {branch}", cwd=app_dir)
					nxcli.run(reset_cmd, cwd=app_dir)
					nxcli.run("git reflog expire --all", cwd=app_dir)
					nxcli.run("git gc --prune=all", cwd=app_dir)
				else:
					nxcli.run("git fetch --all", cwd=app_dir)
					nxcli.run(reset_cmd, cwd=app_dir)
			else:
				nxcli.run(f"git pull {rebase} {remote} {branch}", cwd=app_dir)
			nxcli.run('find . -name "*.pyc" -delete', cwd=app_dir)


def use_rq(nxcli_path):
	nxcli_path = os.path.abspath(nxcli_path)
	celery_app = os.path.join(nxcli_path, "apps", "nxenv", "nxenv", "celery_app.py")
	return not os.path.exists(celery_app)


def get_repo_dir(app, nxcli_path="."):
	return os.path.join(nxcli_path, "apps", app)


def is_git_repo(app_path):
	try:
		git.Repo(app_path, search_parent_directories=False)
		return True
	except git.exc.InvalidGitRepositoryError:
		return False


def install_apps_from_path(path, nxcli_path="."):
	apps = get_apps_json(path)
	for app in apps:
		get_app(
			app["url"],
			branch=app.get("branch"),
			nxcli_path=nxcli_path,
			skip_assets=True,
		)


def get_apps_json(path):
	import requests

	if path.startswith("http"):
		r = requests.get(path)
		return r.json()

	with open(path) as f:
		return json.load(f)


def is_cache_hash_valid(cache_path: Path) -> bool:
	parts = cache_path.name.split(".")
	if len(parts) < 2 or not parts[-2].startswith("md5-"):
		return False

	md5 = parts[-2].split("-")[1]
	return get_file_md5(cache_path) == md5


def unlink_no_throw(path: Path):
	if not path.exists():
		return

	try:
		path.unlink(True)
	except Exception:
		pass


def get_app_cache_path(app_name: str, cache_key: str) -> "Optional[Path]":
	cache_path = get_nxcli_cache_path("apps")
	glob_pattern = f"{app_name}.{cache_key}.md5-*"

	for app_cache_path in cache_path.glob(glob_pattern):
		return app_cache_path

	return None


def validate_cache_and_get_path(app_name: str, cache_key: str) -> "Optional[Path]":
	if not cache_key:
		return

	if not (cache_path := get_app_cache_path(app_name, cache_key)):
		return

	if not cache_path.is_file():
		click.secho(
			f"Nxcli app-cache: file check failed for {cache_path.as_posix()}, skipping cache",
			fg="yellow",
		)
		unlink_no_throw(cache_path)
		return

	if not is_cache_hash_valid(cache_path):
		click.secho(
			f"Nxcli app-cache: hash validation failed for {cache_path.as_posix()}, skipping cache",
			fg="yellow",
		)
		unlink_no_throw(cache_path)
		return

	return cache_path
