"""
tenable_config.py

This module handles the configuration for the Tenable.io API client.
It retrieves the API keys from environment variables and provides a
function to initialize the TenableIO client.

Environment Variables:
- TENABLE_ACCESS_KEY: Your Tenable.io access key.
- TENABLE_SECRET_KEY: Your Tenable.io secret key.
"""

import os
from tenable.io import TenableIO

def get_tenable_io_client():
    """
    Initializes and returns a TenableIO client.

    This function retrieves the access and secret keys from the environment
    variables TENABLE_ACCESS_KEY and TENABLE_SECRET_KEY. It then creates
    and returns a TenableIO client instance.

    Returns:
        TenableIO: An initialized TenableIO client.

    Raises:
        ValueError: If the TENABLE_ACCESS_KEY or TENABLE_SECRET_KEY
                    environment variables are not set.
    """
    access_key = os.getenv("TENABLE_ACCESS_KEY")
    secret_key = os.getenv("TENABLE_SECRET_KEY")

    if not access_key or not secret_key:
        raise ValueError(
            "TENABLE_ACCESS_KEY and TENABLE_SECRET_KEY environment variables must be set."
        )

    return TenableIO(access_key, secret_key)