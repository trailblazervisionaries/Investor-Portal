import os
import subprocess
import boto3
from urllib.parse import urlparse
from datetime import datetime

POSTGRES_URL = os.getenv("POSTGRES_URL")
# Clean the URL (remove +asyncpg if present so urlparse handles it correctly)
clean_url = POSTGRES_URL.replace("+asyncpg", "")
result = urlparse(clean_url)
S3_REGION = "east"
DB_USER = result.username
DB_PASSWORD = result.password
DB_HOST = result.hostname
DB_PORT = result.port
DB_NAME = result.path.lstrip('/')

# 2. S3 Configuration
S3_BUCKET = os.getenv("DATABASE_BUCKET_BACKUP")
date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
file_name = f"backup_{DB_NAME}_{date_str}.sql.gz"
local_path = f"./{file_name}"

def run_backup():
    # Set the password for pg_dump to use
    os.environ['PGPASSWORD'] = DB_PASSWORD
    
    # Construct the pg_dump command
    # -h: host, -U: user, -p: port
    dump_cmd = (
        f"pg_dump -h {DB_HOST} -U {DB_USER} -p {DB_PORT} {DB_NAME} "
        f"| gzip > {local_path}"
    )
    
    try:
        print(f"📦 Starting backup for {DB_NAME}...")
        subprocess.run(dump_cmd, shell=True, check=True)
        
        # # 3. Upload to S3
        # print(f"🚀 Uploading {file_name} to S3...")
        # s3 = boto3.client('s3')
        # s3.upload_file(local_path, S3_BUCKET, file_name)
        
        print("✅ Backup and Upload successful!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # 4. Cleanup local file
        if os.path.exists(local_path):
            # os.remove(local_path)

            print("🧹 Local temporary file removed.")


if __name__ == "__main__":
    run_backup()



