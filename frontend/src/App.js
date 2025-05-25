import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true);
      fetchAnalyses();
    }
  }, [token]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isRegistering ? '/api/register' : '/api/login';
      const response = await axios.post(`${BACKEND_URL}${endpoint}`, {
        username,
        password
      });

      const newToken = response.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      setIsAuthenticated(true);
      setUsername('');
      setPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setAnalysisResult(null);
    setAnalyses([]);
    setSelectedFile(null);
    setPreview(null);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const analyzeImage = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${BACKEND_URL}/api/analyze-currency`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      setAnalysisResult(response.data);
      fetchAnalyses(); // Refresh the list
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fetchAnalyses = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/analysis`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setAnalyses(response.data.analyses);
    } catch (err) {
      console.error('Failed to fetch analyses:', err);
    }
  };

  const renderCurrencyResults = (result, provider) => {
    if (!result) return null;

    if (result.error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="font-semibold text-red-800 mb-2">{provider} Error:</h4>
          <p className="text-red-600">{result.error}</p>
        </div>
      );
    }

    const currencies = result.currencies_detected || [];
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
          <span className="w-3 h-3 rounded-full mr-2" 
                style={{backgroundColor: provider.includes('OpenAI') ? '#10B981' : '#3B82F6'}}></span>
          {provider}
        </h4>
        
        {currencies.length > 0 ? (
          <div className="space-y-2">
            {currencies.map((currency, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <span className="font-medium text-lg">{currency.currency_type}</span>
                  <span className="ml-2 text-gray-600">×{currency.quantity}</span>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold">{currency.denomination}</div>
                  <span className={`text-xs px-2 py-1 rounded ${
                    currency.confidence === 'high' ? 'bg-green-100 text-green-800' :
                    currency.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {currency.confidence} confidence
                  </span>
                </div>
              </div>
            ))}
            
            {result.total_value && (
              <div className="mt-3 p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                <strong>Total Value: {result.total_value}</strong>
              </div>
            )}
            
            {result.notes && (
              <div className="mt-2 text-sm text-gray-600 italic">
                Notes: {result.notes}
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-500 italic">
            {result.raw_response ? (
              <div>
                <p className="mb-2">Raw AI Response:</p>
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {typeof result.raw_response === 'string' ? result.raw_response : JSON.stringify(result.raw_response, null, 2)}
                </pre>
              </div>
            ) : (
              'No currencies detected'
            )}
          </div>
        )}
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">💰 Currency AI</h1>
            <p className="text-gray-600">AI-powered currency recognition</p>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Please wait...' : (isRegistering ? 'Sign Up' : 'Sign In')}
            </button>

            <button
              type="button"
              onClick={() => setIsRegistering(!isRegistering)}
              className="w-full text-blue-600 hover:text-blue-700 text-sm"
            >
              {isRegistering ? 'Already have an account? Sign in' : 'Need an account? Sign up'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">💰 Currency AI Recognition</h1>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload Currency Image</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="fileInput"
                />
                <label htmlFor="fileInput" className="cursor-pointer">
                  <div className="text-gray-500 mb-2">
                    📷 Click to select an image
                  </div>
                  <div className="text-sm text-gray-400">
                    Supports: JPG, PNG, WEBP
                  </div>
                </label>
              </div>

              {selectedFile && (
                <div className="mt-4">
                  <p className="text-sm text-gray-600 mb-2">Selected: {selectedFile.name}</p>
                  <button
                    onClick={analyzeImage}
                    disabled={isAnalyzing}
                    className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-medium"
                  >
                    {isAnalyzing ? '🔄 Analyzing with AI...' : '🚀 Analyze Currency'}
                  </button>
                </div>
              )}
            </div>

            {preview && (
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Preview:</h3>
                <img 
                  src={preview} 
                  alt="Preview" 
                  className="w-full h-64 object-contain bg-gray-100 rounded-lg"
                />
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}
        </div>

        {/* Analysis Results */}
        {analysisResult && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">
              🤖 AI Analysis Results
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {renderCurrencyResults(analysisResult.openai_result, "OpenAI GPT-4o-mini")}
              {renderCurrencyResults(analysisResult.gemini_result, "Google Gemini 2.0 Flash")}
            </div>

            {/* Combined Analysis */}
            {analysisResult.combined_analysis && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-semibold text-blue-800 mb-2">🔍 AI Comparison Summary</h3>
                <div className="text-sm text-blue-700">
                  <p><strong>Analysis ID:</strong> {analysisResult.analysis_id}</p>
                  <p><strong>Timestamp:</strong> {new Date(analysisResult.timestamp).toLocaleString()}</p>
                  {analysisResult.combined_analysis.discrepancies && analysisResult.combined_analysis.discrepancies.length > 0 && (
                    <div className="mt-2">
                      <strong>Discrepancies:</strong>
                      <ul className="list-disc list-inside ml-2">
                        {analysisResult.combined_analysis.discrepancies.map((disc, idx) => (
                          <li key={idx}>{disc}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recent Analyses */}
        {analyses.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">📊 Recent Analyses</h2>
            <div className="space-y-3">
              {analyses.slice(0, 5).map((analysis) => (
                <div key={analysis.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-800">{analysis.filename || 'Unknown file'}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(analysis.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      ID: {analysis.id.substring(0, 8)}...
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
          <h3 className="font-semibold text-blue-800 mb-2">🎯 Supported Currencies</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="text-blue-700">
              <strong>🇺🇦 UAH</strong> - Ukrainian Hryvnia
            </div>
            <div className="text-blue-700">
              <strong>🇺🇸 USD</strong> - US Dollar  
            </div>
            <div className="text-blue-700">
              <strong>🇪🇺 EUR</strong> - Euro
            </div>
          </div>
          <p className="text-xs text-blue-600 mt-3">
            This app uses dual AI analysis with OpenAI GPT-4o-mini and Google Gemini 2.0 Flash for enhanced accuracy.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
