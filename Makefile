docker-up:
	@bash bin/start-docker.sh up -d

docker_down:
	@bash bin/start-docker.sh down

local-db-create:
	@bash bin/local-db.sh create

runserver:
	@bash bin/local-runserver.sh

clone-repository:
	@bash bin/clone-repository.sh $(filter-out $@,$(MAKECMDGOALS))

generate-https-certs:
	@bash bin/generate-https-certs.sh
