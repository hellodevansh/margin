from app.services.data_room import FIXTURE_DIR, REQUIRED_FILENAMES, ingest_data_room


def test_comprehensive_demo_data_room_has_clear_lineage():
    ingestion = ingest_data_room()
    assert ingestion.summary.documents == 7
    assert ingestion.summary.records == 60
    assert ingestion.summary.vendors == 12
    assert ingestion.summary.coverage == 0.96
    assert len(ingestion.evidence) == 9
    assert all(document.row_count > 0 for document in ingestion.documents)
    assert sum(document.evidence_count for document in ingestion.documents) == len(ingestion.evidence)


def test_uploaded_csv_is_parsed_into_data_room():
    ingestion = ingest_data_room([("supplement.csv", b"vendor,value\nExample,42\nSecond,84\n")])
    uploaded = next(document for document in ingestion.documents if document.name == "supplement.csv")
    assert uploaded.status == "parsed"
    assert uploaded.row_count == 2
    assert ingestion.summary.documents == 8


def test_uploaded_demo_package_is_complete_without_prefilled_documents():
    uploads = [(filename, (FIXTURE_DIR / filename).read_bytes()) for filename in REQUIRED_FILENAMES]
    ingestion = ingest_data_room(uploads, include_fixtures=False)
    assert ingestion.summary.documents == 7
    assert ingestion.summary.records == 60
    assert ingestion.summary.coverage == 0.96
    assert all(document.status == "parsed" for document in ingestion.documents)
    assert sum(document.evidence_count for document in ingestion.documents) == len(ingestion.evidence)
