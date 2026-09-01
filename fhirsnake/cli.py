import argparse
import logging
import os

import uvicorn
from export import export_resources
from watch import start_watcher

logging.basicConfig(level=logging.INFO)

DEFAULT_INPUT_DIR = "resources"

root_dir = os.path.dirname(os.path.abspath(__file__))
default_input_dir_abs_path = os.path.join(root_dir, DEFAULT_INPUT_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI for fhirsnake")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to run")

    # TODO: add "serve" as alias
    server_parser = subparsers.add_parser("server", help="Run fhirsnake FHIR server")
    server_parser.add_argument(
        "--input",
        help=f"Directory of FHIR JSON resources to load (default: {default_input_dir_abs_path})",
    )
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
    server_parser.add_argument(
        "--prefer-resource-id",
        action="store_true",
        default=False,
        help="Use the id declared inside a resource file instead of the filename-derived id",
    )

    export_parser = subparsers.add_parser("export", help="Export resources as .json (Bundle) or .ndjson or .ndjson.gz")
    export_parser.add_argument(
        "--input",
        action="append",
        help=f"Input directories to load resources from (default: {default_input_dir_abs_path})",
    )
    export_parser.add_argument(
        "--external-questionnaire-fce-fhir-converter-url",
        required=False,
        type=str,
        help="External Questionnaire FCE FHIR Converter URL",
    )
    export_parser.add_argument(
        "--embed-mapping",
        action="store_true",
        default=False,
        help="Embed Mapping resources as JSON strings into Questionnaire extensions",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Specify the output filename",
    )
    export_parser.add_argument(
        "--prefer-resource-id",
        action="store_true",
        default=False,
        help="Use the id declared inside a resource file instead of the filename-derived id",
    )

    watch_parser = subparsers.add_parser("watch", help="Watch resources changes and send them to FHIR server")
    watch_parser.add_argument(
        "--input",
        action="append",
        help=f"Input directories to load resources from (default: {default_input_dir_abs_path})",
    )
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
    watch_parser.add_argument(
        "--embed-mapping",
        action="store_true",
        default=False,
        help="Embed Mapping resources as JSON strings into Questionnaire extensions",
    )
    watch_parser.add_argument(
        "--prefer-resource-id",
        action="store_true",
        default=False,
        help="Use the id declared inside a resource file instead of the filename-derived id",
    )
    args = parser.parse_args()

    if args.command == "server":
        server(args.input or default_input_dir_abs_path, args.host, args.port, args.prefer_resource_id)

    if args.command == "export":
        export(
            args.input or [default_input_dir_abs_path],
            args.output,
            args.external_questionnaire_fce_fhir_converter_url,
            args.embed_mapping,
            args.prefer_resource_id,
        )

    if args.command == "watch":
        watch(
            args.input or [default_input_dir_abs_path],
            args.external_fhir_server_url,
            args.external_fhir_server_header,
            args.external_questionnaire_fce_fhir_converter_url,
            args.embed_mapping,
            args.prefer_resource_id,
        )


def validate_input_dirs(input_dirs: list[str]) -> None:
    for input_dir in input_dirs:
        if not os.path.isdir(input_dir):
            raise RuntimeError(f"Required directory '{input_dir}' does not exist. Stopping application.")


def server(input_dir: str, host: str, port: int, prefer_resource_id: bool = False) -> None:
    from server import create_app

    validate_input_dirs([input_dir])
    config = uvicorn.Config(create_app(input_dir, prefer_resource_id), host=host, port=port)
    server = uvicorn.Server(config)
    server.run()


def export(
    input_dirs: list[str],
    output: str,
    external_questionnaire_fce_fhir_converter_url: str | None,
    embed_mapping: bool = False,
    prefer_resource_id: bool = False,
):
    validate_input_dirs(input_dirs)
    export_resources(
        input_dirs, output, external_questionnaire_fce_fhir_converter_url, embed_mapping, prefer_resource_id
    )


def watch(
    input_dirs: list[str],
    url: str,
    headers_list: list[str] | None,
    external_questionnaire_fce_fhir_converter_url: str | None,
    embed_mapping: bool = False,
    prefer_resource_id: bool = False,
):
    validate_input_dirs(input_dirs)
    headers = {v.split(":", 1)[0].strip(): v.split(":", 1)[1].strip() for v in (headers_list or [])}
    start_watcher(
        input_dirs, url, headers, external_questionnaire_fce_fhir_converter_url, embed_mapping, prefer_resource_id
    )


if __name__ == "__main__":
    main()
