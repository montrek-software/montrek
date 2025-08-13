FROM nginx:1.28.0-alpine

RUN apk add --no-cache gettext

RUN rm /etc/nginx/conf.d/default.conf
COPY templates/*.conf.template /etc/nginx/templates/


COPY certs/fullchain.crt /etc/ssl/fullchain.crt
COPY certs/cert.key /etc/ssl/cert.key
COPY bin/nginx-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
