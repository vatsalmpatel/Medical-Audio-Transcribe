import boto3
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import uuid
import logging

app = Flask(__name__)

# Configure AWS credentials
aws_access_key_id = "ADD YOUR AWS ACCESS KEY HERE"
aws_secret_access_key = "ADD YOUR AWS SECRET KEY HERE"
aws_region = 'us-east-1'

s3_client = boto3.client('s3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

transcribe_client = boto3.client('transcribe',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Configure upload settings
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
S3_BUCKET = "ADD OYUR BUCKET NAME HERE"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_transcript_from_s3(transcript_uri):
    try:
        # Extract bucket and key from the URI
        # URI format: https://s3.[region].amazonaws.com/[bucket]/[key]
        uri_parts = transcript_uri.replace('https://', '').split('/')
        bucket = uri_parts[1]
        key = '/'.join(uri_parts[2:])
        
        logging.debug(f"Attempting to get transcript from bucket: {bucket}, key: {key}")
        
        # Get the transcript file from S3
        transcript_obj = s3_client.get_object(Bucket=bucket, Key=key)
        transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))
        
        # Medical transcripts have a different structure than standard transcripts
        if 'results' in transcript_data:
            # Handle medical transcript format
            segments = transcript_data['results'].get('transcripts', [])
            if segments:
                return segments[0].get('transcript', '')
            else:
                logging.error("No segments found in transcript")
                return "No transcript text available."
        else:
            logging.error("Unexpected transcript format")
            return "Error: Unexpected transcript format"
            
    except Exception as e:
        logging.error(f"Error getting transcript from S3: {str(e)}")
        return f"Error retrieving transcript: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{str(uuid.uuid4())}_{filename}"
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file locally temporarily
            file.save(local_path)
            
            # Upload to S3
            s3_path = f'uploads/{unique_filename}'
            s3_client.upload_file(local_path, S3_BUCKET, s3_path)
            
            # Start transcription job
            job_name = f"medical_transcription_{str(uuid.uuid4())}"
            s3_uri = f's3://{S3_BUCKET}/{s3_path}'
            
            response = transcribe_client.start_medical_transcription_job(
                MedicalTranscriptionJobName=job_name,
                LanguageCode='en-US',
                MediaFormat=filename.rsplit('.', 1)[1].lower(),
                Media={'MediaFileUri': s3_uri},
                OutputBucketName=S3_BUCKET,
                Specialty='PRIMARYCARE',
                Type='CONVERSATION'
            )
            
            logging.debug(f"Transcription job started: {job_name}")
            
            # Clean up local file
            os.remove(local_path)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'job_name': job_name
            }), 200
            
        except Exception as e:
            logging.error(f"Upload error: {str(e)}")
            # Clean up local file in case of error
            if os.path.exists(local_path):
                os.remove(local_path)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/status/<job_name>', methods=['GET'])
def get_job_status(job_name):
    try:
        response = transcribe_client.get_medical_transcription_job(
            MedicalTranscriptionJobName=job_name
        )
        
        job = response['MedicalTranscriptionJob']
        status = job['TranscriptionJobStatus']
        
        logging.debug(f"Job status for {job_name}: {status}")
        
        if status == 'COMPLETED':
            try:
                transcript_uri = job['Transcript']['TranscriptFileUri']
                transcript_text = get_transcript_from_s3(transcript_uri)
                
                return jsonify({
                    'status': status,
                    'transcript_text': transcript_text
                })
            except KeyError as e:
                logging.error(f"KeyError in transcript access: {str(e)}")
                return jsonify({
                    'status': status,
                    'error': 'Transcript structure error',
                    'details': str(e)
                })
        elif status == 'FAILED':
            failure_reason = job.get('FailureReason', 'Unknown reason')
            return jsonify({
                'status': status,
                'error': failure_reason
            })
        
        return jsonify({'status': status})
        
    except Exception as e:
        logging.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)