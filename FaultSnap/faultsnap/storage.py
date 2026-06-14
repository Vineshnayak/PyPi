import os
import json
import shutil
from datetime import datetime, timedelta
from faultsnap.config import config
from faultsnap.capsule import write_capsule

def _get_index_path():
    return os.path.join(config.repository_dir, "index.json")

def _read_index():
    index_path = _get_index_path()
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _write_index(index_data):
    index_path = _get_index_path()
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)

def save_crash(crash_data, prefix="crash_"):
    manifest = crash_data.get("metadata", {})
    exc_type = manifest.get("exception_type", "Unknown")
    fingerprint = manifest.get("fingerprint", "Unknown")
    timestamp_str = manifest.get("timestamp")
    
    if timestamp_str:
        try:
            dt = datetime.fromisoformat(timestamp_str)
        except Exception:
            dt = datetime.now()
    else:
        dt = datetime.now()
        manifest["timestamp"] = dt.isoformat()
        
    date_str = dt.strftime("%Y-%m-%d")
    time_prefix = dt.strftime("%H%M%S")
    
    if prefix == "crash_":
        file_prefix = f"crash_{time_prefix}_"
    else:
        file_prefix = f"{prefix}{time_prefix}_"
        
    target_dir = os.path.join(config.repository_dir, exc_type, date_str, fingerprint)
    os.makedirs(target_dir, exist_ok=True)
    
    # Write capsule
    capsule_path = write_capsule(crash_data, output_dir=target_dir, prefix=file_prefix)
    
    # Write HTML
    try:
        from faultsnap.html import generate_html_report
        html_path = generate_html_report(capsule_path)
    except Exception:
        html_path = None
        
    # Write metadata.json
    metadata_path = os.path.join(target_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    # Update latest
    latest_dir = os.path.join(config.repository_dir, "latest")
    os.makedirs(latest_dir, exist_ok=True)
    latest_capsule = os.path.join(latest_dir, "latest.faultsnap")
    shutil.copy2(capsule_path, latest_capsule)
    latest_html = os.path.join(latest_dir, "latest.html")
    if html_path and os.path.exists(html_path):
        shutil.copy2(html_path, latest_html)
        
    # Update index
    index = _read_index()
    index.append({
        "timestamp": manifest.get("timestamp"),
        "exception": exc_type,
        "fingerprint": fingerprint,
        "capsule_path": capsule_path,
        "html_path": html_path,
        "python_version": manifest.get("python_version"),
        "platform": manifest.get("platform")
    })
    _write_index(index)
    
    # Clean old reports
    try:
        clean_old_reports()
    except Exception:
        pass # Never fail a crash capture on cleanup
        
    return capsule_path

def clean_old_reports():
    index = _read_index()
    if not index:
        return
        
    cutoff_date = datetime.now() - timedelta(days=config.max_days_to_keep)
    
    fingerprint_counts = {}
    new_index = []
    files_to_remove = []
    
    # Process from newest to oldest
    for entry in reversed(index):
        ts_str = entry.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts_str)
        except Exception:
            dt = datetime.now()
            
        fp = entry.get("fingerprint")
        
        # Check age
        if dt < cutoff_date:
            files_to_remove.append(entry)
            continue
            
        # Check count
        count = fingerprint_counts.get(fp, 0)
        if count >= config.max_reports_per_fingerprint:
            files_to_remove.append(entry)
            continue
            
        fingerprint_counts[fp] = count + 1
        new_index.insert(0, entry) # Insert at beginning to restore order
        
    # Remove files
    for entry in files_to_remove:
        try:
            capsule_path = entry.get("capsule_path")
            if capsule_path and os.path.exists(capsule_path):
                os.remove(capsule_path)
            html_path = entry.get("html_path")
            if html_path and os.path.exists(html_path):
                os.remove(html_path)
            
            # Clean up empty parent directories
            if capsule_path:
                d = os.path.dirname(capsule_path)
                try:
                    # Remove metadata if we are removing the last items
                    files = [f for f in os.listdir(d) if f != "metadata.json"]
                    if not files:
                        os.remove(os.path.join(d, "metadata.json"))
                        os.rmdir(d)
                except Exception:
                    pass
        except Exception:
            pass
            
    if len(files_to_remove) > 0:
        _write_index(new_index)
