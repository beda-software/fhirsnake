import os
import re

ALLOWED_KEYS_TO_CONVERT = ["reference", "uri", "fullUrl"]


def substitute_env_vars(obj):
    if isinstance(obj, dict):
        return {k: substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(i) for i in obj]
    elif isinstance(obj, str):

        def replacer(match):
            var_name = match.group(1)
            if var_name not in os.environ:
                raise KeyError(f"Environment variable '{var_name}' is not set")
            return os.environ[var_name]

        return re.sub(r"\$\{(\w+)\}", replacer, obj)
    else:
        return obj


def convert_uri_to_reference(uri: str) -> str:
    if uri.startswith("urn:uuid:"):
        split = uri.split(":")
        return f"{split[2]}/{split[3]}"
    return uri


def replace_urn_uuid_with_reference(obj):
    if isinstance(obj, dict):
        return {
            key: (
                convert_uri_to_reference(value)
                if key in ALLOWED_KEYS_TO_CONVERT and isinstance(value, str)
                else replace_urn_uuid_with_reference(value)
            )
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [replace_urn_uuid_with_reference(item) for item in obj]
    return obj
