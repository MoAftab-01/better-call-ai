"""Bounded, inspectable OFFLINE query intent; no legal-code equivalence mapping."""
import re
from . import evidence as prior

# Ordinary English inflections only; never translate statute/provision identifiers.
MORPH = {}
for root, forms in {
    'refuse':'refusal refuses refused refusing', 'require':'requires required requiring',
    'make':'makes made making maker', 'counterfeit':'counterfeits counterfeited counterfeiting',
    'exclude':'excluded excluding exclusion exclusions', 'prosecute':'prosecuting prosecution prosecuted prosecutions',
    'diligent':'diligently diligence', 'contradict':'contradicting contradicted contradiction',
    'corroborate':'corroborating corroborated corroboration', 'impeach':'impeaching impeached',
    'confirm':'confirming confirmed', 'prove':'proved proving proven',
}.items():
    for form in forms.split(): MORPH[form] = root
FUNCTION = set('but while their these each has have been be than also'.split())
FRAME = re.compile(r'\b(?:(?:a|an|the|each)\s+)?(?:training|museum|history|study|source[- ]reading|classroom)\s+(?:cards?|worksheets?|exercises?|seminars?|appendi(?:x|ces)|indexes?|indices|tasks?|files?|lessons?)\b(?:\s+needs)?', re.I)
NAV_TAIL = re.compile(r'[.;]\s*(?:locate|find|show|provide)\s+(?:(?:the|two|both|separate|distinct|archival|original|passages|paragraphs|materials)\b[\s,]*)+[.!?]?$',re.I)
UPDATE = re.compile(r'\b(?:supersed\w*|rescind\w*|revok\w*|withdraw\w*|replac\w*|overrid\w*|remov\w*|abolish\w*|lift\w*|chang\w*)\b',re.I)
LATER = re.compile(r'\b(?:new|fresh|another|later|subsequent|since|after|yet)\b',re.I)
STATUS = re.compile(r'\b(?:exceptions?|entr(?:y|ies)|notifications?|commencement|restrictions?|provisions?|laws?|force|status|rules?|procedures?|penalt(?:y|ies)|punishments?|evidence)\b',re.I)
RELATIVE = re.compile(r'\b(?:next|last|this|coming|previous)\s+(?:week|month|year)\b|\b(?:tomorrow|yesterday|recently|henceforth)\b',re.I)


def historical_task(question):
    return bool(re.search(r'\b(?:original|archiv\w*)\b',question,re.I) and re.search(r'\b(?:find|locate|quote|inspect|paragraph|text|state|say|describe|explain)\w*\b',question,re.I))


def scope_text(question):
    """Strip only a bounded trailing meta-disclaimer, never a second status ask."""
    if not historical_task(question):return question
    match=re.search(r'[,;]\s*(?:without|not)\s+(?:treating|using|claiming|asserting|presenting)\b[^.;?!]{0,160}[.?!]?$',question,re.I)
    if match and re.search(r'\b(?:current|present|today)\b',match[0],re.I):
        if not re.search(r'\b(?:but|however|and|or|is|are|does|do|has|have|can|will|was|were)\b',match[0],re.I):
            return question[:match.start()]
    return question


def temporal_class(question, dates):
    # Inspect the raw question for scope/injection/personal restrictions first.
    if prior.INJECTION.search(question) or prior.OUTSIDE.search(question) or prior.PERSONAL.search(question):return 'scope_restricted'
    scoped=scope_text(question)
    if RELATIVE.search(scoped):return 'current_or_later'
    if UPDATE.search(scoped) and STATUS.search(scoped):
        if LATER.search(scoped) or (not historical_task(scoped) and re.search(r'\b(?:has|have|is|are|did|does|was|were|any|anything)\b',scoped,re.I)):
            return 'current_or_later'
    return prior.temporal_class(scoped,dates)


def absence_claim(question):
    return bool(re.search(r'\b(?:without|no)\s+(?:any\s+)?(?:exceptions?|qualifiers?|carve[- ]?outs?|exemptions?)\b|\bevery\s+(?:provision|entry)\b|\bunconditionally\b',question,re.I))


def content_words(text):
    text=FRAME.sub(' ',text)
    text=NAV_TAIL.sub(' ',text)
    text=re.sub(r'\b(?:locate|provide|find|supply)\s+(?:archival\s+)?material\b',' ',text,flags=re.I)
    text=re.sub(r'\bmaterial(?=\s+for\b)|\bfor these distinct archival tasks\b',' ',text,flags=re.I)
    text=re.sub(r'^\s*(?:locate|find|show|quote|inspect|provide|discuss(?:es)?)\b',' ',text,flags=re.I)
    result=set()
    for token in re.findall(r'[a-z]+|\d+',text.lower()):
        token=MORPH.get(token,prior.FAMILIES.get(token,token))
        if token.endswith('s') and len(token)>4 and not token.endswith(('ss','us','is')):token=token[:-1]
        if token not in prior.BOILER and token not in FUNCTION:result.add(token)
    return result


def focused_text(question):
    """A concrete final locate-about request may narrow a teaching preamble."""
    q=scope_text(question)
    parts=re.split(r'(?<=[.!?])\s+(?=(?:find|locate|quote|inspect)\b)',q,flags=re.I)
    topics=list(prior.TOPIC_PATTERN.finditer(q))
    names={prior.NAMES.get(h[0].lower(),h[0].lower()) for h in topics}
    if len(parts)>1 and len(names)==1 and (FRAME.search(parts[0]) or re.search(r'\b(?:worksheet|seminar|museum card|training card|study index)\b',parts[0],re.I)):
        last=parts[-1]
        if re.search(r'\b(?:about|on|concerning)\s+(?!it\b|them\b|these\b)\S+',last,re.I):
            return topics[0][0]+' '+last
    return NAV_TAIL.sub('',q)


def plan(question):
    q=focused_text(question)
    hits=list(prior.TOPIC_PATTERN.finditer(q));notice=bool(prior.NOTICE_QUERY.search(q))
    if not hits:return prior.plan(q)
    topics=[prior.NAMES.get(h[0].lower(),h[0].lower()) for h in hits]
    distinct=list(dict.fromkeys(topics))
    if len(distinct)>1:
        fragments=[(topics[n],q[h.end():hits[n+1].start() if n+1<len(hits) else len(q)]) for n,h in enumerate(hits)]
    else:
        # Only explicit comparison/conflation syntax licenses same-instrument splitting.
        compare=re.search(r'\b(?:compare|comparison|difference|versus|distinguish\w*|conflat\w*)\b',q,re.I)
        if compare:
            core=re.sub(r'^.*?\b(?:conflat\w*|distinguish\w*)\s+','',q,flags=re.I) if re.search(r'conflat|distinguish',q,re.I) else q
            splitter=r'\b(?:with|from)\b' if re.search(r'conflat|distinguish',q,re.I) else r'\band\b|\bversus\b'
            fragments=[(distinct[0],s) for s in re.split(splitter,core,flags=re.I)]
        else:fragments=[(distinct[0],q)]
    groups=[]
    for topic,fragment in fragments:
        fragment=re.sub(r'^\s*(?:discuss(?:es)?|locate|find|show|provide)\b',' ',fragment,flags=re.I)
        if notice and absence_claim(question):
            # Retrieve the original paragraph to TEST the premise; the raw claim
            # remains available to the mandatory exception guard in assess().
            fragment=re.sub(r'\b(?:without|no)\s+(?:any\s+)?(?:exceptions?|qualifiers?|carve[- ]?outs?|exemptions?)\b',' exception ',fragment,flags=re.I)
            fragment=re.sub(r'\b(?:confirm|every|without|any|unconditionally)\b',' ',fragment,flags=re.I)
        anchor=content_words(fragment)
        if notice:
            anchor-={'notification','force','schedule','first','entry','2023','2024'}
            if not anchor:anchor=content_words(q)-{'notification','force','schedule','first','entry','2023','2024'}
        # Canonical English forms improve lexical candidate collection; source text is untouched.
        expansion=set(anchor)|{word for word,root in MORPH.items() if root in anchor}
        query=topic+' '+fragment+' '+' '.join(sorted(expansion))+(' commencement notification' if notice else '')
        groups.append(prior.Group(topic,query,frozenset(anchor),notice))
    return groups
