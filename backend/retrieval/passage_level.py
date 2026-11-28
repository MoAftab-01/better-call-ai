"""Stage 6F OFFLINE passage retrieval. No runtime integration or approval capability."""
from collections import Counter,defaultdict
import math
import re
from . import evidence as prior
from . import intent as earlier
from .hardened import HardenedPolicy
from .optimized import RequestSources, request_index, Inspection
from .offline import make_citation, validate_citation
from .scoring import query_policy, reciprocal_rank_fusion
from backend.review.service import validate_candidate, exclusion_reasons, span_text

absence_claim=earlier.absence_claim
focused_text=earlier.focused_text
RELATIVE=re.compile(r'\b(?:next|last|this|coming|previous)\s+(?:[a-z-]+\s+){0,2}(?:week|month|year)\b',re.I)
CHANGE=re.compile(r'\b(?:displac\w*|annul\w*|invalidat\w*|suspend\w*|revis\w*|cancel\w*)\b',re.I)


def temporal_class(question,dates):
    if prior.INJECTION.search(question) or prior.OUTSIDE.search(question) or prior.PERSONAL.search(question):return 'scope_restricted'
    q=earlier.scope_text(question)
    if RELATIVE.search(q):return 'current_or_later'
    if CHANGE.search(q) and earlier.STATUS.search(q):
        if earlier.LATER.search(q) or (not earlier.historical_task(q) and re.search(r'\b(?:has|have|is|are|did|does|can|was|were|any)\b',q,re.I)):
            return 'current_or_later'
    return earlier.temporal_class(question,dates)


def framing(text):
    text=re.sub(r'\bfor\s+(?:an?|the)\s+(?:original[- ]text|source[- ]text)\s+reading[, :]*',' ',text,flags=re.I)
    text=re.sub(r'(\b(?:paragraph|passage|text|wording)\s+)(?:defining|describing|addressing)\b',r'\1',text,flags=re.I)
    text=re.sub(r'\band\s+addressing\b',' and ',text,flags=re.I)
    return text


class Lexicon:
    """Corpus-bounded English inflections; ambiguous roots are not guessed."""
    def __init__(self,passages):
        self.vocabulary={w for p in passages for w in re.findall(r'[a-z]+',p.text.lower())}
        self.variants=defaultdict(list)
        for word in sorted(self.vocabulary):self.variants[self.canonical(word)].append(word)

    def canonical(self,word):
        if word in earlier.MORPH:return earlier.MORPH[word]
        if word in prior.FAMILIES:return prior.FAMILIES[word]
        if word in {'objection','objections'}:return 'object'
        possible=set()
        if word.endswith('ies') and len(word)>4:possible.add(word[:-3]+'y')
        if word.endswith('es') and len(word)>4:possible.add(word[:-2])
        if word.endswith('s') and len(word)>4 and not word.endswith(('ss','us','is')):possible.add(word[:-1])
        # Only a unique corpus-attested stem is used; ambiguity preserves the token.
        for suffix in ('ing','ed'):
            if word.endswith(suffix) and len(word)>len(suffix)+3:
                stem=word[:-len(suffix)];possible.update({stem,stem+'e'})
                if len(stem)>2 and stem[-1]==stem[-2]:possible.add(stem[:-1])
        known=possible & self.vocabulary
        return next(iter(known)) if len(known)==1 else word

    def terms(self,text,*,query=False):
        if query:text=framing(text)
        text=earlier.FRAME.sub(' ',text)
        text=re.sub(r'[a-z]+',lambda m:self.canonical(m[0]),text.lower())
        return earlier.content_words(text)

    def groups(self,question):
        q=earlier.focused_text(framing(question));hits=list(prior.TOPIC_PATTERN.finditer(q));notice=bool(prior.NOTICE_QUERY.search(q))
        if not hits:return earlier.plan(q)
        topics=[prior.NAMES.get(h[0].lower(),h[0].lower()) for h in hits]
        compare=bool(re.search(r'\b(?:compare|comparison|difference|versus|distinguish\w*|conflat\w*)\b',q,re.I))
        if len(set(topics))>1 or (compare and len(hits)>1):
            fragments=[(topics[n],q[h.end():hits[n+1].start() if n+1<len(hits) else len(q)]) for n,h in enumerate(hits)]
        elif compare:
            special=bool(re.search(r'conflat|distinguish',q,re.I))
            core=re.sub(r'^.*?\b(?:conflat\w*|distinguish\w*)\s+','',q,flags=re.I) if special else q
            splitter=r'\b(?:with|from)\b' if special else r'\band\b|\bversus\b|\bwith\b'
            fragments=[(topics[0],s) for s in re.split(splitter,core,flags=re.I)]
        else:fragments=[(topics[0],q)]
        groups=[]
        for topic,fragment in fragments:
            fragment=re.sub(r'^\s*(?:discuss(?:es)?|locate|find|show|provide)\b',' ',fragment,flags=re.I)
            if notice and absence_claim(question):
                fragment=re.sub(r'\b(?:without|no)\s+(?:any\s+)?(?:exceptions?|qualifiers?|carve[- ]?outs?|exemptions?)\b',' exception ',fragment,flags=re.I)
                fragment=re.sub(r'\b(?:confirm|every|without|any|unconditionally)\b',' ',fragment,flags=re.I)
            anchors=self.terms(fragment,query=True)
            if notice:
                remove={'notification','force','schedule','first','entry','2023','2024'};anchors-=remove
                if not anchors:anchors=self.terms(q,query=True)-remove
            expansion=set(anchors)
            for term in sorted(anchors):expansion.update(self.variants.get(term,[])[:4])
            query=(topic+' '+fragment+' '+' '.join(sorted(expansion)[:64])+(' commencement notification' if notice else ''))[:2400]
            groups.append(prior.Group(topic,query,frozenset(anchors),notice))
        return groups


class PassagePolicy(HardenedPolicy):
    MAX_POOL=60
    def __init__(self,index):
        self.index=index;self.lexicon=Lexicon(index.passages)
        self.forms={p.identifier:self.lexicon.terms(p.text) for p in index.passages}
        self.df=Counter(t for terms in self.forms.values() for t in terms)

    def _matches(self,p,g):
        if prior.topic_of(p)!=g.topic or (p.printed_number is None)!=g.notification:return False
        anchors=set(g.anchors);terms=self.lexicon.terms(p.text)
        if not anchors:return g.notification
        overlap=anchors & terms;minimum=1 if g.notification else 2
        if len(anchors)<minimum or len(overlap)<minimum:return False
        weight=lambda t:math.log(1+(len(self.index.passages)+1)/(1+self.df[t]))
        # Explicit scope/qualification anchors must survive; ordinary descriptive
        # framing still uses the established weighted coverage floor.
        qualifiers=anchors & {'special','only','except','unless','exclusive','sole','proper','not','without'}
        return qualifiers<=overlap and sum(weight(t) for t in overlap)>=.5*sum(weight(t) for t in anchors)

    def _rank(self,question,groups,live,mode,limit,max_characters):
        if query_policy(question) is None:return []
        pools=[]
        def collect(query,ids=None):
            # Independent lexical candidates survive a dense-fusion top-five cutoff.
            modes=['bm25','hybrid'] if mode=='hybrid' else ['bm25']
            for candidate_mode in modes:
                pools.append(self.index.search(query,limit=5,max_characters=24000,source_ids=ids,mode=candidate_mode))
        collect(question)
        for g in groups:
            ids=sorted({p.candidate.document_id for p in self.index.passages if prior.topic_of(p)==g.topic and (p.printed_number is None)==g.notification})
            if ids:collect(g.query,ids)
        if sum(len(pool) for pool in pools)>self.MAX_POOL:raise ValueError('Candidate pool bound exceeded')
        found={};matching={}
        for pool in pools:
            for p in pool:
                item,doc=validate_candidate(live,p.candidate)
                if exclusion_reasons(item,p.candidate) or span_text(doc,p.candidate.spans[0])!=p.text or prior.INJECTION.search(p.text):raise ValueError('Excluded/tampered candidate')
                coverage={n for n,g in enumerate(groups) if self._matches(p,g)}
                if coverage:found[p.identifier]=p;matching[p.identifier]=coverage
        order=reciprocal_rank_fusion([[p.identifier for p in pool if p.identifier in found] for pool in pools])
        ranked=[];covered=set();size=0
        while order and len(ranked)<limit:
            key=min(order,key=lambda p:(-len(matching[p]-covered),order.index(p)));order.remove(key);p=found[key]
            if size+len(p.text)>max_characters:continue
            ranked.append(p);covered|=matching[key];size+=len(p.text)
        return ranked

    def assess(self,question,*,mode='bm25',limit=5,max_characters=24000,diagnostic_retrieval=False):
        if type(question) is not str or not 0<len(question)<=2000:raise ValueError('Question must contain one to 2000 characters')
        if type(max_characters) is not int or not 1<=max_characters<=24000:raise ValueError('Invalid evidence budget')
        if mode not in {'bm25','hybrid'} or type(limit) is not int or not 1<=limit<=5:raise ValueError('Invalid mode/limit')
        if mode=='hybrid' and self.index.semantic is None:raise ValueError('Hybrid unavailable')
        try:
            live,dates=self._sources();kind=temporal_class(question,dates);groups=self.lexicon.groups(question)
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


class PassageEvidenceRetriever:
    """Read-only offline wrapper retaining all Stage 6D handoff checks."""
    def __init__(self,index):self.index=index

    def inspect(self,question,**kwargs):
        snapshot=None
        try:
            snapshot=RequestSources(self.index)
            active=request_index(self.index,snapshot)
            result=PassagePolicy(active).assess(question,**kwargs)
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
