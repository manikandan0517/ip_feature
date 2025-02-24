import json
from config import AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,AWS_S3_REGION_NAME
from db_manager import DBManager, PDFStatus
from s3_manager import S3Manager
from deficiency_report import DeficiencyReportGenerator
from botocore.exceptions import ClientError
from datadog_api_client.v2 import ApiClient, ApiException, Configuration
from datadog_api_client.v2.api import logs_api
from datadog_api_client.v2.models import HTTPLog, HTTPLogItem
import os
import logging
import sys

class DDHandler(logging.StreamHandler):
    def __init__(self, configuration, service_name, ddsource):
        super().__init__()
        self.configuration = configuration
        self.service_name = service_name
        self.ddsource = ddsource

    def emit(self, record):
        msg = self.format(record)
        with ApiClient(self.configuration) as api_client:
            api_instance = logs_api.LogsApi(api_client)
            body = HTTPLog([
                HTTPLogItem(
                    ddsource=self.ddsource,
                    ddtags=f"env:{os.getenv('ENV', 'DEV')}",
                    message=msg,
                    service=self.service_name,
                )
            ])
            try:
                api_instance.submit_log(body)
            except ApiException as e:
                # Print the error so that it also appears in CloudWatch.
                print(f"Error sending log to Datadog: {e}")


class Logger:
    def __init__(self, service_name, ddsource):
        # Configure the logger to send logs both to Datadog and CloudWatch.
        self.configuration = Configuration()
        self.logger = logging.getLogger("datadog_logger")
        self.logger.setLevel(logging.INFO)

        # Datadog Handler
        dd_handler = DDHandler(self.configuration, service_name, ddsource)
        dd_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(dd_handler)

        # CloudWatch (stdout) Handler
        cw_handler = logging.StreamHandler(sys.stdout)
        cw_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(cw_handler)

    def log(self, message, level="info"):
        if level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)


# Set DataDog related environment variables.
os.environ["DD_API_KEY"] = os.environ.get("DATADOG_API_KEY")
os.environ["DD_SITE"] = os.environ.get("DD_SITE")
os.environ["ENV"] = "DEV"  # This can be overridden if needed.

logger = Logger(service_name="INSPECTPOINT-AI", ddsource="python")
logger.log("Logger initialized.")
def lambda_handler(event, context):
        
    db_manager = DBManager()
    s3_manager = S3Manager(AWS_STORAGE_BUCKET_NAME,AWS_SECRET_ACCESS_KEY,AWS_ACCESS_KEY_ID,AWS_S3_REGION_NAME)
    report_generator = DeficiencyReportGenerator()

    pdfs_to_process = db_manager.fetch_not_processed_pdfs()

    if not pdfs_to_process:
        logger.info("No PDFs to process.")
        return {"statusCode": 200, "body": json.dumps({"message": "No PDFs to process."})}

    results = []
    for pdf in pdfs_to_process:
        pdf_id, pdf_url = str(pdf["id"]), str(pdf["url"])
        db_manager.update_pdf_status(pdf_id,PDFStatus.PROCESSING)

        try:
            
            try:
                local_pdf_path = s3_manager.download_file(pdf_url)
            except ClientError as e:
                print(f"Error downloading file {pdf_url} from S3: {e}")
                logger.log(f"Error downloading file {pdf_url} from S3: {e}")
                db_manager.update_deficiency_response(pdf_id, None, PDFStatus.PROCESS_FAILED)
                results.append({"id": pdf_id, "status": "Failed", "error": str(e)})
                continue
            try:
                report = report_generator.generate_report(local_pdf_path, pdf_id)
                report_json = json.dumps(report, indent=4)
                report_filename = f"{pdf_id}/{pdf_id}_report.json"
            except Exception as e:
                print(f"Error generating report for PDF {pdf_id}: {e}")
                logger.log(f"Error generating report for PDF {pdf_id}: {e}")
                db_manager.update_deficiency_response(pdf_id, None, PDFStatus.PROCESS_FAILED)
                results.append({"id": pdf_id, "status": "Failed", "error": str(e)})
                continue
            try:
                s3_manager.upload_file(report_json, report_filename)
            except ClientError as e:
                print(f"Error uploading report to S3: {e}")
                logger.log(f"Error uploading report to S3: {e}")
                db_manager.update_deficiency_response(pdf_id, None, PDFStatus.PROCESS_FAILED)
                results.append({"id": pdf_id, "status": "Failed", "error": str(e)})
                continue
            
            db_manager.update_deficiency_response(pdf_id, report_filename, PDFStatus.PROCESS_SUCCESS)
            
            results.append({"id": pdf_id, "status": "Success", "report_s3_path": report_filename})
            
        except Exception as e:
            logger.log(f"Error processing PDF {pdf_id}: {e}", "error")
            
            db_manager.update_deficiency_response(pdf_id, None, PDFStatus.PROCESS_FAILED)

            results.append({"id": pdf_id, "status": "Failed", "error": str(e)})

    return {"statusCode": 200, "body": json.dumps({"processed": results})}

