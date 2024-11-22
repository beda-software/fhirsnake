import argparse
import gzip
import logging

import ndjson
import uvicorn
from initial_resources import initial_resources
from watch import start_watcher

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI for fhirsnake")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to run")

    export_parser = subparsers.add_parser("export", help="Export resources as .ndjson or .ndjson.gz")
    export_parser.add_argument(
        "--output",
        required=True,
        help="Specify the output filename",
    )

    # TODO: add "serve" as alias
    server_parser = subparsers.add_parser("server", help="Run fhirsnake FHIR server")
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host",
    )

    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port",
    )

    watch_parser = subparsers.add_parser("watch", help="Watch resources changes and send them to FHIR server")
    watch_parser.add_argument(
        "--external-fhir-server-url",
        required=True,
        type=str,
        help="External FHIR Server URL",
    )

    watch_parser.add_argument(
        "--external-fhir-server-header",
        required=False,
        type=str,
        action="append",
        help="External FHIR Server header",
    )
    args = parser.parse_args()

    if args.command == "export":
        export_resources(args.output)

    if args.command == "server":
        server(args.host, args.port)

    if args.command == "watch":
        watch(args.external_fhir_server_url, args.external_fhir_server_header)


def server(host: str, port: int) -> None:
    config = uvicorn.Config("server:app", host=host, port=port)
    server = uvicorn.Server(config)
    server.run()


def watch(url: str, headers: list[str] | None):
    headers = headers or []
    headers = {v.split(":", 1)[0]: v.split(":", 1)[1] for v in headers}
    start_watcher(url, headers)


def export_resources(output: str) -> None:
    gzipped = output.endswith(".gz")
    resources_list = flatten_resources(initial_resources)
    dumped_resources = ndjson.dumps(resources_list)

    if gzipped:
        with gzip.open(output, "w+") as f:
            f.write(dumped_resources.encode())
    else:
        with open(output, "w+") as f:
            f.write(dumped_resources)


def flatten_resources(resources: dict[str, dict[str, dict]]) -> list[dict]:
    return [resource for by_resource_type in resources.values() for resource in by_resource_type.values()]


if __name__ == "__main__":
    main()
