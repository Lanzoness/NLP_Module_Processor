import React, { useState } from 'react'
import './components_styles/score.css';

const ScoreCounter = ({ text = 'Score: 00/72' }) => {
    return (
        <div className="score-counter">
            {text}
        </div>
    );
};

export default ScoreCounter;

