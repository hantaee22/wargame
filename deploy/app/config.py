import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Key paths (used when Section 3/4 are implemented later)
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "keys", "ed25519_private.pem")
PUBLIC_KEY_PATH  = os.path.join(BASE_DIR, "static", "ed25519_public.pub")

# Database path
DB_PATH = os.path.join(BASE_DIR, "app.db")
