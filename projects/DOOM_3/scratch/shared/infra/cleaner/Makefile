.PHONY: build up down test

build:
	 docker-compose -f docker-compose.yml build
up:
	 docker-compose -f docker-compose.yml up -d
down:
	 docker-compose -f docker-compose.yml down

test:
	 curl -s http://localhost:8080/health
