#include <stdio.h>
#include <unistd.h>
#include <sys/capability.h>

static const cap_value_t raise_setpcap[1] = { CAP_SETPCAP };

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <command> [args...]\n", argv[0]);
        return 1;
    }

    int ret = 0;

    cap_t caps = cap_get_proc();
    if (cap_clear_flag(caps, CAP_INHERITABLE) != 0) {
        perror("unable to clear CAP_INHERITABLE");
        ret = -1;
        goto free;
    }

    cap_t orig = cap_dup(caps);
    if (caps == NULL || orig == NULL) {
        perror("failed to get caps");
        return -1;
    }

    if (cap_set_flag(caps, CAP_EFFECTIVE, 1, raise_setpcap, CAP_SET) != 0) {
        perror("unable to select CAP_SETPCAP");
        ret = -1;
        goto free;
    }

    if (cap_drop_bound(CAP_NET_ADMIN) != 0) {
        perror("unable to drop CAP_NET_ADMIN");
        ret = -1;
        goto free;
    }

    if (cap_set_proc(orig) != 0) {
        perror("failed to lower CAP_SETPCAP after dropping CAP_NET_ADMIN");
        ret = -1;
        goto free;
    }


free:
    if (cap_free(caps) != 0 || cap_free(orig) != 0) {
        perror("cap_free() failed");
        return -2;
    }

    execvp(argv[1], argv + 1);
    perror("execl() failed");

    return ret;
}
