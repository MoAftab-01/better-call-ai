"""Stage 6E opt-in OFFLINE sufficiency. No production/publication integration."""
from collections import Counter
import math
import re
from . import evidence as prior
from .intent import absence_claim, content_words, focused_text, plan, temporal_class
from .optimized import RequestSources, request_index, Inspection
from .offline import make_citation, validate_citation


class HardenedPolicy(prior.EvidenceRetriever):
    def __init__(self,index):
        self.index=index
        self.forms={p.identifier:content_words(p.text) for p in index.passages}
        self.df=Counter(t for terms in self.forms.values() for t in terms)

    def _matches(self,p,g):
        if prior.topic_of(p)!=g.topic or (p.printed_number is None)!=g.notification:return False
        anchors=set(g.anchors);terms=content_words(p.text)
        if not anchors:return g.notification
        overlap=anchors & terms
        minimum=1 if g.notification else 2
        if len(anchors)<minimum or len(overlap)<minimum:return False
        weight=lambda t:math.log(1+(len(self.index.passages)+1)/(1+self.df[t]))
        return sum(weight(t) for t in overlap)>=.5*sum(weight(t) for t in anchors)

    def assess(self,question,*,mode='bm25',limit=5,max_characters=24000,diagnostic_retrieval=False):
        if type(question) is not str or not 0<len(question)<=2000:raise ValueError('Question must contain one to 2000 characters')
        if type(max_characters) is not int or not 1<=max_characters<=24000:raise ValueError('Invalid evidence budget')
        if mode not in {'bm25','hybrid'} or type(limit) is not int or not 1<=limit<=5:raise ValueError('Invalid mode/limit')
        if mode=='hybrid' and self.index.semantic is None:raise ValueError('Hybrid unavailable')
        try:
            live,dates=self._sources();kind=temporal_class(question,dates);groups=plan(question)
            ranked=self._rank(focused_text(question),groups,live,mode,limit,max_characters) if kind!='scope_restricted' and len(groups)<=5 and (kind=='historical_text' or diagnostic_retrieval) else []
            covered=sum(any(self._matches(p,g) for p in ranked) for g in groups)
            common=dict(ranked=ranked,source_dates=dates,required_groups=len(groups),covered_groups=covered,required_topics=sorted({g.topic for g in groups}))
            if kind=='current_or_later':return prior.EvidenceResult('insufficient_current_evidence',kind,'The archive cannot establish a requested later change, relative-date position or current applicability; no absence of later instruments is inferred.',**common)
            if kind=='scope_restricted':return prior.EvidenceResult('insufficient_evidence',kind,'Existing scope, personal-advice and injection restrictions preserved.',**common)
            if any(g.topic not in {'bns','bnss','bsa'} for g in groups):
                return prior.EvidenceResult('insufficient_evidence',kind,'Required legacy/other instrument is absent; no numbering or legal-code equivalence inferred.',**common)
            if re.search(r'\bsection\s+\d+',question,re.I) and not ranked and len(groups)==1 and not groups[0].notification:
                return prior.EvidenceResult('insufficient_evidence',kind,'Exact numbered reference lacks validated archival support.',**common)
            if kind=='ambiguous' or not groups or len(groups)>5 or any(len(g.anchors)<2 and not g.notification for g in groups):
                return prior.EvidenceResult('clarification_required','ambiguous','Clarify instruments, concepts and historical source scope.',**common)
            if absence_claim(question) and any('except' in prior.words(p.text) for p in ranked):
                return prior.EvidenceResult('misleading_premise',kind,'The complete original paragraph contains a qualifier/exception; an unqualified premise is unsupported.',**common)
            if not ranked or covered<len(groups):return prior.EvidenceResult('insufficient_evidence',kind,'Missing required relevant concept/instrument evidence; comparison withheld.',**common)
            return prior.EvidenceResult('historical_evidence_available',kind,'Matched original text only; not independently approved, current-law proof or proof of external applicability.',selected=ranked,**common)
        except (ValueError,OSError,KeyError,TypeError):
            return prior.EvidenceResult('source_integrity_failed','unverified','Source, candidate, provenance or QA validation failed.')


class HardenedEvidenceRetriever:
    """Keep the Stage 6D source snapshot, trust reloads and fresh citation handoff."""
    def __init__(self,index):self.index=index

    def inspect(self,question,**kwargs):
        snapshot=None
        try:
            snapshot=RequestSources(self.index)
            active=request_index(self.index,snapshot)
            result=HardenedPolicy(active).assess(question,**kwargs)
            allowed={p.identifier for p in result.ranked};count=0
            for n,p in enumerate(result.ranked,1):
                validate_citation(active,make_citation(active,p,n),n,allowed);count+=1
            snapshot.refresh_sources()
            return Inspection(result,count)
        except (ValueError,OSError,KeyError,TypeError):
            return Inspection(prior.EvidenceResult('source_integrity_failed','unverified','Fresh source, trust, review or citation check failed; no selected evidence.'),0)
        finally:
            if snapshot is not None:snapshot.close()

    def assess(self,question,**kwargs):return self.inspect(question,**kwargs).result
