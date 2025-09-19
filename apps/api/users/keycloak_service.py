from django.conf import settings
from keycloak import KeycloakOpenID
from .virtual_user import VirtualUser

class KeycloakService:
    def __init__(self, realm='spoton-uat'):
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=realm,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET
        )

    def get_user_info_from_token(self, access_token):
        try:
            user_info = self.keycloak_openid.userinfo(access_token)
            return VirtualUser(user_info)
        except Exception as e:
            # Handle token verification error
            return None

    def get_user_by_id(self, user_id):
        # This will require admin credentials, to be implemented later
        pass

    def find_user_by_email(self, email):
        # This will require admin credentials, to be implemented later
        pass 