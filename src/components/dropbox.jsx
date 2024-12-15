import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { saveAs } from 'file-saver';
import './components_styles/dropbox.css';

function Dropbox() {
    const [fileContent, setFileContent] = useState(null);

    const onDrop = useCallback((acceptedFiles) => {
        const reader = new FileReader();
        reader.onload = () => {
            const text = reader.result;
            setFileContent(text);

            // Create a Blob from the file content and save it
            const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
            saveAs(blob, acceptedFiles[0].name);
        };
        reader.readAsText(acceptedFiles[0]);
    }, []);

    const { getRootProps, getInputProps } = useDropzone({ onDrop });

    return (
        <div {...getRootProps()} className="dropbox">
            <input {...getInputProps()} />
            <p>Drag 'n' drop some files here, or click to select files</p>
            {fileContent && <div><h3>File Content:</h3><pre>{fileContent}</pre></div>}
        </div>
    );
}

export default Dropbox;