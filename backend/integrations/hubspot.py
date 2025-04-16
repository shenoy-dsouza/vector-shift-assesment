import base64
import json
import logging
import os
import secrets

import httpx
import requests
from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from fastapi.responses import HTMLResponse

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, delete_key_redis, get_value_redis

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Environment variables
CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")
AUTHORIZATION_URL = os.getenv(
    "HUBSPOT_AUTH_URL", "https://app.hubspot.com/oauth/authorize"
)
TOKEN_URL = os.getenv(
    "HUBSPOT_TOKEN_URL", "https://api.hubapi.com/oauth/v1/token"
)
SCOPES = [
    "oauth",
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.companies.read",
    "crm.objects.companies.write",
]
HUBSPOT_OBJECTS = {
    "Contact": "contacts",
    "Company": "companies",
}
HUBSPOT_API_BASE_URL = os.getenv(
    "HUBSPOT_API_BASE_URL", "https://api.hubapi.com/crm/v3/objects/"
)

encoded_client_id_secret = base64.b64encode(
    f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
).decode()


def _encode_state(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def _decode_state(encoded: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(encoded).decode())


async def authorize_hubspot(user_id: str, org_id: str) -> str:
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }

    encoded_state = _encode_state(state_data)
    scope = " ".join(SCOPES)
    auth_url = (
        f"{AUTHORIZATION_URL}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}&state={encoded_state}"
    )

    await add_key_value_redis(
        f"hubspot_state:{org_id}:{user_id}", json.dumps(state_data), expire=600
    )
    return auth_url


async def oauth2callback_hubspot(request: Request):
    if request.query_params.get("error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=request.query_params.get("error_description"),
        )

    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")
    state_data = _decode_state(encoded_state)
    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")

    # Retrieve and verify state_data from Redis
    saved_state = await get_value_redis(f"hubspot_state:{org_id}:{user_id}")
    if not saved_state or state_data.get("state") != json.loads(
        saved_state
    ).get("state"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch."
        )

    # Get access token using the authorization code
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token exchange failed.",
        )

    credentials = response.json()
    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(credentials),
        expire=600,
    )

    # Delete state_data from Redis as it is no longer needed
    await delete_key_redis(f"hubspot_state:{org_id}:{user_id}")

    # Close the popup window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)


async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}"
    )
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No credentials found.",
        )
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No credentials found.",
        )
    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")
    return credentials


async def create_integration_item_metadata_object(
    response_json: dict, item_type: str, parent_id=None, parent_name=None
) -> dict:
    parent_id = None if parent_id is None else parent_id + "_Hubspot"
    integration_item_metadata = IntegrationItem(
        id=str(response_json.get("id", None)) + "_" + item_type,
        name=response_json.get("properties", {}).get("name")
        or response_json.get("properties", {}).get("firstname")
        or response_json.get("properties", {}).get("lastname"),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )

    return integration_item_metadata.__dict__


async def get_items_hubspot(credentials):
    """Fetch contacts, companies from HubSpot and return metadata."""
    credentials = json.loads(credentials)
    access_token = credentials.get("access_token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    list_of_integration_item_metadata = []

    for item_type, object_type in HUBSPOT_OBJECTS.items():
        url = f"{HUBSPOT_API_BASE_URL}/{object_type}"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"limit": 10}
        more_results = True
        after = None

        while more_results:
            if after:
                params["after"] = after

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == status.HTTP_200_OK:
                json_response = response.json()
                for item in json_response.get("results", []):
                    metadata = await create_integration_item_metadata_object(
                        item, item_type
                    )
                    list_of_integration_item_metadata.append(metadata)

                paging = json_response.get("paging", {})
                next_link = paging.get("next", {}).get("after")
                if next_link:
                    after = next_link
                else:
                    more_results = False
            else:
                more_results = False
                logger.error(f"Error fetching {object_type}: {response.text}")

    return json.dumps(list_of_integration_item_metadata)
