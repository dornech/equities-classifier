"""httpx logger"""

# ruff and mypy per file settings
#

# fmt: off


# use:
# client = httpx.Client(
#     event_hooks={
#         "request": [log_request],
#         "response": [log_response],
#     },
# )


import httpx


def log_request(request: httpx.Request) -> None:

    print("=" * 80)
    print(f">>> {request.method} {request.url}")

    print("--- Request headers ---")
    for name, value in request.headers.multi_items():
        print(f"{name}: {value}")

    if request.content:
        print("--- Request body - content native ---")
        print(request.content)
        print("--- Request body - decode ---")
        print(request.content.decode("utf-8", errors="replace"))


def log_response(response: httpx.Response) -> None:
    response.read()

    print(f"<<< {response.status_code} {response.reason_phrase}")
    print(f"HTTP version: {response.http_version}")

    print("--- Response headers ---")
    for name, value in response.headers.multi_items():
        print(f"{name}: {value}")

    print("--- Response body content ---")
    print(response.content)
    print("--- Response body text ---")
    print(response.text)

    print("=" * 80)
