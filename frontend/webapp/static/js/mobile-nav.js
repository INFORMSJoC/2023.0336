// Enable mobile tool nav dropdown
$("#tool-navigation .nav-item.active").click((e) => {
  // Only prevent default on width < 1000
  if ($(window).width() < 1000) {
    e.preventDefault();
  }
});

// Click anywhere outside of the tool nav dropdown to close it
$(document).on('click', (event) => {
  var screenWidth = $(window).width();
  if (screenWidth < 1000) {
    const toolNav = $("#tool-navigation");
    if (toolNav.hasClass("show-nav-dropdown")) {
      if(!$(event.target).closest('#tool-navigation').length) {
        toolNav.removeClass("show-nav-dropdown");
      }
    }   
  }
});