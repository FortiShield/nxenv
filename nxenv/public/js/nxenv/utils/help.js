// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.provide("nxenv.help");

nxenv.help.youtube_id = {};

nxenv.help.has_help = function (doctype) {
	return nxenv.help.youtube_id[doctype];
};

nxenv.help.show = function (doctype) {
	if (nxenv.help.youtube_id[doctype]) {
		nxenv.help.show_video(nxenv.help.youtube_id[doctype]);
	}
};

nxenv.help.show_video = function (youtube_id, title) {
	if (nxenv.utils.is_url(youtube_id)) {
		const expression =
			'(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (nxenv.help_feedback_link || "")
	let dialog = new nxenv.ui.Dialog({
		title: title || __("Help"),
		size: "large",
	});

	let video = $(
		`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`
	);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr;
	nxenv.utils.load_video_player().then(() => {
		plyr = new nxenv.Plyr(video[0], {
			hideControls: true,
			resetOnEnd: true,
		});
	});

	dialog.onhide = () => {
		plyr?.destroy();
	};
};

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && nxenv.help.show(doctype);
});
