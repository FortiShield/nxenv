# imports - third party imports
import click

# imports - module imports
from nxcli.utils.cli import (
	MultiCommandGroup,
	print_nxcli_version,
	use_experimental_feature,
	setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
	"--version",
	is_flag=True,
	is_eager=True,
	callback=print_nxcli_version,
	expose_value=False,
)
@click.option(
	"--use-feature",
	is_eager=True,
	callback=use_experimental_feature,
	expose_value=False,
)
@click.option(
	"-v",
	"--verbose",
	is_flag=True,
	callback=setup_verbosity,
	expose_value=False,
)
def nxcli_command(nxcli_path="."):
	import nxcli

	nxcli.set_nxenv_version(nxcli_path=nxcli_path)


from nxcli.commands.make import (
	drop,
	exclude_app_for_update,
	get_app,
	include_app_for_update,
	init,
	new_app,
	pip,
	remove_app,
	validate_dependencies,
)

nxcli_command.add_command(init)
nxcli_command.add_command(drop)
nxcli_command.add_command(get_app)
nxcli_command.add_command(new_app)
nxcli_command.add_command(remove_app)
nxcli_command.add_command(exclude_app_for_update)
nxcli_command.add_command(include_app_for_update)
nxcli_command.add_command(pip)
nxcli_command.add_command(validate_dependencies)


from nxcli.commands.update import (
	retry_upgrade,
	switch_to_branch,
	switch_to_develop,
	update,
)

nxcli_command.add_command(update)
nxcli_command.add_command(retry_upgrade)
nxcli_command.add_command(switch_to_branch)
nxcli_command.add_command(switch_to_develop)


from nxcli.commands.utils import (
	app_cache_helper,
	backup_all_sites,
	nxcli_src,
	disable_production,
	download_translations,
	find_nxclies,
	migrate_env,
	renew_lets_encrypt,
	restart,
	set_mariadb_host,
	set_nginx_port,
	set_redis_cache_host,
	set_redis_queue_host,
	set_redis_socketio_host,
	set_ssl_certificate,
	set_ssl_certificate_key,
	set_url_root,
	start,
)

nxcli_command.add_command(start)
nxcli_command.add_command(restart)
nxcli_command.add_command(set_nginx_port)
nxcli_command.add_command(set_ssl_certificate)
nxcli_command.add_command(set_ssl_certificate_key)
nxcli_command.add_command(set_url_root)
nxcli_command.add_command(set_mariadb_host)
nxcli_command.add_command(set_redis_cache_host)
nxcli_command.add_command(set_redis_queue_host)
nxcli_command.add_command(set_redis_socketio_host)
nxcli_command.add_command(download_translations)
nxcli_command.add_command(backup_all_sites)
nxcli_command.add_command(renew_lets_encrypt)
nxcli_command.add_command(disable_production)
nxcli_command.add_command(nxcli_src)
nxcli_command.add_command(find_nxclies)
nxcli_command.add_command(migrate_env)
nxcli_command.add_command(app_cache_helper)

from nxcli.commands.setup import setup

nxcli_command.add_command(setup)


from nxcli.commands.config import config

nxcli_command.add_command(config)

from nxcli.commands.git import remote_reset_url, remote_set_url, remote_urls

nxcli_command.add_command(remote_set_url)
nxcli_command.add_command(remote_reset_url)
nxcli_command.add_command(remote_urls)

from nxcli.commands.install import install

nxcli_command.add_command(install)
