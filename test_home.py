from pathlib import Path

print(f"Path.home(): {Path.home()}")
print(f"Home exists: {Path.home().exists()}")
print(f"Home is dir: {Path.home().is_dir()}")

qzone_dir = Path.home() / ".qzone"
print(f"\nQzone dir: {qzone_dir}")
print(f"Qzone dir exists: {qzone_dir.exists()}")
print(f"Qzone dir is dir: {qzone_dir.is_dir()}")

db_path = qzone_dir / "qzone.db"
print(f"\nDB path: {db_path}")
print(f"DB parent exists: {db_path.parent.exists()}")
