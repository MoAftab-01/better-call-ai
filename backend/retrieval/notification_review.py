"""Local notification inspection packets. Rendering/checks do not constitute approval."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from backend.app.ingestion.extraction import normalize_text
from backend.app.ingestion.paths import source_path
from backend.app.ingestion.pipeline import canonical_json
from backend.publication.bindings import ReadOnlyReview, proposals, verify_metadata
from backend.review.models import Candidate
from backend.review.service import read_json, validate_candidate
from .engine import ROOT
from .offline import WARNINGS, new_output


def rights_binding(matrix, candidate):
    """The dossier uses public raw-hash IDs, not ingestion catalogue IDs."""
    matches = [row for row in matrix if row["raw_sha256"] == candidate.raw_sha256]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous rights dossier source hash")
    row = matches[0]
    date = candidate.source_metadata.publication_date
    if (row["instrument"] != candidate.original_identifiers["notification_number"] or
            row["official_source_url"] != candidate.source_metadata.source_url or
            row["publication_date"] != (str(date) if date else None)):
        raise ValueError("Rights dossier/source identity mismatch")
    return row


def build(root, output):
    # Verify before creating a directory; missing/tampered sources never become a packet.
    catalog, saved = verify_metadata(root)
    for document_id in catalog.documents: catalog.document(document_id)
    if proposals(catalog) != saved:
        raise ValueError("Saved and regenerated notification packets differ")
    if len(saved) != 3 or ReadOnlyReview(catalog).replay() != ([], {}):
        raise ValueError("Three unchanged proposals and an empty review ledger required")
    rights_path = source_path(catalog.root, "docs/publication-review.json")
    rights = read_json(rights_path)
    for packet in saved:
        rights_binding(rights["rights_matrix"], Candidate.model_validate(packet["candidate"]))
    target = new_output(catalog.root, output)
    target.mkdir(parents=True, exist_ok=False)
    import pymupdf
    summary=[]
    for packet in saved:
        candidate=Candidate.model_validate(packet["candidate"])
        item,doc=validate_candidate(catalog,candidate)
        number=candidate.original_identifiers["notification_number"]
        name={"S.O. 850(E)":"bns-so-850-e", "S.O. 848(E)":"bnss-so-848-e", "S.O. 849(E)":"bsa-so-849-e"}[number]
        rights_row=rights_binding(rights["rights_matrix"],candidate)
        raw=source_path(catalog.root,candidate.raw_path).read_bytes()
        renders=[]
        with pymupdf.open(stream=raw,filetype="pdf") as pdf:
            text="\n".join(p.get_text("text",sort=False) for p in pdf)
            unchanged=all(normalize_text(pdf[n].get_text("text",sort=False))==p.text for n,p in enumerate(doc.pages))
            checks=dict(all_page_extraction_matches=unchanged,
                issuing_authority="MINISTRY OF HOME AFFAIRS" in text,
                title="NOTIFICATION" in text,
                notification_identifier=number in text,
                notification_heading_date="23rd February, 2024" in text,
                publication_header_date=bool(re.search(r"FEBRUARY\s*24\s*,\s*2024",text)),
                complete_english_paragraph=packet["gate_checks"]["full_english_operative_paragraph"])
            for ordinal in (1,2):
                image_path=target/f"{name}-page-{ordinal}.png"
                pdf[ordinal-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(image_path)
                renders.append(dict(physical_page=ordinal,file=image_path.name,
                    sha256=hashlib.sha256(image_path.read_bytes()).hexdigest()))
        report=dict(schema_version=1,kind="offline_notification_review",warnings=WARNINGS,
            status="PARTIAL",human_approved=False,publication_authorized=False,legal_currentness="unknown",
            automated_checks=checks,visual_comparison="NOT PERFORMED BY CLI; use the rendered originals and a separate observation record",
            source_metadata=doc.metadata.model_dump(mode="json"),original_identifiers=candidate.original_identifiers,
            raw_sha256=candidate.raw_sha256,processed_sha256=candidate.processed_sha256,
            unchanged_original_proposal=packet,renders=renders,
            rights_dossier_sha256=hashlib.sha256(rights_path.read_bytes()).hexdigest(),rights_review=rights_row,
            outstanding_rights_questions=rights["outstanding_questions"],
            unresolved=["Hindi glyph mapping not visually certified.","Typography, layout and signature validity are not certified by text equality.",
                "Later notifications/amendments/current applicability unresolved.","Human evidence and separate publication decisions absent."])
        with (target/f"{name}.json").open("xb") as stream:stream.write(canonical_json(report))
        summary.append(dict(notification=number,document_id=candidate.document_id,report=f"{name}.json",status="PARTIAL",checks=checks))
    for document_id in catalog.documents:catalog.document(document_id)
    result=dict(warnings=WARNINGS,reports=summary,rendered_pages=6,review_events_created=0,publication_authorized=False)
    with (target/'inventory.json').open('xb') as stream:stream.write(canonical_json(result))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        print(json.dumps(build(ROOT,args.output),indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,'Notification inspection blocked: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
