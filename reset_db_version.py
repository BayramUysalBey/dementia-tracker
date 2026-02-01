
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')

url = os.environ.get('DATABASE_URL')
print(f"Connecting to {url}...")
try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    print("Deleting from alembic_version...")
    cursor.execute("DELETE FROM alembic_version;")
    conn.commit()
    print("Successfully cleared alembic_version table!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
