import hashlib
import traceback

def compute_fingerprint(exc_type, exc_value, exc_traceback):
    """
    Computes a deterministic crash fingerprint.
    Uses the exception type and normalized stack frames (filenames and function names)
    to group similar crashes even if line numbers change.
    """
    elements = []
    
    # Exception Type
    elements.append(exc_type.__name__ if hasattr(exc_type, '__name__') else str(exc_type))
    
    # Extract traceback frames
    tb = traceback.extract_tb(exc_traceback)
    for frame in tb:
        # frame is a FrameSummary: filename, lineno, name, line
        filename = frame.filename
        # Normalize paths slightly (just take the basename or last two parts to avoid full absolute paths differing across machines)
        if filename:
            parts = filename.split('/')
            if len(parts) >= 2:
                normalized_file = f"{parts[-2]}/{parts[-1]}"
            else:
                normalized_file = filename.split('\\')[-1] # handle windows fallback just in case
        else:
            normalized_file = "unknown"
            
        elements.append(f"{normalized_file}::{frame.name}")
        
    fingerprint_string = "||".join(elements)
    
    return hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()
