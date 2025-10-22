# security/restore_codes_store.py
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from security.encryption import load_symmetric_key, encrypt_message, decrypt_message

class RestoreCodeStore:
    """
    Stores restore codes OUTSIDE the main SQLite DB.
    Each field is encrypted individually using the existing symmetric key utilities.
    File format: JSON list of encrypted dicts.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.file_path = os.path.join(data_dir, "restore_codes.json")
        self.key = load_symmetric_key()

    # ---------- low-level helpers ----------
    def _load_all_raw(self) -> List[Dict]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except Exception:
            # Corrupt/missing file → treat as empty
            return []

    def _save_all_raw(self, records: List[Dict]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    # ---------- public API ----------
    def add_code(self, admin_id: int, backup_filename: str, code: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        enc_record = {
            "code": encrypt_message(code, self.key),
            "admin_id": encrypt_message(str(admin_id), self.key),
            "backup_filename": encrypt_message(backup_filename, self.key),
            "created_at": encrypt_message(now, self.key)
        }
        records = self._load_all_raw()
        records.append(enc_record)
        self._save_all_raw(records)

    def has_code_for_admin(self, admin_id: int) -> bool:
        records = self._load_all_raw()
        for rec in records:
            try:
                aid = int(decrypt_message(rec["admin_id"], self.key))
                if aid == admin_id:
                    return True
            except Exception:
                continue
        return False

    def find_matching_code(self, code_input: str, admin_id: int) -> Optional[Tuple[int, Dict]]:
        """
        Returns (index, record) for the first matching code that belongs to admin_id.
        """
        records = self._load_all_raw()
        for idx, rec in enumerate(records):
            try:
                dec_code = decrypt_message(rec["code"], self.key)
                dec_admin_id = int(decrypt_message(rec["admin_id"], self.key))
                if dec_code == code_input and dec_admin_id == admin_id:
                    return idx, rec
            except Exception:
                continue
        return None

    def consume_code_by_index(self, index: int) -> None:
        records = self._load_all_raw()
        if 0 <= index < len(records):
            del records[index]
            self._save_all_raw(records)

    def list_all_decrypted(self) -> List[Dict]:
        """
        Only for super-admin viewing/revoking:
        Returns list of dicts with decrypted values.
        """
        out = []
        records = self._load_all_raw()
        for rec in records:
            try:
                out.append({
                    "code": decrypt_message(rec["code"], self.key),
                    "admin_id": int(decrypt_message(rec["admin_id"], self.key)),
                    "backup_filename": decrypt_message(rec["backup_filename"], self.key),
                    "created_at": decrypt_message(rec["created_at"], self.key)
                })
            except Exception:
                continue
        return out
