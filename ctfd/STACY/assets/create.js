const md = CTFd.lib.markdown();
CTFd.lib.$('a[href="#new-desc-preview"]').on('shown.bs.tab', function (event) {
    if (event.target.hash == '#new-desc-preview') {
        const editor_value = CTFd.lib.$('#new-desc-editor').val();
        CTFd.lib.$(event.target.hash).html(
            md.render(editor_value)
        );
    }
});

$("#solve-attempts-checkbox").change(function() {
    if(this.checked) {
        $('#solve-attempts-input').show();
    } else {
        $('#solve-attempts-input').hide();
        $('#max_attempts').val('');
    }
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

CTFd.lib.$('input[name="flag_mode"]').change(e => {
  if ($(e.target).val() == 1) {
    CTFd.lib.$('#flag-random-length-value').removeAttr('disabled');
  } else {
    CTFd.lib.$('#flag-random-length-value').attr('disabled', true);
  }
});
