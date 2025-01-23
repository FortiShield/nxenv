import * as Sentry from "@sentry/browser";

Sentry.init({
	dsn: nxenv.boot.sentry_dsn,
	release: nxenv?.boot?.versions?.nxenv,
	autoSessionTracking: false,
	initialScope: {
		// don't use nxenv.session.user, it's set much later and will fail because of async loading
		user: { id: nxenv.boot.sitename },
		tags: { nxenv_user: nxenv.boot.user.name ?? "Unidentified" },
	},
	beforeSend(event, hint) {
		// Check if it was caused by nxenv.throw()
		if (
			hint.originalException instanceof Error &&
			hint.originalException.stack &&
			hint.originalException.stack.includes("nxenv.throw")
		) {
			return null;
		}
		return event;
	},
});
