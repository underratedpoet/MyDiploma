import os

admin_password = os.environ.get("ADMIN_PASSWORD")

def check_auth(request):
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {admin_password}"
