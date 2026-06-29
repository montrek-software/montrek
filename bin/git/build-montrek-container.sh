# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Check if required variables are set
if [[ -z "$GIT_PAT" ]]; then
  echo "One or more required environment variables are missing in .env:"
  echo "GIT_PAT"
  exit 1
fi
echo $PAT | docker login ${CONTAINER_REGISTRY:-ghcr.io} -u YOUR_GITHUB_USERNAME --password-stdin

docker build -t ${CONTAINER_REGISTRY:-ghcr.io}/montrek-software/montrek-container:latest .
docker push ${CONTAINER_REGISTRY:-ghcr.io}/montrek-software/montrek-container:latest
