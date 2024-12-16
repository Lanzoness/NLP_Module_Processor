import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import multer from 'multer';
import fs from 'fs';

// Get the current filename
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 5137; // Set the port to 5137

app.use(cors());
app.use(bodyParser.json());

// Set up multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/'); // Specify the directory to save uploaded files
    },
    filename: (req, file, cb) => {
        cb(null, file.originalname); // Use the original file name
    }
});

const upload = multer({ storage });

// Endpoint to handle file upload
app.post('/upload', upload.single('pdfFile'), (req, res) => {
    const pdfPath = req.file.path; // Get the path of the uploaded file
    console.log('Received PDF path:', pdfPath);

    // Construct the command to run the Python script
    const command = `python testpy.py "${pdfPath}"`; // Adjust the command if necessary

    // Execute the Python script
    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing script: ${error.message}`);
            console.error(`stderr: ${stderr}`);
            return res.status(500).json({ error: 'Error executing script', details: stderr });
        }
        console.log(`Script output: ${stdout}`);
        
        // Ensure the latest questions are read
        const questionsFilePath = path.join(__dirname, 'generated_questions.txt');
        fs.readFile(questionsFilePath, 'utf8', (err, data) => {
            if (err) {
                console.error('Error reading questions file:', err);
                return res.status(500).json({ error: 'Error reading questions file' });
            }

            // Parse the questions from the file and send them as JSON
            const questions = parseQuestions(data);
            res.json({ message: 'File path received and script executed', questions });
        });
    });
});

// Add this endpoint to handle the request for questions
app.get('/questions', (req, res) => {
    // Read the generated questions from the file
    const questionsFilePath = path.join(__dirname, 'generated_questions.txt');
    fs.readFile(questionsFilePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading questions file:', err);
            return res.status(500).json({ error: 'Error reading questions file' });
        }

        // Parse the questions from the file and send them as JSON
        const questions = parseQuestions(data);
        res.json(questions);
    });
});

// Helper function to parse questions from the file
function parseQuestions(data) {
    const questions = [];
    const questionBlocks = data.split('----------------------------').filter(block => block.trim());

    questionBlocks.forEach(block => {
        const lines = block.trim().split('\n');
        const questionLine = lines[0];
        const options = lines.slice(2, -1).map(line => line.split('. ')[1]).filter(option => option);
        const answerLine = lines[lines.length - 1];
        const answerMatch = answerLine.match(/\(Answer: (.+)\)/);
        const answer = answerMatch ? answerMatch[1] : null;

        if (questionLine && options.length === 4 && answer) {
            questions.push({
                question: questionLine.split('. ')[1],
                options,
                answer
            });
        }
    });

    return questions;
}

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'src')));

// Start the server on localhost:5137
app.listen(PORT, 'localhost', () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});