import pytest
import json
from httpx import Response
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from starlette.datastructures import QueryParams
from integrations import hubspot

pytestmark = pytest.mark.asyncio


@patch("redis_client.add_key_value_redis", new_callable=AsyncMock)
async def test_authorize_hubspot(mock_redis):
    url = await hubspot.authorize_hubspot("user123", "org456")
    assert url.startswith("https://app.hubspot.com/oauth/authorize")
    assert "client_id=" in url
    assert "state=" in url
    mock_redis.assert_called_once()


@patch("redis_client.get_value_redis", new_callable=AsyncMock)
@patch("redis_client.delete_key_redis", new_callable=AsyncMock)
@patch("httpx.AsyncClient.post")
async def test_oauth2callback_success(mock_post, mock_delete, mock_get):
    state_data = {"state": "xyz", "user_id": "user123", "org_id": "org456"}
    encoded_state = hubspot._encode_state(state_data)

    mock_get.return_value = json.dumps(state_data)
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"access_token": "token"})

    request = MagicMock()
    request.query_params = QueryParams({"code": "auth_code", "state": encoded_state})

    resp = await hubspot.oauth2callback_hubspot(request)
    assert resp.status_code == 200
    assert "window.close()" in resp.body.decode()
    mock_get.assert_called_once()
    mock_post.assert_called_once()
    mock_delete.assert_called_once()


async def test_oauth2callback_error():
    request = MagicMock()
    request.query_params = QueryParams({"error": "access_denied", "error_description": "User denied access"})
    with pytest.raises(HTTPException) as exc:
        await hubspot.oauth2callback_hubspot(request)
    assert exc.value.status_code == 400


@patch("redis_client.get_value_redis", new_callable=AsyncMock)
async def test_get_hubspot_credentials_success(mock_get):
    mock_get.return_value = json.dumps({"access_token": "abc"})
    with patch("redis_client.delete_key_redis", new_callable=AsyncMock):
        creds = await hubspot.get_hubspot_credentials("user123", "org456")
        assert creds["access_token"] == "abc"


@patch("redis_client.get_value_redis", new_callable=AsyncMock)
async def test_get_hubspot_credentials_not_found(mock_get):
    mock_get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await hubspot.get_hubspot_credentials("user123", "org456")
    assert exc.value.detail == "No credentials found."


async def test_create_integration_item_metadata_object():
    response_json = {
        "id": "001",
        "properties": {
            "firstname": "John",
            "lastname": "Doe",
        },
    }
    metadata = await hubspot.create_integration_item_metadata_object(response_json, "Contact")
    assert metadata["id"] == "001_Contact"
    assert metadata["name"] == "John" or metadata["name"] == "Doe"


@patch("integrations.hubspot.requests.get")
async def test_get_items_hubspot(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"id": "001", "properties": {"firstname": "John"}},
        ],
        "paging": {},
    }
    mock_requests.return_value = mock_response

    creds = json.dumps({"access_token": "xyz"})
    items = await hubspot.get_items_hubspot(creds)
    parsed = json.loads(items)
    assert isinstance(parsed, list)
    assert parsed[0]["id"].endswith("_Contact")
