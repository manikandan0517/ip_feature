import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class PDFStatus(models.TextChoices):
    NOT_PROCESSED = 'Not Processed', _('Not Processed')
    PROCESSING = 'Processing', _('Processing')
    PROCESS_SUCCESS = 'Process Successful', _('Process Successful')
    PROCESS_FAILED = 'Process Failed', _('Process Failed')

def pdf_upload_path(instance, filename):
    return f'{instance.id}/{filename}'

class PDF(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_file = models.FileField(upload_to=pdf_upload_path, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=PDFStatus.choices, default=PDFStatus.NOT_PROCESSED)
    deficiency_report = models.FileField(upload_to=pdf_upload_path, blank=True, null=True)

    def __str__(self):
        return f"PDF Document {self.id}"
    
    class Meta:
        db_table = 'pdf_documents'
        verbose_name_plural = "PDF Documents"
