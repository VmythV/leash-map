#include "http.h"

#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int send_all(int fd, const char *buf, size_t len) {
    size_t off = 0;
    while (off < len) {
        ssize_t w = send(fd, buf + off, len - off, 0);
        if (w <= 0) return -1;
        off += (size_t)w;
    }
    return 0;
}

int lm_http_post(const char *host, int port, const char *path, const char *token,
                 const char *body, char *resp, size_t resp_n) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        close(fd);
        return -1;
    }
    if (connect(fd, (struct sockaddr *)&addr, sizeof addr) != 0) {
        close(fd);
        return -1;
    }

    char req[2048];
    int n = snprintf(req, sizeof req,
                     "POST %s HTTP/1.1\r\n"
                     "Host: %s:%d\r\n"
                     "Authorization: Bearer %s\r\n"
                     "Content-Type: application/json\r\n"
                     "Content-Length: %zu\r\n"
                     "Connection: close\r\n"
                     "\r\n"
                     "%s",
                     path, host, port, token, strlen(body), body);
    if (n < 0 || (size_t)n >= sizeof req || send_all(fd, req, (size_t)n) != 0) {
        close(fd);
        return -1;
    }

    /* read the whole response (server closes the connection) */
    char buf[8192];
    size_t total = 0;
    ssize_t r;
    while ((r = recv(fd, buf + total, sizeof buf - 1 - total, 0)) > 0) {
        total += (size_t)r;
        if (total >= sizeof buf - 1) break;
    }
    close(fd);
    buf[total] = '\0';

    int status = -1;
    sscanf(buf, "HTTP/1.1 %d", &status);

    const char *bodysep = strstr(buf, "\r\n\r\n");
    const char *rbody = bodysep ? bodysep + 4 : "";
    snprintf(resp, resp_n, "%s", rbody);
    return status;
}
