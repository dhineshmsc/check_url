from django import forms

class URLCheckForm(forms.Form):
    input_url = forms.URLField(label='Enter URL to Check')

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File')