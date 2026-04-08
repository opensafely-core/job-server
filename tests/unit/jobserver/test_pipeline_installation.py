import pipeline.loading


def test_fastparser_available():
    assert pipeline.loading.FAST_PARSER is not None, (
        "Expected the pipeline fastparser to be available, but it was not detected"
    )
