# ConsultBae AI Automation

A practical automation project built around candidate data consolidation, duplicate detection, workflow automation, and audio submissions.

This project was built as part of the ConsultBae AI Automation assignment, with a focus on handling messy data, building a useful automation flow, and shipping a working application end-to-end.

## What This Project Does

The project covers three main workflows:

1. **Candidate Data Consolidation**
   - Works with three candidate data sources.
   - Normalizes and consolidates candidate information.
   - Resolves records that belong to the same person.
   - Stores the processed data in a structured database.

2. **Duplicate Candidate Automation**
   - Receives candidate information through an n8n webhook.
   - Checks the candidate against the existing candidate data.
   - Identifies an existing candidate.
   - Prepares the candidate details for an alert.
   - Sends a Gmail notification when a duplicate is detected.

3. **Audio Submission**
   - Allows a worker to enter their name and phone number.
   - Supports audio file upload.
   - Stores the submitted audio and submission details.
   - Extracts audio metadata such as duration, sample rate, bitrate, and loudness.
   - Lists submitted recordings and provides audio playback.

---

## Project Structure

```text
ConsultBae-AI-Automation/
│
├── app/            # FastAPI application
├── data/           # Source CSV files and processed data
├── database/       # Database schema and database files
├── docs/           # Reports and project documentation
├── frontend/       # Audio submission interface
├── n8n/            # Exported n8n workflow
├── scripts/        # Utility and processing scripts
├── src/            # Data processing and entity-resolution logic
├── tests/          # Automated tests
│
└── README.md
```

## Data Sources

The candidate data comes from three fictional sources provided for the assignment:

- `source1_naukri_applicants.csv`
- `source2_gig_workers.csv`
- `source3_cbnexus_contacts.csv`

The records were profiled and normalized before being consolidated.

## Data Quality Report

The source data contains issues such as:

- Invalid email addresses
- Missing email values
- Invalid phone numbers
- Missing or inconsistent candidate information
- Cross-source matching and duplicate records

The detailed findings and handling decisions are documented here:

**[Data Quality Report](docs/DATA_QUALITY_REPORT.md)**

---

## Candidate Data Flow

```text
Three Source CSVs
       │
       ▼
Data Profiling
       │
       ▼
Normalization
       │
       ▼
Entity Resolution
       │
       ▼
Consolidated Candidate Data
       │
       ▼
Database
       │
       ▼
FastAPI Search / Query Endpoints
```

The entity-resolution layer maps source records to a common `person_id`, allowing records belonging to the same person to be represented as one consolidated person.

---

## Duplicate Candidate Automation

The n8n workflow handles the duplicate-candidate alerting process.

```text
Candidate Information
        │
        ▼
      Webhook
        │
        ▼
   HTTP Request
        │
        ▼
   Duplicate Check
        │
        ▼
      IF Node
        │
        ▼
   Edit Candidate Data
        │
        ▼
    Gmail Alert
```

When the candidate already exists in the consolidated data, the workflow follows the duplicate path and sends a Gmail notification.

The exported workflow is available here:

`n8n/ConsultBae - Duplicate Candidate Automation.json`

---

## Audio Submission Flow

```text
Name + Phone
     │
     ▼
Audio File Upload
     │
     ▼
Audio Validation
     │
     ▼
Audio Storage
     │
     ▼
Metadata Extraction
     │
     ├── Duration
     ├── Sample Rate
     ├── Bitrate
     └── Loudness
     │
     ▼
Submission Record
     │
     ▼
Submission List + Playback
```

The assignment allows either browser recording or audio-file upload. This implementation uses the **audio-file upload** approach.

---

## Running the Project

### 1. Install dependencies

Make sure Python 3.10+ is available.

```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI backend

From the project root:

```bash
uvicorn app.main:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

The Swagger interface can be used to explore and test the available API endpoints.

### 3. Open the audio application

Open the audio submission frontend from the `frontend/` directory in a browser.

The application allows you to enter worker details, upload an audio file, submit it, and view previous submissions with their extracted audio properties.

### 4. Run the n8n workflow

Start n8n:

```bash
n8n
```

Then open:

```text
http://localhost:5678
```

Import:

`n8n/ConsultBae - Duplicate Candidate Automation.json`

The workflow can then be executed using the webhook trigger.

---

## API Highlights

The FastAPI application provides endpoints for:

- Database summary
- Candidate search
- Candidate/source information
- Multi-source entity information
- Data-quality issues
- Data-quality summary
- Audio submission
- Audio submissions and playback

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Documentation

- **[Data Quality Report](https://github.com/shreyaspandey0/ConsultBae-AI-Automation/blob/master/docs/DATA_QUALITY_REPORT.md)** Data issues identified during profiling and how they were handled.

- **[Scalability Plan](https://github.com/shreyaspandey0/ConsultBae-AI-Automation/blob/master/docs/SCALABILITY_PLAN.md)** Considerations for handling the system at a larger scale.

---

## Stuck / Debugging Log

### 1. Audio metadata and database schema mismatch

I initially faced an issue where the audio submission endpoint was using database column names that did not match the existing SQLite schema. The API returned a database error during submission.

I inspected the SQLite schema and compared it with the INSERT query. I also used AI assistance to understand the error and identify the mismatch. I rejected the idea of changing the database blindly because it could affect the existing data model. Instead, I aligned the API query and schema carefully and verified the result by submitting an actual audio file.

### 2. NumPy value could not be serialized by FastAPI

While returning the calculated audio loudness, FastAPI raised an error related to a NumPy float value that could not be serialized correctly.

I searched the error and asked AI about FastAPI JSON serialization of NumPy types. I considered changing the entire response structure but rejected that because the problem was specifically the NumPy value. I converted the calculated value to a native Python float before returning/storing it and tested the endpoint again.

### 3. Audio file caused UTF-8 decoding error

While testing the audio submissions listing, I encountered a UnicodeDecodeError because binary audio data was being treated as text.

I traced the error to the response handling rather than the audio-processing logic. I used debugging output and AI assistance to identify that the audio file itself should be served as binary data instead of being decoded as UTF-8. I corrected the audio-serving logic and verified the playback endpoint with an actual MP3 file.
## Testing

The repository includes automated tests covering key application functionality.

```text
tests/
```

The goal was to verify the important paths rather than relying only on manual testing.

---

## Key Takeaways

This project brought together a few different parts of a real automation workflow:

- Cleaning and consolidating messy candidate data
- Resolving records across multiple sources
- Exposing the data through an API
- Automating duplicate-candidate alerts
- Handling audio submissions and metadata
- Tracking data-quality problems
- Documenting debugging decisions
- Planning for future scalability

The main focus was not just building individual features, but getting the complete flow working together.

---

## Repository

GitHub:

https://github.com/shreyaspandey0/ConsultBae-AI-Automation
