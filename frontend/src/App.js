import {
  PlasmicRootProvider,
  PageParamsProvider,
  PlasmicComponent
} from '@plasmicapp/loader-react';
import { BrowserRouter as Router, Routes, Route, useLocation, useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { PLASMIC } from './plasmic-init';

const API_URL = 'http://localhost:5000/api';

function AppRoot() {
  return (
    <PlasmicRootProvider loader={PLASMIC}>
      <Router>
        <Routes>
          <Route path="/" element={<CatchAllPage />} />
          <Route path="/about" element={<CatchAllPage />} />
        </Routes>
      </Router>
    </PlasmicRootProvider>
  );
}

export function CatchAllPage() {
  const [loading, setLoading] = useState(true);
  const [pageData, setPageData] = useState(null);
  const location = useLocation();
  const searchParams = useSearchParams();
  
  // GPX converter state
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

  useEffect(() => {
    async function load() {
      const pageData = await PLASMIC.maybeFetchComponentData(location.pathname);
      setPageData(pageData);
      setLoading(false);
    }
    load();
  }, [location.pathname]);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!pageData) {
    return <div>Not found</div>;
  }
  return (
    <PageParamsProvider route={location.pathname} query={Object.fromEntries(searchParams)}>
      <PlasmicComponent 
        component={location.pathname}
        props={{
          // Pass GPX converter functionality to Plasmic component
          onFileChange: handleFileChange,
          onUpload: handleUpload,
          onDownload: handleDownload,
          file: file,
          uploading: uploading,
          converting: converting,
          result: result,
          error: error
        }}
      />
    </PageParamsProvider>
  );
}

export default AppRoot;
