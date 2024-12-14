import fitz  # PyMuPDF
import spacy
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

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
            # Extract text from the page
            page_text = page.get_text("text")
            lines = page_text.split('\n')
            processed_lines = []
            current_line = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Split by numbered list pattern
                numbered_parts = re.split(r'(\d+\.\s+)', line)
                
                for part in numbered_parts:
                    # If this part is a number with period (e.g., "1. "), start a new line
                    if re.match(r'^\d+\.\s+$', part):
                        if current_line:
                            processed_lines.append(current_line.strip())
                            current_line = ""
                        current_line = part
                        continue
                    
                    # Split remaining parts by sentence boundaries
                    sentence_parts = re.split(r'(?<=[.?!])\s+(?=[A-Z])', part)
                    
                    for sent in sentence_parts:
                        # Check for other list item markers
                        is_list_item = bool(re.match(r'^\s*(?:[^a-zA-Z0-9\s])', sent))
                        
                        if is_list_item:
                            if current_line:
                                processed_lines.append(current_line.strip())
                                current_line = ""
                            current_line = sent
                        else:
                            if current_line:
                                current_line += " " + sent
                            else:
                                current_line = sent
            
            if current_line:
                processed_lines.append(current_line.strip())
            
            # Combine all lines and add double newline for page separation
            text += '\n'.join(processed_lines) + "\n\n"
        
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
    # Split the text into pages based on double newlines
    pages = text.split("\n\n")
    
    entities_with_context = []
    
    # Add custom date range detection using regex for year ranges
    date_pattern = r'\b(\d{4}\s*–\s*\d{4})\b'  # Matches patterns like "1642 – 1945"
    
    for page in pages:
        # Store matches before spaCy processing
        date_matches = [(match.group(), match.start(), match.end()) for match in re.finditer(date_pattern, page)]
        
        # Now process with spaCy
        doc = nlp(page)
        
        # Iterate over named entities from spaCy
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC", "MONEY", "PRODUCT", "WORK_OF_ART", "TIME"]:
                # Capture only the sentence containing the entity
                sentence = ent.sent.text.strip()
                entities_with_context.append((ent.text.strip(), ent.label_, sentence))
        
        # Handle custom ENTITY_DATE matches
        for match_text, start, end in date_matches:
            # Identify the sentence containing the date
            for sent in doc.sents:
                if sent.start_char <= start < sent.end_char:
                    entities_with_context.append((match_text, "DATE", sent.text.strip()))
                    break
    
    return entities_with_context



def generate_multiple_choice_questions(entities_with_context):
    """Generates multiple-choice questions based on entity context."""
    questions = []
    
    # Create a list of all available entities for choices
    all_entities = [(e[0], i) for i, e in enumerate(entities_with_context)]  # Include index for uniqueness
    used_entities = set()  # Track used entities to prevent duplicates
    
    for entity, label, sentence in entities_with_context:
        entity_id = (entity, label)  # Create a unique identifier for the entity
        
        # Skip if this entity has already been used
        if entity_id in used_entities:
            continue
        
        # Use the full sentence for the question
        question_text = sentence.replace(entity, "______")
        
        # Generate answer options from all entities, including dates
        available_entities = [e for e in all_entities if e[0] != entity and (e[0], entities_with_context[e[1]][1]) not in used_entities]
        if len(available_entities) < 3:
            continue  # Skip if we don't have enough options
            
        incorrect_answers = random.sample(available_entities, min(3, len(available_entities)))
        options = incorrect_answers + [(entity, label)]  # Keep entity with its label
        random.shuffle(options)
        
        # Format the question
        options_text = "\n".join([f"{chr(97 + i)}. {option[0]}" for i, option in enumerate(options)])
        question = f"{question_text}\n{options_text}"
        questions.append({"question": question, "answer": entity})
        
        # Mark the entity as used
        used_entities.add(entity_id)
    
    return questions

def save_questions_to_file(filename, multiple_choice_questions):
    """Saves generated questions to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write("Multiple-Choice Questions:\n")
        for i, q in enumerate(multiple_choice_questions, 1):
            file.write(f"\n{i}. {q['question']} \n(Answer: {q['answer']})\n")
            file.write("----------------------------")

def save_entities_to_file(filename, entities_with_context):
    """Saves entities and their corresponding sentences to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        for entity, label, sentence in entities_with_context:
            file.write(f"Entity: {entity}\nLabel: {label}\nSentence: {sentence}\n\n")
    print(f"Entities and sentences have been saved to {filename}")

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    entities_with_context = extract_named_entities_with_context(text)

    # Save entities and sentences to a file
    entity_sentence_file = "entity_sentence.txt"
    save_entities_to_file(entity_sentence_file, entities_with_context)

    # Generate questions
    multiple_choice_questions = generate_multiple_choice_questions(entities_with_context)

    # Save questions to a file
    output_file = "generated_questions.txt"
    save_questions_to_file(output_file, multiple_choice_questions)
    print(f"Questions have been saved to {output_file}")

if __name__ == "__main__":
    pdf_path = "Module_01_Introduction_to_Computer_Organization_and_Architecture.pdf"  # Replace with your PDF file path
    main(pdf_path)
