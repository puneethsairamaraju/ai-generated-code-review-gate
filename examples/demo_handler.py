"""Demo payload parser: deserialize JSON instead of executing source code."""
import json


def parse_payload(user_input):
    return json.loads(user_input)
