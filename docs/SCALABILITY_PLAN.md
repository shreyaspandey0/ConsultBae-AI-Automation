# Audio App Scalability Plan

## Scenario

The current audio application works well for a small local workload. If
5,000 gig workers submit recordings during a single weekend, the main
risks would be storage capacity, upload traffic, concurrent processing,
database load, failed uploads, duplicate submissions, and unexpected cost.

## 1. What Breaks First

The first bottleneck would likely be the application server handling many
simultaneous file uploads and audio-processing operations.

The current application saves files locally and performs metadata extraction
during the submission request. This approach is acceptable for a prototype
but is not ideal for thousands of concurrent users.

## 2. Storage

I would move audio files from local disk to object storage such as Amazon S3,
Cloudflare R2, or another compatible object-storage service.

The database should store only the file URL/key and metadata rather than
storing the audio binary itself.

I would also configure:

- Maximum upload size
- Allowed audio formats
- Lifecycle/retention rules
- Storage monitoring
- Backup and recovery

This makes storage scalable without depending on the application server's
local disk.

## 3. Upload Handling

Uploads should be separated from the main API server.

The application could generate a short-lived upload URL and allow the browser
to upload the audio directly to object storage.

After the upload completes, the API records the submission and an asynchronous
worker processes the audio metadata.

This prevents large audio files from blocking normal API requests.

## 4. Audio Processing

Metadata extraction and loudness calculation should run asynchronously using
a background job queue.

For example:

1. User uploads audio.
2. API records the submission as `PENDING`.
3. Audio is stored in object storage.
4. A processing job is created.
5. Worker extracts duration, sample rate, bitrate and loudness.
6. Database is updated to `COMPLETED`.

This prevents slow audio processing from causing request timeouts.

## 5. Failed Uploads and Retries

Every submission should have a clear processing status:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

Failed jobs should be retried automatically with a limited number of
attempts.

If processing continues to fail, the job should be moved to a dead-letter
queue or failure list for manual review.

The user should see a clear status instead of submitting the same recording
multiple times.

## 6. Duplicate Submissions

Duplicate submissions are likely when users experience network problems or
refresh the page after clicking Submit.

I would introduce an idempotency key for each submission.

The system could also calculate a file hash such as SHA-256 and compare it
with existing submissions.

This would help detect the same audio file being uploaded multiple times.

## 7. Database

SQLite is suitable for the prototype but would not be my choice for a
5,000-user weekend workload with concurrent writes.

Before launch, I would migrate to PostgreSQL.

Indexes should be added for commonly queried fields such as:

- person_id
- phone
- submission status
- created_at
- file hash

Connection pooling would also reduce unnecessary database connections.

## 8. Reliability and Monitoring

Before launch I would add:

- Application logs
- Upload success/failure metrics
- Processing failure metrics
- Storage usage monitoring
- Database monitoring
- Error alerts
- Health checks

I would also perform a load test before the real launch to identify the
maximum safe concurrency.

## 9. Cost Control

The largest variable cost would likely be audio storage, bandwidth and
processing.

To control cost:

- Use compressed/approved audio formats
- Enforce a maximum recording duration
- Enforce a maximum file size
- Store audio in object storage instead of application servers
- Configure lifecycle policies for old recordings
- Process files asynchronously
- Monitor storage and bandwidth usage

## 10. Launch Plan

Before opening the application to 5,000 workers, I would:

1. Move audio storage to object storage.
2. Move the database to PostgreSQL.
3. Separate uploads from API processing.
4. Add background audio-processing workers.
5. Add retry and failure handling.
6. Add duplicate/idempotency protection.
7. Add monitoring and alerts.
8. Run a load test using realistic upload sizes and concurrency.

The current application proves the end-to-end workflow. The production version
would mainly replace local storage and synchronous processing with scalable,
observable and failure-tolerant components.