
function addJQ_find_sample() {

	$("button#find-btn").click(function () {
        sample_id = $("input#find-sample-field").value();
        if (sample_id) {
            window.location = '/pc/'
        }
        alert('yep');
    };);

}