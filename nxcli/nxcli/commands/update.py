# imports - third party imports
import click

# imports - module imports
from nxcli.app import pull_apps
from nxcli.utils.nxcli import post_upgrade, patch_sites, build_assets


@click.command(
	"update",
	help="Performs an update operation on current nxcli. Without any flags will backup, pull, setup requirements, build, run patches and restart nxcli. Using specific flags will only do certain tasks instead of all",
)
@click.option("--pull", is_flag=True, help="Pull updates for all the apps in nxcli")
@click.option("--apps", type=str)
@click.option("--patch", is_flag=True, help="Run migrations for all sites in the nxcli")
@click.option("--build", is_flag=True, help="Build JS and CSS assets for the nxcli")
@click.option(
	"--requirements",
	is_flag=True,
	help="Update requirements. If run alone, equivalent to `nxcli setup requirements`",
)
@click.option(
	"--restart-supervisor", is_flag=True, help="Restart supervisor processes after update"
)
@click.option(
	"--restart-systemd", is_flag=True, help="Restart systemd units after update"
)
@click.option(
	"--no-backup",
	is_flag=True,
	help="If this flag is set, sites won't be backed up prior to updates. Note: This is not recommended in production.",
)
@click.option(
	"--no-compile",
	is_flag=True,
	help="[DEPRECATED] This flag doesn't do anything now.",
)
@click.option("--force", is_flag=True, help="Forces major version upgrades")
@click.option(
	"--reset",
	is_flag=True,
	help="Hard resets git branch's to their new states overriding any changes and overriding rebase on pull",
)
def update(
	pull,
	apps,
	patch,
	build,
	requirements,
	restart_supervisor,
	restart_systemd,
	no_backup,
	no_compile,
	force,
	reset,
):
	from nxcli.utils.nxcli import update

	update(
		pull=pull,
		apps=apps,
		patch=patch,
		build=build,
		requirements=requirements,
		restart_supervisor=restart_supervisor,
		restart_systemd=restart_systemd,
		backup=not no_backup,
		compile=not no_compile,
		force=force,
		reset=reset,
	)


@click.command("retry-upgrade", help="Retry a failed upgrade")
@click.option("--version", default=5)
def retry_upgrade(version):
	pull_apps()
	patch_sites()
	build_assets()
	post_upgrade(version - 1, version)


@click.command(
	"switch-to-branch",
	help="Switch all apps to specified branch, or specify apps separated by space",
)
@click.argument("branch")
@click.argument("apps", nargs=-1)
@click.option("--upgrade", is_flag=True)
def switch_to_branch(branch, apps, upgrade=False):
	from nxcli.utils.app import switch_to_branch

	switch_to_branch(branch=branch, apps=list(apps), upgrade=upgrade)


@click.command("switch-to-develop")
def switch_to_develop(upgrade=False):
	"Switch nxenv and erpnext to develop branch"
	from nxcli.utils.app import switch_to_develop

	switch_to_develop(apps=["nxenv", "erpnext"])
