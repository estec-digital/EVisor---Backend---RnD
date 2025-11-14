import subprocess
import os
from minio import Minio
from datetime import datetime, timedelta

def Backup_Postgresql_function(conn, input, minio_client: Minio, MINIO_BUCKET: str):
    """
    Backup PostgreSQL database từ Docker và upload lên MinIO.
    Trả về link tải về file.
    """
    try:
        backup_file = backup_postgres()
        file_name = os.path.basename(backup_file)
        print(file_name)

        object_name = f"data/RD/Backup/database/{file_name}"
        print(object_name)
        
        # Upload lên MinIO
        minio_client.fput_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            file_path=backup_file
        )

        presigned_url = minio_client.presigned_get_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            expires=timedelta(seconds=3600)
        )

        return {
            "status": "success",
            "url": presigned_url
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def backup_postgres():
    backup_file = f"F:/E-Visor/EVisor---Backend---RnD/minio/minio_data/backup/backup_database.sql"
    cmd = f'docker-compose exec -T postgres pg_dump -U evisor estecdb'
    with open(backup_file, 'w') as f:
        subprocess.run(cmd, shell=True, stdout=f)

    return backup_file