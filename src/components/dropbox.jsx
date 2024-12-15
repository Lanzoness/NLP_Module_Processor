import React, {useCallback} from 'react'
import {useDropzone} from 'react-dropzone'
import './components_styles/dropbox.css'

 
function Dropbox() {
  // callback function that recieves the accepted files  


  const onDrop = useCallback(acceptedFiles => {
    console.log(acceptedFiles)
  }, [])
   
// react hook components with the onDrop callback function called 
  const {getRootProps, getInputProps, isDragActive} = useDropzone({onDrop})

  return (
    // drag and drop functionality
    <div className='dropbox' {...getRootProps()}>
    {/* container for the input drag and drop functionality */}
      <input {...getInputProps()} />
      {        
        isDragActive ?
          <p>Supported file types: .pdf</p>:
          <p>Drag and drop a file or browse a file
            <br/>
          <p>Supported file types: .pdf</p>
          </p> 
      }
    </div>
  )
}


export default Dropbox;