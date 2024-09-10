from django.shortcuts import render,redirect
from .forms import URLCheckForm, ExcelUploadForm
from .models import SourcedURL
from .models import SourcedURL
from datetime import datetime
from django.db import connection
from django.contrib import messages
from pymongo import MongoClient
from django.http import HttpResponse
import pandas as pd
import os
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

# Set up the MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['urls_db']
collection = db['data']


@csrf_exempt
def check_url(request):
    result = None
    form = URLCheckForm(request.POST or None)

    try:
        if request.method == 'POST':
            if form.is_valid():
                input_url = request.POST.get('input_url').strip()

                # Check if the URL already exists in MongoDB
                if collection.find_one({"url": input_url}):
                    result = "The URL is already available in DB"
                else:
                    result = "New URL, You can add it"
                    if 'confirm' in request.POST:
                        employee_id = request.POST.get('employee_id', None)
                        
                        # Insert the new URL document into MongoDB
                        collection.insert_one({
                            "url": input_url,
                            "employee_id": employee_id,
                            "created_at": datetime.now()
                        })
                        messages.success(request, f"The URL has been added to the database: {input_url}")
                        return redirect('check_url')

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    # Do not close the connection here. Let Django or the app manage the connection lifecycle.
    return render(request, 'check_url.html', {'form': form, 'result': result})

@csrf_exempt
def upload_excel(request):
    try:
        if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file)

                for url in df['URL']:
                    if pd.notna(url):
                        # Check if the URL already exists in MongoDB
                        if not collection.find_one({"url": url}):
                            # Insert the URL with current timestamp and default employee_id into MongoDB
                            collection.insert_one({
                                "url": url,
                                "created_at": datetime.now(),
                                "employee_id": '-'  # Default employee_id
                            })
                messages.success(request, "Upload Data Successfully")
                return redirect('check_url')
        else:
            form = ExcelUploadForm()

    except Exception as e:
        messages.error(request, f"An error occurred during upload: {str(e)}")

    return render(request, 'upload_excel.html', {'form': form})

@csrf_exempt
def show_all_urls(request):
    try:
        if 'download' in request.GET:
            # Retrieve all URLs from MongoDB
            all_urls = list(collection.find({}, {'_id': 0, 'url': 1, 'created_at': 1, 'employee_id': 1}).sort('created_at', -1))

            # Convert the MongoDB data to a DataFrame
            df = pd.DataFrame(all_urls)
            
            if not df.empty:
                # Format the DataFrame
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df['employee_id'] = df['employee_id'].replace('unknown', '-')
                df.columns = ['URL',  'Employee ID','Created At']

            # Generate the file name with the current date and time
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'urls_{current_time}.xlsx'
            file_path = os.path.join('C:\\Apache24\\htdocs\\static', filename)

            # Save the Excel file to the specified location
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='URLs')

            # Serve the file as a download
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)

        # Retrieve all URLs to display on the page
        all_urls = list(collection.find({}).sort('created_at', -1))

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return render(request, 'show_all_urls.html', {'all_urls': all_urls})