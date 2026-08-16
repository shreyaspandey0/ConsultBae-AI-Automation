from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import librosa
import numpy as np
import sqlite3
from pathlib import Path
import shutil
import uuid
import mimetypes

from mutagen import File as MutagenFile

from src.queries import (
    get_person,
    get_person_sources,
    search_people,
    get_multi_source_entities,
    get_source_statistics,
    find_candidates_by_city,
    find_candidates_by_skill,
    get_naukri_details,
    get_gig_details,
    get_cbnexus_details,
    get_data_quality_issues,
    get_data_quality_summary,
    get_database_summary,
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="ConsultBae Candidate Data API",
    description="API for candidate entity resolution, source data, and data-quality analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# BASIC ENDPOINTS
# =========================================================

@app.get("/")
def root():
    return {
        "message": "ConsultBae Candidate Data API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# =========================================================
# PERSON ENDPOINTS
# =========================================================

@app.get("/persons/search")
def search(
    q: str = Query(
        ...,
        min_length=1,
        description="Name, email, phone, or city search term",
    )
):
    return search_people(q)


@app.get("/persons/{person_id}")
def person(person_id: str):
    result = get_person(person_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Person '{person_id}' not found.",
        )

    return result


@app.get("/persons/{person_id}/sources")
def person_sources(person_id: str):
    result = get_person_sources(person_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No source records found for person '{person_id}'.",
        )

    return result


# =========================================================
# ENTITY / SOURCE ENDPOINTS
# =========================================================

@app.get("/entities/multi-source")
def multi_source_entities():
    return get_multi_source_entities()


@app.get("/statistics/sources")
def source_statistics():
    return get_source_statistics()


# =========================================================
# CANDIDATE SEARCH ENDPOINTS
# =========================================================

@app.get("/candidates/city/{city}")
def candidates_by_city(city: str):
    return find_candidates_by_city(city)


@app.get("/candidates/skill/{skill}")
def candidates_by_skill(skill: str):
    return find_candidates_by_skill(skill)


# =========================================================
# PERSON SOURCE DETAILS
# =========================================================

@app.get("/persons/{person_id}/naukri")
def naukri_details(person_id: str):
    return get_naukri_details(person_id)


@app.get("/persons/{person_id}/gig")
def gig_details(person_id: str):
    return get_gig_details(person_id)


@app.get("/persons/{person_id}/cbnexus")
def cbnexus_details(person_id: str):
    return get_cbnexus_details(person_id)


# =========================================================
# DATA QUALITY
# =========================================================

@app.get("/data-quality/issues")
def data_quality_issues():
    return get_data_quality_issues()


@app.get("/data-quality/summary")
def data_quality_summary():
    return get_data_quality_summary()


# =========================================================
# DATABASE SUMMARY
# =========================================================

@app.get("/database/summary")
def database_summary():
    return get_database_summary()


# =========================================================
# TASK 3: AUDIO CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"

DB_PATH = BASE_DIR / "database" / "consultbae.db"


# Create uploads directory if it does not exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_text(value):
    """
    Convert SQLite values into safe JSON/string values.
    Handles normal strings and bytes safely.
    """

    if value is None:
        return None

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    return str(value)


def safe_float(value):
    """
    Safely convert a value to float.

    Important:
    Existing database records may contain invalid binary
    values in loudness_db. Instead of crashing the API,
    return None for invalid values.
    """

    if value is None:
        return None

    if isinstance(value, bytes):
        try:
            value = value.decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            return None

    try:
        return float(value)

    except (ValueError, TypeError, OverflowError):
        return None


def safe_int(value):
    """
    Safely convert a value to integer.
    """

    if value is None:
        return None

    if isinstance(value, bytes):
        try:
            value = value.decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            return None

    try:
        return int(value)

    except (ValueError, TypeError, OverflowError):
        return None


# =========================================================
# TASK 3: AUDIO SUBMISSION
# =========================================================

@app.post("/audio/submit")
async def submit_audio(
    name: str = Form(...),
    phone: str = Form(...),
    audio: UploadFile = File(...),
):

    # =====================================================
    # 1. VALIDATE AUDIO FILE
    # =====================================================

    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio filename is required.",
        )

    if not audio.content_type:
        raise HTTPException(
            status_code=400,
            detail="Audio content type is missing.",
        )

    if not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid audio file.",
        )


    # =====================================================
    # 2. CREATE UNIQUE FILE NAME
    # =====================================================

    extension = Path(audio.filename).suffix.lower()

    if not extension:
        extension = ".wav"

    filename = f"{uuid.uuid4()}{extension}"

    file_path = UPLOAD_DIR / filename


    # =====================================================
    # 3. SAVE UPLOADED AUDIO FILE
    # =====================================================

    try:

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save audio file: {str(e)}",
        )


    # =====================================================
    # 4. EXTRACT AUDIO METADATA
    # =====================================================

    duration = None
    sample_rate = None
    bitrate = None
    loudness_db = None


    try:

        audio_file = MutagenFile(file_path)

        if audio_file is not None and audio_file.info is not None:

            info = audio_file.info

            # Duration in seconds
            duration = safe_float(
                getattr(
                    info,
                    "length",
                    None,
                )
            )

            # Sample rate in Hz
            sample_rate = safe_int(
                getattr(
                    info,
                    "sample_rate",
                    None,
                )
            )

            # Bitrate in bits per second
            bitrate = safe_int(
                getattr(
                    info,
                    "bitrate",
                    None,
                )
            )

    except Exception as e:

        print(
            f"Metadata extraction error: {e}"
        )


    # =====================================================
    # 5. CALCULATE AUDIO LOUDNESS
    # =====================================================

    try:

        samples, sr = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        if len(samples) > 0:

            rms = np.sqrt(
                np.mean(
                    samples ** 2
                )
            )

            if rms > 0:

                loudness_db = float(
                    20 * np.log10(rms)
                )

    except Exception as e:

        print(
            f"Loudness calculation error: {e}"
        )


    # =====================================================
    # 6. SAVE SUBMISSION TO DATABASE
    # =====================================================

    db = None

    try:

        db = sqlite3.connect(DB_PATH)

        cursor = db.execute(
            """
            INSERT INTO audio_submissions
            (
                person_name,
                phone,
                audio_filename,
                audio_path,
                duration_seconds,
                sample_rate,
                bitrate,
                loudness_db
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                phone,
                audio.filename,

                str(
                    file_path.relative_to(
                        BASE_DIR
                    )
                ),

                safe_float(duration),

                safe_int(sample_rate),

                safe_int(bitrate),

                safe_float(loudness_db),
            ),
        )

        submission_id = cursor.lastrowid

        db.commit()

    except sqlite3.Error as e:

        if db:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    finally:

        if db:
            db.close()


    # =====================================================
    # 7. RETURN SUCCESS RESPONSE
    # =====================================================

    return {
        "message": "Audio submitted successfully.",
        "submission_id": safe_int(submission_id),
        "name": name,
        "phone": phone,
        "filename": audio.filename,

        "duration_seconds": safe_float(
            duration
        ),

        "sample_rate": safe_int(
            sample_rate
        ),

        "bitrate": safe_int(
            bitrate
        ),

        "loudness_db": safe_float(
            loudness_db
        ),
    }


# =========================================================
# TASK 3: LIST AUDIO SUBMISSIONS
# =========================================================

@app.get("/audio/submissions")
def get_audio_submissions():

    db = None

    try:

        db = sqlite3.connect(DB_PATH)

        db.row_factory = sqlite3.Row

        rows = db.execute(
            """
            SELECT
                submission_id,
                person_name,
                phone,
                audio_filename,
                audio_path,
                duration_seconds,
                sample_rate,
                bitrate,
                loudness_db,
                created_at
            FROM audio_submissions
            ORDER BY submission_id DESC
            """
        ).fetchall()


        # -------------------------------------------------
        # Convert SQLite rows into JSON-safe values
        # -------------------------------------------------

        submissions = []


        for row in rows:

            submissions.append(
                {
                    "submission_id": safe_int(
                        row["submission_id"]
                    ),

                    "person_name": safe_text(
                        row["person_name"]
                    ),

                    "phone": safe_text(
                        row["phone"]
                    ),

                    "audio_filename": safe_text(
                        row["audio_filename"]
                    ),

                    "audio_path": safe_text(
                        row["audio_path"]
                    ),

                    "duration_seconds": safe_float(
                        row["duration_seconds"]
                    ),

                    "sample_rate": safe_int(
                        row["sample_rate"]
                    ),

                    "bitrate": safe_int(
                        row["bitrate"]
                    ),

                    # IMPORTANT:
                    # This prevents the previous
                    # b'\x91(\xc1' error.
                    "loudness_db": safe_float(
                        row["loudness_db"]
                    ),

                    "created_at": safe_text(
                        row["created_at"]
                    ),
                }
            )


        return {
            "count": len(submissions),
            "submissions": submissions,
        }


    except sqlite3.Error as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )


    finally:

        if db:
            db.close()


# =========================================================
# TASK 3: AUDIO PLAYBACK
# =========================================================

@app.get("/audio/play/{submission_id}")
def play_audio(submission_id: int):

    db = None

    try:

        db = sqlite3.connect(DB_PATH)

        db.row_factory = sqlite3.Row

        row = db.execute(
            """
            SELECT
                audio_path,
                audio_filename
            FROM audio_submissions
            WHERE submission_id = ?
            """,
            (submission_id,),
        ).fetchone()

    except sqlite3.Error as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    finally:

        if db:
            db.close()


    # -----------------------------------------------------
    # Submission does not exist
    # -----------------------------------------------------

    if row is None:

        raise HTTPException(
            status_code=404,
            detail=f"Audio submission '{submission_id}' not found.",
        )


    # -----------------------------------------------------
    # Build actual file path
    # -----------------------------------------------------

    audio_path = row["audio_path"]

    audio_path = safe_text(
        audio_path
    )

    if not audio_path:

        raise HTTPException(
            status_code=404,
            detail="Audio path is missing from the database.",
        )


    file_path = BASE_DIR / audio_path


    # -----------------------------------------------------
    # Audio file does not exist
    # -----------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Audio file not found on the server.",
        )


    # -----------------------------------------------------
    # Make sure it is actually a file
    # -----------------------------------------------------

    if not file_path.is_file():

        raise HTTPException(
            status_code=404,
            detail="Audio path does not point to a valid file.",
        )


    # -----------------------------------------------------
    # Determine MIME type from file extension
    # -----------------------------------------------------

    media_type, _ = mimetypes.guess_type(
        str(file_path)
    )

    if media_type is None:

        media_type = "application/octet-stream"


    # -----------------------------------------------------
    # Safe filename
    # -----------------------------------------------------

    original_filename = safe_text(
        row["audio_filename"]
    )

    if not original_filename:

        original_filename = file_path.name


    # -----------------------------------------------------
    # Return audio file
    # -----------------------------------------------------

    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type=media_type,
    )