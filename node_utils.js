const fs = require("fs");
const path = require("path");
const redis = require("@redis/client");
let nxcli_path;
if (process.env.NXENV_NXCLI_ROOT) {
	nxcli_path = process.env.NXENV_NXCLI_ROOT;
} else {
	nxcli_path = path.resolve(__dirname, "..", "..");
}

const dns = require("dns");

// Since node17, node resolves to ipv6 unless system is configured otherwise.
// In Nxenv context using ipv4 - 127.0.0.1 is fine.
dns.setDefaultResultOrder("ipv4first");

function get_conf() {
	// defaults
	var conf = {
		socketio_port: 9000,
	};

	var read_config = function (file_path) {
		const full_path = path.resolve(nxcli_path, file_path);

		if (fs.existsSync(full_path)) {
			var nxcli_config = JSON.parse(fs.readFileSync(full_path));
			for (var key in nxcli_config) {
				if (nxcli_config[key]) {
					conf[key] = nxcli_config[key];
				}
			}
		}
	};

	// get ports from nxcli/config.json
	read_config("config.json");
	read_config("sites/common_site_config.json");

	// set overrides from environment
	if (process.env.NXENV_SITE) {
		conf.default_site = process.env.NXENV_SITE;
	}
	if (process.env.NXENV_REDIS_CACHE) {
		conf.redis_cache = process.env.NXENV_REDIS_CACHE;
	}
	if (process.env.NXENV_REDIS_QUEUE) {
		conf.redis_queue = process.env.NXENV_REDIS_QUEUE;
	}
	if (process.env.NXENV_SOCKETIO_PORT) {
		conf.socketio_port = process.env.NXENV_SOCKETIO_PORT;
	}
	if (process.env.NXENV_SOCKETIO_UDS) {
		conf.socketio_uds = process.env.NXENV_SOCKETIO_UDS;
	}
	return conf;
}

function get_redis_subscriber(kind = "redis_queue", options = {}) {
	const conf = get_conf();
	const connStr = conf[kind];
	let client;
	// TODO: revise after https://github.com/redis/node-redis/issues/2530
	// is solved for a more elegant implementation
	if (connStr && connStr.startsWith("unix://")) {
		client = redis.createClient({
			socket: { path: connStr.replace("unix://", "") },
			...options,
		});
	} else {
		client = redis.createClient({ url: connStr, ...options });
	}
	return client;
}

module.exports = {
	get_conf,
	get_redis_subscriber,
};
