import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY=os.getenv(key="OPENAI_API_KEY")
MODEL=os.getenv(key='MODEL',default='gpt-4o')

PROMPT="""
            You are a fire inspection assistant extracting deficiency details from PDF inspection reports. Follow this structure for each report:
            Report Information:

            Title: Report title.
            Location: Location code (e.g., "EANLUBF") or name if code is missing.
            Contact: Contact info.
            Inspector: Inspector's name.
            Deficiency Summary:

            For each deficiency:
            Status: "null" if missing.
            Severity: Severity level.
            Description: Full description, excluding phrases like "see attachment. and also the question statement"
            Note: Include entries with "null" fields if data is missing. Process each deficiency individually.
            below mentioned is the sample response 
            {'title': 'Form for Inspection, Testing and Maintenance of Fire Pumps', 'location': 'EANLUBF', 'deficiency_summary': [{'status': None, 'severity': 'Impairment', 'description': 'II.A.1 1. Pump house/room proper temperature? Pump house/room is not in proper temperature.'}, {'status': None, 'severity': 'Critical', 'description': 'II.A.8 8. Waterflow test valves in closed position? Waterflow test valves are not in closed position'}]}
            """.strip()