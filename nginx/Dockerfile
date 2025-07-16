FROM nginx:1.28.0-alpine

RUN apk add --no-cache gettext

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template


COPY certs/fullchain.crt /etc/ssl/fullchain.crt
COPY certs/cert.key /etc/ssl/cert.key

CMD /bin/sh -c "envsubst '\$APP_PORT \$DEPLOY_PORT \$DEPLOY_HOST \$KEYCLOAK_PORT' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
