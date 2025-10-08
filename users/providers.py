import os

from dotenv import load_dotenv

load_dotenv()

SOCIALACCOUNT_PROVIDERS = {
    "microsoft": {
        "APP": {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
            "secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
            "key": "",
        },
        "AUTH_PARAMS": {"tenant": os.getenv("MICROSOFT_TENANT_ID")},
    }
}
