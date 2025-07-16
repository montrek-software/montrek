FROM nginx:1.28.0-alpine

RUN apk add --no-cache gettext

RUN rm /etc/nginx/conf.d/default.conf
COPY templates/*.conf.template /etc/nginx/templates/


COPY certs/fullchain.crt /etc/ssl/fullchain.crt
COPY certs/cert.key /etc/ssl/cert.key

CMD /bin/sh -c '\
  envsubst "\$APP_PORT \$DEPLOY_PORT \$DEPLOY_HOST" < /etc/nginx/templates/django.conf.template > /tmp/django.conf && \
  if [ "$ENABLE_KEYCLOAK" = "1" ]; then \
  envsubst "\$DEPLOY_HOST \$KEYCLOAK_PORT" < /etc/nginx/templates/keycloak.conf.template > /tmp/keycloak.conf; \
  cat /tmp/django.conf /tmp/keycloak.conf > /etc/nginx/conf.d/default.conf; \
  else \
  cp /tmp/django.conf /etc/nginx/conf.d/default.conf; \
  fi && \
  nginx -g "daemon off;"'
