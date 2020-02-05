CTFd._internal.challenge.data = undefined;

CTFd._internal.challenge.renderer = CTFd.lib.markdown();


CTFd._internal.challenge.preRender = function () {};

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
};

function stacyFetch(path, args) {
    return CTFd.fetch(path, args)
        .then(res => {
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
        })
        .catch(e => {
            console.error(e);
            alert(e);
        });
}

CTFd._internal.challenge.postRender = function () {
    CTFd.lib.$('#challenge-launch').click(() => {
        const challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());
        stacyFetch(`/plugins/stacy/api/instances/${challenge_id}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
    });
    CTFd.lib.$('#challenge-delete').click(() => {
        const challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());
        stacyFetch(`/plugins/stacy/api/instances/${challenge_id}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
    });
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
