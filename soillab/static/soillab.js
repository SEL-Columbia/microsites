
function goto_children_link(elem) {
    return window.location = $(elem).children("a").attr('href');
}

function sample_list_init() {
    // list link on main list access to samples
    $("ul#mainlist li, #topmenu div.link").click(function () {
        goto_children_link($(this));
    });
}