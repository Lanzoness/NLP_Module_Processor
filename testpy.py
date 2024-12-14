import fitz  # PyMuPDF
import spacy
import random
import re

# Load SpaCy's English NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file and corrects spacing issues."""
    text = ""
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)
        
        # Iterate through each page
        for page in doc:
            # Extract text from the page and combine all lines
            page_text = page.get_text("text")
            # Remove existing newlines and extra spaces
            page_text = ' '.join(page_text.split())
            
            # Add the processed page text with a newline
            text += page_text + "\n\n"
        
        # Close the document
        doc.close()
        
        # Save raw text to file
        with open("raw_module.txt", "w", encoding="utf-8") as raw_file:
            raw_file.write(text)
        
        print("Raw text saved to raw_module.txt")
        return text
        
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_named_entities_with_context(text):
    """Extracts named entities and their surrounding context from the text."""
    # First, preprocess the text to join split lines
    lines = text.splitlines()
    processed_text = ""
    i = 0
    while i < len(lines):
        current_line = lines[i].strip()
        if not current_line:
            processed_text += "\n"
            i += 1
            continue
            
        # If the current line has an unmatched parenthesis
        if '(' in current_line and ')' not in current_line:
            # Look ahead to the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if ')' in next_line:
                    # Join the lines
                    processed_text += current_line + " " + next_line + "\n"
                    i += 2
                    continue
        
        processed_text += current_line + "\n"
        i += 1
    
    # Now process with spaCy
    doc = nlp(processed_text)
    entities_with_context = []
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC"]:
            sentence = ent.sent.text.strip()
            entity_text = ent.text.strip()
            
            # If entity contains opening parenthesis, ensure we capture everything
            if '(' in entity_text:
                # Find the position in the sentence
                start_pos = sentence.find(entity_text)
                if start_pos != -1:
                    # Look for closing parenthesis after the entity
                    remaining = sentence[start_pos:]
                    open_count = remaining.count('(')
                    close_count = remaining.count(')')
                    
                    if open_count > close_count:
                        # Find position of the last closing parenthesis
                        last_close = -1
                        count = open_count - close_count
                        temp = remaining
                        while count > 0 and (pos := temp.find(')')) != -1:
                            last_close = pos
                            temp = temp[pos + 1:]
                            count -= 1
                        
                        if last_close != -1:
                            # Include everything up to the last needed closing parenthesis
                            entity_text = remaining[:last_close + 1]
            
            # Ensure sentences are concise
            if len(sentence.split()) <= 30:  # Limit to 30 words
                entities_with_context.append((entity_text, ent.label_, sentence))
    
    return entities_with_context


def generate_multiple_choice_questions(entities_with_context):
    """Generates multiple-choice questions based on entity context."""
    questions = []
    for entity, label, sentence in entities_with_context:
        # Replace the entity in the sentence with a blank
        question_text = sentence.replace(entity, "______")

        # Generate answer options
        incorrect_answers = random.sample(
            [e[0] for e in entities_with_context if e[0] != entity], min(3, len(entities_with_context) - 1))
        options = incorrect_answers + [entity]
        random.shuffle(options)

        # Format the question
        options_text = "\n".join([f"{chr(97 + i)}. {option}" for i, option in enumerate(options)])
        question = f"{question_text}\n{options_text}"
        questions.append({"question": question, "answer": entity})
    return questions

def save_questions_to_file(filename, multiple_choice_questions):
    """Saves generated questions to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write("Multiple-Choice Questions:\n")
        for i, q in enumerate(multiple_choice_questions, 1):
            file.write(f"\n{i}. {q['question']} \n(Answer: {q['answer']})\n")
            file.write("----------------------------")

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    entities_with_context = extract_named_entities_with_context(text)

    # Generate questions
    multiple_choice_questions = generate_multiple_choice_questions(entities_with_context)

    # Save questions to a file
    output_file = "generated_questions.txt"
    save_questions_to_file(output_file, multiple_choice_questions)
    print(f"Questions have been saved to {output_file}")

if __name__ == "__main__":
    pdf_path = "Module_01_Introduction_to_Computer_Organization_and_Architecture-cropped.pdf"  # Replace with your PDF file path
    main(pdf_path)
