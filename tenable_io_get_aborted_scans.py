#!/usr/bin/env python3
'''
Tenable.io - Aborted Scans with Notes

Description:
  This script retrieves all scans from Tenable.io that are in an "aborted" state and are enabled. For each aborted scan,
  it fetches the most recent scan results using the `history_uuid` and `scan_id`. It then extracts any notes associated with that scan run,
  along with optional context about the scan's run status, error messages, and reasons for abortion. The collected data is
  compiled into a pandas DataFrame and saved as a CSV file for reporting purposes.

Requires:
  pip install pytenable pandas

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.
  
Outputs:
  - CSV file with details of aborted scans and their associated notes, including scan ID, scan name, note title, note message, and optional context about the scan run status, error, and reason for abortion.
'''
from tenable.io import TenableIO
import json
import os
import pandas as pd
import logging

# Note: The above imports assume you have pytenable installed and properly configured with your Tenable.io credentials.

# Bootstrap Tenable.io client
io = TenableIO()
# Pull in all scans
scans = io.scans.list()
# Grab all scans that are aborted and enabled
aborted_scans = [d for d in scans if d['status'] is 'aborted' and d['enabled'] is True]

rows = []

for a in aborted_scans:
    # Get the per-run results (your script uses history_uuid + scan_id)
    hist_results = io.scans.results(history_uuid=a['uuid'], scan_id=a['id'])

    # Normalize notes to a list
    notes = hist_results.get('notes', [])
    if not isinstance(notes, list):
        notes = []

    # Optional: pull helpful reason fields directly from this run
    run_status = hist_results.get('status')
    run_error  = hist_results.get('error') or (hist_results.get('info') or {}).get('error')
    run_reason = (hist_results.get('info') or {}).get('reason') or (hist_results.get('info') or {}).get('message')

    if notes:
        for n in notes:
            n = n or {}
            rows.append({
                "scan_id": a.get("id"),
                "scan_name": a.get("name"),
                "note_title": n.get("title"),
                "note_message": n.get("message"),
                # optional context to help explain *why* it aborted
                "run_status": run_status,
                "run_error": run_error,
                "run_reason": run_reason,
            })
    else:
        # If no notes, still include a row so you can see which scan/run lacked notes
        rows.append({
            "scan_id": a.get("id"),
            "scan_name": a.get("name"),
            "note_title": None,
            "note_message": None,
            "run_status": run_status,
            "run_error": run_error,
            "run_reason": run_reason,
        })

# Create the DataFrame
df = pd.DataFrame(rows, columns=[
    "scan_id", "scan_name", "note_title", "note_message",
    "run_status", "run_error", "run_reason"
])

# Basic description of notes collected
print("Summary of notes collected from aborted scans:")
df['note_title'].describe()

# Example: filter to only rows that actually have a note
# df_with_notes = df.dropna(subset=["note_title", "note_message"], how="all")

# Save for reporting
df.to_csv("aborted_scans_with_notes.csv", index=False)