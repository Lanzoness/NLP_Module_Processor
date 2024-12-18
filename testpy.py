import fitz  # PyMuPDF
import spacy
import random
import re
import sys
import logging

# Configure logging
log_file = open("console.log", "w", encoding="utf-8")  # Explicitly open the log file

logging.basicConfig(
    stream=log_file,  # Write to the opened file handler
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load SpaCy's English NLP model
nlp = spacy.load("en_core_web_sm")


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file and corrects spacing issues."""
    text = ""
    try:
        doc = fitz.open(pdf_path)  # Open the PDF file
        logging.info(f"Opened PDF file: {pdf_path}")

        for page in doc:  # Iterate through each page
            page_text = page.get_text("text")
            lines = page_text.split("\n")
            processed_lines = []
            current_line = ""

            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                # Add space after bullet symbols like , , etc.
                line = re.sub(r"^(|)(\S)", r"\1 \2", line)  # Ensure space between bullet and text

                # Handle bullet points and symbols like , , etc.
                if line.startswith(("", "", "-")) or re.match(r"^\d+\.", line):
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
        logging.info("Closed PDF document.")

        # Save raw text to file
        with open("raw_module.txt", "w", encoding="utf-8") as raw_file:
            raw_file.write(text)
        logging.info("Raw text saved to raw_module.txt")
        return text

    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return ""


def extract_named_entities_with_context(text):
    """Extracts named entities and their surrounding context from the text."""
    # Split the text into pages based on double newlines
    pages = text.split("\n\n")
    logging.info(f"Text split into {len(pages)} pages.")

    entities_with_context = []

    # Add custom date range detection using regex for year ranges
    date_pattern = r"\b(\d{4}\s*–\s*\d{4})\b"  # Matches patterns like "1642 – 1945"

    # Regex pattern to check for non-alphanumeric characters, including specified symbols and space
    non_alphanumeric_pattern = r"[^a-zA-Z0-9.:,?/(){}[\]_+=\-*`\"'#@$! ]"  # Matches any non-alphanumeric character, including specified symbols and space

    # Define a set of blacklisted words
    blacklist = {"vs"}

    for page_num, page in enumerate(pages):
        logging.debug(f"Processing page {page_num+1}...")
        # Store matches before spaCy processing
        date_matches = [
            (match.group(), match.start(), match.end())
            for match in re.finditer(date_pattern, page)
        ]
        logging.debug(f"Found {len(date_matches)} date matches on page {page_num+1}.")

        # Now process with spaCy
        doc = nlp(page)

        # Iterate over named entities from spaCy
        for ent in doc.ents:
            # Skip entities that contain non-alphanumeric characters
            if re.search(non_alphanumeric_pattern, ent.text):
                logging.debug(
                    f"Skipping entity '{ent.text}' on page {page_num+1} due to non-alphanumeric characters."
                )
                continue

            # Skip entities that are in the blacklist
            if ent.text.lower() in blacklist:  # Use lower() for case-insensitive comparison
                logging.debug(
                    f"Skipping entity '{ent.text}' on page {page_num+1} as it is blacklisted."
                )
                continue

            if ent.label_ in [
                "PERSON",
                "ORG",
                "GPE",
                "DATE",
                "EVENT",
                "LOC",
                "MONEY",
                "PRODUCT",
                "WORK_OF_ART",
                "TIME",
            ]:
                # Capture only the sentence containing the entity
                sentence = ent.sent.text.strip()

                # Check the length condition
                if len(sentence) <= len(ent.text) + 5:
                    logging.debug(
                        f"Skipping entity '{ent.text}' on page {page_num+1} as sentence is too short."
                    )
                    continue  # Skip this entity if the condition is met

                entities_with_context.append((ent.text.strip(), ent.label_, sentence))
                logging.debug(
                    f"Added entity '{ent.text}' of type '{ent.label_}' with context on page {page_num+1}."
                )

        # Handle custom ENTITY_DATE matches
        for match_text, start, end in date_matches:
            # Identify the sentence containing the date
            for sent in doc.sents:
                if sent.start_char <= start < sent.end_char:
                    entities_with_context.append((match_text, "DATE", sent.text.strip()))
                    logging.debug(
                        f"Added custom date entity '{match_text}' with context on page {page_num+1}."
                    )
                    break
    logging.info(f"Found {len(entities_with_context)} entities with context.")
    return entities_with_context


def validate_entity_for_question(
    entity, label, sentence, all_entities, used_entities, entities_with_context
):
    """Validates if an entity is suitable for generating a question."""

    entity_id = (entity, label)
    if entity_id in used_entities:
        logging.debug(
            f"validate_entity: Skipping entity '{entity}' of type '{label}' as it has already been used."
        )
        return False

    available_entities = [
        e
        for e in all_entities
        if e[0] != entity
        and (e[0], entities_with_context[e[1]][1]) not in used_entities
    ]
    if len(available_entities) < 3:
        logging.debug(
            f"validate_entity: Skipping entity '{entity}' of type '{label}' due to insufficient answer options. Available options: {len(available_entities)}, entity: {entity}, label: {label}"
        )
        return False

    logging.debug(
        f"validate_entity: Entity '{entity}' of type '{label}' is valid for question generation. Available options: {len(available_entities)}"
    )
    return True

def generate_multiple_choice_questions(entities_with_context):
    """Generates multiple-choice questions with 4 options each."""
    questions = []
    logging.info("Starting question generation.")

    all_entities = [(e[0], e[1], i) for i, e in enumerate(entities_with_context)]  # Include label in all_entities
    used_entities = set()

    for entity_idx, (entity, label, sentence) in enumerate(entities_with_context):
        logging.debug(f"generate_question: Processing entity '{entity}' of type '{label}'. Index: {entity_idx}")

        if (entity, label) in used_entities:  # Check if entity is already used
            logging.debug(f"Skipping already used entity: {entity}")
            continue
        
        available_entities = [e for e in all_entities if e[0] != entity and (e[0],e[1]) not in used_entities]  # Check used_entities for entity and label

        incorrect_answers = set()
        num_options = 4  # We want 4 options total (including the correct answer)

        # Attempt to get 3 unique incorrect answers (robustly)
        while len(incorrect_answers) < num_options - 1 and available_entities: #check if available_entities is not empty
            try:
                # Pick a random entity (with its label)
                chosen_entity, chosen_label, _ = random.choice(available_entities)

                if (chosen_entity, chosen_label) not in incorrect_answers and (chosen_entity, chosen_label) != (entity, label):  # and not already chosen as incorrect
                    incorrect_answers.add((chosen_entity, chosen_label))
                    logging.debug(f"Added incorrect answer: {chosen_entity}")

                available_entities.remove((chosen_entity,chosen_label,_))  # Remove the chosen entity, whether it was added as an incorrect answer or not

            except IndexError as e:
                logging.error(f"IndexError during option generation: {e}. Available Entities: {available_entities}")
                break  # Exit the while loop if an IndexError occurs

            except Exception as e:  # Log and handle any other exceptions
                logging.error(f"Error during option generation: {e}")
                break  # Important: Exit the loop on any error to avoid freezing

        if len(incorrect_answers) < num_options - 1:
            logging.warning(f"Not enough unique entities to create 4 options for '{entity}'. Skipping.")  # Explicit logging for insufficient options
            continue  # Skip to the next entity


        # Create options list and shuffle
        options = [(entity, label)] + list(incorrect_answers) # Cast incorrect_answers to a list before adding
        random.shuffle(options)

        question = {
            "question": sentence.replace(entity, "______"),
            "answer": entity,
            "options": options,
        }
        questions.append(question)
        used_entities.add((entity, label))  # Mark as used after successful question generation

    logging.info(f"Generated {len(questions)} questions.")
    return questions

def save_questions_to_file(filename, multiple_choice_questions):
    """Saves generated questions to a text file, including options."""
    with open(filename, "w", encoding="utf-8") as file:
        # file.write("Multiple-Choice Questions:\n")
        for i, q in enumerate(multiple_choice_questions, 1):
            file.write(f"\n{i}. {q['question']} \n")
            # Add options to the file first
            options_text = "\n".join(
                [f"{chr(65 + j)}. {option[0]}" for j, option in enumerate(q["options"])]
            )
            file.write(f"Options:\n{options_text}\n")
            # Now add the answer
            file.write(f"(Answer: {q['answer']})\n")
            file.write("----------------------------")
    logging.info(f"Questions saved to {filename}")


def save_entities_to_file(filename, entities_with_context):
    """Saves entities and their corresponding sentences to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        for entity, label, sentence in entities_with_context:
            file.write(f"Entity: {entity}\nLabel: {label}\nSentence: {sentence}\n\n")
    logging.info(f"Entities and sentences have been saved to {filename}")


def display_questions_and_get_score(multiple_choice_questions):
    """Returns questions and options as an object for JavaScript access."""
    questions_data = []

    for question in multiple_choice_questions:
        question_data = {
            "question": question["question"],
            "options": [option[0] for option in question["options"]],
            "answer": question["answer"],
        }
        questions_data.append(question_data)

    return questions_data

def main(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    entities_with_context = extract_named_entities_with_context(text)

    # Save entities and sentences to a file
    entity_sentence_file = "entity_sentence.txt"
    save_entities_to_file(entity_sentence_file, entities_with_context)
    
    # Debugging: Log entities before passing to question generation
    logging.debug(f"main: Entities with context before question generation: {entities_with_context}")
    logging.debug(f"main: Length of entities_with_context before question generation: {len(entities_with_context)}")

    # Generate questions
    multiple_choice_questions = generate_multiple_choice_questions(entities_with_context)

    logging.info(f"main: Generated {len(multiple_choice_questions)} questions in total.")


    # Save questions to a file
    output_file = "generated_questions.txt"
    save_questions_to_file(output_file, multiple_choice_questions)
    logging.info(f"Questions have been saved to {output_file}")

    # Display questions and get score
    display_questions_and_get_score(multiple_choice_questions)

if __name__ == "__main__":
    # Get the PDF path from command line arguments
    #main("Module_01_Introduction_to_Computer_Organization_and_Architecture.pdf")
    #main("NCS.pdf")
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]  # The first argument is the PDF path
        main(pdf_path)
    else:
        logging.error("Please provide the path to the PDF file.")