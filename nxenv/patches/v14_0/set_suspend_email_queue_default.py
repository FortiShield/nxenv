import nxenv
from nxenv.cache_manager import clear_defaults_cache


def execute():
	nxenv.db.set_default(
		"suspend_email_queue",
		nxenv.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	nxenv.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()
