# PICK: Policy Control Study App

A Flask web application for a user study on attribute-based access control (ABAC) policy authoring, built for the ECOOP artifact evaluation.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

## Building the image

```bash
docker build -t pick-policy-control-study-app:artifact .
```

## Running the container

### Option A: SQLite (no external database required)

Run the app with an in-memory SQLite database. This is the simplest option for artifact reviewers — no MySQL setup needed. Data is stored in memory and lost when the container stops.

```bash
docker run -d --name pick-app -p 8080:8080 pick-policy-control-study-app:artifact
```

Then open http://localhost:8080.

### Option B: MySQL

For persistent storage, run MySQL alongside the app on a shared Docker network.

**1. Create a network:**

```bash
docker network create pick-net
```

**2. Start MySQL:**

```bash
docker run -d --name pick-db --network pick-net \
  -e MYSQL_DATABASE=pick_policy-control_app \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=apppassword \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  mysql:8.4
```

**3. Start the app** (wait ~15 seconds for MySQL to initialize):

```bash
docker run -d --name pick-app --network pick-net -p 8080:8080 \
  -e DB_USER=appuser \
  -e DB_PASSWORD=apppassword \
  -e DB_HOST=pick-db \
  -e DB_PORT=3306 \
  -e DB_NAME=pick_policy-control_app \
  pick-policy-control-study-app:artifact
```

Then open http://localhost:8080.

### Stopping and cleaning up

```bash
docker rm -f pick-app pick-db 2>/dev/null
docker network rm pick-net 2>/dev/null
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DB_USER` | — | MySQL username. If unset, the app falls back to SQLite. |
| `DB_PASSWORD` | — | MySQL password |
| `DB_HOST` | — | MySQL hostname |
| `DB_PORT` | — | MySQL port |
| `DB_NAME` | — | MySQL database name |

When any of the `DB_*` variables are missing, the app automatically uses an in-memory SQLite database.
