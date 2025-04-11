import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { FiUpload, FiCheck, FiPlay, FiTrash, FiDownload, FiX } from 'react-icons/fi';
import backgroundImage from './assets/background_2.png';
import AboutModal from './components/AboutModal';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  // Add console log to check environment variables
  // console.log('Environment Variables:', {
  //   devMode: process.env.REACT_APP_DEV_MODE,
  //   klingKey: process.env.REACT_APP_KLING_API_KEY,
  //   minmaxKey: process.env.REACT_APP_MINMAX_API_KEY,
  //   minmaxGroupId: process.env.REACT_APP_MINMAX_GROUP_ID,
  // });

  const [images, setImages] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState(null);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [apiProviders, setApiProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [accessKeyId, setAccessKeyId] = useState('');
  const [accessKeySecret, setAccessKeySecret] = useState('');
  const [groupId, setGroupId] = useState('');
  const [isDevMode, setIsDevMode] = useState(process.env.REACT_APP_DEV_MODE === 'true');
  const videoRef = useRef(null);

  // Effect to handle dev mode credentials
  useEffect(() => {
    if (isDevMode && selectedProvider) {
      console.log('Setting dev credentials for provider:', selectedProvider);
      if (selectedProvider === 'kling') {
        setAccessKeyId(process.env.REACT_APP_KLING_ACCESS_KEY_ID || '');
        setAccessKeySecret(process.env.REACT_APP_KLING_ACCESS_KEY_SECRET || '');
        setApiKey(''); // Clear API key for Kling
        setGroupId(''); // Clear group ID
      } else if (selectedProvider === 'minmax') {
        setApiKey(process.env.REACT_APP_MINMAX_API_KEY || '');
        setGroupId(process.env.REACT_APP_MINMAX_GROUP_ID || '');
        setAccessKeyId(''); // Clear Kling credentials
        setAccessKeySecret('');
      }
    } else if (!isDevMode) {
      // Clear all credentials when dev mode is off
      setApiKey('');
      setAccessKeyId('');
      setAccessKeySecret('');
      setGroupId('');
    }
  }, [isDevMode, selectedProvider]);

  // Fetch available API providers
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await axios.get('/api-providers');
        const providers = response.data.providers;
        setApiProviders(providers);
        
        if (providers.length > 0) {
          const defaultProvider = providers[0].id;
          setSelectedProvider(defaultProvider);
        }
      } catch (error) {
        console.error('Error fetching API providers:', error);
        setError('Failed to fetch available API providers.');
      }
    };
    
    fetchProviders();
  }, []);

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length < 1 || acceptedFiles.length > 6) {
      setError(`Please upload between 1 and 6 images. You uploaded ${acceptedFiles.length}.`);
      return;
    }
    
    setError(null);
    
    // Create image previews and initialize prompts
    const newImages = acceptedFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setImages(newImages);
    setPrompts(new Array(newImages.length).fill(''));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif']
    },
    multiple: true
  });

  const handlePromptChange = (index, value) => {
    const newPrompts = [...prompts];
    newPrompts[index] = value;
    setPrompts(newPrompts);
  };

  const handleProviderChange = (event) => {
    const newProvider = event.target.value;
    console.log('Provider changed to:', newProvider);
    
    // First set the new provider
    setSelectedProvider(newProvider);
    
    // Reset credentials
    if (!isDevMode) {
      setApiKey('');
      setAccessKeyId('');
      setAccessKeySecret('');
      setGroupId('');
    }
    // Dev mode credentials will be handled by the useEffect
  };

  const toggleDevMode = () => {
    const newDevMode = !isDevMode;
    console.log('Toggling dev mode:', newDevMode);
    setIsDevMode(newDevMode);
    // Credentials will be handled by the useEffect
  };

  const handleGenerateVideo = async () => {
    // Validate input
    if (images.length < 1 || images.length > 6) {
      setError('Please upload between 1 and 6 images.');
      return;
    }
    
    if (prompts.some(prompt => !prompt.trim())) {
      setError('Please provide a prompt for each image.');
      return;
    }

    if (!selectedProvider) {
      setError('Please select an API provider.');
      return;
    }

    // Validate credentials based on provider
    if (selectedProvider === 'kling') {
      if (!accessKeyId || !accessKeySecret) {
        setError('Please provide both Access Key ID and Access Key Secret for Kling AI.');
        return;
      }
    } else if (selectedProvider === 'minmax') {
      if (!apiKey) {
        setError('Please provide an API key for Minimax.');
        return;
      }
      if (!groupId) {
        setError('Please provide a Group ID for Minimax API.');
        return;
      }
    }
    
    setError(null);
    setIsGenerating(true);
    setStatusMessage('Uploading images...');
    
    try {
      // Upload images
      const formData = new FormData();
      images.forEach(image => {
        formData.append('files', image.file);
      });
      
      await axios.post('/upload-images', formData);
      
      setStatusMessage(`Generating videos with ${apiProviders.find(p => p.id === selectedProvider)?.name}...`);
      
      // Generate video with API credentials
      const response = await axios.post('/generate-video', {
        prompts,
        provider: selectedProvider,
        apiKey: selectedProvider === 'kling' ? accessKeyId : apiKey,
        accessKeySecret: selectedProvider === 'kling' ? accessKeySecret : undefined,
        groupId: selectedProvider === 'minmax' ? groupId : undefined
      });
      
      const videoId = response.data.video_id;
      
      setStatusMessage('Processing video...');
      
      // Poll for video completion
      const checkVideoStatus = async () => {
        try {
          const videoUrl = `/video/${videoId}`;
          const response = await axios.head(videoUrl);
          
          if (response.status === 200) {
            setGeneratedVideo(videoUrl);
            setIsGenerating(false);
            setStatusMessage('');
          } else {
            setTimeout(checkVideoStatus, 5000);
          }
        } catch (error) {
          if (error.response && error.response.status !== 404) {
            setError('An error occurred while generating the video.');
            setIsGenerating(false);
            setStatusMessage('');
          } else {
            setTimeout(checkVideoStatus, 5000);
          }
        }
      };
      
      checkVideoStatus();
    } catch (error) {
      console.error('Error:', error);
      setError(error.response?.data?.detail || 'An error occurred while generating the video.');
      setIsGenerating(false);
      setStatusMessage('');
    }
  };

  const handleReset = () => {
    setImages([]);
    setPrompts([]);
    setGeneratedVideo(null);
    setError(null);
    setStatusMessage('');
    
    // Clean up object URLs to avoid memory leaks
    images.forEach(image => URL.revokeObjectURL(image.preview));
  };

  const handleDownload = () => {
    if (generatedVideo) {
      const link = document.createElement('a');
      link.href = generatedVideo;
      link.download = 'generated-video.mp4';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="app-wrapper" style={{
      backgroundImage: `url(${backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed'
    }}>
      <button className="about-button" onClick={() => setShowAboutModal(true)}>about</button>
      
      {/* Dev Mode Toggle */}
      <div className="dev-mode-toggle">
        <label className="switch">
          <input
            type="checkbox"
            checked={isDevMode}
            onChange={toggleDevMode}
          />
          <span className="slider round"></span>
        </label>
        <span className="dev-mode-label">Dev Mode</span>
      </div>

      {/* About Modal */}
      {showAboutModal && <AboutModal onClose={() => setShowAboutModal(false)} />}

      <div className="app-container">
        <h1>Video Generator with AI</h1>
        
        {error && <div className="alert alert-danger">{error}</div>}
        
        {!generatedVideo ? (
          <>
            {images.length === 0 ? (
              <div 
                {...getRootProps()} 
                className={`dropzone ${isDragActive ? 'active' : ''}`}
              >
                <input {...getInputProps()} />
                <FiUpload className="upload-icon" />
                <p>Drag & drop 1-6 images here, or click to select files</p>
              </div>
            ) : (
              <div className="content-container">
                <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
                  {images.map((image, index) => (
                    <div key={index} className="col">
                      <div className="image-input-container card h-100">
                        <div className="image-container card-img-top">
                          <img 
                            src={image.preview} 
                            alt={`Uploaded ${index + 1}`} 
                            className="preview-image" 
                          />
                          <div className="image-number">{index + 1}</div>
                        </div>
                        <div className="card-body">
                          <textarea
                            placeholder={`Enter prompt for image ${index + 1}...`}
                            value={prompts[index]}
                            onChange={(e) => handlePromptChange(index, e.target.value)}
                            className="form-control prompt-input"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="api-provider-selector mt-4">
                  <label htmlFor="api-provider" className="form-label">Select API Provider:</label>
                  <select 
                    id="api-provider" 
                    value={selectedProvider}
                    onChange={handleProviderChange}
                    disabled={isGenerating || apiProviders.length === 0}
                    className="form-select"
                  >
                    <option value="">Select a provider</option>
                    {apiProviders.map(provider => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>

                  {selectedProvider && (
                    <div className="api-credentials mt-3">
                      {selectedProvider === 'minmax' ? (
                        <>
                          <div className="mb-3">
                            <label htmlFor="minmaxApiKey" className="form-label">Minmax API Key:</label>
                            <input
                              type="password"
                              id="minmaxApiKey"
                              className="form-control"
                              value={apiKey}
                              onChange={(e) => setApiKey(e.target.value)}
                              placeholder="Enter your Minmax API key"
                              disabled={isDevMode}
                            />
                          </div>
                          <div className="mb-3">
                            <label htmlFor="groupId" className="form-label">Group ID:</label>
                            <input
                              type="password"
                              id="groupId"
                              className="form-control"
                              value={groupId}
                              onChange={(e) => setGroupId(e.target.value)}
                              placeholder="Enter your Minmax Group ID"
                              disabled={isDevMode}
                            />
                            {isDevMode && (
                              <small className="text-muted mt-1 d-block">
                                Using Group ID from environment variables
                              </small>
                            )}
                          </div>
                        </>
                      ) : selectedProvider === 'kling' ? (
                        <>
                          <div className="mb-3">
                            <label htmlFor="accessKeyId" className="form-label">Kling Access Key ID:</label>
                            <input
                              type="text"
                              id="accessKeyId"
                              className="form-control"
                              value={accessKeyId}
                              onChange={(e) => setAccessKeyId(e.target.value)}
                              placeholder="Enter your Kling Access Key ID"
                              disabled={isDevMode}
                            />
                          </div>
                          <div className="mb-3">
                            <label htmlFor="accessKeySecret" className="form-label">Kling Access Key Secret:</label>
                            <input
                              type="password"
                              id="accessKeySecret"
                              className="form-control"
                              value={accessKeySecret}
                              onChange={(e) => setAccessKeySecret(e.target.value)}
                              placeholder="Enter your Kling Access Key Secret"
                              disabled={isDevMode}
                            />
                            {isDevMode && (
                              <small className="text-muted mt-1 d-block">
                                Using Kling credentials from environment variables
                              </small>
                            )}
                          </div>
                        </>
                      ) : null}
                      
                      {isDevMode && (
                        <div className="alert alert-info">
                          Using credentials from environment variables in Dev Mode
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="buttons-container mt-4">
                  <button 
                    onClick={handleReset} 
                    className="btn btn-outline-secondary"
                    disabled={isGenerating}
                  >
                    <FiTrash /> Reset
                  </button>
                  <button 
                    onClick={handleGenerateVideo} 
                    className="btn btn-primary"
                    disabled={isGenerating || apiProviders.length === 0}
                  >
                    {isGenerating ? (
                      <>Generating... <div className="spinner"></div></>
                    ) : (
                      <><FiPlay /> Generate Video</>
                    )}
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="video-result-container">
            <video 
              ref={videoRef}
              src={generatedVideo}
              controls
              className="video-player"
            />
            <button 
              onClick={handleDownload}
              className="btn btn-success mt-3"
            >
              <FiDownload /> Download Video
            </button>
          </div>
        )}
        
        {statusMessage && (
          <div className="alert alert-info mt-3">
            {statusMessage}
          </div>
        )}
      </div>
      <div className="copyright">
        Copywrite@2024
      </div>
    </div>
  );
}

export default App; 