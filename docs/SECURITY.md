# Security & Privacy Architecture

1. **Password Hashing (`PBKDF2-HMAC-SHA256`):** Passwords are salted with a 16-byte cryptographic random hex salt and hashed using Python's standard library `hashlib.pbkdf2_hmac('sha256', ...)` with 260,000 iterations (`backend/app/security.py`), verified via constant-time `hmac.compare_digest`. Changing a password via `PATCH /api/v1/auth/me` requires verifying `current_password`.
2. **Production Secret Key Enforcement:** If `APP_ENV=production` is set while `SECRET_KEY` is still a known default or shorter than 32 characters, `backend/app/config.py` raises a fatal `RuntimeError` on startup.
3. **Role-Based Access Control for Corpus Ingestion (`is_admin`):** Shared statutory ingestion endpoints (`POST /api/v1/sources/ingest` and `/ingest-pdf`) require `get_current_admin_user` (`is_admin == True`), preventing standard users from poisoning the shared RAG corpus. The account registered with `ADMIN_EMAIL` (configured in `.env`) receives administrator privileges.
4. **Horizontal Authorization Isolation:** Every complaint (`/api/v1/complaints/*`) and demand letter (`/api/v1/letters/*`) endpoint verifies `record.user_id == current_user.id` on the server before returning, updating, analyzing, or deleting data.
5. **Rate Limiting & Upload Bounds:**
   - PDF uploads are streamed in 64 KB chunks and aborted immediately if the stream exceeds 5 MB (`413 Content Too Large`).
   - An in-memory per-IP sliding-window rate limiter protects API routes. **Operational Note:** Because the rate limiter stores timestamps in process memory, it resets on process restart and is designed for single-worker deployments. Multi-worker production deployments should move the sliding window state to Redis or an API gateway (e.g., Nginx / Cloudflare).
