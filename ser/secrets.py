import secrets
from jwcrypto import jwk
import string

key = jwk.JWK.generate(kty='RSA', size=2048, alg='RSA-OAEP-256', use='enc', kid='12345')
public_key = key.export_public(as_dict=True)["n"]
private_key = key.export_private(as_dict=True)["d"]


generate_random_client_id = lambda: secrets.token_hex(16)
generate_random_client_secret = lambda: secrets.token_hex(32)




alphabet = string.ascii_letters + string.digits

generate_random_password = lambda: secrets.token_hex(16)