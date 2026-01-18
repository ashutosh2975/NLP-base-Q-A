from models import init_db
from database import get_db

# Initialize database
init_db()

# Check tables
db = get_db()
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables in database: {tables}")
db.close()
