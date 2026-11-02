"""Verification engine for package sources, digital signatures, and file hashes."""

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()

# Trusted winget source names
TRUSTED_WINGET_SOURCES = {"winget", "msstore"}


class PackageVerifier:
    """Ensures packages come from trusted sources and pass cryptographic signature checks."""

    @staticmethod
    def verify_winget_source(source_name: Optional[str]) -> Tuple[bool, str]:
        """Validates that the package originates from an official, verified winget source."""
        if not source_name:
            return False, "Unspecified or unknown source repository"

        clean_src = source_name.strip().lower()
        if clean_src in TRUSTED_WINGET_SOURCES:
            return True, f"Verified trusted repository ({clean_src})"

        return False, f"Untrusted source repository '{source_name}'"

    @staticmethod
    def verify_file_hash(file_path: Path, expected_sha256: str) -> Tuple[bool, str]:
        """Calculates SHA-256 of the installer file and matches against expected hash."""
        if not file_path.exists():
            return False, f"Installer file does not exist: {file_path}"

        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest().lower()
            expected_clean = expected_sha256.strip().lower()

            if actual_sha == expected_clean:
                return True, "SHA-256 checksum verified"
            else:
                return False, f"SHA-256 mismatch: expected {expected_clean}, got {actual_sha}"
        except Exception as e:
            return False, f"Error calculating checksum: {e}"

    @staticmethod
    def verify_authenticode_signature(file_path: Path) -> Tuple[bool, str, Optional[str]]:
        """Verifies the Windows Authenticode digital signature on an executable installer.
        
        Returns:
            (is_valid, status_message, signer_subject)
        """
        if not file_path.exists():
            return False, f"File does not exist: {file_path}", None

        ps_cmd = (
            f"$sig = Get-AuthenticodeSignature -LiteralPath '{file_path}'; "
            "[PSCustomObject]@{"
            "Status = [int]$sig.Status; "
            "StatusMessage = $sig.StatusMessage; "
            "SignerCertificate = $sig.SignerCertificate.Subject"
            "} | ConvertTo-Json -Compress"
        )

        try:
            res = silent_run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            if res.returncode != 0:
                return False, f"Authenticode check returned error code {res.returncode}", None

            data = json.loads(res.stdout.strip())
            # Status == 0 corresponds to SignatureType.Valid
            status_code = data.get("Status")
            status_msg = data.get("StatusMessage") or "Unknown"
            signer = data.get("SignerCertificate")

            if status_code == 0:
                return True, f"Valid signature ({signer or 'Verified Signer'})", signer
            else:
                return False, f"Invalid or untrusted signature: {status_msg} (Code {status_code})", signer
        except Exception as e:
            logger.error(f"Error checking Authenticode signature for {file_path}: {e}")
            return False, f"Authenticode verification failed: {e}", None

