CTFd.lib.$('input[name="flag_mode"]').change(e => {
  if ($(e.target).val() == 1) {
    CTFd.lib.$('#flag-random-length-value').removeAttr('disabled');
  } else {
    CTFd.lib.$('#flag-random-length-value').attr('disabled', true);
  }
});
