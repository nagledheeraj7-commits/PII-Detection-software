#!/usr/bin/env python3
"""
Flask PII Detection Web Application
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import re
import io
import csv
from datetime import datetime

app = Flask(__name__)

def detect_emails(text):
    """Detect email addresses using regex"""
    if pd.isna(text):
        return 0
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return len(re.findall(email_pattern, str(text)))

def detect_phones(text):
    """Detect phone numbers (10 digits, with spaces or dashes)"""
    if pd.isna(text):
        return 0
    phone_patterns = [
        r'\b\d{10}\b',  # 10 digits
        r'\b\d{3}[-\s]\d{3}[-\s]\d{4}\b',  # 123-456-7890 or 123 456 7890
        r'\b\d{3}[-\s]\d{7}\b',  # 123-4567890
        r'\b\d{7}[-\s]\d{3}\b'  # 4567890-123
    ]
    total = 0
    for pattern in phone_patterns:
        total += len(re.findall(pattern, str(text)))
    return total

def detect_names(text):
    """Detect names (alphabets and spaces only, length > 3)"""
    if pd.isna(text):
        return 0
    text_str = str(text).strip()
    if len(text_str) > 3 and re.match(r'^[a-zA-Z\s]+$', text_str):
        words = text_str.split()
        if len(words) >= 2 and all(word.istitle() for word in words if word.strip()):
            return 1
    return 0

def analyze_column_pii(column_data):
    """Analyze a column for PII types"""
    emails = 0
    phones = 0
    names = 0
    
    for value in column_data:
        emails += detect_emails(value)
        phones += detect_phones(value)
        names += detect_names(value)
    
    if emails > 0:
        column_type = "Email"
    elif phones > 0:
        column_type = "Phone"
    elif names > 0:
        column_type = "Name"
    else:
        column_type = "Non-PII"
    
    return {
        'type': column_type,
        'emails': emails,
        'phones': phones,
        'names': names,
        'total_pii': emails + phones + names
    }

def analyze_pii(df):
    """Analyze DataFrame for PII (limited to first 1000 rows)"""
    df_limited = df.head(1000)
    
    results = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'analyzed_rows': len(df_limited),
        'total_emails': 0,
        'total_phones': 0,
        'total_names': 0,
        'total_pii_found': 0,
        'column_analysis': {}
    }
    
    for column in df_limited.columns:
        column_result = analyze_column_pii(df_limited[column])
        results['column_analysis'][column] = column_result
        results['total_emails'] += column_result['emails']
        results['total_phones'] += column_result['phones']
        results['total_names'] += column_result['names']
        results['total_pii_found'] += column_result['total_pii']
    
    return results

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle CSV file upload and analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file'}), 400
        
        # Read CSV file
        df = pd.read_csv(file)
        
        # Analyze PII
        results = analyze_pii(df)
        
        # Prepare data for frontend
        response_data = {
            'success': True,
            'file_info': {
                'total_rows': results['total_rows'],
                'total_columns': results['total_columns']
            },
            'preview': df.head(5).to_dict('records'),
            'columns': df.columns.tolist(),
            'results': {
                'analyzed_rows': results['analyzed_rows'],
                'total_emails': results['total_emails'],
                'total_phones': results['total_phones'],
                'total_names': results['total_names'],
                'total_pii_found': results['total_pii_found']
            },
            'column_analysis': []
        }
        
        # Calculate detection percentage
        total_cells = results['analyzed_rows'] * results['total_columns']
        if total_cells > 0:
            response_data['results']['detection_percentage'] = round(
                (results['total_pii_found'] / total_cells) * 100, 1
            )
        else:
            response_data['results']['detection_percentage'] = 0.0
        
        # Prepare column analysis data
        for col_name, col_analysis in results['column_analysis'].items():
            response_data['column_analysis'].append({
                'column': col_name,
                'pii_type': col_analysis['type'],
                'count': col_analysis['total_pii'],
                'emails': col_analysis['emails'],
                'phones': col_analysis['phones'],
                'names': col_analysis['names']
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download')
def download():
    """Download analysis results as CSV"""
    try:
        # Get results from session or request
        results_data = request.args.get('data')
        if not results_data:
            return jsonify({'error': 'No data to download'}), 400
        
        import json
        results = json.loads(results_data)
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Column', 'PII Type', 'Count'])
        
        # Write data
        for col_data in results.get('column_analysis', []):
            writer.writerow([
                col_data['column'],
                col_data['pii_type'],
                col_data['count']
            ])
        
        # Create file
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pii_analysis_report_{timestamp}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'Error generating download: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
