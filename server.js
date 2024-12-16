import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the current filename
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 5137; // You can choose any available port

app.use(cors());
app.use(bodyParser.json());

// Endpoint to handle file upload
app.post('/upload', (req, res) => {
    const { pdfPath } = req.body;
    console.log('Received PDF path:', pdfPath);
    res.json({ message: 'File path received' }); // Send a JSON response
});

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'src')));

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});