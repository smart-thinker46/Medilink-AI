from medilink_ai.gateway.output import GatewayCitation, validate_citations


def test_valid_citation():
    assert validate_citations([GatewayCitation(source_id="S1", claim="Supported")], {"S1", "S2"}) == ()


def test_unknown_citation_is_rejected():
    failures = validate_citations([GatewayCitation(source_id="S99", claim="Unsupported")], {"S1", "S2"})
    assert failures and failures[0].reason_code == "CITATION_SOURCE_NOT_IN_EVIDENCE"

