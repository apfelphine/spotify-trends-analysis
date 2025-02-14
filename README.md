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

## Available services
| Service     | URL                                                              | Credentials                   |
|-------------|------------------------------------------------------------------|-------------------------------|
| Application | [http://localhost:8080](http://localhost:8080)                   | Non required                  |
| API         | [http://localhost:8080/api/docs](http://localhost:8888/api/docs) | Non required                  |
| PostGIS     | [http://localhost:5432](http://localhost:5432)                   | postgres:postgres             |
| pgAdmin     | [http://localhost:8888](http://localhost:8888)                   | postgres@postgres.de:postgres |

### Connecting to the database with pgAdmin
- **Hostname**: db
- **Port**: 5432
- **Credentials**: See above (postgres:postgres)