import os
import tarfile
import time
import json
from utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_DIR = os.path.join(os.path.expanduser("~"), "aria", "backups")
ARIA_HOME = os.path.join(os.path.expanduser("~"), "aria")
PROJECTS_DIR = os.path.join(os.path.expanduser("~"), "aria_projects")

def _compute_manifest(paths):
    """Return a dict of {rel_path: {'size': int, 'mtime': float}} for given list of (abs_path, arcname)."""
    manifest = {}
    for abs_path, arcname in paths:
        if os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, os.path.expanduser("~"))
                    try:
                        stat = os.stat(full)
                        manifest[rel] = {"size": stat.st_size, "mtime": stat.st_mtime}
                    except OSError:
                        pass
        elif os.path.isfile(abs_path):
            rel = os.path.relpath(abs_path, os.path.expanduser("~"))
            try:
                stat = os.stat(abs_path)
                manifest[rel] = {"size": stat.st_size, "mtime": stat.st_mtime}
            except OSError:
                pass
    return manifest

def _load_previous_manifest():
    """Return (manifest_dict, filename) of the most recent backup, or (None, None)."""
    if not os.path.isdir(BACKUP_DIR):
        return None, None
    backups = list_backups()
    for bkp in backups:
        manifest_file = os.path.join(BACKUP_DIR, bkp.replace(".tar.gz", ".json"))
        if os.path.isfile(manifest_file):
            with open(manifest_file, 'r') as f:
                return json.load(f), bkp
    return None, None

def create_backup(custom_name=None):
    """Create a timestamped backup. If custom_name given, use it instead of timestamp.
    Returns (backup_filename, diff_text)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if custom_name:
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in custom_name)
        backup_name = f"backup_{safe_name}.tar.gz"
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    sources = [
        (os.path.join(ARIA_HOME, "config"), "config"),
        (os.path.join(ARIA_HOME, "data"), "data"),
        (os.path.join(ARIA_HOME, "plugins"), "plugins"),
    ]
    if os.path.exists(PROJECTS_DIR):
        sources.append((PROJECTS_DIR, "aria_projects"))

    new_manifest = _compute_manifest(sources)

    try:
        with tarfile.open(backup_path, "w:gz") as tar:
            for abs_path, arcname in sources:
                if os.path.exists(abs_path):
                    tar.add(abs_path, arcname=arcname)
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise RuntimeError(f"Backup failed: {e}")

    manifest_path = os.path.join(BACKUP_DIR, backup_name.replace(".tar.gz", ".json"))
    with open(manifest_path, 'w') as f:
        json.dump(new_manifest, f, indent=2)

    prev_manifest, prev_name = _load_previous_manifest()
    diff = _generate_diff(prev_manifest, new_manifest, prev_name)

    logger.info(f"Backup created: {backup_path}")
    return backup_name, diff

def _generate_diff(old_manifest, new_manifest, old_name):
    """Return a human-readable diff string between two manifests."""
    if old_manifest is None:
        return "ℹ️ No previous backup to compare.\nAll current files are included."
    
    old_files = set(old_manifest.keys())
    new_files = set(new_manifest.keys())
    
    added = new_files - old_files
    removed = old_files - new_files
    common = old_files & new_files
    
    changed = []
    for f in common:
        if old_manifest[f]["size"] != new_manifest[f]["size"]:
            changed.append(f)
    
    lines = [f"📊 Compared to previous backup: {old_name}"]
    if added:
        lines.append(f"  ➕ Added files ({len(added)}):")
        for f in sorted(added):
            lines.append(f"     - {f}")
    if removed:
        lines.append(f"  ➖ Removed files ({len(removed)}):")
        for f in sorted(removed):
            lines.append(f"     - {f}")
    if changed:
        lines.append(f"  ✏️ Modified files ({len(changed)}):")
        for f in sorted(changed):
            lines.append(f"     - {f}")
    if not added and not removed and not changed:
        lines.append("  ✅ No changes detected.")
    return "\n".join(lines)

def list_backups():
    """
    Return list of backup filenames sorted by modification time (NEWEST FIRST).
    This ensures the most recent backup is always at the top, regardless of its custom name.
    """
    if not os.path.isdir(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".tar.gz")]
    # Sort by modification time, newest first
    files.sort(key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)), reverse=True)
    return files

def get_backup_diff(backup_filename):
    """Return the diff text for a given backup compared to its previous one."""
    manifest_path = os.path.join(BACKUP_DIR, backup_filename.replace(".tar.gz", ".json"))
    if not os.path.isfile(manifest_path):
        return "No manifest available."
    with open(manifest_path, 'r') as f:
        new_manifest = json.load(f)
    
    backups = list_backups()
    try:
        idx = backups.index(backup_filename)
    except ValueError:
        return "Backup not found."
    
    if idx + 1 < len(backups):
        prev_bkp = backups[idx+1]
        prev_manifest_path = os.path.join(BACKUP_DIR, prev_bkp.replace(".tar.gz", ".json"))
        if os.path.isfile(prev_manifest_path):
            with open(prev_manifest_path, 'r') as f:
                prev_manifest = json.load(f)
            return _generate_diff(prev_manifest, new_manifest, prev_bkp)
        else:
            return "Previous manifest not available."
    else:
        return "No previous backup to compare."

def restore_backup(backup_filename):
    """Extract a backup tarball to home directory. Overwrites existing files."""
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_filename}")

    home = os.path.expanduser("~")
    try:
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=home)
        logger.info(f"Backup restored: {backup_filename}")
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise RuntimeError(f"Restore failed: {e}")
