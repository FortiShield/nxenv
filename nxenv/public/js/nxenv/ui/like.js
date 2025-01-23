// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.ui.is_liked = function (doc) {
	return nxenv.ui.get_liked_by(doc).includes(nxenv.session.user);
};

nxenv.ui.get_liked_by = function (doc) {
	return doc._liked_by ? JSON.parse(doc._liked_by) : [];
};

nxenv.ui.toggle_like = function ($btn, doctype, name, callback) {
	const add = $btn.hasClass("not-liked") ? "Yes" : "No";
	// disable click
	$btn.css("pointer-events", "none");

	nxenv.call({
		method: "nxenv.desk.like.toggle_like",
		quiet: true,
		args: {
			doctype: doctype,
			name: name,
			add: add,
		},
		callback: function (r) {
			// renable click
			$btn.css("pointer-events", "auto");

			if (r.exc) {
				return;
			}

			$btn.toggleClass("not-liked", add === "No");
			$btn.toggleClass("liked", add === "Yes");

			// update in locals (form)
			const doc = locals[doctype] && locals[doctype][name];
			if (doc) {
				let liked_by = nxenv.ui.get_liked_by(doc);

				if (add === "Yes" && !liked_by.includes(nxenv.session.user)) {
					liked_by.push(nxenv.session.user);
				}

				if (add === "No" && liked_by.includes(nxenv.session.user)) {
					liked_by = liked_by.filter((user) => user !== nxenv.session.user);
				}

				doc._liked_by = JSON.stringify(liked_by);
			}

			if (callback) {
				callback();
			}
		},
	});
};

nxenv.ui.click_toggle_like = function () {
	console.warn("`nxenv.ui.click_toggle_like` is deprecated and has no effect.");
};

nxenv.ui.setup_like_popover = ($parent, selector) => {
	if (nxenv.dom.is_touchscreen()) {
		return;
	}

	$parent.on("mouseover", selector, function () {
		const target_element = $(this);
		target_element.popover({
			animation: true,
			placement: "bottom",
			trigger: "manual",
			template: `<div class="liked-by-popover popover">
				<div class="arrow"></div>
				<div class="popover-body popover-content"></div>
			</div>`,
			content: () => {
				let liked_by = target_element.parents(".liked-by").attr("data-liked-by");
				liked_by = liked_by ? decodeURI(liked_by) : "[]";
				liked_by = JSON.parse(liked_by);

				if (!liked_by.length) {
					return "";
				}

				let liked_by_list = $(`<ul class="list-unstyled"></ul>`);

				// to show social profile of the user
				let link_base = "/app/user-profile/";

				liked_by.forEach((user) => {
					// append user list item
					liked_by_list.append(`
						<li data-user=${user}>${nxenv.avatar(user, "avatar-xs")}
							<span>${nxenv.user.full_name(user)}</span>
						</li>
					`);
				});

				liked_by_list.children("li").click((ev) => {
					let user = ev.currentTarget.dataset.user;
					target_element.popover("hide");
					nxenv.set_route(link_base + user);
				});

				return liked_by_list;
			},
			html: true,
			container: "body",
		});

		target_element.popover("show");

		$(".popover").on("mouseleave", () => {
			target_element.popover("hide");
		});

		target_element.on("mouseout", () => {
			setTimeout(() => {
				if (!$(".popover:hover").length) {
					target_element.popover("hide");
				}
			}, 100);
		});
	});
};
