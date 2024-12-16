/* uses the file reader API to read the file and display the file content  as a url 
* File reader API: https://developer.mozilla.org/en-US/docs/Web/API/FileReader  
* uses the dropzone library to handle the file upload 
* Dropzone: https://www.npmjs.com/package/react-dropzone || https://github.com/* react-dropzone/react-dropzone/
* uses the useState hook to manage the file name
*/
import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import './components_styles/dropbox.css'

function Dropbox() {
  const [fileName, setFileName] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    // Check if more than one file is being uploaded
    if (acceptedFiles.length > 1) {
      alert("maximum number of module that can be uploaded is 1");
      return;
    }

    const file = acceptedFiles[0];

    // Check if file is PDF
    if (file.type !== 'application/pdf') {
      alert("invalid file type!\nSupported file types: .pdf");
      return;
    }

    // If there's already a file, log replacement message
    if (fileName) {
      console.log(`file replaced to: ${file.name}`);
    }

    // Set the file name to display
    setFileName(file.name);

    // Create new FileReader instance
    const reader = new FileReader();

    // Set up FileReader events
    reader.onload = (e) => {
      // Log the file content (uses the file reader API)
      console.log('File content:', e.target.result);
      if (!fileName) {
        console.log(`file uploaded successfully\nFile Name: ${file.name}`);
      }
    };
    // error handling 
    reader.onerror = (error) => {
      console.error('Error reading file:', error);
    };

    // Read the file as DataURL
    reader.readAsDataURL(file);
    
  }, []) // Remove fileName from dependencies

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']  // limits the file type to .pdf
    },
    maxFiles: 1  // file limit upload: 1 pdf
  })

  return (
    // two styles: one for default and w/ an uploaded file
    <div className={`dropbox ${fileName ? 'dropbox-with-file' : ''}`} {...getRootProps()}>
       {/* ...getRootProps() takes the uploaded file and passes it to  the div  */}
      <input {...getInputProps()} />
      {/* getInputProps() : takes the file input props and passes them to the input element */}
      {
        fileName ? (
          <p>Uploaded Module: <br />{fileName}
           <br />
           <br /> 
           <span className="replace-msg">Drag or drop a different file to replace the uploaded module</span>
          </p>
        ) : (
          isDragActive ? (
            <p>Supported file type: .pdf</p>
          ) : (
            <p>
              Drag and drop a file or browse a file
              <br />
              <p>Supported file type: .pdf</p>
            </p>
          )
        )
      }
    </div>
  )
}

export default Dropbox;