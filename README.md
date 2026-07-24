<img src="https://github.com/beda-software/fhirsnake/raw/main/coral%20snake.webp" alt="fhirsnake Image" height="200">

# fhirsnake: turn static files to a FHIR server

![image](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)

## What is it?
**fhirsnake** is a minimalistic FHIR server that serve yaml and json files as FHIR resources

## How it works?
The server reads all `yaml` and `json` files from an input directory (`resources` by default).
The input directory should have subdirectories with names equal to resource types:
```markdown
resources/
├── Patient/
│   ├── example.yaml
│   ├── john-doe.json
│   └── patient3.yaml
├── Questionnaire/
│   ├── questionnaire1.yaml
│   ├── questionnaire2.yaml
│   └── subdir/
│       └── questionnaire3.yaml
```

Use the `--input` flag to specify a custom input directory. For `export` and `watch` commands, `--input` can be passed multiple times to load resources from several directories.

## Questionnaire language files

Questionnaires that share the same `url` (or `id` when `url` is missing) and differ by `language` are merged into a single resource during `export` and `watch` startup.

Rely only on `Questionnaire.language` and `Questionnaire.url` — filenames are ignored for grouping.

- Baseline: `language` missing or `en` (defaults to `en` when omitted)
- Variants: other languages (`de`, `fr`, …)
- A single questionnaire per url/id is left unchanged
- Flat and nested `item` trees in language files are both supported (`linkId` uniqueness)
- Only baseline `linkId`s are translated; extra `linkId`s in a variant are skipped
- Translations are stored as FHIR primitive extensions (`_text`, `_title`, `_description`) using `http://hl7.org/fhir/StructureDefinition/translation`

Example layout:

```markdown
Questionnaire/
  demo-questionnaire.yaml      # language: en (or omitted)
  demo-questionnaire.de.yaml   # language: de
  demo-questionnaire.fr.yaml   # language: fr (items may be flat)
```

## Environment variable substitution

To use environment variables in resources, you can use the syntax `${VAR_NAME}`.
In the case of missing environment variable, the exception will be raised.

NOTE: The syntax `$VAR` without braces is not supported because it might be used in resources.

## Supported operations
> [!IMPORTANT]
> All created and updated resources persist in runtime only. All changes are vanished after service restart

- **read**, **create** and **update** operations are supported
- **search** - limied support without any search params
- `GET /$index` operation returns a map of all resources in format `<resource_type>:<id>`


## Usage

1. Organize resources in a directory

### Server

```bash
docker run \
  -p 8002:8000 \
  -v ./resources:/resources \
  bedasoftware/fhirsnake server --input /resources
```

Or build a custom image with `Dockerfile.resources`:
```bash
docker build -t bedasoftware/fhirsnake -f Dockerfile.resources .
docker run -p 8000:8000 fhirsnake-resources
```

### Export

Export resources as `.json` (Bundle), `.ndjson`, or `.ndjson.gz`:

```bash
docker run \
  -v ./resources:/resources \
  -v ./output:/output \
  bedasoftware/fhirsnake export \
    --input /resources \
    --output /output/seeds.ndjson.gz
```

Multiple input directories:
```bash
docker run \
  -v ./resources1:/resources1 \
  -v ./resources2:/resources2 \
  -v ./output:/output \
  bedasoftware/fhirsnake export \
    --input /resources1 \
    --input /resources2 \
    --output /output/seeds.ndjson.gz
```

With external FCE->FHIR converter:
```bash
docker run \
  -v ./resources:/resources \
  -v ./output:/output \
  bedasoftware/fhirsnake export \
    --input /resources \
    --output /output/seeds.ndjson.gz \
    --external-questionnaire-fce-fhir-converter-url http://host.docker.internal:3000/to-fhir
```

### Watch

Watch resources for changes and send as PUT requests to an external FHIR server:

```bash
docker run \
  -v ./resources:/resources \
  bedasoftware/fhirsnake watch \
    --input /resources \
    --external-fhir-server-url http://host.docker.internal:8080
```

With auth headers:
```bash
docker run \
  -v ./resources:/resources \
  bedasoftware/fhirsnake watch \
    --input /resources \
    --external-fhir-server-url http://host.docker.internal:8080 \
    --external-fhir-server-header "Authorization: Token token"
```

Multiple input directories:
```bash
docker run \
  -v ./resources1:/resources1 \
  -v ./resources2:/resources2 \
  bedasoftware/fhirsnake watch \
    --input /resources1 \
    --input /resources2 \
    --external-fhir-server-url http://host.docker.internal:8080
```

### External questionnaire FCE->FHIR converter

The image `bedasoftware/questionnaire-fce-fhir-converter:latest` provides a `/to-fhir` endpoint that can be used with the `--external-questionnaire-fce-fhir-converter-url` flag in `export` and `watch` commands.

   
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

