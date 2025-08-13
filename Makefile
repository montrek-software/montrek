.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: local-init
local-init: # Install local python environment and necessary packages
	@bash bin/local/init.sh

.PHONY: local-runserver
local-runserver: # Run the montrek django app locally (non-docker).
	@bash bin/local/runserver.sh
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
	@bash bin/docker/logs.sh
.PHONY: docker-build
docker-build: # Shut the docker compose container down and up again
	@bash bin/docker/build.sh

.PHONY: docker-db-backup
docker-db-backup: # Make a backup of the docker database.
	@bash bin/docker/db.sh backup

.PHONY: docker-db-restore
docker-db-restore: # Restore the docker database from a backup.
	@bash bin/docker/db.sh restore


.PHONY: docker-django-manage
docker-django-manage: # Collect static files for the montrek django app.
	@bash bin/docker/django-manage.sh $(filter-out $@,$(MAKECMDGOALS))
%:
	@:

.PHONY: git-clone-repository
git-clone-repository: # Clone a montrek repository (expects a repository name like 'mt_economic_common').
	@bash bin/git/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: server-generate-https-certs
server-generate-https-certs: # Generate HTTPS certificates for the montrek django app.
	@bash bin/server/generate-https-certs.sh

.PHONY: sync-local-python-env
sync-local-python-env: # Sync the local (non-docker) python environment with the requirements specified in the montrek repositories.
	@bash bin/local/sync-python-env.sh

.PHONY: update-repositories
update-repositories: # Update all montrek repositories to the latest git tags.
	@bash bin/update-repositories-to-latest-tags.sh

.PHONY: docker-cleanup
docker-cleanup: # Remove unused docker artifacts.
	@bash bin/docker/cleanup.sh

.PHONY: update-server
update-server: # Stop all docker containers, update the repositories to the latest git tags, and start the containers again.
	@bash bin/start-docker.sh down
	@bash bin/update-repositories-to-latest-tags.sh
	@bash bin/start-docker.sh up -d --build
	@bash bin/docker-prune.sh

.PHONY: sonarqube-scan
sonarqube-scan: # Run a SonarQube scan and open in SonarQube (Add NO_TESTS=true to skip tests)
	@bash bin/sonarqube_scan.sh NO_TESTS=$(NO_TESTS) $(filter-out $@,$(MAKECMDGOALS))

%:
	@
.PHONY: build-montrek-container
build-montrek-container: # Build the container to run montrek in docker or github actions
	@bash bin/build-montrek-container.sh
%:
	@:
