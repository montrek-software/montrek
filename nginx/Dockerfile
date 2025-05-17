FROM nginx:1.28.0-alpine

RUN apk add --no-cache gettext

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template


COPY certs/cert.crt /etc/ssl/cert.crt
COPY certs/cert.key /etc/ssl/cert.key

CMD /bin/sh -c "envsubst '\$APP_PORT \$DEPLOY_PORT \$PROJECT_NAME' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
