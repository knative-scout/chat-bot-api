.PHONY: docker-cloud docker-local docker-build docker-run docker-push db db-cli production staging


DB_DATA_DIR ?= container-data/db
DB_CONTAINER_NAME ?= kscout-bot-api-db
DB_USER ?= kscout-dev
DB_PASSWORD ?= secretpassword

DOCKER_TAG_VERSION ?= staging-latest
DOCKER_TAG ?= kscout/bot-api:${DOCKER_TAG_VERSION}


NAMESPACE ?= kscoutbot
POD ?= staging-bot-api

PROD_NAMESPACE ?= kscoutbot
PROD_POD ?= prod-bot-api


# Build and Push to docker hub
docker-cloud: docker-build docker-push


# build Docker image
docker-build:
	docker build -t ${DOCKER_TAG} .


# Push the docker image for bot-api to docker hub
docker-push:
	docker push ${DOCKER_TAG}


# Runs the bot-api docker image on local machine
docker-run:
	docker run -it --rm -e API_KEY=${API_KEY} -e WORKSPACE_ID=${WORKSPACE_ID} --net host ${DOCKER_TAG}


# Start MongoDB server in container
# Pulls docker image for latest mongo build and runs the container
db:
	mkdir -p ${DB_DATA_DIR}
	docker run \
		-it --rm --net host --name ${DB_CONTAINER_NAME} \
		-v ${PWD}/${DB_DATA_DIR}:/data/db \
		-e MONGO_INITDB_ROOT_USERNAME=${DB_USER} \
		-e MONGO_INITDB_ROOT_PASSWORD=${DB_PASSWORD} \
		mongo:latest

# Runs mongo on shell
db-cli:
	docker run -it --rm --net host mongo:latest mongo -u ${DB_USER} -p ${DB_PASSWORD}



#Staging the app
staging: docker-cloud staging-rollout

# Deploy code to Production:
production:
	./deploy/deploy.sh -n ${PROD_NAMESPACE} -p ${PROD_POD} -t prod

#deploy code to staging:
staging-rollout:
	./deploy/deploy.sh -n ${NAMESPACE} -p ${POD} -t staging