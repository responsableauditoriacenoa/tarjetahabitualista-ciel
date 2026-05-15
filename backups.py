from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from storage import DATA_DIR


BACKUPS_DIR = Path("backups")


def inicializar_backups() -> None:
    BACKUPS_DIR.mkdir(exist_ok=True)


def crear_backup(motivo: str = "manual") -> Path:
    inicializar_backups()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre = f"backup_{timestamp}_{slug(motivo)}.zip"
    destino = BACKUPS_DIR / nombre

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if DATA_DIR.exists():
            for path in DATA_DIR.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(DATA_DIR.parent))
    return destino


def slug(texto: str) -> str:
    limpio = "".join(ch.lower() if ch.isalnum() else "_" for ch in texto)
    return "_".join(part for part in limpio.split("_") if part)[:40] or "manual"


def listar_backups() -> list[Path]:
    inicializar_backups()
    return sorted(BACKUPS_DIR.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)


def restaurar_backup(uploaded_file) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    backup_previo = crear_backup("antes_de_restaurar")

    temp_path = BACKUPS_DIR / f"restore_{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    with temp_path.open("wb") as archivo:
        shutil.copyfileobj(uploaded_file, archivo)

    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)

    with zipfile.ZipFile(temp_path, "r") as zf:
        for member in zf.namelist():
            if member.startswith("data/") and not member.endswith("/"):
                zf.extract(member, DATA_DIR.parent)

    temp_path.unlink(missing_ok=True)
    if not backup_previo.exists():
        raise RuntimeError("No se pudo crear backup previo a la restauracion.")
