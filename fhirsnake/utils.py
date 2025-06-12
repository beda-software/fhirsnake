import os
import re


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
