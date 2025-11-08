"""generated with djinit"""

from rest_framework.response import Response


def success(data=None, status_code=200):
    """Return a successful response."""
    return Response({"success": True, "data": data}, status=status_code)


def error(message, status_code=400):
    """Return an error response."""
    return Response({"success": False, "message": message}, status=status_code)
