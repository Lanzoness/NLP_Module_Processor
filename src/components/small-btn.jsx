import React from 'react';
import './components_styles/small-btn.css'

const SmallBrn = ({ text = "button text" }) => {
    const handleClick = () => {
        window.location.replace('/index.html');
    };
  
    return (
        <button className="small-btn" onClick={handleClick}>
            {text}
        </button>
    );
};
  
  export default SmallBrn;