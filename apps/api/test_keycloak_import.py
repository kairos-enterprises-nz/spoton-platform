#!/usr/bin/env python3
"""
Test file to verify keycloak imports work
"""
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

print("✅ SUCCESS: Keycloak imports work correctly!")
print(f"KeycloakAdmin class: {KeycloakAdmin}")
print(f"KeycloakError exception: {KeycloakError}")
