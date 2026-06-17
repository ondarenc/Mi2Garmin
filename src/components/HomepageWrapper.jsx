import React, { useState } from 'react';
import { PlasmicHomepage } from './plasmic/mi_2_garmin/PlasmicHomepage';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export default function HomepageWrapper() {
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
    <div>
      <PlasmicHomepage
        overrides={{
          textbox2: {
            props: {
              onChange: handleFileChange,
              value: '',
            },
          },
          label: {
            render: () => (
              <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <span style={{ marginLeft: '8px' }}>
                  {fileName ? fileName : 'Upload CSV file'}
                </span>
              </label>
            ),
          },
          button: {
            render: () => (
              <button 
                onClick={result ? handleDownload : handleUpload}
                disabled={!file || uploading || converting}
                style={{
                  padding: '12px 24px',
                  backgroundColor: (!file || uploading || converting) ? '#ccc' : '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: (!file || uploading || converting) ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
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
            ),
          },
        }}
      />
      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      {error && (
        <div style={{ color: 'red', marginTop: '20px', textAlign: 'center' }}>
          {error}
        </div>
      )}
      {result && !uploading && (
        <div style={{ color: 'green', marginTop: '20px', textAlign: 'center' }}>
          <p>Successfully processed {result.files_count} files!</p>
        </div>
      )}
    </div>
  );
}
