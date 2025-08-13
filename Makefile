.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: local-init
local-init: # Install local python environment and necessary packages
	@bash bin/local/init.sh

.PHONY: local-runserver
local-runserver: # Run the montrek django app locally (non-docker).
	@bash bin/local/runserver.sh

.PHONY: sync-local-python-env
sync-local-python-env: # Sync the local (non-docker) python environment with the requirements specified in the montrek repositories.
	@bash bin/local/sync-python-env.sh

.PHONY: local-sonarqube-scan
local-sonarqube-scan: # Run a SonarQube scan and open in SonarQube (Add NO_TESTS=true to skip tests)
	@bash bin/local/sonarqube_scan.sh NO_TESTS=$(NO_TESTS) $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-up
docker-up: # Start all docker containers in detached mode.
	@bash bin/docker/run.sh up -d

.PHONY: docker-down
docker-down: # Stop all docker containers.
	@bash bin/docker/run.sh down

.PHONY: docker-restart
docker-restart: # Shut the docker compose container down and up again
	@bash bin/docker/restart.sh

.PHONY: docker-logs
docker-logs: # Show docker compose logs
	@bash bin/docker/logs.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-build
docker-build: # Build the docker images
	@bash bin/docker/build.sh

.PHONY: docker-db-backup
docker-db-backup: # Make a backup of the docker database.
	@bash bin/docker/db.sh backup

.PHONY: docker-db-restore
docker-db-restore: # Restore the docker database from a backup.
	@bash bin/docker/db.sh restore

.PHONY: docker-django-manage
docker-django-manage: # Run Django management commands inside the docker container.
	@bash bin/docker/django-manage.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: docker-cleanup
docker-cleanup: # Remove unused docker artifacts.
	@bash bin/docker/cleanup.sh

.PHONY: git-clone-repository
git-clone-repository: # Clone a montrek repository (expects a repository name like 'mt_economic_common').
	@bash bin/git/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: git-update-repositories
git-update-repositories: # Update all montrek repositories to the latest git tags.
	@bash bin/git/update-repositories-to-latest-tags.sh

.PHONY: git-build-montrek-container
git-build-montrek-container: # Build the container to run montrek in docker or github actions
	@bash bin/git/build-montrek-container.sh

.PHONY: server-generate-https-certs
server-generate-https-certs: # Generate HTTPS certificates for the montrek django app.
	@bash bin/server/generate-https-certs.sh

.PHONY: server-update
server-update: # Stop all docker containers, update the repositories to the latest git tags, and start the containers again.
	@bash bin/server/update.sh

%:
	@:
