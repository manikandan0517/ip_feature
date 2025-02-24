import boto3
import tempfile
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .serializers import PdfSerializer
from .models import PDF, PDFStatus
from .utils.deficiency_report import DeficiencyReportGenerator
from django.conf import settings
from django.http import JsonResponse
import os
import json
from datetime import datetime 
import requests
logger = logging.getLogger(__name__)

@extend_schema(
    tags=['Pdf'],
    request={'multipart/form-data': {'type': 'object', 'properties': {'pdf_file': {'type': 'string', 'format': 'binary'}}, 'required': ['pdf_file']}},
    responses=PdfSerializer
)
@api_view(['POST'])
def upload_pdf(request):
    print(json.dumps(dict(request.headers), indent=4)) 
    logger.info("Received request to upload PDF.")
    pdf_file = request.FILES.get('pdf_file')
    if not pdf_file:
        logger.warning("No file provided in the request.")
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    pdf_instance = PDF.objects.create(pdf_file=pdf_file)
    logger.info(f"PDF uploaded successfully with ID: {pdf_instance.id}")
    return Response(PdfSerializer(pdf_instance).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Pdf'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'pdf_files': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'Select multiple PDF files to upload.'
                }
            },
            'required': ['pdf_files']
        }
    },
    responses=PdfSerializer(many=True)
)
# @api_view(['POST'])
# def upload_multiple_pdfs(request):
#     logger.info("Received request to upload a folder of PDFs.")
    
#     pdf_files = request.FILES.getlist('pdf_files')
#     if not pdf_files:
#         logger.warning("No files provided in the request.")
#         return Response({'error': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
#     uploaded_pdfs = []
#     for pdf_file in pdf_files:
#         pdf_instance = PDF.objects.create(pdf_file=pdf_file)
#         logger.info(f"PDF uploaded successfully with ID: {pdf_instance.id}")
#         uploaded_pdfs.append(pdf_instance)
    
#     return Response(PdfSerializer(uploaded_pdfs, many=True).data, status=status.HTTP_201_CREATED)

@extend_schema(tags=['Pdf'], responses=PdfSerializer)
@api_view(['GET'])
def get_pdf(request, start_date, end_date):
    logger.info(f"Fetching PDFs between {start_date} and {end_date}.")
    try:
        start_date, end_date = datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')
        pdf_documents = PDF.objects.filter(uploaded_at__date__range=[start_date, end_date])
        logger.info(f"Fetched {pdf_documents.count()} PDFs.")
        return Response(PdfSerializer(pdf_documents, many=True).data, status=status.HTTP_200_OK)
    except ValueError as e:
        logger.error(f"Invalid date format provided: {e}")
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=['Report'])
@api_view(["GET"])
def generate_deficiency_report(request, id):
    logger.info(f"Generating deficiency report for PDF ID: {id}")
    try:
        pdf = PDF.objects.get(id=id)
        if pdf.deficiency_report:
            logger.info(f"Report already exists for PDF file with ID: {id}")
            return Response(PdfSerializer(pdf).data, status=status.HTTP_208_ALREADY_REPORTED)

        update_pdf_status(pdf, PDFStatus.PROCESSING)
        s3_client = boto3.client('s3',
                                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
                                 )
        s3_bucket = settings.AWS_STORAGE_BUCKET_NAME  
        s3_key = pdf.pdf_file.name  

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            s3_client.download_fileobj(s3_bucket, s3_key, temp_file)
            temp_file_path = temp_file.name  

        report_generator = DeficiencyReportGenerator()
        report = report_generator.generate_report(temp_file_path, pdf)

        update_pdf_status(pdf, PDFStatus.PROCESS_SUCCESS)
        logger.info(f"Deficiency report generated successfully for PDF ID: {id}")

        os.remove(temp_file_path)

        return Response(PdfSerializer(report).data, status=status.HTTP_200_OK)
    except PDF.DoesNotExist:
        error_message = f"PDF with ID {id} not found."
        logger.error(error_message)
        return Response({"error": error_message}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error processing PDF ID {id}: {e}")
        update_pdf_status(pdf, PDFStatus.PROCESS_FAILED)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@extend_schema(tags=['Report'])
@api_view(["GET"])
def get_deficiency_report(request, id):
    logger.info(f"Retrieving deficiency report for PDF ID: {id}")
    try:
        pdf = PDF.objects.get(id=id)
        if not pdf.deficiency_report:
            return Response(PdfSerializer(pdf).data, status=status.HTTP_404_NOT_FOUND)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        report_key = str(pdf.deficiency_report)

        s3_object = s3_client.get_object(Bucket=bucket_name, Key=report_key)
        report_data = json.loads(s3_object['Body'].read().decode('utf-8'))

        logger.info(f"Deficiency report retrieved successfully for PDF ID: {id}")
        # url=pdf.deficiency_report.url
        # response=requests.get(url)
        return JsonResponse(report_data, status=status.HTTP_200_OK)
    except PDF.DoesNotExist:
        error_message = f"PDF with ID {id} not found."
        logger.error(error_message)
        return Response({"error": error_message}, status=status.HTTP_404_NOT_FOUND)
    except s3_client.exceptions.NoSuchKey:
        error_message = f"Report file not found in S3 for PDF ID: {id}."
        logger.error(error_message)
        return Response({"error": error_message}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving report for PDF ID {id}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def update_pdf_status(pdf: PDF, status: str):
    pdf.status = status
    pdf.save()
    logger.info(f"PDF ID {pdf.id} status updated to {status}")