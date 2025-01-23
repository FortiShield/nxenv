nxenv.provide("nxenv.ui.misc");
nxenv.ui.misc.about = function () {
	if (!nxenv.ui.misc.about_dialog) {
		var d = new nxenv.ui.Dialog({ title: __("Nxenv Framework") });

		$(d.body).html(
			repl(
				`<div>
					<p>${__("Open Source Applications for the Web")}</p>
					<p><i class='fa fa-globe fa-fw'></i>
						${__("Website")}:
						<a href='https://nxenvframework.com' target='_blank'>https://nxenvframework.com</a></p>
					<p><i class='fa fa-github fa-fw'></i>
						${__("Source")}:
						<a href='https://github.com/nxenv' target='_blank'>https://github.com/nxenv</a></p>
					<p><i class='fa fa-graduation-cap fa-fw'></i>
						Nxenv School: <a href='https://nxenv.school' target='_blank'>https://nxenv.school</a></p>
					<p><i class='fa fa-linkedin fa-fw'></i>
						Linkedin: <a href='https://linkedin.com/company/nxenv-tech' target='_blank'>https://linkedin.com/company/nxenv-tech</a></p>
					<p><i class='fa fa-twitter fa-fw'></i>
						Twitter: <a href='https://twitter.com/nxenvtech' target='_blank'>https://twitter.com/nxenvtech</a></p>
					<p><i class='fa fa-youtube fa-fw'></i>
						YouTube: <a href='https://www.youtube.com/@nxenvtech' target='_blank'>https://www.youtube.com/@nxenvtech</a></p>
					<hr>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<p>
						<b>
							<a href="/attribution" target="_blank" class="text-muted">
								${__("Dependencies & Licenses")}
							</a>
						</b>
					</p>
					<hr>
					<p class='text-muted'>${__("&copy; Nxenv Technologies Pvt. Ltd. and contributors")} </p>
					</div>`,
				nxenv.app
			)
		);

		nxenv.ui.misc.about_dialog = d;

		nxenv.ui.misc.about_dialog.on_page_show = function () {
			if (!nxenv.versions) {
				nxenv.call({
					method: "nxenv.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(nxenv.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				let text;
				if (v.branch) {
					text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			nxenv.versions = versions;
		};
	}

	nxenv.ui.misc.about_dialog.show();
};
