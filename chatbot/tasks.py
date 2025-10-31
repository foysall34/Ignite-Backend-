from celery import shared_task
from .utils_process import process_file_from_s3
from .models import UploadRecord

@shared_task(bind=True)
def process_s3_file_task(self, upload_record_id, file_key):
    try:
        # update status
        UploadRecord.objects.filter(id=upload_record_id).update(status="processing")
        result = process_file_from_s3(file_key)
        if result.get("success"):
            UploadRecord.objects.filter(id=upload_record_id).update(status="done")
            return {"status": "done", "chunks": result.get("chunks", 0)}
        else:
            UploadRecord.objects.filter(id=upload_record_id).update(status="failed", error=result.get("message"))
            return {"status": "failed", "message": result.get("message")}
    except Exception as e:
        UploadRecord.objects.filter(id=upload_record_id).update(status="failed", error=str(e))
        raise
