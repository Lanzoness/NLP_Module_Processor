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

// At the top with other imports
let questionsCache = null; // Global variable to store questions

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

// Modified upload endpoint
app.post('/upload', upload.single('pdfFile'), async (req, res) => {
    try {
        // Clear cache immediately
        questionsCache = null;
        
        const pdfPath = req.file.path;
        console.log('Received PDF path:', pdfPath);

        // Run Python script using 'py' instead of 'python'
        await new Promise((resolve, reject) => {
            exec(`py testpy.py "${pdfPath}"`, (error, stdout, stderr) => {
                if (error) {
                    reject({ error, stderr });
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });

        // Ensure file is written before reading
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Read new questions
        const questionsFilePath = path.join(__dirname, 'generated_questions.txt');
        const data = await fs.promises.readFile(questionsFilePath, 'utf8');
        questionsCache = parseQuestions(data);
        
        res.json({ 
            message: 'File processed successfully', 
            questions: questionsCache,
            success: true 
        });
    } catch (error) {
        console.error('Error processing upload:', error);
        res.status(500).json({ error: 'Error processing upload', success: false });
    }
});

// Modified questions endpoint
app.get('/questions', async (req, res) => {
    try {
        if (!questionsCache) {
            const questionsFilePath = path.join(__dirname, 'generated_questions.txt');
            const data = await fs.promises.readFile(questionsFilePath, 'utf8');
            questionsCache = parseQuestions(data);
        }
        res.json(questionsCache);
    } catch (error) {
        console.error('Error fetching questions:', error);
        res.status(500).json({ error: 'Error fetching questions' });
    }
});

// Helper function to parse questions from the file
function parseQuestions(data) {
    const questions = [];
    const questionBlocks = data.split('----------------------------').filter(block => block.trim());

    questionBlocks.forEach(block => {
        const lines = block.trim().split('\n');
        
        // Find the index where options begin
        const optionsIndex = lines.findIndex(line => line.trim() === 'Options:');
        
        if (optionsIndex === -1) return; // Skip if no options found
        
        // Join all lines before "Options:" as the complete question
        const questionText = lines.slice(0, optionsIndex)
            .join(' ')
            .replace(/^\d+\.\s*/, '') // Remove question number
            .trim();
            
        // Get options and answer
        const options = lines.slice(optionsIndex + 1, -1)
            .map(line => line.split('. ')[1])
            .filter(option => option);
            
        const answerLine = lines[lines.length - 1];
        const answerMatch = answerLine.match(/\(Answer: (.+)\)/);
        const answer = answerMatch ? answerMatch[1] : null;

        if (questionText && options.length === 4 && answer) {
            questions.push({
                question: questionText,
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