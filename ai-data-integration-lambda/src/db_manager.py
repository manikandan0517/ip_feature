import psycopg2
from psycopg2 import sql
import os
from enum import Enum

class PDFStatus(Enum):
    NOT_PROCESSED = "Not Processed"
    PROCESSING = "Processing"
    PROCESS_SUCCESS = "Process Successful"
    PROCESS_FAILED = "Process Failed"

class DBManager:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    def fetch_not_processed_pdfs(self):
        query = """
        SELECT id, pdf_file AS url
        FROM pdf_documents
        WHERE status = %s
        """
        try:
            self.cursor.execute(query, (PDFStatus.NOT_PROCESSED.value,))
            columns = [desc[0] for desc in self.cursor.description]
            results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return results
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise

    def update_pdf_status(self, pdf_id, status: PDFStatus):
        query = """
        UPDATE pdf_documents
        SET status = %s
        WHERE id = %s
        """
        try:
            self.cursor.execute(query, (status.value, pdf_id))
            print(f"Rows affected: {self.cursor.rowcount}")
        except psycopg2.Error as e:
            print(f"Error updating status: {e}")
            self.connection.rollback()
            raise

    def update_deficiency_response(self, pdf_id, report_filename, status: PDFStatus):
        query = """
        UPDATE pdf_documents
        SET status = %s,
            deficiency_report = %s
        WHERE id = %s
        """
        try:
            self.cursor.execute(query, (status.value, report_filename, pdf_id))
            print(f"Rows affected: {self.cursor.rowcount}")
        except psycopg2.Error as e:
            print(f"Error updating deficiency response: {e}")
            self.connection.rollback()
            raise

    def close_connection(self):
        self.cursor.close()
        self.connection.close()
