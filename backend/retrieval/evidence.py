"""Opt-in OFFLINE evidence sufficiency; never a public corpus/approval bypass."""
from collections import Counter
from dataclasses import dataclass, field
import math
import re

from backend.publication.bindings import ReadOnlyReview
from backend.review.service import validate_candidate, exclusion_reasons, span_text
from .scoring import INJECTION, OUTSIDE, query_policy, reciprocal_rank_fusion, tokens

TOPIC_PATTERN = re.compile(r"\b(bnss|bns|bsa|ipc|crpc)\b|bharatiya nagarik suraksha sanhita|bharatiya nyaya sanhita|bharatiya sakshya adhiniyam|indian evidence act",re.I)
NAMES={'bharatiya nagarik suraksha sanhita':'bnss','bharatiya nyaya sanhita':'bns','bharatiya sakshya adhiniyam':'bsa','indian evidence act':'legacy_evidence'}
NOTICES={'S.O. 850(E)':'bns','S.O. 848(E)':'bnss','S.O. 849(E)':'bsa'}
TEMPORAL=re.compile(r"\b(current(?:ly)?|today|now|latest|present|updated|subsequent|later|amend\w*|repeal\w*|still|unchanged|applicable|valid|binding)\b|\bas\s+of\b|\bin\s+force\s+(?:yet|already)\b|\b(?:is|are|has|have|does|do)\b.{0,90}\b(?:in force|commenced|legal position)\b",re.I)
PERSONAL=re.compile(r"\b(my|i am|am i|should i|will i|legal advice)\b",re.I)
COMPARE=re.compile(r"\b(compare|comparison|versus|difference|across|both)\b",re.I)
NOTICE_QUERY=re.compile(r"notificat|commenc|first\s+schedule|(?:come|came|into).{0,15}force|s\.?\s*o\.?\s*(?:848|849|850)",re.I)
# Small, inspectable English word families, not mappings between legal instruments.
FAMILIES={'marital':'marriage','married':'marriage','marrying':'marriage',
 'communications':'communication','communicating':'communication',
 'interpreting':'interpret','interpreted':'interpret','interpretation':'interpret',
 'judicially':'judicial','especially':'special','exceptions':'except','exception':'except',
 'commencement':'force','commence':'force','commenced':'force','appointed':'appoint',
 'acting':'act','acts':'act','following':'follow','proving':'prove','provisions':'provision',
 'excepted':'except','concurrently':'concurrent','consecutively':'consecutive',
 'inducement':'induce','induces':'induce','inducing':'induce','recording':'record','considering':'consider'}
BOILER=set('qualification qualifier surround paragraph multiple several follow relate related a an the of in on at to for and or is are was were does do what when which this that it its about how who whom with by from under within into as any original originally archived archival text passage passages rule rules say says said state states explain compare comparison versus difference following concerning regarding treatment describe describes treatment please tell known whether someone person persons law laws bns bnss bsa ipc crpc bharatiya nyaya nagarik suraksha sanhita sakshya adhiniyam act section'.split())


def words(text):
    result=set()
    for token in re.findall(r'[a-z]+|\d+',text.lower()):
        token=FAMILIES.get(token,token)
        if token.endswith('s') and len(token)>4 and not token.endswith(('ss','us','is')):token=token[:-1]
        if token not in BOILER:result.add(token)
    return result


def topic_of(p):
    if p.instrument in NOTICES:return NOTICES[p.instrument]
    return next((t[6:] for t in tokens(p.title) if t.startswith('topic_')),None)


@dataclass(frozen=True)
class Group:
    topic: str
    query: str
    anchors: frozenset
    notification: bool


@dataclass
class EvidenceResult:
    status: str
    temporal_class: str
    reason: str
    ranked: list = field(default_factory=list)
    selected: list = field(default_factory=list)
    required_groups: int = 0
    covered_groups: int = 0
    required_topics: list = field(default_factory=list)
    source_dates: list = field(default_factory=list)
    legal_currentness: str = 'unknown'
    human_approved: bool = False
    publication_authorized: bool = False

    def metadata(self):
        return dict(status=self.status,temporal_class=self.temporal_class,reason=self.reason,
            ranked_ids=[p.identifier for p in self.ranked],selected_ids=[p.identifier for p in self.selected],
            required_groups=self.required_groups,covered_groups=self.covered_groups,required_topics=self.required_topics,
            covered_documents=sorted({p.candidate.document_id for p in self.selected}),source_dates=self.source_dates,
            legal_currentness=self.legal_currentness,human_approved=False,publication_authorized=False)


def temporal_class(question, source_dates):
    if INJECTION.search(question) or OUTSIDE.search(question) or PERSONAL.search(question):return 'scope_restricted'
    if TEMPORAL.search(question) or re.search(r'\blegal position\b',question,re.I):return 'current_or_later'
    original_wording=bool(re.search(r'original|archiv|s\.?\s*o\.?\s*(?:848|849|850)',question,re.I) and re.search(r'text|paragraph|state|say|appoint|notification|quote|inspect',question,re.I))
    if not original_wording and re.search(r'\b(?:in|during|since|after|before)\s+(?:[a-z]+\s+)?(?:19|20)\d{2}\b|\bwhen\b.{0,60}\b(?:force|commence)',question,re.I):return 'current_or_later'
    known={str(d['publication_date'])[:4] for d in source_dates if d['publication_date']}
    years=set(re.findall(r'\b(?:19|20)\d{2}\b',question))
    if years-known:return 'current_or_later'  # Unknown time coverage, not proof of an amendment.
    if re.search(r'\b(this|that) (?:provision|law|section)\b|\b(?:these|the two) laws\b',question,re.I):return 'ambiguous'
    return 'historical_text'


def plan(question):
    hits=list(TOPIC_PATTERN.finditer(question));notice=bool(NOTICE_QUERY.search(question))
    if not hits:
        numbered=re.search(r'\b(?:848|849|850)\b',question)
        if numbered:hits_topic={'848':'bnss','849':'bsa','850':'bns'}[numbered[0]];return [Group(hits_topic,question,frozenset(),True)]
        return []
    topics=[NAMES.get(h[0].lower(),h[0].lower()) for h in hits]
    distinct=list(dict.fromkeys(topics))
    comparison=bool(COMPARE.search(question)) or len(distinct)>1
    fragments=[]
    if len(distinct)>1:
        for n,hit in enumerate(hits):
            part=question[hit.end():hits[n+1].start() if n+1<len(hits) else len(question)]
            fragments.append((topics[n],part))
    elif comparison and re.search(r'\band\b|\bversus\b',question,re.I):
        fragments=[(distinct[0],p) for p in re.split(r'\band\b|\bversus\b',question,flags=re.I)]
    else:fragments=[(distinct[0],question)]
    groups=[]
    for topic,fragment in fragments:
        anchor=words(fragment)-{'notification','force','schedule','first','entry'} if notice else words(fragment)
        if not anchor and notice:anchor=words(question)-{'notification','force','schedule','first','entry'}
        # Named notification identity suffices for a request to inspect that original paragraph.
        if notice:anchor-=set(str(y) for y in (2023,2024))
        groups.append(Group(topic,topic+' '+fragment+(' commencement notification' if notice else ''),frozenset(anchor),notice))
    return groups


class EvidenceRetriever:
    """Uses existing BM25/FAISS and QA gates; no labels/answers/provider in policy."""
    def __init__(self,index):
        self.index=index
        self.forms={p.identifier:words(p.text) for p in index.passages}
        self.df=Counter(t for terms in self.forms.values() for t in terms)

    def _sources(self):
        if not self.index.catalog:raise ValueError('Missing source catalogue')
        live,_=self.index.loader(self.index.root)
        if (live.digest,live.qa_hash)!=(self.index.catalog.digest,self.index.catalog.qa_hash):raise ValueError('Stale catalogue')
        ReadOnlyReview(live).replay()
        dates=[]
        for identifier in live.documents:
            _,doc=live.document(identifier)
            dates.append(dict(document_id=identifier,publication_date=str(doc.metadata.publication_date) if doc.metadata.publication_date else None,
                version=doc.metadata.amendment_version,legal_currentness='unknown'))
        return live,dates

    def _matches(self,p,g):
        if topic_of(p)!=g.topic or (p.printed_number is None)!=g.notification:return False
        terms=words(p.text);anchors=set(g.anchors)
        if g.notification:
            return not anchors or bool(anchors & terms)
        if len(anchors)<2:return False
        overlap=anchors & terms
        weight=lambda t:math.log(1+(len(self.index.passages)+1)/(1+self.df[t]))
        return len(overlap)>=2 and sum(weight(t) for t in overlap)>=.5*sum(weight(t) for t in anchors)

    def _rank(self,question,groups,live,mode,limit,max_characters):
        if query_policy(question) is None:return []
        pools=[self.index.search(question,limit=5,max_characters=24000,mode=mode)]
        expand_groups=[] if len(groups)==1 and any(self._matches(p,groups[0]) for p in pools[0]) else groups
        for g in expand_groups:
            ids=sorted({p.candidate.document_id for p in self.index.passages if topic_of(p)==g.topic and (p.printed_number is None)==g.notification})
            if not ids:continue
            # Add English forms to the query, never rewrite source text or legal identifiers.
            forms=set(g.anchors)|{word for word,base in FAMILIES.items() if base in g.anchors}
            expanded=g.query+' '+' '.join(sorted(forms))
            pools.append(self.index.search(expanded,source_ids=ids,limit=5,max_characters=24000,mode=mode))
        found={}
        for pool in pools:
            for p in pool:
                item,doc=validate_candidate(live,p.candidate)
                if exclusion_reasons(item,p.candidate) or span_text(doc,p.candidate.spans[0])!=p.text:
                    raise ValueError('Excluded or tampered candidate')
                if INJECTION.search(p.text):raise ValueError('Instruction-like candidate')
                found[p.identifier]=p
        order=reciprocal_rank_fusion([[p.identifier for p in pool] for pool in pools])
        matching={p:{n for n,g in enumerate(groups) if self._matches(found[p],g)} for p in order}
        order=[p for p in order if matching[p]]
        ranked=[];covered=set();size=0
        while order and len(ranked)<limit:
            # Complementary *relevant clause* coverage, not an unconditional document quota.
            identifier=min(order,key=lambda p:(-len(matching[p]-covered),order.index(p)))
            order.remove(identifier);p=found[identifier]
            if size+len(p.text)>max_characters:continue
            ranked.append(p);covered|=matching[identifier];size+=len(p.text)
        return ranked

    def assess(self,question,*,mode='bm25',limit=5,max_characters=24000,diagnostic_retrieval=False):
        if type(question) is not str or not 0<len(question)<=2000:raise ValueError('Question must contain one to 2000 characters')
        if type(max_characters) is not int or not 1<=max_characters<=24000:raise ValueError('Invalid evidence budget')
        if mode not in {'bm25','hybrid'} or type(limit) is not int or not 1<=limit<=5:raise ValueError('Invalid mode/limit')
        if mode=='hybrid' and self.index.semantic is None:raise ValueError('Hybrid unavailable')
        try:
            live,dates=self._sources();kind=temporal_class(question,dates);groups=plan(question)
            ranked=self._rank(question,groups,live,mode,limit,max_characters) if len(groups)<=5 and (kind=='historical_text' or diagnostic_retrieval) else []
            covered=sum(any(self._matches(p,g) for p in ranked) for g in groups)
            common=dict(ranked=ranked,source_dates=dates,required_groups=len(groups),covered_groups=covered,required_topics=sorted({g.topic for g in groups}))
            if kind=='current_or_later':return EvidenceResult('insufficient_current_evidence',kind,'Original source dates/editions do not verify the requested current or later legal claim; no absence of amendments is inferred.',**common)
            if kind=='scope_restricted':return EvidenceResult('insufficient_evidence',kind,'Existing scope/personal-advice/injection restrictions preserved.',**common)
            if re.search(r'\bsection\s+\d+',question,re.I) and not ranked and len(groups)==1 and not groups[0].notification:
                return EvidenceResult('insufficient_evidence',kind,'The exact numbered reference lacks validated archival support; no attribution invented.',**common)
            if kind=='ambiguous' or not groups or len(groups)>5 or any(len(g.anchors)<2 and not g.notification for g in groups):
                return EvidenceResult('clarification_required','ambiguous','Name the instruments, concepts and historical scope to compare.',**common)
            if any(g.topic not in {'bns','bnss','bsa'} for g in groups):
                return EvidenceResult('insufficient_evidence',kind,'One or more required instruments are absent; no legacy-code mapping is inferred.',**common)
            if re.search(r'without (?:any )?exceptions?|no exceptions?|every (?:provision|entry)',question,re.I) and any('except' in words(p.text) for p in ranked):
                return EvidenceResult('misleading_premise',kind,'The original paragraph contains an exception and cannot support an unqualified premise.',**common)
            if not ranked or covered<len(groups):
                return EvidenceResult('insufficient_evidence',kind,'Required concept/instrument evidence is missing; comparison withheld rather than padded with irrelevant sources.',**common)
            return EvidenceResult('historical_evidence_available',kind,'Only the matched original archival text is available; not human approved or current-law proof.',selected=ranked,**common)
        except (ValueError,OSError,KeyError,TypeError):
            return EvidenceResult('source_integrity_failed','unverified','Source, candidate or QA bindings failed; no evidence selected.')
