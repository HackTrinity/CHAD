CTFd._internal.challenge.data = undefined;
CTFd._internal.challenge.renderer = CTFd.lib.markdown();


CTFd._internal.challenge.preRender = function () {};
CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown);
};

function stacyResCheck(res) {
    if (!res.ok) {
        return res.json()
            .then(r => {
                if (r.message) {
                    throw r.message;
                }
                throw JSON.stringify(r);
            })
    }
    return res.json();
}
function stacyActionButton(selector, action) {
    const el = CTFd.lib.$(selector);
    const spinner = el.find('.spinner-border');
    el.click(() => {
        el.attr('disabled', true);
        spinner.removeAttr('style');

        const done = () => {
            spinner.attr('style', 'display: none;');
            el.removeAttr('disabled');
        };

        action()
            .then(done, done);
    })
}
function stacyPing(challengeId) {
    CTFd.fetch(`/plugins/stacy/api/instances/${challengeId}`, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(res => {
            CTFd.lib.$('#instance-status-loading').attr('style', 'display: none;');
            if (!res.ok) {
                if (res.status == 404) {
                    CTFd.lib.$('#instance-controls').attr('style', 'display: none;');
                    CTFd.lib.$('#challenge-launch').removeAttr('style');
                    return;
                }

                return stacyResCheck(res);
            }

            CTFd.lib.$('#instance-controls').removeAttr('style');
            CTFd.lib.$('#challenge-launch').attr('style', 'display: none;');
        })
        .catch(e => {
            console.log(e);
            alert(e);
        })
}

CTFd._internal.challenge.postRender = function () {
    const challengeId = parseInt(CTFd.lib.$('#challenge-id').val());

    stacyPing(challengeId);
    CTFd._internal.challenge.ping = setInterval(stacyPing.bind(null, challengeId), 10000);
    CTFd.lib.$('#challenge-window').on('hidden.bs.modal', () => clearInterval(CTFd._internal.challenge.ping));

    stacyActionButton('#challenge-launch', () =>
        CTFd.fetch(`/plugins/stacy/api/instances/${challengeId}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(stacyResCheck)
            .then(() => stacyPing(challengeId))
            .catch(e => {
                console.log(e);
                alert(e);
            })
    );

    stacyActionButton('#challenge-reset', () =>
        CTFd.fetch(`/plugins/stacy/api/instances/${challengeId}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(stacyResCheck)
            .then(() => stacyPing(challengeId))
            .catch(e => {
                console.log(e);
                alert(e);
            })
    );
    stacyActionButton('#challenge-delete', () =>
        CTFd.fetch(`/plugins/stacy/api/instances/${challengeId}`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(stacyResCheck)
            .then(() => stacyPing(challengeId))
            .catch(e => {
                console.log(e);
                alert(e);
            })
    );
};


CTFd._internal.challenge.submit = function (preview) {
    const challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());
    const submission = CTFd.lib.$('#submission-input').val();

    const body = {
        'challenge_id': challenge_id,
        'submission': submission,
    };
    const params = {};
    if (preview) {
        params['preview'] = true;
    }

    return CTFd.api.post_challenge_attempt(params, body).then(response => {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response;
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response;
        }
        return response;
    });
};
