docker-up:
	@bash bin/start-docker.sh up -d

docker_down:
	@bash bin/start-docker.sh down

local-db-create:
	@bash bin/local-db.sh create
