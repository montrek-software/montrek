.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: docker-up
docker-up: # Start all docker containers in detached mode.
	@bash bin/start-docker.sh up -d

.PHONY: docker-down
docker-down: # Stop all docker containers.
	@bash bin/start-docker.sh down

.PHONY: docker-restart
local-db-backup: # Make a backup of the local (non-docker) database.
	@bash bin/local-db.sh backup

.PHONY: docker-restore
local-db-restore: # Restore the local (non-docker) database from a backup.
	@bash bin/local-db.sh restore

.PHONY: db-backup
db-backup: # Make a backup of the docker database.
	@bash bin/docker-db.sh backup

.PHONY: db-restore
db-restore: # Restore the docker database from a backup.
	@bash bin/docker-db.sh restore

.PHONY: runserver
runserver: # Run the montrek django app locally (non-docker).
	@bash bin/local-runserver.sh

.PHONY: collect-static
collect-static: # Collect static files for the montrek django app.
	@bash bin/collect-static.sh


.PHONY: clone-repository
clone-repository: # Clone a montrek repository (expects a repository name like 'mt_economic_common').
	@bash bin/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

.PHONY: generate-https-certs
generate-https-certs: # Generate HTTPS certificates for the montrek django app.
	@bash bin/generate-https-certs.sh

.PHONY: sync-local-python-env
sync-local-python-env: # Sync the local (non-docker) python environment with the requirements specified in the montrek repositories.
	@bash bin/sync-local-python-env.sh

.PHONY: update-repositories
update-repositories: # Update all montrek repositories to the latest git tags.
	@bash bin/update-repositories-to-latest-tags.sh

.PHONY: update-server
update-server: # Stop all docker containers, update the repositories to the latest git tags, and start the containers again.
	@bash bin/start-docker.sh down
	@bash bin/update-repositories-to-latest-tags.sh
	@bash bin/start-docker.sh up -d --build --prune
