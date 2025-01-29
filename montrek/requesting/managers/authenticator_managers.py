from base64 import b64encode


class RequestAuthenticator:
    def get_headers(self):
        return {}


class RequestUserPasswordAuthenticator:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    def get_headers(self):
        credentials = b64encode(f"{self.user}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}


class RequestBearerAuthenticator:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}


class RequestSlugAuthenticator:
    def __init__(self, slug: str, token: str):
        self.slug = slug
        self.token = token

    def get_headers(self):
        return {"Authorization": f"{self.slug}:{self.token}"}
