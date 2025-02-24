from rest_framework import serializers
from .models import PDF
import json
class PdfSerializer(serializers.ModelSerializer):
    request_id = serializers.CharField(source='id') 
    class Meta:
        model = PDF
        # fields = ('request_id', 'pdf_file', 'uploaded_at', 'status', 'deficiency_report')  
        exclude = ['id']
        
        # fields = '__all__'
        # exclude=('id')