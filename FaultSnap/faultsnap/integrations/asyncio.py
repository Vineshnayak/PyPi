import sys
import asyncio
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

def faultsnap_asyncio_exception_handler(loop, context):
    """
    Custom exception handler for asyncio event loops.
    """
    try:
        exception = context.get('exception')
        if exception:
            exc_type = type(exception)
            exc_value = exception
            exc_traceback = exception.__traceback__
        else:
            # Fallback for 'Task was destroyed but it is pending!' type errors
            exc_type = RuntimeError
            exc_value = RuntimeError(context.get('message', 'Unknown asyncio error'))
            exc_traceback = None
            
        crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
        filename = save_crash(crash_data)
        print(f"\n[FaultSnap] AsyncIO crash captured. Saved to {filename}", file=sys.stderr)
    except Exception as capture_err:
        print(f"\n[FaultSnap] Failed to capture AsyncIO crash: {capture_err}", file=sys.stderr)
    except BaseException:
        print("\n[FaultSnap] Critical internal error while capturing AsyncIO crash. Aborting capture.", file=sys.stderr)
        
    # Always call default handler
    loop.default_exception_handler(context)

def install(loop=None, **kwargs):
    """
    Install FaultSnap into the asyncio event loop to capture unhandled task exceptions.
    If `loop` is None, it uses asyncio.get_event_loop().
    """
    from faultsnap.config import configure
    if kwargs:
        configure(**kwargs)
        
    if loop is None:
        loop = asyncio.get_event_loop()
        
    loop.set_exception_handler(faultsnap_asyncio_exception_handler)
