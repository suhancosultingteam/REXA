"""AES-GCM으로 저장한 user_id_enc를 복호화하고 user_key 해시를 검증한다.

주의:
- chat_logs.user_id_enc 는 복호화 가능하다.
- chat_logs.user_key 는 SHA-256 해시이므로, user_key 값만으로 원문을 복원할 수는 없다.

usage:
    python -m rexa.scripts.decode_user_id --user-id-enc <base64> --enc-key <base64-key>
    python -m rexa.scripts.decode_user_id --user-id-enc <base64> --enc-key <base64-key> --salt <salt>
    python -m rexa.scripts.decode_user_id --user-id-enc <base64> --enc-key <base64-key> --salt <salt> --user-key <sha256>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def hash_user_id(user_id: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{user_id}".encode("utf-8")).hexdigest()


def decrypt_user_id(encrypted_value: str, enc_key_b64: str) -> str:
    key = base64.b64decode(enc_key_b64)
    if len(key) not in (16, 24, 32):
        raise ValueError("enc-key must be a base64-encoded 16/24/32-byte AES key.")

    raw = base64.b64decode(encrypted_value)
    if len(raw) <= 12:
        raise ValueError("user-id-enc is too short. expected base64(nonce||ciphertext).")

    nonce, ciphertext = raw[:12], raw[12:]
    return AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="user_id_enc를 복호화하고, 필요하면 salt로 user_key 해시를 재계산해 검증한다."
    )
    parser.add_argument(
        "--user-id-enc",
        default="",
        help="chat_logs.user_id_enc 값 (base64, nonce||ciphertext)",
    )
    parser.add_argument(
        "--enc-key",
        default=os.getenv("CHAT_LOG_USER_ID_ENC_KEY", "").strip(),
        help="AES 키(base64). 미입력 시 CHAT_LOG_USER_ID_ENC_KEY 사용",
    )
    parser.add_argument(
        "--salt",
        default=os.getenv("CHAT_LOG_USER_HASH_SALT", ""),
        help="user_key 해시 salt. 미입력 시 CHAT_LOG_USER_HASH_SALT 사용",
    )
    parser.add_argument(
        "--user-key",
        default="",
        help="검증할 chat_logs.user_key 값(SHA-256 hex). 단독 복원은 불가하고 비교만 가능",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if not args.user_id_enc:
        if args.user_key:
            raise SystemExit(
                "user_key는 해시라서 단독 복원할 수 없습니다. "
                "--user-id-enc 와 --enc-key 를 함께 넣어 주세요."
            )
        raise SystemExit("--user-id-enc 이 필요합니다.")

    if not args.enc_key:
        raise SystemExit("--enc-key 이 필요합니다 (또는 CHAT_LOG_USER_ID_ENC_KEY env 설정).")

    try:
        user_id = decrypt_user_id(args.user_id_enc, args.enc_key)
    except Exception as exc:
        raise SystemExit(f"복호화 실패: {exc}") from exc

    print(f"user_id={user_id}")

    if args.salt:
        derived_user_key = hash_user_id(user_id, args.salt)
        print(f"derived_user_key={derived_user_key}")
        if args.user_key:
            print(f"user_key_match={'yes' if derived_user_key == args.user_key else 'no'}")
    elif args.user_key:
        print("salt가 없어서 user_key 검증은 생략했습니다.")


if __name__ == "__main__":
    main()
