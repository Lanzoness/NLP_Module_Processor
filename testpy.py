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
        doc = fitz.open(pdf_path)  # Open the PDF file
        
        for page in doc:  # Iterate through each page
            page_text = page.get_text("text")
            lines = page_text.split('\n')
            processed_lines = []
            current_line = ""

            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Add space after bullet symbols like , , etc.
                line = re.sub(r"^(|)(\S)", r"\1 \2", line)  # Ensure space between bullet and text
                
                # Handle bullet points and symbols like , , etc.
                if line.startswith(("", "", "-")) or re.match(r'^\d+\.', line):
                    if current_line:  # Append previous line if it exists
                        processed_lines.append(current_line.strip())
                        current_line = ""
                    current_line = line  # Start a new bullet point
                else:
                    # Combine with the current line if it's part of the same paragraph
                    if current_line and not current_line.endswith((".", ":", "?")):
                        current_line += " " + line
                    else:
                        if current_line:  # Add finished lines
                            processed_lines.append(current_line.strip())
                        current_line = line

            # Append the last line on the page if it exists
            if current_line:
                processed_lines.append(current_line.strip())
            
            # Add page separator
            text += "\n".join(processed_lines) + "\n\n"

        doc.close()  # Close the document
        
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
    
    # Define a set of patterns to exclude from being detected as entities
    exclude_patterns = [
        r'^\s*[\u2022]\s*',  # Bullet points
        r'^\s*[-•*]\s*',     # Other list item markers
        r'^\s*\d+\.\s*',     # Numbered list items
        r'^\s*[\u25AA]\s*',  # Square bullet
        r'^\s*[\u25AB]\s*',  # Hollow square bullet
        r'^\s*[\u25CF]\s*',  # Black circle bullet
        r'^\s*[\u25CB]\s*',  # White circle bullet
        r'^\s*[\u25C6]\s*',  # Black diamond bullet
        r'^\s*[\u25B6]\s*',  # Right-pointing triangle bullet
        r'^\s*[\u25C7]\s*',  # White diamond bullet
        r'^\s*[\u25A0]\s*',  # Black square bullet
        r'^\s*[\u25A1]\s*',  # White square bullet
        r'^\s*[\u25B2]\s*',  # Black up-pointing triangle
        r'^\s*[\u25BC]\s*',  # Black down-pointing triangle
        r'^\s*[\u25B3]\s*',  # White up-pointing triangle
        r'^\s*[\u25BD]\s*',  # White down-pointing triangle
        r'^\s*[\u25D0]\s*',  # Circle with left half black
        r'^\s*[\u25D1]\s*',  # Circle with right half black
        r'^\s*[\u25D2]\s*',  # Circle with upper half black
        r'^\s*[\u25D3]\s*',  # Circle with lower half black
        r'^\s*\s*'         # Specific character to exclude
    ]
    
    for page in pages:
        # Store matches before spaCy processing
        date_matches = [(match.group(), match.start(), match.end()) for match in re.finditer(date_pattern, page)]
        
        # Now process with spaCy
        doc = nlp(page)
        
        # Iterate over named entities from spaCy
        for ent in doc.ents:
            # Skip entities that match any of the exclude patterns
            if any(re.match(pattern, ent.text) for pattern in exclude_patterns):
                continue
            
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
