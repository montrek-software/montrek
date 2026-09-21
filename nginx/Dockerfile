FROM nginx:1.30.3-alpine

RUN apk add --no-cache gettext openssl

RUN rm /etc/nginx/conf.d/default.conf
COPY templates/*.conf.template /etc/nginx/templates/


# Fallback certificate. SSL_CERT_PATH/SSL_KEY_PATH normally point at a mounted
# cert; the entrypoint generates a throwaway self-signed pair at container start
# and falls back to it if the mount is unusable, so that a broken mount degrades
# to "wrong cert" rather than "nginx will not start".
#
# Generated at runtime rather than here, so no private key ever ends up in an
# image layer: a key baked at build time is identical in every container that
# ever runs this image and is readable by anyone who can pull it.
COPY bin/nginx-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
