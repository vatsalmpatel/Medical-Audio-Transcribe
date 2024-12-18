## Medical Audio Transcription using AWS Medical Transcribe

The purpose of this project is to take in audio files (patient-doctor conversations or any form of conversational audio file) and generate a transcript and send the generated transcript to the users email, so that it can viewed later for reference. For example, this can be used by a Primary Care Physician or an Oncologist to recall the conversation he had with this patient and curate a treatement plan based on the conversation he had with this patient and curate the treatment plan accordingly.

The AWS services used in this project is [AWS Medical Transcribe](https://aws.amazon.com/transcribe/medical/), which is a fully managed service that automatically converts speech to text, specifically designed for medical professionals. It helps transcribe clinical conversations accurately, supporting medical terminology and integrating with other healthcare applications. I use S3 to store the audio files and final generated transcripts for archieval purposes, which will be automatically deleted after 90 days.

### Pre-requisites before running the code:

- You must have you AWS account configured and have YOUR_AWS_ACCESS_KEY, YOUR_AWS_SECRET_KEY and S3 bucket created.

- You will need to configure bucket policies to Configure CORS as such:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST"],
        "AllowedOrigins": ["http://localhost:5000"],
        "ExposeHeaders": ["ETag"]
    }
]
```

- You will also need to create an IAM user that has programmatic access, and attach a custom policy to the IAM user as such, and then save the AWS Access Key and Secret Key that we will use in the project:

```json
{
    "Version": "2012-10-23",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "transcribe:StartMedicalTranscriptionJob",
                "transcribe:GetMedicalTranscriptionJob"
            ],
            "Resource": "*"
        }
    ]
}
```

- Again, you will also need to configure the bucket policy that allows the transcribe services to put objects into the S3 bucket, which will look something like this:

```json
{
    "Version": "2012-10-23",
    "Statement": [
        {
            "Sid": "AllowTranscribeAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "transcribe.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowAppAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/YOUR-IAM-USER"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

- After you have your bucket name, AWS Access Key and Secret key, you will need to update `aws_access_key_id`, `aws_secret_access_key`, and `S3_BUCKET` variables in the code.


### How to run the code?

After you performed the above steps, you just need to run the following command to start a flask application and use the transcription service:

```bash
python app.py
```

### Folder Structure:

- `templates/`: contains the HTML webpage that gives you the functionality to upload audio files and track progress of the transcription. you can also view the finished transcription.

- `app.py`: contains the backend code for the project. This code connects to the AWS transcribe service, starts a batch job, and once finished, it returns the transcript and displays the transcript on the screen.

- `temp_uploads`: contains the audio file which needs to be transcribed. This folder  does not have to be necessarily in this folder, it can be located anywhere within you machine.

### Future Modifications and Improvements:

- In its current state, it does not send the finished transcripts to any e-mail, it just displays it on the screen, meaning that the user has to currently wait for the transcription jon to finish, which needs to change. The user just has to upload the file, and he will received the final transcriptions via email.

- The current version of the code starts a batch transcription job on AWS Medical Transcribe, which takes a few minutes to transcribe a small audio file (2 to 5 minute audio files), which can greatly improved.

- Explore real-time audio transcription, which can mitigate the short commings of the above point.

### Output from the Code:

- This is what the landing page looks like:

    ![landing_page](/static/landing-page.png)

- This is what the app displays when the transcription is in progress:

    ![transcription_in_progress](/static/transcription-in-progress.png)

- And this is what the transcription looks like on the screen:

    ![finished_transcription](/static/finished-transcription.png)

- The finished transcripts will also be stored in the S3 bucket you have specified:

    ![s3_disp](/static/s3_disp.png)