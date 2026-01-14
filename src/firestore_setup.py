import asyncio
import os
import traceback

import firebase_admin
from firebase_admin import credentials, firestore

from memorydb import InMemoryDB
from settings import FIREBASE_CONFIG_PATH


def _ensure_firebase_key_file() -> str:
    # Replit: put your entire Firebase service account JSON into FIREBASE_KEY_JSON secret
    firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
    if not firebase_key_json:
        return FIREBASE_CONFIG_PATH

    try:
        with open("/tmp/serviceAccount.json", "w") as f:
            f.write(firebase_key_json)
        return "/tmp/serviceAccount.json"
    except Exception as e:
        print(f"[WARN] Could not write FIREBASE_KEY_JSON: {e}")
        return FIREBASE_CONFIG_PATH


FIREBASE_CONFIG_FILE = _ensure_firebase_key_file()


def _init_firestore():
    try:
        cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
        firebase_admin.initialize_app(cred)
        firestore_db = firestore.client()
        print("[OK] Firebase initialized.")
        return firestore_db
    except Exception as e:
        print(f"[ERR] Firebase init failed: {e}")
        print("[INFO] Using in-memory storage (bills will not persist)")
        return InMemoryDB()


db = _init_firestore()

# Global lock to prevent concurrent Firestore client reinitialization
firestore_reinit_lock = asyncio.Lock()


async def ensure_firestore():
    """
    Ensure Firestore client is healthy. If the gRPC channel is dead (Errno 5),
    tear down and rebuild the Firebase app with fresh credentials.

    This fixes the root cause of persistent [Errno 5] errors where all retries
    reuse the same broken gRPC connection.

    Returns the current (or freshly recreated) Firestore client.
    """
    global db

    # If using in-memory DB, just return it
    if isinstance(db, InMemoryDB):
        return db

    try:
        # REAL health check - do a lightweight round-trip query
        # CRITICAL: Run in thread pool to avoid blocking the event loop!
        await asyncio.to_thread(lambda: list(db.collection('_health_check').limit(1).stream()))
        return db
    except (OSError, Exception) as check_err:
        # Channel is dead, recreate it
        print(f"[WARN] Firestore health check failed (gRPC channel dead): {check_err}")
        print(f"[INFO] Attempting Firestore client recreation...")

        async with firestore_reinit_lock:
            # Double-check another coroutine didn't already fix it
            try:
                await asyncio.to_thread(lambda: list(db.collection('_health_check').limit(1).stream()))
                print("[OK] Firestore client already healthy (another task fixed it)")
                return db
            except Exception:
                pass

            try:
                # Tear down existing Firebase app
                try:
                    firebase_admin.delete_app(firebase_admin.get_app())
                    print("[OK] Deleted old Firebase app")
                except Exception:
                    pass  # App might already be deleted

                # Add small delay to ensure clean teardown
                await asyncio.sleep(0.5)

                # Rebuild with fresh credentials
                cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("[OK] ✅ Firestore client recreated successfully!")

                # Verify new client works with multiple retries
                for retry in range(3):
                    try:
                        await asyncio.to_thread(lambda: list(db.collection('_health_check').limit(1).stream()))
                        print("[OK] ✅ New Firestore client verified healthy!")
                        return db
                    except Exception as verify_err:
                        if retry < 2:
                            print(f"[WARN] Firestore verification attempt {retry + 1}/3 failed, retrying...")
                            await asyncio.sleep(0.5)
                        else:
                            print(f"[ERR] ⚠️ New Firestore client still unhealthy after 3 attempts: {verify_err}")
                            raise OSError("[Errno 5] Firestore connection failed - network may be down") from verify_err

                return db

            except Exception as reinit_err:
                print(f"[ERR] ❌ CRITICAL: Failed to recreate Firestore client: {reinit_err}")
                traceback.print_exc()
                # Don't silently fail - raise the error so commands fail fast with clear message
                raise OSError("[Errno 5] Database connection lost - please try again in a moment") from reinit_err
