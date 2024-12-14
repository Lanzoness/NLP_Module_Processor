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
        # Expanded list of entity labels to include dates and names
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC", "MONEY", "PRODUCT", "WORK_OF_ART", "TIME"]:
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
            
            # Increase the sentence length limit
            if len(sentence.split()) <= 30:  # Limit to 30 words
                entities_with_context.append((entity_text, ent.label_, sentence))
    
    return entities_with_context


def generate_multiple_choice_questions(entities_with_context):
    """Generates multiple-choice questions based on entity context."""
    questions = []
    
    # Create a list of all available entities for choices
    all_entities = [e[0] for e in entities_with_context]
    
    for entity, label, sentence in entities_with_context:
        # Replace the entity in the sentence with a blank
        question_text = sentence.replace(entity, "______")
        
        # Generate answer options from unused entities
        available_entities = [e for e in all_entities if e != entity and e not in sentence]
        if len(available_entities) < 3:
            continue  # Skip if we don't have enough options
            
        incorrect_answers = random.sample(available_entities, min(3, len(available_entities)))
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
