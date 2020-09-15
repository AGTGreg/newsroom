$('document').ready(function() {

  // Dropdowns ===================================================================
  // Show the selected option in the dropdown's button and set the dropdown item
  // active.
  $('.dropdown').on('click', function(e) {
    var btnToggle = false;
    var btnItem = false;
    if ($(e.target).hasClass('dropdown-toggle')) {
      btnToggle = $(e.target);
      btnItem = $(e.target).next('.dropdown-menu').find('.dropdown-item.active');
    } else if ($(e.target).hasClass('dropdown-item')) {
      btnItem = $(e.target);
      // If this is a simble select and not a multiselect then deactivate any active elements
      // before activating the selected element.
      if (btnItem.closest('multiselect').length <= 0) btnItem.closest('.dropdown-menu').find('.active').removeClass('active');
      btnItem.addClass('active');
      btnToggle = $(e.target).closest('.dropdown-menu').prev('.dropdown-toggle');
    }
    if (btnToggle != false && btnItem != false) {
      btnToggle.text(btnItem.text());
    }
  });

});
