import sys
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

class FaultSnapMiddleware:
    """
    Django middleware to catch unhandled exceptions and create a FaultSnap capsule.
    Add 'faultsnap.integrations.django.FaultSnapMiddleware' to your MIDDLEWARE list.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        try:
            crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
            filename = save_crash(crash_data)
            print(f"\n[FaultSnap] Django error captured. Saved to {filename}", file=sys.stderr)
        except Exception as capture_err:
            print(f"\n[FaultSnap] Failed to capture Django error: {capture_err}", file=sys.stderr)
        
        # Return None lets Django's default exception handling continue
        return None
