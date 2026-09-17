FROM nginx:1.30.3-alpine

RUN apk add --no-cache gettext openssl

RUN rm /etc/nginx/conf.d/default.conf
COPY templates/*.conf.template /etc/nginx/templates/


# Bundled fallback certificate. SSL_CERT_PATH/SSL_KEY_PATH normally point at a
# mounted cert instead; the entrypoint falls back to this if that is unusable,
# so that a broken mount degrades to "wrong cert" rather than "nginx will not
# start".
#
# Generated here rather than COPY'd from nginx/certs/: copying baked the
# instance's real private key into an image layer. This throwaway keypair is
# only ever served to warn that the real certificate is missing. RSA because
# the entrypoint's usable() check compares moduli with `openssl rsa`.
RUN openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
  -subj "/CN=montrek-fallback-certificate-not-for-production" \
  -keyout /etc/ssl/cert.key \
  -out /etc/ssl/fullchain.crt \
  && chmod 600 /etc/ssl/cert.key
COPY bin/nginx-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
