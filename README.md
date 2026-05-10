# SwiftDeploy
SwiftDeploy is a CLI tool that deploys a containerised app using a single `manifest.yaml` file. You edit the manifest, the tool handles everything else.

## Requirements
- Docker
- Docker Compose
- Python 3
- curl

## Project Structure

- `app/` - FastAPI app, Dockerfile, and requirements.txt
- `templates/` - Nginx and Docker Compose templates
- `manifest.yaml` - single source of truth for the deployment
- `swiftdeploy` - the CLI tool

## Setup

Fork this repository by clicking the **Fork** button on the top right of this page:
`https://github.com/Dorcas-BD/swiftdeploy`

Then clone your forked copy:
```bash
git clone https://github.com/your-usernamee/swiftdeploy.git
cd swiftdeploy
```

Build the Docker image:
```bash
cd app
docker build -t swift-deploy-1-node:latest .
cd ..
```

Make the CLI executable:
```bash
chmod +x swiftdeploy
```

## Commands

### init
Generates `nginx.conf` and `docker-compose.yml` from the templates using values in `manifest.yaml`.
```bash
./swiftdeploy init
```

### validate
Runs 5 checks before you deploy. Stops and tells you what failed if anything is wrong.
```bash
./swiftdeploy validate
```
What it checks:
1. manifest.yaml exists and is valid YAML
2. All required fields are filled in
3. Docker image exists locally
4. Nginx port is not already in use
5. nginx.conf has been generated

### deploy
Runs init, starts the stack, and waits until the app is healthy before returning.
```bash
./swiftdeploy deploy
```

### promote
Switches the app between stable and canary mode without taking everything down.
```bash
./swiftdeploy promote canary
./swiftdeploy promote stable
```

### teardown
Stops and removes all containers, networks, and volumes.
```bash
./swiftdeploy teardown
```

To also delete the generated config files:
```bash
./swiftdeploy teardown --clean
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| / | GET | Returns mode, version, and current timestamp |
| /healthz | GET | Returns status and how long the app has been running |
| /chaos | POST | Simulates failures, only works in canary mode |

### Chaos examples

Slow responses:
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "slow", "duration": 5}'
```

Random errors:
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "error", "rate": 0.5}'
```

Back to normal:
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "recover"}'
```

## Modes

**stable** - normal production mode

**canary** - test mode, enables the chaos endpoint and adds an `X-Mode: canary` header to every response


## Demo

### Step 1 — deploy and promote to canary
```bash
./swiftdeploy deploy - (X2)
curl http://localhost:8080/
./swiftdeploy promote canary
```


### Step 2 — open the status dashboard in a second terminal
```bash
./swiftdeploy status
```

### Step 3 — inject errors and generate traffic
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "error", "rate": 0.5}'

for i in {1..20}; do curl -s http://localhost:8080/ > /dev/null; done
```

### Step 4 — try to promote, it will be blocked
```bash
./swiftdeploy promote stable
```

### Step 5 — recover and promote successfully
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "recover"}'

for i in {1..500}; do curl -s http://localhost:8080/ > /dev/null; done

./swiftdeploy promote stable
```
