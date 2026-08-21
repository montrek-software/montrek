FROM nginx:1.30.3-alpine

RUN apk add --no-cache gettext openssl

RUN rm /etc/nginx/conf.d/default.conf
COPY templates/*.conf.template /etc/nginx/templates/


# Bundled fallback certificate. SSL_CERT_PATH/SSL_KEY_PATH normally point at a
# mounted cert instead; the entrypoint falls back to these if that is unusable.
COPY certs/fullchain.crt /etc/ssl/fullchain.crt
COPY certs/cert.key /etc/ssl/cert.key
COPY bin/nginx-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
