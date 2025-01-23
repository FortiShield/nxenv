// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
nxenv._ = function (txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = "";

	let key = txt; // txt.replace(/\n/g, "");
	if (context) {
		translated_text = nxenv._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = nxenv._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = nxenv._;

nxenv.get_languages = function () {
	if (!nxenv.languages) {
		nxenv.languages = [];
		$.each(nxenv.boot.lang_dict, function (lang, value) {
			nxenv.languages.push({ label: lang, value: value });
		});
		nxenv.languages = nxenv.languages.sort(function (a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return nxenv.languages;
};
