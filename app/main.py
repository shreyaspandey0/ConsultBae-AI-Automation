from fastapi import FastAPI, HTTPException, Query

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


app = FastAPI(
    title="ConsultBae Candidate Data API",
    description="API for candidate entity resolution, source data, and data-quality analysis.",
    version="1.0.0",
)


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

@app.get("/persons/search")
def search(
    q: str = Query(..., min_length=1, description="Name, email, phone, or city search term")
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



@app.get("/entities/multi-source")
def multi_source_entities():
    return get_multi_source_entities()


@app.get("/statistics/sources")
def source_statistics():
    return get_source_statistics()


@app.get("/candidates/city/{city}")
def candidates_by_city(city: str):
    return find_candidates_by_city(city)


@app.get("/candidates/skill/{skill}")
def candidates_by_skill(skill: str):
    return find_candidates_by_skill(skill)


@app.get("/persons/{person_id}/naukri")
def naukri_details(person_id: str):
    return get_naukri_details(person_id)


@app.get("/persons/{person_id}/gig")
def gig_details(person_id: str):
    return get_gig_details(person_id)


@app.get("/persons/{person_id}/cbnexus")
def cbnexus_details(person_id: str):
    return get_cbnexus_details(person_id)


@app.get("/data-quality/issues")
def data_quality_issues():
    return get_data_quality_issues()


@app.get("/data-quality/summary")
def data_quality_summary():
    return get_data_quality_summary()


@app.get("/database/summary")
def database_summary():
    return get_database_summary()