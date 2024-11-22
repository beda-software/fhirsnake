<img src="https://github.com/beda-software/fhirsnake/raw/main/coral%20snake.webp" alt="fhirsnake Image" height="200">

# fhirsnake: turn static files to a FHIR server

![image](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)

## What is it?
**fhirsnake** is a minimalistic FHIR server that serve yaml and json files as FHIR resources

## How it works?
The server reads all `yaml` and `json` files from `resources` directory.
Resources directory should have subdirectories with names equal resource types:
```markdown
resources/
├── Patient/
│   ├── example.yaml
│   ├── john-doe.json
│   └── patient3.yaml
├── Questionnaire/
│   ├── questionnaire1.yaml
│   ├── questionnaire2.yaml
│   └── questionnaire3.yaml
```

## Supported operations
> [!IMPORTANT]
> All created and updated resources persist in runtime only. All changes are vanished after service restart

- **read**, **create** and **update** operations are supported
- **search** - limied support without any search params
- `GET /$index` operation returns a map of all resources in format `<resource_type>:<id>`


## Usage

1. Organize resources in a directory

### Server
1. Option A: Run a container
    ```bash
    docker run -p 8002:8000 -v ./resources:/app/resources bedasoftware/fhirsnake
    ```
2. Option B: Adjust source destination in `Dockerfile.resources` if required
2.1. Build an image using the base image
    ```bash
    docker build -t fhirsnake-resources:latest -f Dockerfile.resources .
    docker run -p 8000:8000 fhirsnake-resources 
    ```

### Export
1. Export resources as .ndjson or ndjson.gz
    ```bash
    docker run -v ./resources:/app/resources -v ./output:/output bedasoftware/fhirsnake export --output /output/seeds.ndjson.gz
    ```

### Watch
1. Watch resources for changes and send as PUT requests to external fhir server
    ```bash
    docker run -v ./resources:/app/resources -v ./output:/output bedasoftware/fhirsnake watch --external-fhir-server-url http://localhost:8080 --external-fhir-server-header "Authorization: Token token"
    ```    

   
## Contribution and feedback
Please, use [Issues](https://github.com/beda-software/fhirsnake/issues)


## Development

### Format and fix with ruff
   ```sh
   ruff format
   ruff check . --fix
   ```

### Issue new version - run [semantic release](https://semantic-release.gitbook.io/semantic-release/usage/installation) locally
   ```sh
   npx semantic-release --no-ci
   ```

### Publish to pypi
   ```sh
   poetry build
   poetry publish
   ```

