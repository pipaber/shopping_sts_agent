"""Descarga los ficheros de ESCI que usa el proyecto (si aún no están).

Uso::

    python -m shopping_agent.data.download --out datasets
"""

from __future__ import annotations

import argparse
import shutil
import urllib.request
from pathlib import Path

from shopping_agent.data.prepare import EXAMPLES_FILE, PRODUCTS_FILE

BASE_URL = "https://github.com/amazon-science/esci-data/raw/main/shopping_queries_dataset"


def download(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in (EXAMPLES_FILE, PRODUCTS_FILE):
        target = out_dir / name
        if target.exists():
            print(f"ya existe: {target}")
            continue
        print(f"descargando {name} ...")
        partial = target.with_suffix(".part")
        with urllib.request.urlopen(f"{BASE_URL}/{name}") as response, partial.open("wb") as file:
            shutil.copyfileobj(response, file, length=1 << 20)
        partial.replace(target)
        print(f"listo: {target} ({target.stat().st_size / 2**20:.0f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga ESCI (examples y products).")
    parser.add_argument("--out", type=Path, default=Path("datasets"))
    args = parser.parse_args()
    download(args.out)


if __name__ == "__main__":
    main()
