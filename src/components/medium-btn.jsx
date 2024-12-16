import React from 'react';
import './components_styles/medium-btn.css';

const MediumBtn = ({text = 'button text'}) => {
    const handleClick = () => {
        window.location.replace('/index.html');
    };
  
    return (
        <button className="medium-btn" onClick={handleClick}>
            {text}
        </button>
    );
}

export default MediumBtn;
