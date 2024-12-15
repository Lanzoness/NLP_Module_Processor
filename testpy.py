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
    
    # Regex pattern to check for non-alphanumeric characters, including specified symbols and space
    non_alphanumeric_pattern = r'[^a-zA-Z0-9.:,?/(){}[\]_+=\-*`"\'#@$! ]'  # Matches any non-alphanumeric character, including specified symbols and space
    
    # Define a set of blacklisted words
    blacklist = {
        "vs"
    }
    
    for page in pages:
        # Store matches before spaCy processing
        date_matches = [(match.group(), match.start(), match.end()) for match in re.finditer(date_pattern, page)]
        
        # Now process with spaCy
        doc = nlp(page)
        
        # Iterate over named entities from spaCy
        for ent in doc.ents:
            # Skip entities that contain non-alphanumeric characters
            if re.search(non_alphanumeric_pattern, ent.text):
                continue
            
            # Skip entities that are in the blacklist
            if ent.text.lower() in blacklist:  # Use lower() for case-insensitive comparison
                continue
            
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC", "MONEY", "PRODUCT", "WORK_OF_ART", "TIME"]:
                # Capture only the sentence containing the entity
                sentence = ent.sent.text.strip()
                
                # Check the length condition
                if len(sentence) <= len(ent.text) + 5:
                    continue  # Skip this entity if the condition is met
                
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
        question = {
            "question": question_text,
            "answer": entity,
            "options": options  # Add options to the question dictionary
        }
        questions.append(question)
        
        # Mark the entity as used
        used_entities.add(entity_id)
    
    return questions

def save_questions_to_file(filename, multiple_choice_questions):
    """Saves generated questions to a text file, including options."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write("Multiple-Choice Questions:\n")
        for i, q in enumerate(multiple_choice_questions, 1):
            file.write(f"\n{i}. {q['question']} \n")
            # Add options to the file first
            options_text = "\n".join([f"{chr(65 + j)}. {option[0]}" for j, option in enumerate(q['options'])])
            file.write(f"Options:\n{options_text}\n")
            # Now add the answer
            file.write(f"(Answer: {q['answer']})\n")
            file.write("----------------------------")

def save_entities_to_file(filename, entities_with_context):
    """Saves entities and their corresponding sentences to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        for entity, label, sentence in entities_with_context:
            file.write(f"Entity: {entity}\nLabel: {label}\nSentence: {sentence}\n\n")
    print(f"Entities and sentences have been saved to {filename}")

def display_questions_and_get_score(multiple_choice_questions):
    """Displays questions and options, and calculates the score based on user input."""
    score = 0
    
    for question in multiple_choice_questions:
        print(question['question'])  # Display the question
        print("Options:")
        
        # Display the options
        options = question['options']  # Assuming options are stored in the question dict
        for i, option in enumerate(options):
            print(f"{chr(65 + i)}. {option[0]}")  # A, B, C, D for options
        
        # Get user input
        user_answer = input("Enter your answer (A, B, C, or D): ").strip().upper()
        
        # Check if the answer is correct
        if user_answer in ['A', 'B', 'C', 'D']:
            selected_index = ord(user_answer) - 65  # Convert A, B, C, D to index 0, 1, 2, 3
            if options[selected_index][0] == question['answer']:  # Compare with the correct answer
                score += 1
                print("Correct!\n")
            else:
                print("Wrong answer.\n")
        else:
            print("Invalid input. Please enter A, B, C, or D.\n")
    
    print(f"Your total score is: {score}/{len(multiple_choice_questions)}")

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

    # Display questions and get score
    display_questions_and_get_score(multiple_choice_questions)

if __name__ == "__main__":
    pdf_path = "Module_01_Introduction_to_Computer_Organization_and_Architecture.pdf"  # Replace with your PDF file path
    main(pdf_path)
