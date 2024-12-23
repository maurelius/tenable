"""install_linux_sensor.py: Installs a Tenable.io network scanner onto a Linux server, locally, and links it to our container"""
__version__ = "1.0"

# Import Azure KV Module from https://github.com/maurelius/azkvsecrets
# If you don't use this method, comment out the line below and store it as plaintext in a variable below
from Azure import az_kv_secrets as azkv
import subprocess
import socket
import getpass  # This is for retrieving your sudo password securely

# Grab hostname for scanner_name
scanner_name = socket.gethostname()
# Change this to the scanner group it should be added to
# If you want, you can grab the group names via `[d['name'] for d in io.scanner_groups.list()]`
scanner_group = "your_scanner_group"
# Grab the key from a keyvault to link to our container
# Comment this out if you don't import the KV module
linkingKey = azkv.get_linkingKey()
# Uncomment linkingKey below to store it in plaintext if you don't import the KV module above
# Reference Documentation: https://docs.tenable.com/vulnerability-management/Content/Settings/Sensors/RetrieveAgentLinkingKey.htm
# linkingKey = "ChangeMeToYourLinkingKey"

def install_scanner(linkingKey, scanner_name, scanner_group):
  # Get password securely from user
  password = getpass.getpass("Enter sudo password: ")

  # Construct the command with environment variable
  command = f"curl -H 'X-Key: {linkingKey}' 'https://sensor.cloud.tenable.com/install/scanner?name={scanner_name}&groups={scanner_group}' | sudo -S --stdin bash"

  # Execute the command with password
  subprocess.run(command.split(), input=password.encode('utf-8'), check=True)

install_scanner(linkingKey, scanner_name, scanner_group)