import React from 'react'
import ReactDOM from 'react-dom/client'
import Dropbox from './components/dropbox.jsx'
import LongBtn from './components/long-btn.jsx'
import MediumBtn from './components/medium-btn.jsx'
import QuitBtn from './components/quit-button.jsx'

// Get the current page name from the URL
const currentPage = window.location.pathname.split('/').pop();

// Render components based on the current page
if (currentPage === 'resultsPage.html') {
    const buttonContainer = document.getElementById('medium-btn');
    const buttonText = buttonContainer.textContent;
    
    ReactDOM.createRoot(buttonContainer).render(
        <React.StrictMode>
            <MediumBtn text={buttonText} />
        </React.StrictMode>
    )
} else if (currentPage === 'index.html' || currentPage === '') {
    // Render other components for other pages
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
}else if (currentPage === 'QuizPage.html') {
    const buttonContainer = document.getElementById('quit-button');
    const buttonText = buttonContainer.textContent;

    ReactDOM.createRoot(buttonContainer).render(
        <React.StrictMode>
            <QuitBtn text={buttonText} />
        </React.StrictMode>
    )
}   

