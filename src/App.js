import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [converting, setConverting] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    } else {
      setError('Please select a CSV file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setSessionId(response.data.session_id);
      setUploading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Error uploading file');
      setUploading(false);
    }
  };

  const handleDownload = async () => {
    if (!sessionId) return;

    setConverting(true);
    try {
      const response = await axios.get(`${API_URL}/download/${sessionId}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'garmin_gpx_files.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      setConverting(false);
    } catch (err) {
      setError('Error downloading files');
      setConverting(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <div className="header">
          <h1>Mi Fitness to Garmin Converter</h1>
        </div>

        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              type="file"
              id="file-input"
              accept=".csv"
              onChange={handleFileChange}
            />
            <label htmlFor="file-input" className="file-label">
              {file ? file.name : 'Upload CSV file'}
            </label>
          </div>

          <button
            onClick={result ? handleDownload : handleUpload}
            disabled={!file || uploading || converting}
            className={`action-button ${(!file || uploading || converting) ? 'disabled' : ''}`}
          >
            {uploading ? 'Processing...' : (result ? 'Download ZIP' : 'Convert to Garmin')}
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {result && !uploading && (
          <div className="success-message">
            <p>Successfully processed {result.files_count} files!</p>
          </div>
        )}

        <div className="instructions">
          <h2>Instructions:</h2>
          <ol>
            <li>Upload a CSV file containing GPX file URLs in the 'GPX' column</li>
            <li>The system will automatically download all GPX files</li>
            <li>Each file is converted to Garmin-compatible format with continuous timestamps</li>
            <li>Download the ZIP file containing all converted GPX files</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;
