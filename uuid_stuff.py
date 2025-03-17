import uuid
import base64
def generate_short_code():
    uuid_bytes = uuid.uuid4().bytes
    short_code = base64.b32encode(uuid_bytes).decode('utf-8').rstrip('=')
    return short_code[:6]
