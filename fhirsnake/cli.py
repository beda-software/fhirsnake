import argparse
import logging

import uvicorn
from export import export_resources
from watch import start_watcher

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI for fhirsnake")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to run")

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

    export_parser = subparsers.add_parser("export", help="Export resources as .json (Bundle) or .ndjson or .ndjson.gz")
    export_parser.add_argument(
        "--external-questionnaire-fce-fhir-converter-url",
        required=False,
        type=str,
        help="External Questionnaire FCE FHIR Converter URL",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Specify the output filename",
    )

    watch_parser = subparsers.add_parser("watch", help="Watch resources changes and send them to FHIR server")
    watch_parser.add_argument(
        "--external-questionnaire-fce-fhir-converter-url",
        required=False,
        type=str,
        help="External Questionnaire FCE FHIR Converter URL",
    )

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

    if args.command == "server":
        server(args.host, args.port)

    if args.command == "export":
        export(args.output, args.external_questionnaire_fce_fhir_converter_url)

    if args.command == "watch":
        watch(
            args.external_fhir_server_url,
            args.external_fhir_server_header,
            args.external_questionnaire_fce_fhir_converter_url,
        )


def server(host: str, port: int) -> None:
    config = uvicorn.Config("server:app", host=host, port=port)
    server = uvicorn.Server(config)
    server.run()


def export(output: str, external_questionnaire_fce_fhir_converter_url: str | None):
    export_resources(output, external_questionnaire_fce_fhir_converter_url)


def watch(url: str, headers_list: list[str] | None, external_questionnaire_fce_fhir_converter_url: str | None):
    headers = {v.split(":", 1)[0]: v.split(":", 1)[1] for v in (headers_list or [])}
    start_watcher(url, headers, external_questionnaire_fce_fhir_converter_url)


if __name__ == "__main__":
    main()
