
import os
from urllib.parse import urlparse

# =============================================================================
# SAML Configuration for CloudCraver
# =============================================================================
# This file centralizes the SAML settings for the application.
# It is designed to be integrated with the main configuration system.
#
# To use this configuration, you will need to provide values for:
#   - idp_entity_id: The EntityID of your Identity Provider.
#   - idp_sso_url: The Single Sign-On URL of your Identity Provider.
#   - idp_x509_cert: The X.509 certificate of your Identity Provider.
#
# These values are typically provided by your IdP administrator.
# For development, you can use a mock IdP like MockSAML (mocksaml.com).
# =============================================================================

# --- Base Configuration ---
# The base URL of the Service Provider (our application)
SP_BASE_URL = os.environ.get("SP_BASE_URL", "http://localhost:8000")

# --- Identity Provider (IdP) Settings ---
# These settings must be configured for your specific IdP.
IDP_ENTITY_ID = os.environ.get("IDP_ENTITY_ID", "https://mocksaml.com/api/saml/metadata")
IDP_SSO_URL = os.environ.get("IDP_SSO_URL", "https://mocksaml.com/api/saml/sso")
IDP_X509_CERT = os.environ.get("IDP_X509_CERT", "")  # This should be the actual certificate content

# --- Service Provider (SP) Settings ---
# These settings define our application's SAML endpoints and behavior.
SP_ENTITY_ID = f"{SP_BASE_URL}/saml/metadata"
SP_ACS_URL = f"{SP_BASE_URL}/saml/acs"
SP_SLS_URL = f"{SP_BASE_URL}/saml/sls"

# --- Advanced Security Settings ---
# These settings control the security aspects of the SAML communication.
# It's recommended to sign assertions and enable other security features in production.
SAML_SECURITY_CONFIG = {
    "authnRequestsSigned": True,
    "logoutRequestSigned": True,
    "logoutResponseSigned": True,
    "signMetadata": True,
    "wantAssertionsSigned": True,
    "wantMessagesSigned": True,
    "wantNameId": True,
    "requestedAuthnContext": False,
    "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
}


def get_saml_settings():
    """
    Constructs the SAML settings dictionary required by python3-saml.
    """
    # For production, you should load the SP certificate and private key from a secure location.
    # For this example, we assume they are not set, but python3-saml can generate them if needed.
    sp_cert_path = os.path.join(os.path.dirname(__file__), "certs/sp.crt")
    sp_key_path = os.path.join(os.path.dirname(__file__), "certs/sp.key")

    # Ensure the certs directory exists
    os.makedirs(os.path.dirname(sp_cert_path), exist_ok=True)

    settings = {
        "strict": True,
        "debug": os.environ.get("DEBUG", "False").lower() == "true",
        "sp": {
            "entityId": SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": SP_ACS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": SP_SLS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            "x509cert": open(sp_cert_path).read() if os.path.exists(sp_cert_path) else "",
            "privateKey": open(sp_key_path).read() if os.path.exists(sp_key_path) else "",
        },
        "idp": {
            "entityId": IDP_ENTITY_ID,
            "singleSignOnService": {
                "url": IDP_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": IDP_X509_CERT,
        },
        "security": SAML_SECURITY_CONFIG,
    }
    return settings
