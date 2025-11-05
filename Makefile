SECURE_WRAPPER := bash bin/secrets/secure-wrapper.sh

.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: local-init
local-init: # Install local python environment and necessary packages
	@$(SECURE_WRAPPER) bin/local/init.sh

.PHONY: local-runserver
local-runserver: # Run the montrek django app locally (non-docker).
	@$(SECURE_WRAPPER) bin/local/runserver.sh

.PHONY: sync-local-python-env
sync-local-python-env: # Sync the local (non-docker) python environment with the requirements specified in the montrek repositories.
	@$(SECURE_WRAPPER) bin/local/sync-python-env.sh

.PHONY: local-sonarqube-scan
local-sonarqube-scan: # Run a SonarQube scan and open in SonarQube (Add NO_TESTS=true to skip tests)
	@$(SECURE_WRAPPER) bin/local/sonarqube_scan.sh NO_TESTS=$(NO_TESTS) $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-up
docker-up: # Start all docker containers in detached mode.
	@$(SECURE_WRAPPER) bin/docker/run.sh up -d

.PHONY: docker-down
docker-down: # Stop all docker containers.
	@$(SECURE_WRAPPER) bin/docker/run.sh down

.PHONY: docker-restart
docker-restart: # Shut the docker compose container down and up again
	@$(SECURE_WRAPPER) bin/docker/restart.sh

.PHONY: docker-logs
docker-logs: # Show docker compose logs
	@$(SECURE_WRAPPER) bin/docker/logs.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-build
docker-build: # Build the docker images
	@$(SECURE_WRAPPER) bin/docker/build.sh

.PHONY: docker-db-backup
docker-db-backup: # Make a backup of the docker database.
	@$(SECURE_WRAPPER) bin/docker/db.sh backup

.PHONY: docker-db-restore
docker-db-restore: # Restore the docker database from a backup.
	@$(SECURE_WRAPPER) bin/docker/db.sh restore

.PHONY: docker-django-manage
docker-django-manage: # Run Django management commands inside the docker container.
	@$(SECURE_WRAPPER)  bin/docker/django-manage.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-cleanup
docker-cleanup: # Remove unused docker artifacts.
	@$(SECURE_WRAPPER) bin/docker/cleanup.sh

.PHONY: git-clone-repository
git-clone-repository: # Clone a montrek repository (expects a repository name like 'mt_economic_common').
	@$(SECURE_WRAPPER) bin/git/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: git-update-repositories
git-update-repositories: # Update all montrek repositories to the latest git tags.
	@$(SECURE_WRAPPER) bin/git/update-repositories-to-latest-tags.sh

.PHONY: git-build-montrek-container
git-build-montrek-container: # Build the container to run montrek in docker or github actions
	@$(SECURE_WRAPPER) bin/git/build-montrek-container.sh

.PHONY: server-generate-https-certs
server-generate-https-certs: # Generate HTTPS certificates for the montrek django app.
	@$(SECURE_WRAPPER) bin/server/generate-https-certs.sh

.PHONY: server-update
server-update: # Stop all docker containers, update the repositories to the latest git tags, and start the containers again.
	@$(SECURE_WRAPPER) bin/server/update.sh

.PHONY: secrets-encrypt
secrets-encrypt: # Encrypt the .env file with a generated password
	@bash bin/secrets/encrypt.sh $(filter-out $@,$(MAKECMDGOALS))
.PHONY: secrets-decrypt
secrets-decrypt: # Decrypt the .env file
	@bash bin/secrets/decrypt.sh $(filter-out $@,$(MAKECMDGOALS))
.PHONY: secrets-edit-env
secrets-edit-env: # Edit the .env file
	@$(SECURE_WRAPPER) bin/secrets/edit-env.sh
%:
	@:
