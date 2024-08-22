# coralsnake: turn static files to a FHIR server

## What is it?
**coralsnake** is a minimalistic FHIR server that serve yaml and json files as FHIR resources

## How it works?
The server reads all `yaml` and `json` files from `resources` directory.
Rsources directory should have subdirectories with names equal resource types:
```
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
```
GET /Patient

GET /Patient/example

POST /Patient

PUT /Patient/new

GET /$index # get a map of all resources in format <resource_type>:<id>
```

## How to use?
1. Organize resources in a directory
2. Adjust source destination in `Dockerfile.resources` if required
3. Build an image using the base **coralsnake** image
    ```bash
    docker build -t coralsnake-resources:latest -f Dockerfile.resources .
    ```
4. Run a container
    ```bash
    docker run -p 8000:8000 coralsnake-resources 
    ```
   
## Contribution and feedback
Plaease, use [Issues](https://github.com/beda-software/coralsnake/issues)