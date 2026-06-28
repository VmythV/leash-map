/* Minimal blocking HTTP/1.1 POST over a TCP socket (host build only).
 * Plain HTTP, IPv4, Connection: close — just enough for the local bridge. */
#ifndef LM_BRIDGE_HTTP_H
#define LM_BRIDGE_HTTP_H

#include <stddef.h>

/* POST `body` to http://host:port/path with a Bearer token. Copies the
 * response body (after headers) into resp[resp_n]. Returns the HTTP status
 * code, or -1 on a transport error. */
int lm_http_post(const char *host, int port, const char *path, const char *token,
                 const char *body, char *resp, size_t resp_n);

#endif /* LM_BRIDGE_HTTP_H */
