import React from 'react';
import './components_styles/long-btn.css'

const LongBtn = ({ text = "Start Reviewing" }) => {
    const handleClick = () => {
        //window.location.replace('/quizPage.html');
    };
  
    return (
        <button className="long-btn" onClick={handleClick}>
            {text}
        </button>
    );
};
  
  export default LongBtn;