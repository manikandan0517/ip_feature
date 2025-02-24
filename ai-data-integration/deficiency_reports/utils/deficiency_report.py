import fitz
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
import instructor
from django.conf import settings
import os
import json
import boto3
import os
import re
from .config import *
import logging
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DeficiencySummary(BaseModel):
    status: Optional[str] = Field(default=None, description="Status of the deficiency.")
    severity: Optional[str] = Field(default=None, description="Severity of the deficiency.")
    description: Optional[str] = Field(default=None, description="Complete description of the deficiency.")
    # comments: Optional[str] = Field(default=None, description="Comments related to the deficiency.")

class InspectionReport(BaseModel):
    title: str = Field(..., description="The main title of the report")
    location: str = Field(..., description="Location code or name")
    contact: str = Field(..., description="Contact name")
    inspector: str = Field(..., description="Name of the inspector")
    deficiency_summary: List[DeficiencySummary] = Field(..., description="List of deficiencies extracted from the report.")

class DeficiencyReportGenerator:
    def __init__(self):
        self.client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))
        self.s3_client = boto3.client('s3')
        logger.info("DeficiencyReportGenerator initialized with OpenAI and S3 clients")

    def clean_text(self, text: str) -> str:
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        logger.debug(f"Text cleaned: {cleaned_text[:100]}...")  # Log first 100 chars
        return cleaned_text

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a local PDF file."""
        logger.info(f"Extracting text from PDF at path: {pdf_path}")
        all_text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text()
                all_text += text
        logger.info("Text extraction completed from PDF")
        return self.clean_text(all_text)

    def generate_report(self, pdf_path: str, pdf):
        logger.info(f"Starting report generation for PDF ID: {pdf.id}")
        
        try:
            text = self.extract_text_from_pdf(pdf_path)
        except FileNotFoundError as e:
            logger.error(f"Error accessing PDF file: {e}")
            raise Exception(f"Error accessing file: {e}")

        prompt = PROMPT
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_model=InspectionReport,
            temperature=0,
        )
        
        # pdf_name = f'reports/{pdf.id}.json'
        # report_path = os.path.join(settings.MEDIA_ROOT, pdf_name)
        # logger.info(f"Generated report path: {report_path}")

        report = response.dict()
        logger.info(f"Report generated for PDF ID: {pdf.id}, report content: {report}")

        for deficiency in report.get('deficiency_summary', []):
            description = deficiency.get("description", "")
            deficiency["description"] = description.replace('\n', '.') if description else "null"
            logger.debug(f"Processed deficiency: {deficiency}")

        report_content = json.dumps(report, indent=4)

        report_filename = f"{pdf.id}_report.json"

        pdf.deficiency_report.save(report_filename, ContentFile(report_content))
        pdf.save()

        logger.info(f"Deficiency report saved for PDF ID {pdf.id} at {pdf.deficiency_report.url}")
        return pdf