"""Explicit local edits only. Suggestions never authorize execution."""
import re
from .models import Assessment, Repair, Patch, Label
from .engine import analyze

def suggestions(result: Assessment) -> list[Repair]:
    byid={i.id:i for i in result.instructions}; out=[]; seen=set()
    for conflict in result.conflicts:
        items=[byid[x] for x in conflict.instruction_ids]
        for target in items:
            other=next((x for x in items if x.id!=target.id),None)
            replacement=''
            if target.kind=='numerical' and other and other.kind=='numerical':
                replacement=other.text
            elif target.kind=='temporal' and other and other.kind=='temporal':
                if re.search(r'\b\d{1,2}:\d{2}\b', target.text):
                    replacement=re.sub(r'\b\d{1,2}:\d{2}\b',other.value,target.text)
                else:
                    replacement=other.text
            elif target.kind in ('semantic', 'logical') and other:
                replacement=other.text
            elif target.kind=='formatting' and other and target.key=='outside_json':
                replacement=''
            elif target.kind=='formatting' and other and target.key=='json_only':
                replacement='valid Markdown or JSON'

            if replacement == target.text:
                replacement = ''

            key=(target.start,target.end,replacement)
            if key in seen: continue
            seen.add(key)
            fixed=result.original[:target.start]+replacement+result.original[target.end:]
            if not fixed.strip() or fixed == result.original: continue
            action=f'Replace “{target.text}” with “{replacement}”' if replacement else f'Remove “{target.text}”'
            out.append(Repair(id=f'R{len(out)+1}',description=action+'. Unrelated text is retained; review grammar and intent.',prompt=fixed,
                patch=Patch(start=target.start,end=target.end,replacement=replacement,removed_text=target.text)))
    return out

def approve_and_revalidate(prompt: str,approved: bool,mode='rules',client=None):
    if not approved: raise ValueError('Explicit approval is required before accepting the edited prompt.')
    return analyze(prompt,mode=mode,client=client)

def generate_validated(result: Assessment,client,approved: bool):
    if not approved: raise ValueError('Approve the exact current prompt before generation.')
    if result.label!=Label.COMPATIBLE: raise ValueError('Resolve conflicts or missing information, then revalidate before generation.')
    return client.generate(result.original)
