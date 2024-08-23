<img src="https://raw.githubusercontent.com/beda-software/fhirsnake/main/coral%20snake.webp?token=GHSAT0AAAAAACT54SBRTO57XGPIFDF5HSCEZWIUQJA" alt="fhirsnake Image" height="200">

# fhirsnake: turn static files to a FHIR server

![image](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)


## What is it?
**fhirsnake** is a minimalistic FHIR server that serve yaml and json files as FHIR resources

## How it works?
The server reads all `yaml` and `json` files from `resources` directory.
Rsources directory should have subdirectories with names equal resource types:
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
- **read**, **create** and **update** operations are supported
- ❗all created and updated resources persist in runtime only
- ❗all changes are vanished after service restart
- **search** - limied support without any search params
- `GET /$index` operation returns a map of all resources in format `<resource_type>:<id>`


## How to use?
1. Organize resources in a directory
2. Adjust source destination in `Dockerfile.resources` if required
3. Option A: Run a container
    ```bash
    docker run -p 8002:8000 -v ./resources:/app/resources  bedasoftware/fhirsnake
    ```
3. Option B: Build an image using the base image
    ```bash
    docker build -t fhirsnake-resources:latest -f Dockerfile.resources .
    docker run -p 8000:8000 fhirsnake-resources 
    ```
   
## Contribution and feedback
Please, use [Issues](https://github.com/beda-software/fhirsnake/issues)


## Development

#### Format and fix with ruff
   ```sh
   ruff format
   ruff check . --fix
   ```

#### Issue new version - run [semantic release](https://semantic-release.gitbook.io/semantic-release/usage/installation) locally
   ```sh
   npx semantic-release --no-ci
   ```

#### Publish to pypi
   ```sh
   poetry build
   poetry publish
   ```

