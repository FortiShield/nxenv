# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import nxcli
from nxcli.app import use_rq
from nxcli.nxcli import Nxcli
from nxcli.config.common_site_config import (
	get_gunicorn_workers,
	update_config,
	get_default_max_requests,
	compute_max_requests_jitter,
)
from nxcli.utils import exec_cmd, which, get_nxcli_name


def generate_systemd_config(
	nxcli_path,
	user=None,
	yes=False,
	stop=False,
	create_symlinks=False,
	delete_symlinks=False,
):

	if not user:
		user = getpass.getuser()

	config = Nxcli(nxcli_path).conf

	nxcli_dir = os.path.abspath(nxcli_path)
	nxcli_name = get_nxcli_name(nxcli_path)

	if stop:
		exec_cmd(
			f"sudo systemctl stop -- $(systemctl show -p Requires {nxcli_name}.target | cut -d= -f2)"
		)
		return

	if create_symlinks:
		_create_symlinks(nxcli_path)
		return

	if delete_symlinks:
		_delete_symlinks(nxcli_path)
		return

	number_of_workers = config.get("background_workers") or 1
	background_workers = []
	for i in range(number_of_workers):
		background_workers.append(
			get_nxcli_name(nxcli_path) + "-nxenv-default-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_nxcli_name(nxcli_path) + "-nxenv-short-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_nxcli_name(nxcli_path) + "-nxenv-long-worker@" + str(i + 1) + ".service"
		)

	web_worker_count = config.get(
		"gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
	)
	max_requests = config.get(
		"gunicorn_max_requests", get_default_max_requests(web_worker_count)
	)

	nxcli_info = {
		"nxcli_dir": nxcli_dir,
		"sites_dir": os.path.join(nxcli_dir, "sites"),
		"user": user,
		"use_rq": use_rq(nxcli_path),
		"http_timeout": config.get("http_timeout", 120),
		"redis_server": which("redis-server"),
		"node": which("node") or which("nodejs"),
		"redis_cache_config": os.path.join(nxcli_dir, "config", "redis_cache.conf"),
		"redis_queue_config": os.path.join(nxcli_dir, "config", "redis_queue.conf"),
		"webserver_port": config.get("webserver_port", 8000),
		"gunicorn_workers": web_worker_count,
		"gunicorn_max_requests": max_requests,
		"gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
		"nxcli_name": get_nxcli_name(nxcli_path),
		"worker_target_wants": " ".join(background_workers),
		"nxcli_cmd": which("nxcli"),
	}

	if not yes:
		click.confirm(
			"current systemd configuration will be overwritten. Do you want to continue?",
			abort=True,
		)

	setup_systemd_directory(nxcli_path)
	setup_main_config(nxcli_info, nxcli_path)
	setup_workers_config(nxcli_info, nxcli_path)
	setup_web_config(nxcli_info, nxcli_path)
	setup_redis_config(nxcli_info, nxcli_path)

	update_config({"restart_systemd_on_update": False}, nxcli_path=nxcli_path)
	update_config({"restart_supervisor_on_update": False}, nxcli_path=nxcli_path)


def setup_systemd_directory(nxcli_path):
	if not os.path.exists(os.path.join(nxcli_path, "config", "systemd")):
		os.makedirs(os.path.join(nxcli_path, "config", "systemd"))


def setup_main_config(nxcli_info, nxcli_path):
	# Main config
	nxcli_template = nxcli.config.env().get_template("systemd/nxenv-nxcli.target")
	nxcli_config = nxcli_template.render(**nxcli_info)
	nxcli_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + ".target"
	)

	with open(nxcli_config_path, "w") as f:
		f.write(nxcli_config)


def setup_workers_config(nxcli_info, nxcli_path):
	# Worker Group
	nxcli_workers_target_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-workers.target"
	)
	nxcli_default_worker_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-nxenv-default-worker.service"
	)
	nxcli_short_worker_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-nxenv-short-worker.service"
	)
	nxcli_long_worker_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-nxenv-long-worker.service"
	)
	nxcli_schedule_worker_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-nxenv-schedule.service"
	)

	nxcli_workers_target_config = nxcli_workers_target_template.render(**nxcli_info)
	nxcli_default_worker_config = nxcli_default_worker_template.render(**nxcli_info)
	nxcli_short_worker_config = nxcli_short_worker_template.render(**nxcli_info)
	nxcli_long_worker_config = nxcli_long_worker_template.render(**nxcli_info)
	nxcli_schedule_worker_config = nxcli_schedule_worker_template.render(**nxcli_info)

	nxcli_workers_target_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-workers.target"
	)
	nxcli_default_worker_config_path = os.path.join(
		nxcli_path,
		"config",
		"systemd",
		nxcli_info.get("nxcli_name") + "-nxenv-default-worker@.service",
	)
	nxcli_short_worker_config_path = os.path.join(
		nxcli_path,
		"config",
		"systemd",
		nxcli_info.get("nxcli_name") + "-nxenv-short-worker@.service",
	)
	nxcli_long_worker_config_path = os.path.join(
		nxcli_path,
		"config",
		"systemd",
		nxcli_info.get("nxcli_name") + "-nxenv-long-worker@.service",
	)
	nxcli_schedule_worker_config_path = os.path.join(
		nxcli_path,
		"config",
		"systemd",
		nxcli_info.get("nxcli_name") + "-nxenv-schedule.service",
	)

	with open(nxcli_workers_target_config_path, "w") as f:
		f.write(nxcli_workers_target_config)

	with open(nxcli_default_worker_config_path, "w") as f:
		f.write(nxcli_default_worker_config)

	with open(nxcli_short_worker_config_path, "w") as f:
		f.write(nxcli_short_worker_config)

	with open(nxcli_long_worker_config_path, "w") as f:
		f.write(nxcli_long_worker_config)

	with open(nxcli_schedule_worker_config_path, "w") as f:
		f.write(nxcli_schedule_worker_config)


def setup_web_config(nxcli_info, nxcli_path):
	# Web Group
	nxcli_web_target_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-web.target"
	)
	nxcli_web_service_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-nxenv-web.service"
	)
	nxcli_node_socketio_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-node-socketio.service"
	)

	nxcli_web_target_config = nxcli_web_target_template.render(**nxcli_info)
	nxcli_web_service_config = nxcli_web_service_template.render(**nxcli_info)
	nxcli_node_socketio_config = nxcli_node_socketio_template.render(**nxcli_info)

	nxcli_web_target_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-web.target"
	)
	nxcli_web_service_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-nxenv-web.service"
	)
	nxcli_node_socketio_config_path = os.path.join(
		nxcli_path,
		"config",
		"systemd",
		nxcli_info.get("nxcli_name") + "-node-socketio.service",
	)

	with open(nxcli_web_target_config_path, "w") as f:
		f.write(nxcli_web_target_config)

	with open(nxcli_web_service_config_path, "w") as f:
		f.write(nxcli_web_service_config)

	with open(nxcli_node_socketio_config_path, "w") as f:
		f.write(nxcli_node_socketio_config)


def setup_redis_config(nxcli_info, nxcli_path):
	# Redis Group
	nxcli_redis_target_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-redis.target"
	)
	nxcli_redis_cache_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-redis-cache.service"
	)
	nxcli_redis_queue_template = nxcli.config.env().get_template(
		"systemd/nxenv-nxcli-redis-queue.service"
	)

	nxcli_redis_target_config = nxcli_redis_target_template.render(**nxcli_info)
	nxcli_redis_cache_config = nxcli_redis_cache_template.render(**nxcli_info)
	nxcli_redis_queue_config = nxcli_redis_queue_template.render(**nxcli_info)

	nxcli_redis_target_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-redis.target"
	)
	nxcli_redis_cache_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-redis-cache.service"
	)
	nxcli_redis_queue_config_path = os.path.join(
		nxcli_path, "config", "systemd", nxcli_info.get("nxcli_name") + "-redis-queue.service"
	)

	with open(nxcli_redis_target_config_path, "w") as f:
		f.write(nxcli_redis_target_config)

	with open(nxcli_redis_cache_config_path, "w") as f:
		f.write(nxcli_redis_cache_config)

	with open(nxcli_redis_queue_config_path, "w") as f:
		f.write(nxcli_redis_queue_config)


def _create_symlinks(nxcli_path):
	nxcli_dir = os.path.abspath(nxcli_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	config_path = os.path.join(nxcli_dir, "config", "systemd")
	unit_files = get_unit_files(nxcli_dir)
	for unit_file in unit_files:
		filename = "".join(unit_file)
		exec_cmd(
			f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}'
		)
	exec_cmd("sudo systemctl daemon-reload")


def _delete_symlinks(nxcli_path):
	nxcli_dir = os.path.abspath(nxcli_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	unit_files = get_unit_files(nxcli_dir)
	for unit_file in unit_files:
		exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd("sudo systemctl daemon-reload")


def get_unit_files(nxcli_path):
	nxcli_name = get_nxcli_name(nxcli_path)
	unit_files = [
		[nxcli_name, ".target"],
		[nxcli_name + "-workers", ".target"],
		[nxcli_name + "-web", ".target"],
		[nxcli_name + "-redis", ".target"],
		[nxcli_name + "-nxenv-default-worker@", ".service"],
		[nxcli_name + "-nxenv-short-worker@", ".service"],
		[nxcli_name + "-nxenv-long-worker@", ".service"],
		[nxcli_name + "-nxenv-schedule", ".service"],
		[nxcli_name + "-nxenv-web", ".service"],
		[nxcli_name + "-node-socketio", ".service"],
		[nxcli_name + "-redis-cache", ".service"],
		[nxcli_name + "-redis-queue", ".service"],
	]
	return unit_files
