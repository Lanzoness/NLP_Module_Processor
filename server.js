import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import multer from 'multer';

// Get the current filename
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 5137; // You can choose any available port

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
        res.json({ message: 'File path received and script executed', output: stdout });
    });
});

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'src')));

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});