"""Manually checked navigation metadata only; never model citations or retrieved evidence."""
REFERENCES = (
    {"id":"india-code","title":"India Code","url":"https://indiacode.gov.in/",
     "purpose":"Browse legislation on the government portal.","checked_at":"2026-11-24T10:38:37.558115+00:00"},
    {"id":"supreme-court","title":"Supreme Court of India","url":"https://www.sci.gov.in/",
     "purpose":"Visit the court's judgments and official services portal.","checked_at":"2026-11-24T10:38:37.817014+00:00"},
    {"id":"nalsa","title":"National Legal Services Authority (NALSA)","url":"https://nalsa.gov.in/",
     "purpose":"Find official legal-aid and legal-awareness information.","checked_at":"2026-11-24T10:38:38.443699+00:00"},
)


def reference_directory():
    return {"references":[dict(r, final_url=r["url"], http_status=200) for r in REFERENCES],
        "check_scope":"HTTPS accessibility and portal identity checked at the recorded time; not a guarantee of continuing availability, legal currentness or document authenticity.",
        "used_in_ai_answers":False,"sources_verified_for_answers":False}
