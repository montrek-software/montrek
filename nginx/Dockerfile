FROM nginx:1.19.0-alpine

RUN apk add --no-cache gettext

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template

COPY add_hosts.sh /usr/local/bin/add_hosts.sh
RUN chmod +x /usr/local/bin/add_hosts.sh

ENTRYPOINT ["/usr/local/bin/add_hosts.sh"]
CMD /bin/sh -c "envsubst '\$APP_PORT \$PROJECT_NAME' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
