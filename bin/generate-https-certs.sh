#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi
# Check if required variables are set
missing_vars=()

if [[ -z "$DEPLOY_HOST" ]]; then
  missing_vars+=("DEPLOY_HOST")
fi

if [[ -z "$PROJECT_NAME" ]]; then
  missing_vars+=("PROJECT_NAME")
fi

if [[ ${#missing_vars[@]} -ne 0 ]]; then
  echo "One or more required environment variables are missing in .env:"
  for var in "${missing_vars[@]}"; do
    echo "$var"
  done
  exit 1
fi
# Generate a self-signed certificate for the HTTPS server
# Generate an RSA private key of size 2048:

openssl genrsa -des3 -out rootCA.key 2048

# Generate a root certificate valid for two years:

openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 730 -out rootCert.pem

# Generate a private key for the server:

openssl genrsa -out cert.key 2048

# Use the private key to create a certificate signing request (CSR):

openssl req -new -key cert.key -out cert.csr

# Create a configuration file:

echo "# Extensions to add to a certificate request
basicConstraints       = CA:FALSE
authorityKeyIdentifier = keyid:always, issuer:always
keyUsage               = nonRepudiation, digitalSignature, keyEncipherment, dataEncipherment
subjectAltName         = @alt_names
[ alt_names ]
DNS.1 = $PROJECT_NAME.$DEPLOY_HOST
DNS.2 = auth.$PROJECT_NAME.$DEPLOY_HOST
DNS.3 = flower.$PROJECT_NAME.$DEPLOY_HOST" >openssl.cnf

# Sign the CSR using the root certificate and key:
openssl x509 -req -in cert.csr -CA rootCert.pem -CAkey rootCA.key -CAcreateserial -out cert.crt -days 730 -sha256 -extfile openssl.cnf

# Verify that the certificate is built correctly:

openssl verify -CAfile rootCert.pem -verify_hostname $PROJECT_NAME.$DEPLOY_HOST cert.crt
openssl verify -CAfile rootCert.pem -verify_hostname auth.$PROJECT_NAME.$DEPLOY_HOST cert.crt
openssl verify -CAfile rootCert.pem -verify_hostname flower.$PROJECT_NAME.$DEPLOY_HOST cert.crt

mkdir -p nginx/certs

cat cert.crt rootCert.pem >fullchain.crt
mv cert.* nginx/certs/
mv fullchain.crt nginx/certs/

rm -f rootCA.key cert.csr cert.key openssl.cnf
