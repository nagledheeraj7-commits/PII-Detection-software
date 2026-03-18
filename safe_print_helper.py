"""
Safe print helper to avoid Unicode encoding errors
"""

import sys

def safe_print(*args):
    """
    Safe print function that handles Unicode encoding errors
    
    Args:
        *args: Arguments to print (like regular print)
    """
    try:
        print(*args)
    except UnicodeEncodeError:
        # Fallback: remove problematic characters
        safe_msg = ' '.join(str(arg).encode("utf-8", errors="ignore").decode() for arg in args)
        print(safe_msg)
    except Exception as e:
        # Last resort: print error info
        print(f"Print error: {e}")
        print(f"Original message length: {len(str(args))}")

def setup_safe_encoding():
    """
    Setup safe UTF-8 encoding for stdout
    """
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 fallback
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        except:
            pass
    except Exception:
        # If all else fails, continue without reconfiguration
        pass
