import pytest
from django.test import RequestFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app_analytics.middleware import APIUsageMiddleware
from app_analytics.models import Resource
from tests.types import EnableFeaturesFixture


@pytest.mark.parametrize(
    "path, resource_name",
    [
        ("/api/v1/flags", "flags"),
        ("/api/v1/traits", "traits"),
        ("/api/v1/identities", "identities"),
        ("/api/v1/environment-document", "environment-document"),
    ],
)
def test_api_usage_middleware__calls_expected(
    rf: RequestFactory,
    mocker: MockerFixture,
    path: str,
    resource_name: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = True

    mocked_api_usage_cache = mocker.patch(
        "app_analytics.services.api_usage_cache", autospec=True
    )

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_api_usage_cache.track_request.assert_called_once_with(
        resource=Resource.get_from_name(resource_name),
        host="testserver",
        environment_key=environment_key,
        labels={},
    )


@pytest.mark.parametrize(
    "optional_headers,expected_labels",
    [
        ({}, {}),
        (
            {
                "HTTP_Flagsmith-Application-Name": "web",
                "HTTP_Flagsmith-Application-Version": "1.0",
                "HTTP_Unrelated-Header": "value",
            },
            {
                "client_application_name": "web",
                "client_application_version": "1.0",
            },
        ),
    ],
)
@pytest.mark.parametrize(
    "path, resource_name",
    [
        ("/api/v1/flags", "flags"),
        ("/api/v1/traits", "traits"),
        ("/api/v1/identities", "identities"),
        ("/api/v1/environment-document", "environment-document"),
    ],
)
def test_api_usage_middleware__no_cache__calls_expected(
    rf: RequestFactory,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
    path: str,
    resource_name: str,
    settings: SettingsWrapper,
    optional_headers: dict[str, str],
    expected_labels: dict[str, str],
) -> None:
    # Given
    enable_features("sdk_metrics_labels")
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key, **optional_headers}
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.services.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.run_in_thread.assert_called_once_with(
        kwargs={
            "resource": Resource.get_from_name(resource_name),
            "environment_key": environment_key,
            "host": "testserver",
            "labels": expected_labels,
        }
    )


def test_api_usage_middleware__request_not_tracked__not_calls_expected(
    rf: RequestFactory, mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    environment_key = "test"
    headers = {"HTTP_X-Environment-Key": environment_key}
    path = "/api/v1/unknown"
    request = rf.get(path, **headers)  # type: ignore[arg-type]
    settings.USE_CACHE_FOR_USAGE_DATA = False

    mocked_track_request = mocker.patch("app_analytics.services.track_request")

    mocked_get_response = mocker.MagicMock()
    middleware = APIUsageMiddleware(mocked_get_response)

    # When
    middleware(request)

    # Then
    mocked_track_request.delay.assert_not_called()
