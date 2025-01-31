docker-up:
	@bash bin/start-docker.sh up -d

docker-down:
	@bash bin/start-docker.sh down

local-db-create:
	@bash bin/local-db.sh create

local-db-backup:
	@bash bin/local-db.sh backup

local-db-restore:
	@bash bin/local-db.sh restore

runserver:
	@bash bin/local-runserver.sh

collect-static:
	@bash bin/collect-static.sh

clone-repository:
	@bash bin/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

generate-https-certs:
	@bash bin/generate-https-certs.sh

sync-local-python-env:
	@bash bin/sync-local-python-env.sh

