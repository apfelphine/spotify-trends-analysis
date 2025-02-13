# Spotify Trend Analysis App

## Requirements
- Docker Compose (tested with version v.2.32.4, you may check the installed version with `docker compose version`)
- Running Docker Engine

## Technology Stack
- Python backend (Relevant libraries: FastAPI, Pydantic & SQLModel)
- PostGIS database

## Setup Instructions
Start the software stack:
````bash
docker compose up -d
````

Check container logs:
````bash
docker compose logs -f <container-name>
````

Stop the software stack: 
````bash
docker compose down
````

To delete / reset the database add option `-v`:
````bash
docker compose down -v
````
