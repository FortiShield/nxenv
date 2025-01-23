# Copyright (c) 2017, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv


@nxenv.whitelist()
def get_leaderboard_config():
	leaderboard_config = nxenv._dict()
	leaderboard_hooks = nxenv.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(nxenv.get_attr(hook)())

	return leaderboard_config
