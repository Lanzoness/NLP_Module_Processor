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
            # Extract text from the page with better formatting
            page_text = page.get_text("text")
            
            # Clean up unnecessary newlines while preserving paragraphs
            lines = page_text.split('\n')
            cleaned_lines = []
            current_line = ""
            
            for line in lines:
                line = line.strip()
                if not line:  # Empty line indicates paragraph break
                    if current_line:
                        cleaned_lines.append(current_line)
                        current_line = ""
                    cleaned_lines.append("")
                else:
                    if current_line:
                        current_line += " " + line
                    else:
                        current_line = line
            
            if current_line:  # Add the last line if exists
                cleaned_lines.append(current_line)
            
            text += "\n".join(cleaned_lines) + "\n"
        
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
    doc = nlp(text)
    entities_with_context = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC"]:
            sentence = ent.sent.text.strip()
            
            # Find the entity's position in the sentence
            entity_start = sentence.find(ent.text)
            if entity_start != -1:
                # Look ahead for closing parenthesis if we have an opening one
                entity_text = ent.text
                rest_of_sentence = sentence[entity_start + len(ent.text):]
                
                # If the entity contains an opening parenthesis or ends with it
                if '(' in entity_text or entity_text.rstrip().endswith('('):
                    # Count opening parentheses
                    open_count = entity_text.count('(')
                    close_count = entity_text.count(')')
                    
                    # If we need more closing parentheses
                    if open_count > close_count:
                        needed_closing = open_count - close_count
                        # Look in the rest of the sentence for closing parentheses
                        pos = 0
                        for _ in range(needed_closing):
                            next_close = rest_of_sentence[pos:].find(')')
                            if next_close != -1:
                                # Include up to and including the closing parenthesis
                                include_text = rest_of_sentence[pos:pos + next_close + 1]
                                entity_text += include_text
                                pos = next_close + 1
                            else:
                                break
            
            # Ensure sentences are concise by limiting word count
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
