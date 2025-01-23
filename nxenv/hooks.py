import os

from . import __version__ as app_version

app_name = "nxenv"
app_title = "Framework"
app_publisher = "Nxenv Technologies"
app_description = "Full stack web framework with Python, Javascript, MariaDB, Redis, Node"
app_license = "MIT"
app_logo_url = "/assets/nxenv/images/nxenv-framework-logo.svg"
develop_version = "15.x.x-develop"
app_home = "/app/build"

app_email = "info@khulnasoft.com"

before_install = "nxenv.utils.install.before_install"
after_install = "nxenv.utils.install.after_install"

page_js = {"setup-wizard": "public/js/nxenv/setup_wizard.js"}

# website
app_include_js = [
	"libs.bundle.js",
	"desk.bundle.js",
	"list.bundle.js",
	"form.bundle.js",
	"controls.bundle.js",
	"report.bundle.js",
	"telemetry.bundle.js",
	"billing.bundle.js",
]

app_include_css = [
	"desk.bundle.css",
	"report.bundle.css",
]
app_include_icons = [
	"/assets/nxenv/icons/timeless/icons.svg",
	"/assets/nxenv/icons/espresso/icons.svg",
]

doctype_js = {
	"Web Page": "public/js/nxenv/utils/web_template.js",
	"Website Settings": "public/js/nxenv/utils/web_template.js",
}

web_include_js = ["website_script.js"]
web_include_css = []
web_include_icons = [
	"/assets/nxenv/icons/timeless/icons.svg",
	"/assets/nxenv/icons/espresso/icons.svg",
]

email_css = ["email.bundle.css"]

website_route_rules = [
	{"from_route": "/blog/<category>", "to_route": "Blog Post"},
	{"from_route": "/kb/<category>", "to_route": "Help Article"},
	{"from_route": "/newsletters", "to_route": "Newsletter"},
	{"from_route": "/profile", "to_route": "me"},
	{"from_route": "/app/<path:app_path>", "to_route": "app"},
]

website_redirects = [
	{"source": r"/desk(.*)", "target": r"/app\1"},
	{
		"source": "/.well-known/openid-configuration",
		"target": "/api/method/nxenv.integrations.oauth2.openid_configuration",
	},
]

base_template = "templates/base.html"

write_file_keys = ["file_url", "file_name"]

notification_config = "nxenv.core.notifications.get_notification_config"

before_tests = "nxenv.utils.install.before_tests"

email_append_to = ["Event", "ToDo", "Communication"]

calendars = ["Event"]

leaderboards = "nxenv.desk.leaderboard.get_leaderboards"

# login

on_session_creation = [
	"nxenv.core.doctype.activity_log.feed.login_feed",
	"nxenv.core.doctype.user.user.notify_admin_access_to_system_manager",
]

on_logout = "nxenv.core.doctype.session_default_settings.session_default_settings.clear_session_defaults"

# PDF
pdf_header_html = "nxenv.utils.pdf.pdf_header_html"
pdf_body_html = "nxenv.utils.pdf.pdf_body_html"
pdf_footer_html = "nxenv.utils.pdf.pdf_footer_html"

# permissions

permission_query_conditions = {
	"Event": "nxenv.desk.doctype.event.event.get_permission_query_conditions",
	"ToDo": "nxenv.desk.doctype.todo.todo.get_permission_query_conditions",
	"User": "nxenv.core.doctype.user.user.get_permission_query_conditions",
	"Dashboard Settings": "nxenv.desk.doctype.dashboard_settings.dashboard_settings.get_permission_query_conditions",
	"Notification Log": "nxenv.desk.doctype.notification_log.notification_log.get_permission_query_conditions",
	"Dashboard": "nxenv.desk.doctype.dashboard.dashboard.get_permission_query_conditions",
	"Dashboard Chart": "nxenv.desk.doctype.dashboard_chart.dashboard_chart.get_permission_query_conditions",
	"Number Card": "nxenv.desk.doctype.number_card.number_card.get_permission_query_conditions",
	"Notification Settings": "nxenv.desk.doctype.notification_settings.notification_settings.get_permission_query_conditions",
	"Note": "nxenv.desk.doctype.note.note.get_permission_query_conditions",
	"Kanban Board": "nxenv.desk.doctype.kanban_board.kanban_board.get_permission_query_conditions",
	"Contact": "nxenv.contacts.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "nxenv.contacts.address_and_contact.get_permission_query_conditions_for_address",
	"Communication": "nxenv.core.doctype.communication.communication.get_permission_query_conditions_for_communication",
	"Workflow Action": "nxenv.workflow.doctype.workflow_action.workflow_action.get_permission_query_conditions",
	"Prepared Report": "nxenv.core.doctype.prepared_report.prepared_report.get_permission_query_condition",
	"File": "nxenv.core.doctype.file.file.get_permission_query_conditions",
}

has_permission = {
	"Event": "nxenv.desk.doctype.event.event.has_permission",
	"ToDo": "nxenv.desk.doctype.todo.todo.has_permission",
	"Note": "nxenv.desk.doctype.note.note.has_permission",
	"User": "nxenv.core.doctype.user.user.has_permission",
	"Dashboard Chart": "nxenv.desk.doctype.dashboard_chart.dashboard_chart.has_permission",
	"Number Card": "nxenv.desk.doctype.number_card.number_card.has_permission",
	"Kanban Board": "nxenv.desk.doctype.kanban_board.kanban_board.has_permission",
	"Contact": "nxenv.contacts.address_and_contact.has_permission",
	"Address": "nxenv.contacts.address_and_contact.has_permission",
	"Communication": "nxenv.core.doctype.communication.communication.has_permission",
	"Workflow Action": "nxenv.workflow.doctype.workflow_action.workflow_action.has_permission",
	"File": "nxenv.core.doctype.file.file.has_permission",
	"Prepared Report": "nxenv.core.doctype.prepared_report.prepared_report.has_permission",
	"Notification Settings": "nxenv.desk.doctype.notification_settings.notification_settings.has_permission",
}

has_website_permission = {"Address": "nxenv.contacts.doctype.address.address.has_website_permission"}

jinja = {
	"methods": "nxenv.utils.jinja_globals",
	"filters": [
		"nxenv.utils.data.global_date_format",
		"nxenv.utils.markdown",
		"nxenv.website.utils.abs_url",
	],
}

standard_queries = {"User": "nxenv.core.doctype.user.user.user_query"}

doc_events = {
	"*": {
		"on_update": [
			"nxenv.desk.notifications.clear_doctype_notifications",
			"nxenv.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"nxenv.core.doctype.file.utils.attach_files_to_document",
			"nxenv.automation.doctype.assignment_rule.assignment_rule.apply",
			"nxenv.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"nxenv.core.doctype.user_type.user_type.apply_permissions_for_non_standard_user_type",
			"nxenv.core.doctype.permission_log.permission_log.make_perm_log",
		],
		"after_rename": "nxenv.desk.notifications.clear_doctype_notifications",
		"on_cancel": [
			"nxenv.desk.notifications.clear_doctype_notifications",
			"nxenv.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"nxenv.automation.doctype.assignment_rule.assignment_rule.apply",
		],
		"on_trash": [
			"nxenv.desk.notifications.clear_doctype_notifications",
			"nxenv.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
		],
		"on_update_after_submit": [
			"nxenv.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"nxenv.automation.doctype.assignment_rule.assignment_rule.apply",
			"nxenv.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"nxenv.core.doctype.file.utils.attach_files_to_document",
		],
		"on_change": [
			"nxenv.social.doctype.energy_point_rule.energy_point_rule.process_energy_points",
			"nxenv.automation.doctype.milestone_tracker.milestone_tracker.evaluate_milestone",
		],
		"after_delete": ["nxenv.core.doctype.permission_log.permission_log.make_perm_log"],
	},
	"Event": {
		"after_insert": "nxenv.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar",
		"on_update": "nxenv.integrations.doctype.google_calendar.google_calendar.update_event_in_google_calendar",
		"on_trash": "nxenv.integrations.doctype.google_calendar.google_calendar.delete_event_from_google_calendar",
	},
	"Contact": {
		"after_insert": "nxenv.integrations.doctype.google_contacts.google_contacts.insert_contacts_to_google_contacts",
		"on_update": "nxenv.integrations.doctype.google_contacts.google_contacts.update_contacts_to_google_contacts",
	},
	"DocType": {
		"on_update": "nxenv.cache_manager.build_domain_restricted_doctype_cache",
	},
	"Page": {
		"on_update": "nxenv.cache_manager.build_domain_restricted_page_cache",
	},
}

scheduler_events = {
	"cron": {
		# 5 minutes
		"0/5 * * * *": [
			"nxenv.email.doctype.notification.notification.trigger_offset_alerts",
		],
		# 15 minutes
		"0/15 * * * *": [
			"nxenv.oauth.delete_oauth2_data",
			"nxenv.website.doctype.web_page.web_page.check_publish_status",
			"nxenv.twofactor.delete_all_barcodes_for_users",
			"nxenv.email.doctype.email_account.email_account.notify_unreplied",
			"nxenv.utils.global_search.sync_global_search",
			"nxenv.deferred_insert.save_to_db",
			"nxenv.automation.doctype.reminder.reminder.send_reminders",
		],
		# 10 minutes
		"0/10 * * * *": [
			"nxenv.email.doctype.email_account.email_account.pull",
		],
		# Hourly but offset by 30 minutes
		"30 * * * *": [
			"nxenv.core.doctype.prepared_report.prepared_report.expire_stalled_report",
		],
		# Daily but offset by 45 minutes
		"45 0 * * *": [
			"nxenv.core.doctype.log_settings.log_settings.run_log_clean_up",
		],
	},
	"all": [
		"nxenv.email.queue.flush",
		"nxenv.monitor.flush",
	],
	"hourly": [
		"nxenv.model.utils.link_count.update_link_count",
		"nxenv.model.utils.user_settings.sync_user_settings",
		"nxenv.desk.page.backups.backups.delete_downloadable_backups",
		"nxenv.desk.form.document_follow.send_hourly_updates",
		"nxenv.integrations.doctype.google_calendar.google_calendar.sync",
		"nxenv.email.doctype.newsletter.newsletter.send_scheduled_email",
		"nxenv.website.doctype.personal_data_deletion_request.personal_data_deletion_request.process_data_deletion_request",
	],
	"daily": [
		"nxenv.desk.notifications.clear_notifications",
		"nxenv.desk.doctype.event.event.send_event_digest",
		"nxenv.sessions.clear_expired_sessions",
		"nxenv.email.doctype.notification.notification.trigger_daily_alerts",
		"nxenv.website.doctype.personal_data_deletion_request.personal_data_deletion_request.remove_unverified_record",
		"nxenv.desk.form.document_follow.send_daily_updates",
		"nxenv.social.doctype.energy_point_settings.energy_point_settings.allocate_review_points",
		"nxenv.integrations.doctype.google_contacts.google_contacts.sync",
		"nxenv.automation.doctype.auto_repeat.auto_repeat.make_auto_repeat_entry",
		"nxenv.automation.doctype.auto_repeat.auto_repeat.set_auto_repeat_as_completed",
	],
	"daily_long": [
		"nxenv.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_daily",
		"nxenv.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_daily",
		"nxenv.email.doctype.auto_email_report.auto_email_report.send_daily",
		"nxenv.integrations.doctype.google_drive.google_drive.daily_backup",
	],
	"weekly_long": [
		"nxenv.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_weekly",
		"nxenv.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_weekly",
		"nxenv.desk.form.document_follow.send_weekly_updates",
		"nxenv.utils.change_log.check_for_update",
		"nxenv.social.doctype.energy_point_log.energy_point_log.send_weekly_summary",
		"nxenv.integrations.doctype.google_drive.google_drive.weekly_backup",
		"nxenv.desk.doctype.changelog_feed.changelog_feed.fetch_changelog_feed",
	],
	"monthly": [
		"nxenv.email.doctype.auto_email_report.auto_email_report.send_monthly",
		"nxenv.social.doctype.energy_point_log.energy_point_log.send_monthly_summary",
	],
	"monthly_long": [
		"nxenv.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_monthly"
	],
}

sounds = [
	{"name": "email", "src": "/assets/nxenv/sounds/email.mp3", "volume": 0.1},
	{"name": "submit", "src": "/assets/nxenv/sounds/submit.mp3", "volume": 0.1},
	{"name": "cancel", "src": "/assets/nxenv/sounds/cancel.mp3", "volume": 0.1},
	{"name": "delete", "src": "/assets/nxenv/sounds/delete.mp3", "volume": 0.05},
	{"name": "click", "src": "/assets/nxenv/sounds/click.mp3", "volume": 0.05},
	{"name": "error", "src": "/assets/nxenv/sounds/error.mp3", "volume": 0.1},
	{"name": "alert", "src": "/assets/nxenv/sounds/alert.mp3", "volume": 0.2},
	# {"name": "chime", "src": "/assets/nxenv/sounds/chime.mp3"},
]

setup_wizard_exception = [
	"nxenv.desk.page.setup_wizard.setup_wizard.email_setup_wizard_exception",
	"nxenv.desk.page.setup_wizard.setup_wizard.log_setup_wizard_exception",
]

before_migrate = ["nxenv.core.doctype.patch_log.patch_log.before_migrate"]
after_migrate = ["nxenv.website.doctype.website_theme.website_theme.after_migrate"]

otp_methods = ["OTP App", "Email", "SMS"]

user_data_fields = [
	{"doctype": "Access Log", "strict": True},
	{"doctype": "Activity Log", "strict": True},
	{"doctype": "Comment", "strict": True},
	{
		"doctype": "Contact",
		"filter_by": "email_id",
		"redact_fields": ["first_name", "last_name", "phone", "mobile_no"],
		"rename": True,
	},
	{"doctype": "Contact Email", "filter_by": "email_id"},
	{
		"doctype": "Address",
		"filter_by": "email_id",
		"redact_fields": [
			"address_title",
			"address_line1",
			"address_line2",
			"city",
			"county",
			"state",
			"pincode",
			"phone",
			"fax",
		],
	},
	{
		"doctype": "Communication",
		"filter_by": "sender",
		"redact_fields": ["sender_full_name", "phone_no", "content"],
	},
	{"doctype": "Communication", "filter_by": "recipients"},
	{"doctype": "Email Group Member", "filter_by": "email"},
	{"doctype": "Email Unsubscribe", "filter_by": "email", "partial": True},
	{"doctype": "Email Queue", "filter_by": "sender"},
	{"doctype": "Email Queue Recipient", "filter_by": "recipient"},
	{
		"doctype": "File",
		"filter_by": "attached_to_name",
		"redact_fields": ["file_name", "file_url"],
	},
	{
		"doctype": "User",
		"filter_by": "name",
		"redact_fields": [
			"email",
			"username",
			"first_name",
			"middle_name",
			"last_name",
			"full_name",
			"birth_date",
			"user_image",
			"phone",
			"mobile_no",
			"location",
			"banner_image",
			"interest",
			"bio",
			"email_signature",
		],
	},
	{"doctype": "Version", "strict": True},
]

global_search_doctypes = {
	"Default": [
		{"doctype": "Contact"},
		{"doctype": "Address"},
		{"doctype": "ToDo"},
		{"doctype": "Note"},
		{"doctype": "Event"},
		{"doctype": "Blog Post"},
		{"doctype": "Dashboard"},
		{"doctype": "Country"},
		{"doctype": "Currency"},
		{"doctype": "Newsletter"},
		{"doctype": "Letter Head"},
		{"doctype": "Workflow"},
		{"doctype": "Web Page"},
		{"doctype": "Web Form"},
	]
}

override_whitelisted_methods = {
	# Legacy File APIs
	"nxenv.utils.file_manager.download_file": "download_file",
	"nxenv.core.doctype.file.file.download_file": "download_file",
	"nxenv.core.doctype.file.file.unzip_file": "nxenv.core.api.file.unzip_file",
	"nxenv.core.doctype.file.file.get_attached_images": "nxenv.core.api.file.get_attached_images",
	"nxenv.core.doctype.file.file.get_files_in_folder": "nxenv.core.api.file.get_files_in_folder",
	"nxenv.core.doctype.file.file.get_files_by_search_text": "nxenv.core.api.file.get_files_by_search_text",
	"nxenv.core.doctype.file.file.get_max_file_size": "nxenv.core.api.file.get_max_file_size",
	"nxenv.core.doctype.file.file.create_new_folder": "nxenv.core.api.file.create_new_folder",
	"nxenv.core.doctype.file.file.move_file": "nxenv.core.api.file.move_file",
	"nxenv.core.doctype.file.file.zip_files": "nxenv.core.api.file.zip_files",
	# Legacy (& Consistency) OAuth2 APIs
	"nxenv.www.login.login_via_google": "nxenv.integrations.oauth2_logins.login_via_google",
	"nxenv.www.login.login_via_github": "nxenv.integrations.oauth2_logins.login_via_github",
	"nxenv.www.login.login_via_facebook": "nxenv.integrations.oauth2_logins.login_via_facebook",
	"nxenv.www.login.login_via_nxenv": "nxenv.integrations.oauth2_logins.login_via_nxenv",
	"nxenv.www.login.login_via_office365": "nxenv.integrations.oauth2_logins.login_via_office365",
	"nxenv.www.login.login_via_salesforce": "nxenv.integrations.oauth2_logins.login_via_salesforce",
	"nxenv.www.login.login_via_fairlogin": "nxenv.integrations.oauth2_logins.login_via_fairlogin",
}

ignore_links_on_delete = [
	"Communication",
	"ToDo",
	"DocShare",
	"Email Unsubscribe",
	"Activity Log",
	"File",
	"Version",
	"Document Follow",
	"Comment",
	"View Log",
	"Tag Link",
	"Notification Log",
	"Email Queue",
	"Document Share Key",
	"Integration Request",
	"Unhandled Email",
	"Webhook Request Log",
	"Workspace",
	"Route History",
	"Access Log",
	"Permission Log",
]

# Request Hooks
before_request = [
	"nxenv.recorder.record",
	"nxenv.monitor.start",
	"nxenv.rate_limiter.apply",
]

after_request = [
	"nxenv.monitor.stop",
]

# Background Job Hooks
before_job = [
	"nxenv.recorder.record",
	"nxenv.monitor.start",
]

if os.getenv("NXENV_SENTRY_DSN") and (
	os.getenv("ENABLE_SENTRY_DB_MONITORING")
	or os.getenv("SENTRY_TRACING_SAMPLE_RATE")
	or os.getenv("SENTRY_PROFILING_SAMPLE_RATE")
):
	before_request.append("nxenv.utils.sentry.set_sentry_context")
	before_job.append("nxenv.utils.sentry.set_sentry_context")

after_job = [
	"nxenv.recorder.dump",
	"nxenv.monitor.stop",
	"nxenv.utils.file_lock.release_document_locks",
	"nxenv.utils.background_jobs.flush_telemetry",
]

extend_bootinfo = [
	"nxenv.utils.telemetry.add_bootinfo",
	"nxenv.core.doctype.user_permission.user_permission.send_user_permissions",
]

get_changelog_feed = "nxenv.desk.doctype.changelog_feed.changelog_feed.get_feed"

export_python_type_annotations = True

standard_navbar_items = [
	{
		"item_label": "User Settings",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.route_to_user()",
		"is_standard": 1,
	},
	{
		"item_label": "Workspace Settings",
		"item_type": "Action",
		"action": "nxenv.quick_edit('Workspace Settings')",
		"is_standard": 1,
	},
	{
		"item_label": "Session Defaults",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.setup_session_defaults()",
		"is_standard": 1,
	},
	{
		"item_label": "Reload",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.clear_cache()",
		"is_standard": 1,
	},
	{
		"item_label": "View Website",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.view_website()",
		"is_standard": 1,
	},
	{
		"item_label": "Apps",
		"item_type": "Route",
		"route": "/apps",
		"is_standard": 1,
	},
	{
		"item_label": "Toggle Full Width",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.toggle_full_width()",
		"is_standard": 1,
	},
	{
		"item_label": "Toggle Theme",
		"item_type": "Action",
		"action": "new nxenv.ui.ThemeSwitcher().show()",
		"is_standard": 1,
	},
	{
		"item_type": "Separator",
		"is_standard": 1,
		"item_label": "",
	},
	{
		"item_label": "Log out",
		"item_type": "Action",
		"action": "nxenv.app.logout()",
		"is_standard": 1,
	},
]

standard_help_items = [
	{
		"item_label": "About",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.show_about()",
		"is_standard": 1,
	},
	{
		"item_label": "Keyboard Shortcuts",
		"item_type": "Action",
		"action": "nxenv.ui.toolbar.show_shortcuts(event)",
		"is_standard": 1,
	},
	{
		"item_label": "System Health",
		"item_type": "Route",
		"route": "/app/system-health-report",
		"is_standard": 1,
	},
	{
		"item_label": "Nxenv Support",
		"item_type": "Route",
		"route": "https://nxenv.io/support",
		"is_standard": 1,
	},
]

# log doctype cleanups to automatically add in log settings
default_log_clearing_doctypes = {
	"Error Log": 14,
	"Email Queue": 30,
	"Scheduled Job Log": 7,
	"Submission Queue": 7,
	"Prepared Report": 14,
	"Webhook Request Log": 30,
	"Unhandled Email": 30,
	"Reminder": 30,
	"Integration Request": 90,
	"Activity Log": 90,
	"Route History": 90,
}

# These keys will not be erased when doing nxenv.clear_cache()
persistent_cache_keys = [
	"changelog-*",  # version update notifications
	"insert_queue_for_*",  # Deferred Insert
	"recorder-*",  # Recorder
	"global_search_queue",
	"monitor-transactions",
	"rate-limit-counter-*",
	"rl:*",
]
