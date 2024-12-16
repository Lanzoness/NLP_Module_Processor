import React from 'react'
import ReactDOM from 'react-dom/client'
import Dropbox from './components/dropbox.jsx'
import LongBtn from './components/long-btn.jsx'

ReactDOM.createRoot(document.getElementById('dropbox-container')).render(
  <React.StrictMode>
    <Dropbox />
  </React.StrictMode>
)

ReactDOM.createRoot(document.getElementById('long-btn')).render(
  <React.StrictMode>
    <LongBtn />
  </React.StrictMode>
)
