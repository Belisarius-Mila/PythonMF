from __future__ import annotations

import argparse
import base64
import getpass
import json
import mimetypes
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "docs" / "lekarna" / "private-data" / "lekarna.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "lekarna" / "encrypted-data" / "lekarna.enc.json"
ITERATIONS = 310_000


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload = embed_photos(payload, input_path.parent)
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    password = read_password(args.password_env)
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, None)

    encrypted = {
        "version": 1,
        "algorithm": "AES-GCM",
        "kdf": "PBKDF2-SHA256",
        "iterations": ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(encrypted, indent=2), encoding="utf-8")
    print(f"Zašifrováno: {output_path}")
    print("Heslo ani hash hesla nebyly uloženy.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encrypt local Lekarna web data bundle.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to private lekarna.json.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to encrypted output JSON.")
    parser.add_argument(
        "--password-env",
        default="",
        help="Optional env var with password, intended only for automated tests with dummy data.",
    )
    return parser.parse_args()


def read_password(password_env: str) -> str:
    if password_env:
        password = os.environ.get(password_env, "")
        if not password:
            raise SystemExit(f"Promenna {password_env} neni nastavena.")
        return password

    first = getpass.getpass("Heslo pro zašifrování dat lékárny: ")
    second = getpass.getpass("Zopakovat heslo: ")
    if not first:
        raise SystemExit("Heslo nesmí být prázdné.")
    if first != second:
        raise SystemExit("Hesla se neshodují.")
    return first


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def embed_photos(payload: dict, private_root: Path) -> dict:
    medicines = payload.get("medicines", {})
    for medicine in medicines.values():
        photo = medicine.get("photo")
        if not isinstance(photo, str) or not photo:
            continue
        if photo.startswith("data:"):
            continue
        photo_path = (private_root / photo.replace("./private-data/", "")).resolve()
        if not photo_path.exists() or not photo_path.is_file():
            medicine["photo"] = ""
            continue
        mime_type = mimetypes.guess_type(photo_path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(photo_path.read_bytes()).decode("ascii")
        medicine["photo"] = f"data:{mime_type};base64,{encoded}"
    return payload


if __name__ == "__main__":
    main()
