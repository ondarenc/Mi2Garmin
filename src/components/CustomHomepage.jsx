import React, { useState } from 'react';
import axios from 'axios';
import './CustomHomepage.css';

const API_URL = 'http://localhost:5000/api';

export default function CustomHomepage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [converting, setConverting] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError(null);
      setResult(null);
    } else {
      setError('Please select a CSV file');
      setFile(null);
      setFileName('');
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
    <div className="custom-homepage">
      <div className="container">
        <div className="header">
          <div className="icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
            </svg>
          </div>
          <h1>Mi Fitness to Garmin Converter</h1>
        </div>

        <div className="content">
          <div className="prerequisites">
            <h3>Prerequisites</h3>
            <p>
              You already request Xiaomi a download of your fitness history by logging into your Xiaomi cloud account via a web browser.
              You already have you located the file that contains the links (usually named XXXXXX_sport_track_data.csv)
            </p>
          </div>

          <div className="upload-section">
            <div className="file-input-wrapper">
              <input
                type="file"
                id="file-input"
                accept=".csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="file-label">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <span>{fileName || 'Upload CSV file'}</span>
              </label>
            </div>

            <button
              onClick={result ? handleDownload : handleUpload}
              disabled={!file || uploading || converting}
              className={`action-button ${(!file || uploading || converting) ? 'disabled' : ''}`}
            >
              {uploading ? (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spin">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                  </svg>
                  Processing...
                </>
              ) : result ? (
                'Download ZIP'
              ) : (
                'Convert to Garmin'
              )}
            </button>
          </div>

          <div className="instructions">
            <h3>Instructions:</h3>
            <ul>
              <li>Upload a CSV file containing GPX file URLs in the 'GPX' column</li>
              <li>The system will automatically download all GPX files</li>
              <li>Each file is converted to Garmin-compatible format with continuous timestamps</li>
              <li>Download the ZIP file containing all converted GPX files</li>
            </ul>
          </div>

          <div className="about-section">
            <h3>Why this application?</h3>
            <p>
              My wife had a Mi Smartband and tracked her activities there. Then she switched to Garmin and wanted to transfer her workouts there.
              The first step is to ask Xiaomi to send you the data history that you download in CSV format.
              The problem: this format is not compatible with Garmin and all the solutions found in the market, sync apps or anything that could transfer to Garmin is not seamless or just not possible.
              But, into the CSV Mi files, there is one, usually named XXXXXX_sport_track_data that contains the links to every activity in GPX format.
              So, I decided to create this app that can track the CSV file, download every GPX, convert it to Garmin compatible and finally download a ZIP file with all the workouts.
            </p>
          </div>
        </div>
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
    </div>
  );
}
