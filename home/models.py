from django.db import models
from datetime import datetime

class SourcedURL(models.Model):
    url = models.URLField(unique=True)
    employee_id = models.CharField(max_length=20, default='unknown')  # Default value
    created_at = models.DateTimeField(default=datetime.now)  # Set default to current datetime
    
    def __str__(self):
        return self.url