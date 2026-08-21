#!/bin/sh
set -e

FALLBACK_CERT=/etc/ssl/fullchain.crt
FALLBACK_KEY=/etc/ssl/cert.key

# Defaults must match docker-compose.yml so the image behaves the same when run
# directly. /etc/tls is the mount point; /etc/ssl holds the bundled fallback.
SSL_CERT_PATH="${SSL_CERT_PATH:-/etc/tls/fullchain.crt}"
SSL_KEY_PATH="${SSL_KEY_PATH:-/etc/tls/cert.key}"

# nginx refuses to start on a missing or mismatched key pair, which on a
# restart:unless-stopped container means a crash loop and a full outage. Check
# the configured pair first and fall back to the bundled cert if it is unusable,
# so a broken mount degrades to "wrong cert" instead of "site down".
usable() {
  [ -r "$1" ] && [ -r "$2" ] || return 1
  _c=$(openssl x509 -noout -modulus -in "$1" 2>/dev/null | openssl md5)
  _k=$(openssl rsa -noout -modulus -in "$2" 2>/dev/null | openssl md5)
  [ -n "$_c" ] && [ "$_c" = "$_k" ]
}

if ! usable "$SSL_CERT_PATH" "$SSL_KEY_PATH"; then
  echo "WARN: $SSL_CERT_PATH / $SSL_KEY_PATH missing or mismatched;" \
       "falling back to bundled certificate" >&2
  SSL_CERT_PATH="$FALLBACK_CERT"
  SSL_KEY_PATH="$FALLBACK_KEY"
fi

if ! openssl x509 -checkend 0 -noout -in "$SSL_CERT_PATH" >/dev/null 2>&1; then
  echo "WARN: certificate $SSL_CERT_PATH has EXPIRED" >&2
elif ! openssl x509 -checkend 1209600 -noout -in "$SSL_CERT_PATH" >/dev/null 2>&1; then
  echo "WARN: certificate $SSL_CERT_PATH expires within 14 days" >&2
fi
echo "nginx: serving $SSL_CERT_PATH ($(openssl x509 -noout -enddate -in "$SSL_CERT_PATH" 2>/dev/null))"

export SSL_CERT_PATH SSL_KEY_PATH

# Docker's embedded DNS; overridable for non-default networking.
DNS_RESOLVER="${DNS_RESOLVER:-127.0.0.11}"
export DNS_RESOLVER

SUBST='$APP_PORT $DEPLOY_PORT $DEPLOY_HOST $PROJECT_NAME $FLOWER_PORT $KEYCLOAK_PORT $SSL_CERT_PATH $SSL_KEY_PATH $DNS_RESOLVER'

envsubst "$SUBST" </etc/nginx/templates/flower.conf.template >/tmp/nginx.conf
envsubst "$SUBST" </etc/nginx/templates/django.conf.template >>/tmp/nginx.conf
if [ "$ENABLE_KEYCLOAK" = "1" ]; then
  envsubst "$SUBST" </etc/nginx/templates/keycloak.conf.template >/tmp/keycloak.conf
  cat /tmp/nginx.conf /tmp/keycloak.conf >/etc/nginx/conf.d/default.conf
else
  cp /tmp/nginx.conf /etc/nginx/conf.d/default.conf
fi

nginx -t

nginx -g "daemon off;"
