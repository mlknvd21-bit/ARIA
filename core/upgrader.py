import os
import json
import shutil
import subprocess
import tarfile
import time
from utils.logger import get_logger
from utils.backup import BACKUP_DIR

logger = get_logger(__name__)

ARIA_HOME = os.path.expanduser("~/aria")
UPGRADE_BACKUP_DIR = os.path.join(BACKUP_DIR, "upgrade_backups")
VERSION_URL = "https://raw.githubusercontent.com/mlknvd21-bit/ARIA/main/version.json"
REPO_URL = "https://github.com/mlknvd21-bit/ARIA/archive/main.tar.gz"

class Upgrader:
    def __init__(self):
        os.makedirs(UPGRADE_BACKUP_DIR, exist_ok=True)
        self.current_version = self._load_current_version()

    def _load_current_version(self):
        path = os.path.join(ARIA_HOME, "version.json")
        if os.path.isfile(path):
            with open(path, "r") as f:
                data = json.load(f)
            return data.get("version", "0.0.0")
        return "0.0.0"

    def check_for_update(self):
        """Return (True, new_version, notes) if update available, else (False, None, None)."""
        try:
            import httpx
            resp = httpx.get(VERSION_URL, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                remote_version = data.get("version", "0.0.0")
                if remote_version > self.current_version:
                    return True, remote_version, data.get("notes", "")
        except Exception as e:
            logger.error(f"Version check failed: {e}")
        return False, None, None

    def backup_current(self):
        """Backup current ARIA files before upgrade."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_upgrade_{self.current_version}_{timestamp}.tar.gz"
        backup_path = os.path.join(UPGRADE_BACKUP_DIR, backup_name)
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                for folder in ["core", "providers", "tools", "plugins", "ui", "utils", "data", "config"]:
                    fpath = os.path.join(ARIA_HOME, folder)
                    if os.path.exists(fpath):
                        tar.add(fpath, arcname=folder)
                # Also backup main.py, config.yaml, version.json
                for f in ["main.py", "config.yaml", "version.json"]:
                    fpath = os.path.join(ARIA_HOME, f)
                    if os.path.isfile(fpath):
                        tar.add(fpath, arcname=f)
            logger.info(f"Pre-upgrade backup saved: {backup_name}")
            return backup_path
        except Exception as e:
            logger.error(f"Pre-upgrade backup failed: {e}")
            return None

    def download_and_extract(self):
        """Download latest code from GitHub and extract to a temp folder."""
        import httpx
        temp_dir = os.path.join(ARIA_HOME, "temp_upgrade")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        tarball_path = os.path.join(temp_dir, "latest.tar.gz")
        try:
            resp = httpx.get(REPO_URL, timeout=30)
            with open(tarball_path, "wb") as f:
                f.write(resp.content)
            # Extract
            with tarfile.open(tarball_path, "r:gz") as tar:
                tar.extractall(path=temp_dir)
            # The GitHub tarball contains a single folder "ARIA-main"
            extracted = os.path.join(temp_dir, "ARIA-main")
            if os.path.isdir(extracted):
                return extracted
            else:
                # Find the first folder
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        return item_path
                return None
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def apply_upgrade(self, extracted_path):
        """Copy new files over old files, preserving user data."""
        if not extracted_path or not os.path.isdir(extracted_path):
            return False

        # Folders to overwrite
        for folder in ["core", "providers", "tools", "plugins", "ui", "utils"]:
            src = os.path.join(extracted_path, folder)
            dst = os.path.join(ARIA_HOME, folder)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

        # Files to overwrite
        for f in ["main.py", "config.yaml", "version.json"]:
            src = os.path.join(extracted_path, f)
            dst = os.path.join(ARIA_HOME, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        # Cleanup temp
        temp_dir = os.path.join(ARIA_HOME, "temp_upgrade")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        logger.info("Upgrade applied successfully.")
        return True

    def restore_backup(self, backup_name=None):
        """Restore a pre-upgrade backup by filename."""
        if backup_name is None:
            # Find latest backup
            if not os.path.isdir(UPGRADE_BACKUP_DIR):
                return False, "No upgrade backups found."
            files = [f for f in os.listdir(UPGRADE_BACKUP_DIR) if f.endswith(".tar.gz")]
            if not files:
                return False, "No upgrade backups found."
            files.sort(reverse=True)
            backup_name = files[0]

        backup_path = os.path.join(UPGRADE_BACKUP_DIR, backup_name)
        if not os.path.isfile(backup_path):
            return False, f"Backup file not found: {backup_name}"

        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=ARIA_HOME)
            logger.info(f"Restored backup: {backup_name}")
            return True, f"Restored to {backup_name}"
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, str(e)

    def list_backups(self):
        """Return list of upgrade backup filenames."""
        if not os.path.isdir(UPGRADE_BACKUP_DIR):
            return []
        files = [f for f in os.listdir(UPGRADE_BACKUP_DIR) if f.endswith(".tar.gz")]
        files.sort(reverse=True)
        return files
