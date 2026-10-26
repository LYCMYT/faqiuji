"""Pure RFQ membership/revision contract; no CAD or supplier assumptions."""
import csv
import json
import re

RFQ_FIELDS=['family','revision','source_revision','STEP','material_candidate','datums_and_holes','scope','drawing_review','supplier','quantity','quote_CNY','lead_days','supplier_confirmed','first_article_released','manufacturing_release']

def native_source_revision(item):
    """Preserve explicit provenance; new R4 bodies are never labelled R3 retained."""
    return item.get('r4_revision') or item.get('source_revision') or ('R4 self-designed candidate' if re.search(r'(?:^|-)R4(?:-|$)',item['family']) else 'R3 retained')

def first_article_rfq_rows(index,first_article):
    indexed={item['family']:item for item in index};declared={item['family']:item for item in first_article['items']}
    missing=set(declared)-set(indexed)
    if missing:raise ValueError('Declared first-article families absent from native index: '+', '.join(sorted(missing)))
    selected=set(declared)|{family for family in indexed if re.search(r'(?:^|-)R4(?:-|$)',family)}
    result=[]
    for family in sorted(selected):
        item=indexed[family];match=re.search(r'(?:^|-)(R\d+)(?:-|$)',family);revision=item.get('revision') or (match.group(1) if match else None)
        if not revision or match and revision!=match.group(1):raise ValueError('Missing/conflicting native family revision: '+family)
        result.append(dict(family=family,revision=revision,source_revision=native_source_revision(item),STEP=item['step'],material_candidate=item.get('material','OPEN'),datums_and_holes=json.dumps(item.get('holes',[]),ensure_ascii=False),scope=declared.get(family,{}).get('scope','Additional R4 native candidate review'),drawing_review='OPEN',supplier=None,quantity=None,quote_CNY=None,lead_days=None,supplier_confirmed=False,first_article_released=False,manufacturing_release=False))
    return result

def write_first_article_rfq(path,index,first_article):
    rows=first_article_rfq_rows(index,first_article)
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=RFQ_FIELDS);writer.writeheader();writer.writerows(rows)
    return rows
