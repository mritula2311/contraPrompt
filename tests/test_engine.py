import pytest
from contradictprompt import analyze,Label
from contradictprompt.preprocessing import normalize
from contradictprompt.repair import suggestions,approve_and_revalidate,generate_validated
from contradictprompt.satisfaction import check_response
@pytest.mark.parametrize('prompt,label',[
 ('Write exactly 100 words, but use fewer than 80 words.',Label.IMPOSSIBLE),
 ('Use at least 80 words; use at most 80 words.',Label.COMPATIBLE),
 ('Use more than 80 words; use at most 80 words.',Label.IMPOSSIBLE),
 ('Use fewer than 0 words.',Label.IMPOSSIBLE),
 ('Use between 20 and 10 words.',Label.IMPOSSIBLE),
 ('Use at least 1 word; use less than 2 words.',Label.COMPATIBLE),
 ('Use exactly 0 words; use no more than 0 words.',Label.COMPATIBLE),
 ('Use no fewer than 20 words; use under 20 words.',Label.IMPOSSIBLE),
 ('Write exactly 50 words; ideally use fewer than 40 words.',Label.PARTIAL),
 ('In the introduction use exactly 20 words; in the conclusion use exactly 40 words.',Label.COMPATIBLE),
 ('Use bullet points; do not use bullet points.',Label.IMPOSSIBLE),
 ("Use bullet points; don't use bullet points.",Label.IMPOSSIBLE),
 ('Avoid bullet points.',Label.COMPATIBLE),
 ('Do not include a table; use a table.',Label.IMPOSSIBLE),
 ('Return JSON only; explain your reasoning outside JSON.',Label.IMPOSSIBLE),
 ('Return JSON only; put the explanation inside a JSON string.',Label.COMPATIBLE),
 ('For the introduction use bullet points; for the conclusion avoid bullet points.',Label.COMPATIBLE),
 ('Include the word "safe"; do not mention the word "safe".',Label.IMPOSSIBLE),
 ('Include the word "safe"; do not mention the word "unsafe".',Label.COMPATIBLE),
 ('Describe why the sensor is not responding.',Label.COMPATIBLE),
 ('Write a short introduction and a detailed conclusion.',Label.COMPATIBLE),
 ('Write a brief and comprehensive explanation.',Label.PARTIAL),
 ('Write a neutral report; make it persuasive.',Label.PARTIAL),
 ('Write a formal introduction; write a casual conclusion.',Label.COMPATIBLE),
 ('Summarize the attached document.',Label.UNSPECIFIED),
 ('Summarize the following text: plants need sunlight.',Label.COMPATIBLE),
 ('Calculate the mean; the numbers are not supplied.',Label.UNSPECIFIED),
 ('Schedule meeting A on Monday at 09:00; schedule meeting A on Monday at 10:00.',Label.IMPOSSIBLE),
 ('Schedule meeting A on Monday at 09:00; schedule meeting B on Monday at 10:00.',Label.COMPATIBLE),
 ('Schedule meeting A on Monday at 09:00; schedule meeting A on Tuesday at 10:00.',Label.COMPATIBLE),
 ('Schedule meeting A on Monday at 09:00 and at 10:00.',Label.IMPOSSIBLE),
 ('Schedule meeting A on Monday at 09:00; prefer meeting A on Monday at 10:00.',Label.PARTIAL),
 ('Explain the quote "use exactly 10 words and fewer than 5 words".',Label.COMPATIBLE),
 ('Write exactly 100 words; use fewer than 50 words; the document is not supplied.',Label.IMPOSSIBLE),
])
def test_classification(prompt,label): assert analyze(prompt).label==label

def test_offsets_unicode_whitespace():
    p='  Explain café.\n\tWrite exactly 100 words, but use fewer than 80 words. '
    r=analyze(p)
    for i in r.instructions: assert p[i.start:i.end]==i.text
    n=normalize(p)
    assert all(n.text[j]==p[k] or n.text[j]==' ' and p[k].isspace() for j,k in enumerate(n.offsets))
    assert r.original==p
@pytest.mark.parametrize('prompt',['','   ','x'*30001])
def test_input_limits(prompt):
    with pytest.raises(ValueError): analyze(prompt)
def test_repair_preserves_unrelated_text():
    p='Write exactly 100 words, but use fewer than 80 words. Discuss solar panels.'
    for option in suggestions(analyze(p)):
        assert 'Discuss solar panels.' in option.prompt
        assert option.patch.removed_text==p[option.patch.start:option.patch.end]
        assert option.requires_approval
        assert approve_and_revalidate(option.prompt,True).label==Label.COMPATIBLE

def test_approval_required():
    with pytest.raises(ValueError): approve_and_revalidate('Write a summary.',False)
    with pytest.raises(ValueError): generate_validated(analyze('Use bullet points; avoid bullet points.'),None,True)
    with pytest.raises(ValueError): generate_validated(analyze('Write a summary.'),None,False)
def test_satisfaction_is_separate():
    p='Write exactly 3 words.'
    assert analyze(p).label==Label.COMPATIBLE
    assert check_response(p,'too short')['all_supported_pass'] is False
    assert check_response(p,'these three words')['all_supported_pass'] is True
    assert check_response('Discuss economics.','OK')['full_satisfaction'] is None
@pytest.mark.parametrize('answer,valid',[('{"a":1}',True),('Here: {"a":1}',False),('```json\n{}\n```',False)])
def test_json_satisfaction(answer,valid): assert check_response('Return JSON only.',answer)['all_supported_pass']==valid
