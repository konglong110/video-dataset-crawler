"""初始化本地索引数据库，跑一次即可：python scripts/init_db.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import db

if __name__ == "__main__":
    db.init_db()
    print(f"OK, 数据库已初始化。")
