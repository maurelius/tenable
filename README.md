# tenable

A collection of Python scripts for automating various tasks in Tenable.io.

## Installation

To get started, install the necessary Python modules by running the following command:

```bash
pip install -r requirements.txt
```

## Configuration

These scripts require Tenable.io API keys and, in some cases, a linking key to be set as environment variables. This is a security best practice that avoids hardcoding sensitive information in the code.

### Required Environment Variables

-   `TENABLE_ACCESS_KEY`: Your Tenable.io access key.
-   `TENABLE_SECRET_KEY`: Your Tenable.io secret key.
-   `TENABLE_LINKING_KEY`: The linking key for installing new sensors (only required for `install_linux_sensor.py`).

You can set these environment variables in your shell profile (e.g., `~/.bashrc`, `~/.zshrc`) or export them in your current session:

```bash
export TENABLE_ACCESS_KEY="YOUR_ACCESS_KEY"
export TENABLE_SECRET_KEY="YOUR_SECRET_KEY"
export TENABLE_LINKING_KEY="YOUR_LINKING_KEY"
```

## Usage

Once you have configured the environment variables, you can run any of the scripts directly from your terminal. For example:

```bash
python3 tenable_io_scan_counts.py
```

Make sure to review each script's documentation to understand its specific function and any additional parameters it may require.