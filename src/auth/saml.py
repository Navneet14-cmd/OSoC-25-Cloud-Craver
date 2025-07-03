import base64
import json
import logging
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# from saml2.client import Saml2Client
# from saml2.config import Config as OneLogin_Saml2_Settings
# from saml2.s_utils import S_Utils as OneLogin_Saml2_Utils

logger = logging.getLogger(__name__)

SAML_RESPONSE_EVENT = threading.Event()
SAML_RESPONSE_DATA = None


class SAMLCallbackHandler(BaseHTTPRequestHandler):
    """
    A simple HTTP request handler to capture the SAML response from the IdP.
    """

    def do_POST(self):
        """
        Handles the POST request from the IdP containing the SAML assertion.
        """
        global SAML_RESPONSE_DATA, SAML_RESPONSE_EVENT
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        form_data = parse_qs(post_data)

        if "SAMLResponse" in form_data:
            SAML_RESPONSE_DATA = form_data["SAMLResponse"][0]
            SAML_RESPONSE_EVENT.set()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Login successful!</h1>"
                b"<p>You can close this window.</p></body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Login failed.</h1>"
                b"<p>No SAMLResponse found in the request.</p></body></html>"
            )

    def log_message(self, format, *args):
        """Suppress noisy logging from the HTTP server."""
        pass


class SAMLAuthService:
    """
    Provides SAML authentication services.
    """

    def __init__(self, config):
        self.config = config
        self.auth = self._init_saml_auth()

    def _init_saml_auth(self):
        """
        Initializes the OneLogin_Saml2_Auth instance from the configuration.
        """
        saml_settings = OneLogin_Saml2_Settings(
            settings=self.config, custom_base_path=os.path.dirname(__file__)
        )
        return OneLogin_Saml2_Auth(
            {"http": {"server_port": urlparse(self.config["sp"]["assertionConsumerService"]["url"]).port}},
            saml_settings,
        )

    def initiate_login(self):
        """
        Initiates the SAML login process by generating an AuthnRequest.
        """
        return self.auth.login()

    def process_response(self, saml_response_b64):
        """
        Processes the SAML response from the IdP.
        """
        self.auth.process_response(request_id=None, saml_response=saml_response_b64)
        if self.auth.is_authenticated():
            user_data = {
                "name_id": self.auth.get_nameid(),
                "attributes": self.auth.get_attributes(),
                "session_index": self.auth.get_session_index(),
            }
            return user_data
        else:
            logger.error("SAML authentication failed: %s", self.auth.get_last_error_reason())
            return None


def run_callback_server(port, server_class=HTTPServer, handler_class=SAMLCallbackHandler):
    """
    Runs a simple HTTP server to listen for the SAML callback.
    """
    server_address = ("localhost", port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting SAML callback server on http://{server_address[0]}:{port}")
    httpd.serve_forever()


def perform_saml_login(config):
    """
    Orchestrates the SAML login flow.
    """
    global SAML_RESPONSE_DATA, SAML_RESPONSE_EVENT

    saml_service = SAMLAuthService(config)
    login_url = saml_service.initiate_login()

    acs_url = urlparse(config["sp"]["assertionConsumerService"]["url"])
    callback_port = acs_url.port

    server_thread = threading.Thread(target=run_callback_server, args=(callback_port,))
    server_thread.daemon = True
    server_thread.start()

    print(f"Opening browser for SSO login: {login_url}")
    webbrowser.open(login_url)

    SAML_RESPONSE_EVENT.wait(timeout=120)  # Wait for 2 minutes

    if SAML_RESPONSE_DATA:
        user_data = saml_service.process_response(SAML_RESPONSE_DATA)
        if user_data:
            print("\nSSO Login Successful!")
            print(f"  User ID: {user_data['name_id']}")
            print(f"  Attributes: {json.dumps(user_data['attributes'], indent=2)}")
            # Here you would typically create a session token for the user
            return user_data
        else:
            print("\nSSO Login Failed. Please check the logs for details.")
            return None
    else:
        print("\nSSO login timed out. No response from Identity Provider.")
        return None
