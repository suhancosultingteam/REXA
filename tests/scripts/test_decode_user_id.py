from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from rexa.scripts.decode_user_id import decrypt_user_id, hash_user_id


def test_decrypt_user_id_round_trip():
    key = b"0123456789abcdef"
    nonce = b"abcdefghijkl"
    user_id = "kakao-user-123"
    ciphertext = AESGCM(key).encrypt(nonce, user_id.encode("utf-8"), None)
    encrypted_value = base64.b64encode(nonce + ciphertext).decode("ascii")

    assert decrypt_user_id(encrypted_value, base64.b64encode(key).decode("ascii")) == user_id


def test_hash_user_id_matches_expected():
    assert hash_user_id("kakao-user-123", "salt-1") == hash_user_id("kakao-user-123", "salt-1")
    assert hash_user_id("kakao-user-123", "salt-1") != hash_user_id("kakao-user-123", "salt-2")
