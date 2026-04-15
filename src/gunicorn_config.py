import os
port = os.environ.get("PORT", "8080")
bind = f"0.0.0.0:{port}"

# Use 1 worker when no external DB is configured (sqlite:///:memory: is
# per-process, so multiple workers would each have isolated databases).
_has_external_db = all(os.environ.get(k) for k in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"))
workers = 2 if _has_external_db else 1