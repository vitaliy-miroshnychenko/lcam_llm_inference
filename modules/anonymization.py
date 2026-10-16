import spacy
import re

label_map = {
    "PER": "[ПІБ]",
    "LOC": "[АДРЕСА]",
    "ORG": "[ОРГ]"
}  # TODO: add ЄДРПОУ 26125532, айдішкі, податковий номер

NLP = spacy.load("uk_core_news_sm", disable=["parser", "tagger", "lemmatizer"])


def normalize_spaces(text):
    return re.sub(r'\s{2,}', ' ', text)


def anonymize(text, replace_br=False, debug=False, nlp=NLP):
    if debug:
        print("\tanonymization, len(text)", len(text))
    new_text = normalize_spaces(str(text))


    new_text = new_text.replace("<br>", '\n')
    doc = nlp(new_text)

    for ent in reversed(doc.ents):
        if ent.label_ == 'PER':
            label = label_map.get(ent.label_, "[ІНШЕ]")
            new_text = new_text[:ent.start_char] + label + new_text[ent.end_char:]

    new_text = re.sub(r'\d{10}:\d{2}:\d{3}:\d{4}', '[КАДАСТР]', new_text)

    new_text = new_text.replace('\n', "<br>")


    if debug:
        print("\tanonymization, len(anonymized_text)", len(new_text))
    return new_text
