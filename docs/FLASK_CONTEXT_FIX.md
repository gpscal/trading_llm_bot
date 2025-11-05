# Flask Request Context and Eventlet RLock Fix

## Problem

When running SolBot with Gunicorn and eventlet workers, two errors were occurring:

1. **RuntimeError: Working outside of request context**
   - SocketIO emits were being called from background threads (simulation/live trading threads)
   - Flask-SocketIO requires Flask's application context to emit events
   - Background threads don't have this context automatically

2. **RLock(s) were not greened warnings**
   - Standard Python `threading.Lock` objects created before eventlet monkey-patches threading
   - Eventlet workers need locks to be created after monkey-patching occurs
   - This happens when using `preload_app = True` in Gunicorn config

## Solution

### 1. Flask Application Context for Background Thread Emits

**File: `utils/shared_state.py`**

- Added Flask app instance storage
- Wrapped all SocketIO emits with proper error handling for request context issues
- Uses `app.app_context()` when emitting from background threads
- Gracefully handles `RuntimeError: Working outside of request context`

**Changes:**
- Added `set_app_instance()` and `set_socketio_and_app()` functions
- Modified `update_bot_state_safe()` and `append_log_safe()` to use Flask app context
- Added fallback emit attempts when context errors occur

**Files: `web/app.py` and `web/wsgi.py`**

- Updated to register Flask app instance with shared_state module
- Ensures app context is available for background thread emits

### 2. Eventlet Monkey-Patching Before Imports

**Files: `web/wsgi.py` and `web/app.py`**

- Added explicit `eventlet.monkey_patch()` at the very beginning of both files
- This MUST happen before any imports that use threading, locks, or sockets
- Ensures all subsequent imports use eventlet's green-threaded versions

**Critical:** The monkey patch in `wsgi.py` is the primary fix - it happens before any other imports when Gunicorn loads the application.

### 3. Eventlet-Compatible Lock Initialization

**File: `utils/shared_state.py`**

- Changed from module-level `threading.Lock()` to lazy initialization
- Uses `threading.RLock()` which eventlet handles better
- Lock is created on first use (after eventlet monkey-patching)

**Implementation:**
- `_get_lock()` function creates the lock lazily
- `reset_lock()` function allows reinitialization after monkey-patching
- Works correctly with `preload_app = False` in Gunicorn configuration

### 4. Gunicorn Configuration

**File: `web/gunicorn.conf.py`**

- Set `preload_app = False` to prevent locks from being created before monkey-patching
- Added `post_worker_init` hook to reset locks after worker initialization
- This ensures locks are created after eventlet has monkey-patched threading

## Testing

After these changes:

1. **Restart the Gunicorn service:**
   ```bash
   sudo systemctl restart solbot
   ```

2. **Check logs for errors:**
   ```bash
   sudo journalctl -u solbot -f
   ```

3. **The errors should be resolved:**
   - No more "Working outside of request context" errors
   - RLock warnings should be reduced or eliminated
   - WebSocket emits from background threads should work correctly

## Technical Details

### Why App Context is Needed

Flask-SocketIO's `emit()` method accesses Flask's request context to:
- Get the current application instance
- Access configuration
- Handle client connections properly

When called from background threads (like simulation threads), there's no active HTTP request, so Flask needs an explicit application context.

### Why Explicit Monkey-Patching is Required

Even though Gunicorn with eventlet workers should monkey-patch automatically, the timing matters:
1. Gunicorn loads the WSGI application (imports wsgi.py)
2. wsgi.py imports other modules (web.app, utils.shared_state, etc.)
3. If threading is imported before monkey-patching, locks created are not "greened"
4. By monkey-patching at the very start of wsgi.py (before any other imports), we ensure all subsequent imports use the patched versions

### Why `preload_app = False`

With `preload_app = True`:
1. Gunicorn master process loads the application
2. Master process forks worker processes
3. Eventlet monkey-patches threading in each worker process
4. But locks were already created in the master process (not greened)
5. Setting `preload_app = False` ensures the app loads in each worker after monkey-patching

### Eventlet Green Threading

Eventlet uses green threads (lightweight coroutines) instead of OS threads. Standard Python locks need to be "greened" to work with eventlet. This happens automatically when:
- Locks are created after eventlet has monkey-patched threading
- Using eventlet-compatible lock types (RLock works better than Lock)

## Related Files

- `utils/shared_state.py` - Core fix implementation
- `web/app.py` - Flask app initialization
- `web/wsgi.py` - WSGI entry point for Gunicorn
- `web/gunicorn.conf.py` - Gunicorn configuration (uses eventlet workers)

## Notes

- The fixes are backward compatible - if Flask app isn't set, emits fall back to direct emit (may fail but won't crash)
- The lock is thread-safe and works with both standard threads and eventlet green threads
- All SocketIO emits from background threads now properly use Flask's application context
