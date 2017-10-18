$(document).ready(function() {
    //var about_url = window.location.hostname + '/__about__';
    //console.log(about_url);
    //$.getJSON('http://test.siguv.de/__about__', function(data) {
    $.getJSON("http://karl.novareto.de:8080/__about__", function(data) {
	var items = [];
	$.each(data, function(key, val) {
	    items.push( "<li><a href='" + key + "'> 🔓 " + val + "</a></li>");
	});
	$( "<ul/>", {
	    "id": "remotewsgi",
            "class": "list",
	    html: items.join("")
	}).prependTo("body");
    }); 
});
