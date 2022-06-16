import secrets
from jwcrypto import jwk
import string

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

key = rsa.generate_private_key(
    backend=crypto_default_backend(),
    public_exponent=65537,
    key_size=2048
)

private_key = key.private_bytes(
    crypto_serialization.Encoding.PEM,
    crypto_serialization.PrivateFormat.PKCS8,
    crypto_serialization.NoEncryption()
).decode()

public_key = key.public_key().public_bytes(
    crypto_serialization.Encoding.OpenSSH,
    crypto_serialization.PublicFormat.OpenSSH
).decode()


generate_random_client_id = lambda: secrets.token_hex(16)
generate_random_client_secret = lambda: secrets.token_hex(32)




alphabet = string.ascii_letters + string.digits

generate_random_password = lambda: secrets.token_hex(16)