import hashlib
import hmac


def verify_github_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not secret:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    given = signature_header.split("=", 1)[1]
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, given)
