import os
import json
import zipfile
import tempfile
import datetime

class CapsuleCorruptedError(Exception):
    """Raised when a capsule is corrupted, missing files, or contains invalid JSON."""
    pass

def write_capsule(crash_data, output_dir=".", prefix="crash_"):
    """
    Writes crash_data to a compressed .faultsnap ZIP archive.
    Returns the filename.
    """
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}{timestamp_str}.faultsnap"
    filepath = os.path.join(output_dir, filename)
    
    # Secure permissions
    # We will write to a temp file first, set permissions, then move it
    fd, temp_path = tempfile.mkstemp(suffix=".faultsnap")
    os.chmod(temp_path, 0o600) # Only owner can read/write
    
    try:
        with zipfile.ZipFile(temp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # We split the data into manifest and crash_data for easier high-level parsing
            manifest = crash_data.get("metadata", {})
            
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("crash_data.json", json.dumps(crash_data, indent=2))
            
        # Move to final destination
        import shutil
        shutil.move(temp_path, filepath)
    except Exception:
        os.remove(temp_path)
        raise
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
            
    return filepath

def read_capsule(filepath):
    """
    Reads a .faultsnap ZIP archive and returns the crash_data dictionary.
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            if "crash_data.json" not in zf.namelist():
                raise CapsuleCorruptedError(f"Missing 'crash_data.json' in {filepath}")
            with zf.open("crash_data.json") as f:
                return json.load(f)
    except zipfile.BadZipFile:
        raise CapsuleCorruptedError(f"File {filepath} is not a valid zip archive.")
    except json.JSONDecodeError:
        raise CapsuleCorruptedError(f"File {filepath} contains invalid JSON in crash_data.json.")
    except Exception as e:
        if isinstance(e, CapsuleCorruptedError):
            raise
        raise CapsuleCorruptedError(f"Failed to read capsule {filepath}: {e}")

def read_manifest(filepath):
    """
    Reads only the manifest from a .faultsnap ZIP archive.
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            if "manifest.json" not in zf.namelist():
                raise CapsuleCorruptedError(f"Missing 'manifest.json' in {filepath}")
            with zf.open("manifest.json") as f:
                return json.load(f)
    except zipfile.BadZipFile:
        raise CapsuleCorruptedError(f"File {filepath} is not a valid zip archive.")
    except json.JSONDecodeError:
        raise CapsuleCorruptedError(f"File {filepath} contains invalid JSON in manifest.json.")
    except Exception as e:
        if isinstance(e, CapsuleCorruptedError):
            raise
        raise CapsuleCorruptedError(f"Failed to read manifest {filepath}: {e}")
