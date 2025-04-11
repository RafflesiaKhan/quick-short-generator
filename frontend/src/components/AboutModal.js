import React from 'react';
import { FiX } from 'react-icons/fi';

const AboutModal = ({ onClose }) => {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="modal-close" onClick={onClose}>
          <FiX />
        </button>
        <h2>How to Use Video Generator</h2>
        <ol>
          <li>Upload 1-6 images by dragging them into the upload area or clicking to select files.</li>
          <li>For each image, provide a descriptive prompt that explains how you want the image to be animated.</li>
          <li>Select an API provider:
            <ul>
              <li>
                <a href="https://app.klingai.com" target="_blank" rel="noopener noreferrer">
                  Kling
                </a>: Requires both Access Key ID and Access Key Secret - Get your credentials from the{' '}
                <a href="https://klingai.com/global/dev" target="_blank" rel="noopener noreferrer">
                  Kling Dashboard
                </a>
              </li>
              <li>
                <a href="https://hailuoai.video/" target="_blank" rel="noopener noreferrer">
                  Minimax
                </a>: Requires both API Key and Group ID - Access your credentials in the{' '}
                <a href="https://www.minimax.io/platform/document/platform%20introduction?key=66701c8e1d57f38758d58198" target="_blank" rel="noopener noreferrer">
                  Minimax User Center
                </a>
              </li>
            </ul>
          </li>
          <li>Enter your API credentials based on the selected provider:
            <ul>
              <li>For Kling: Enter both your Access Key ID and Access Key Secret</li>
              <li>For Minimax: Enter your API Key and Group ID</li>
            </ul>
          </li>
          <li>Click "Generate Video" and wait for the process to complete.</li>
          <li>Once generated, you can download your video.</li>
        </ol>
        <p className="mt-3"><strong>Note:</strong> In Dev Mode, API credentials will be automatically loaded from environment variables.</p>
        
        <div className="mt-4">
          <h3>Additional Resources</h3>
          <ul>
            <li>
              <a href="https://klingai.com/global/dev" target="_blank" rel="noopener noreferrer">
                Kling API Documentation
              </a>
            </li>
            <li>
              <a href="https://www.minimax.io/platform/document/platform%20introduction?key=66701c8e1d57f38758d58198" target="_blank" rel="noopener noreferrer">
                Minimax API Documentation
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AboutModal; 