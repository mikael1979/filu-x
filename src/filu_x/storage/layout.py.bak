from pathlib import Path
from typing import Optional
import json

class FiluXStorageLayout:
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".local" / "share" / "filu-x"
        self.private_dir = self.base_path / "data" / "user_private"
        self.public_dir = self.base_path / "data" / "public"
        self.posts_dir = self.public_dir / "posts"
        self._ensure_directories()
    
    def _ensure_directories(self):
        for path in [
            self.private_dir / "keys",
            self.private_dir / "sessions",
            self.posts_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    # Julkiset polut
    def profile_path(self) -> Path:
        return self.public_dir / "profile.json"
    
    def manifest_path(self) -> Path:
        return self.public_dir / "Filu-X.json"
    
    def follow_list_path(self) -> Path:
        return self.public_dir / "follow_list.json"
    
    def post_path(self, post_id: str) -> Path:
        return self.posts_dir / f"{post_id}.json"
    
    # Yksityiset polut
    def private_config_path(self) -> Path:
        return self.private_dir / "private_config.json"
    
    def private_key_path(self) -> Path:
        return self.private_dir / "keys" / "ed25519_private.pem"
    
    def public_key_path(self) -> Path:
        return self.private_dir / "keys" / "ed25519_public.pem"
    
    def load_json(self, path: Path) -> dict:
        """Lataa JSON-tiedosto (turvallisesti)"""
        if not path.exists():
            raise FileNotFoundError(f"Tiedostoa ei löydy: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_json(self, path: Path, data: dict, private: bool = False):
        """Tallenna JSON-tiedosto
        
        Args:
            path: Tallennettavan tiedoston polku
            data: Tallennettava JSON-data (dict-muodossa)
            private: Jos True, estä tallentaminen julkiseen hakemistoon
        """
        # Turvallisuustarkistus: älä tallenna salaisuuksia julkiseen hakemistoon
        if not private and "user_private" in str(path):
            raise PermissionError("Yritit tallentaa julkista dataa yksityiseen hakemistoon!")
        
        # Luo hakemistot jos puuttuu
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Tallenna JSON
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
