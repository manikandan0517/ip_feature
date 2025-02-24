from openai import OpenAI
from config import OPENAI_API_KEY, MODEL, PROMPT
from typing import List, Optional
from pydantic import BaseModel, Field
import instructor
import fitz
import re
import json

class DeficiencySummary(BaseModel):
    status: Optional[str] = Field(default=None, description="Status of the deficiency.")
    severity: Optional[str] = Field(default=None, description="Severity of the deficiency.")
    description: Optional[str] = Field(default=None, description="Complete description of the deficiency.")
    page_no: Optional[str] = Field(default=None, description="page number of the deficiency report.")
class InspectionReport(BaseModel):
    title: str = Field(..., description="The main title of the report")
    location: str = Field(..., description="Location code or name")
    contact: str = Field(..., description="Contact name")
    inspector: str = Field(..., description="Name of the inspector")
    deficiency_summary: List[DeficiencySummary] = Field(..., description="List of deficiencies extracted from the report.")


class DeficiencyReportGenerator:
    def __init__(self):
        self.client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))
        

    def clean_text(self, text: str) -> str:
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        
        return cleaned_text
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        all_text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text()
                all_text += text
        return self.clean_text(all_text)
    
    def generate_report(self, pdf_path,pdf_id):
        try:
            text = self.extract_text_from_pdf(pdf_path)
       
            messages = [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": text},
            ]
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_model=InspectionReport,
                temperature=0,
            )
            report = response.dict()
            return report
        except FileNotFoundError as e:
            raise Exception(f"An unexpected error occurred while generating the report for PDF {pdf_id}: {e}")