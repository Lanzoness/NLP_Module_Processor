import PyPDF2
import spacy
import random
import re

# Load SpaCy's English NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file and corrects spacing issues."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text
    return text

def extract_named_entities_with_context(text):
    """Extracts named entities and their surrounding context from the text."""
    doc = nlp(text)
    entities_with_context = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC"]:
            sentence = ent.sent.text
            entities_with_context.append((ent.text, ent.label_, sentence))
    return entities_with_context

def truncate_text(text, max_length):
    """Truncates the text to the maximum length without breaking the context."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def generate_fill_in_the_blank_questions(entities):
    """Generates fill-in-the-blank questions from entities."""
    questions = []
    for entity, label in entities:
        question = f"Fill in the blank: _______ ({label})"
        answer = entity
        questions.append({"question": question, "answer": answer})
    return questions

def generate_multiple_choice_questions(entities_with_context):
    """Generates multiple-choice questions based on entity context."""
    questions = []
    for entity, label, sentence in entities_with_context:
        # Replace the entity in the sentence with a blank
        question_text = sentence.replace(entity, "______")

        # Truncate the question text if it's too long
        question_text = truncate_text(question_text, 150)

        # Generate answer options
        incorrect_answers = random.sample(
            [e[0] for e in entities_with_context if e[0] != entity], min(3, len(entities_with_context) - 1)
        )
        options = incorrect_answers + [entity]
        random.shuffle(options)

        # Format the question
        options_text = "\n".join([f"{chr(97 + i)}. {option}" for i, option in enumerate(options)])
        question = f"{question_text}\n{options_text}"
        questions.append({"question": question, "answer": entity})
    return questions

def save_questions_to_file(filename, fill_in_the_blank_questions, multiple_choice_questions):
    """Saves generated questions to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write("Fill-in-the-Blank Questions:\n")
        for i, q in enumerate(fill_in_the_blank_questions, 1):
            file.write(f"{i}. {q['question']} (Answer: {q['answer']})\n")
        
        file.write("\nMultiple-Choice Questions:\n")
        for i, q in enumerate(multiple_choice_questions, 1):
            file.write(f"\n{i}. {q['question']} \n(Answer: {q['answer']})\n")
            file.write("----------------------------")

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    entities_with_context = extract_named_entities_with_context(text)

    # Generate questions
    fill_in_the_blank_questions = generate_fill_in_the_blank_questions([e[:2] for e in entities_with_context])
    multiple_choice_questions = generate_multiple_choice_questions(entities_with_context)

    # Save questions to a file
    output_file = "generated_questions.txt"
    save_questions_to_file(output_file, fill_in_the_blank_questions, multiple_choice_questions)
    print(f"Questions have been saved to {output_file}")

if __name__ == "__main__":
    pdf_path = "Module_01_Introduction_to_Computer_Organization_and_Architecture-cropped.pdf"  # Replace with your PDF file path
    main(pdf_path)
