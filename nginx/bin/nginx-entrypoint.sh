#!/bin/bash
set -e
envsubst "\$DEPLOY_HOST \$PROJECT_NAME \$FLOWER_PORT" </etc/nginx/templates/flower.conf.template >/tmp/nginx.conf
envsubst "\$APP_PORT \$DEPLOY_PORT \$DEPLOY_HOST \$PROJECT_NAME" </etc/nginx/templates/django.conf.template >>/tmp/nginx.conf
if [ "$ENABLE_KEYCLOAK" = "1" ]; then
  envsubst "\$DEPLOY_HOST \$KEYCLOAK_PORT \$PROJECT_NAME" </etc/nginx/templates/keycloak.conf.template >/tmp/keycloak.conf
  cat /tmp/nginx.conf /tmp/keycloak.conf >/etc/nginx/conf.d/default.conf
else
  cp /tmp/nginx.conf /etc/nginx/conf.d/default.conf
fi
nginx -g "daemon off;"
