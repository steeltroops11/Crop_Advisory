import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  Typography,
  Paper,
  Alert,
  Chip,
  Tooltip,
  Stack,
  Card,
} from '@mui/material';
import { Send, ErrorOutlined } from '@mui/icons-material';
import axios from 'axios';

interface WeatherGateAssessment {
  district: string;
  rain_risk: 'none' | 'moderate' | 'high';
  wind_risk: 'safe' | 'advisory' | 'high_risk';
  irrigation_gate: string;
  fertilizer_gate: string;
  weather_summary_text?: string;
  weather_summary?: string;
  last_updated?: string; // Timestamp of when weather data was last updated
}

interface AdvisoryResponse {
  success: boolean;
  query: string;
  answer: string;
  detected_crop: 'paddy' | 'wheat' | null;
  language_used: string;
  district: string;
  confidence: 'high' | 'medium' | 'low' | 'fallback';
  sources: string[];
  weather_gate?: WeatherGateAssessment;
}

const API_BASE_URL = 'http://localhost:8000';

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [district, setDistrict] = useState<string>('Ludhiana');
  const [language, setLanguage] = useState<string>('auto');
  const [cropHint, setCropHint] = useState<'paddy' | 'wheat' | undefined>(undefined);
  const [response, setResponse] = useState<AdvisoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [weather, setWeather] = useState<WeatherGateAssessment | null>(null);
  const [weatherLoading, setWeatherLoading] = useState<boolean>(false);
  const [history, setHistory] = useState<Array<{ query: string; response: AdvisoryResponse; timestamp: number }>>([]);

  const languageOptions = [
    { value: 'auto', label: 'Auto-detect' },
    { value: 'english', label: 'English' },
    { value: 'hindi', label: 'Hindi' },
    { value: 'punjabi', label: 'Punjabi' },
  ];

  const districtOptions = [
    'Ludhiana', 'Amritsar', 'Jalandhar', 'Bathinda', 'Patiala',
    'Sangrur', 'Firozpur', 'Gurdaspur', 'Hoshiarpur', 'Moga',
    'Muktsar', 'Mansa', 'Kapurthala', 'Fatehgarh Sahib', 'Rupnagar',
    'Fazilka', 'Tarn Taran', 'Barnala',
  ];

  const cropOptions = [
    { value: '', label: 'Auto-detect' },
    { value: 'paddy', label: 'Paddy (Rice)' },
    { value: 'wheat', label: 'Wheat' },
  ];

  const fetchWeather = async () => {
    setWeatherLoading(true);
    try {
      const resp = await axios.post(`${API_BASE_URL}/api/v1/weather`, null, {
        params: { district, crop: cropHint || undefined },
      });

      const data = resp.data as WeatherGateAssessment;
      setWeather({
        ...data,
        weather_summary_text: data.weather_summary_text ?? data.weather_summary ?? '',
        last_updated: new Date().toISOString(), // Store when we received the data
      });
    } catch (err) {
      console.warn('Could not fetch weather data:', err);
    } finally {
      setWeatherLoading(false);
    }
  };

  const submitQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const resp = await axios.post(`${API_BASE_URL}/api/v1/advisory`, {
        query,
        district,
        crop: cropHint,
        language,
        use_weather: true,
      });

      const advisoryResponse = resp.data as AdvisoryResponse;
      setResponse(advisoryResponse);

      setHistory((prev) => [
        {
          query,
          response: advisoryResponse,
          timestamp: Date.now(),
        },
        ...prev.slice(0, 4),
      ]);
    } catch (err: any) {
      const message = !err.response
        ? 'Backend service is unavailable. Please start the API server on localhost:8000.'
        : err.response?.data?.detail || 'Failed to get advice. Please try again.';

      setError(message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, [district, cropHint]);

  const clearForm = () => {
    setQuery('');
    setResponse(null);
    setError(null);
  };

  const getConfidenceColor = (confidence: AdvisoryResponse['confidence']) => {
    switch (confidence) {
      case 'high':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'error';
      case 'fallback':
        return 'info';
      default:
        return 'default';
    }
  };

  const getConfidenceLabel = (confidence: AdvisoryResponse['confidence']) => {
    switch (confidence) {
      case 'high':
        return 'High Confidence';
      case 'medium':
        return 'Medium Confidence';
      case 'low':
        return 'Low Confidence';
      case 'fallback':
        return 'Based on General Knowledge';
      default:
        return confidence;
    }
  };

  const truncateText = (text: string, maxLength: number): string => {
    if (!text || text.length <= maxLength) return text;
    // Try to break at a space near the limit
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    // If we found a space and it's not too far back, use it
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...';
    }
    return truncated + '...';
  };

  const getCropBadge = (crop: AdvisoryResponse['detected_crop'] | null) => {
    if (!crop) return <Chip label="Not detected" color="default" />;
    return (
      <Chip
        label={crop === 'paddy' ? 'Paddy (Chaval)' : 'Wheat (Gehun)'}
        color={crop === 'paddy' ? 'success' : 'info'}
      />
    );
  };

  // Helper function to get color based on gate status
  const getGateColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'none':
      case 'safe':
        return 'success'; // green
      case 'moderate':
      case 'advisory':
        return 'warning'; // amber
      case 'high':
      case 'high_risk':
        return 'error'; // red
      default:
        return 'info';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 }, px: { xs: 1.5, md: 3 } }} className="kisan-shell">
      <Box className="dashboard-frame">
        <Stack spacing={4}>
          {/* Section 1: Hero/header */}
          <Card elevation={3} sx={{ p: 4 }}>
            <Box className="hero-block">
              <Box className="hero-copy">
                <Typography variant="overline" className="eyebrow">
                  Built for modern Punjab farming
                </Typography>
                <Typography variant="h3" className="app-title">
                  AI agronomy cockpit for
                  <span>stronger harvests.</span>
                </Typography>
                <Typography variant="subtitle1" className="app-subtitle">
                  Ask in English, Hindi, or Punjabi and receive practical field advice powered by local weather, PAU agronomic principles, and district-level crop intelligence.
                </Typography>
                <Box className="cta-row">
                  <Button
                    variant="contained"
                    className="primary-action"
                    onClick={() => document.getElementById('query-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                  >
                    Ask advisor
                  </Button>
                  <Chip label="Live guidance" className="soft-pill" size="small" />
                </Box>
              </Box>
            </Box>
          </Card>

          {/* Section 2: Field snapshot (District, Crop selectors) */}
          <Card elevation={3} sx={{ p: 4 }}>
            <Box className="hero-panel">
              <Typography variant="subtitle2" className="panel-kicker">
                Field snapshot
              </Typography>
              <Box className="mini-metric-row">
                <Box className="mini-stat-box">
                  <Typography variant="caption" className="mini-label">District</Typography>
                  <Typography variant="h6" className="mini-value">{district}</Typography>
                </Box>
                <Box className="mini-stat-box">
                  <Typography variant="caption" className="mini-label">Crop</Typography>
                  <Typography variant="h6" className="mini-value">{cropHint ?? 'Auto'}</Typography>
                </Box>
              </Box>
              <Box className="mini-badges">
                <Chip label="Live weather" size="small" className="soft-pill" />
                <Chip label="PAU reference" size="small" className="soft-pill" />
              </Box>
            </Box>
          </Card>

          {/* Section 3: Coverage stats */}
          <Card elevation={3} sx={{ p: 4 }}>
            <Box className="stats-grid">
              <Box className="stat-card">
                <Typography variant="overline" className="stat-label">Coverage</Typography>
                <Typography variant="h5" className="stat-value">18 districts</Typography>
              </Box>
              <Box className="stat-card">
                <Typography variant="overline" className="stat-label">Crop support</Typography>
                <Typography variant="h5" className="stat-value">Paddy + Wheat</Typography>
              </Box>
              <Box className="stat-card">
                <Typography variant="overline" className="stat-label">Response mode</Typography>
                <Typography variant="h5" className="stat-value">AI + weather</Typography>
              </Box>
            </Box>
          </Card>

          {/* Section 4: "Ask your crop question" form */}
          <Card elevation={3} sx={{ p: 4 }} id="query-panel">
            <Box className="card-header-row">
              <Typography variant="h5" className="section-title">
                Ask your crop question
              </Typography>
              <Chip label="Live advisory" size="small" className="live-chip" />
            </Box>

            <Box component="form" onSubmit={submitQuery} className="query-form">
              <Box sx={{ flex: 2, minWidth: 0 }}>
                <TextField
                  label="Your question"
                  placeholder="Example: Paddy me urea kab daalein?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  fullWidth
                  margin="dense"
                  slotProps={{
                    inputLabel: { shrink: true },
                  }}
                  className="query-input"
                />
              </Box>

              <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
                <Box className="field-box field-small">
                  <Select value={language} onChange={(e) => setLanguage(String(e.target.value))} fullWidth>
                    {languageOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </Box>

                <Box className="field-box field-small">
                  <Select value={district} onChange={(e) => setDistrict(e.target.value as string)} fullWidth>
                    {districtOptions.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </Box>

                <Box className="field-box field-small">
                  <Select
                    value={cropHint ?? ''}
                    onChange={(e) => setCropHint(e.target.value ? (e.target.value as 'paddy' | 'wheat') : undefined)}
                    fullWidth
                  >
                    {cropOptions.map((option) => (
                      <MenuItem key={option.value || 'auto'} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </Box>
              </Box>

              <Box sx={{ flex: 0, display: 'flex', alignItems: 'end' }}>
                <Button
                  variant="contained"
                  color="primary"
                  type="submit"
                  startIcon={<Send fontSize="inherit" />}
                  disabled={loading || !query.trim()}
                  className="submit-button"
                  sx={{ minWidth: 160, marginLeft: 2 }}
                >
                  {loading ? 'Getting answer...' : 'Get advice'}
                </Button>
              </Box>
            </Box>
          </Card>

          {/* Section 5: "Weather and PAU gate" results panel */}
          {weatherLoading ? (
            <Card elevation={3} sx={{ p: 4 }}>
              <Box className="panel-header">
                <Typography variant="h6" className="section-title compact">
                  🌤️ Weather and PAU gate
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Updating...
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Fetching latest weather data...
                </Typography>
              </Box>
            </Card>
          ) : weather && (
            <Card elevation={3} sx={{ p: 4, bgcolor: '#f0f9ff' }}>
              <Box className="panel-header">
                <Typography variant="h6" className="section-title compact">
                  🌤️ Weather and PAU gate
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Last updated: {weather.last_updated ? new Date(weather.last_updated).toLocaleTimeString() : 'Just now'}
                </Typography>
              </Box>

              <Typography variant="body2" className="weather-text" sx={{ fontFamily: 'inherit', whiteSpace: 'pre-line' }}>
                {weather.weather_summary_text || weather.weather_summary || 'Weather summary unavailable.'}
              </Typography>

              {/* Weather Gate Recommendations */}
              <Box className="gate-recommendations" sx={{ mt: 2, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Box className="gate-item" sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                    Irrigation Advice:
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize', fontSize: '1.1rem' }}>
                    {weather.irrigation_gate}
                  </Typography>
                </Box>
                <Box className="gate-item" sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                    Fertilizer Advice:
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize', fontSize: '1.1rem' }}>
                    {weather.fertilizer_gate}
                  </Typography>
                </Box>
                <Box className="gate-item" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                    Rain Risk Level:
                  </Typography>
                  <Typography variant="body2" sx={{
                    fontWeight: 600,
                    textTransform: 'capitalize',
                    color: getGateColor(weather.rain_risk),
                    fontSize: '1.1rem'
                  }}>
                    {weather.rain_risk}
                  </Typography>
                </Box>
              </Box>
            </Card>
          )}

          {/* Section 6: "Live field overview" status panel */}
          <Card elevation={3} sx={{ p: 4 }}>
            <Box className="snapshot-card">
              <Typography variant="h6" className="section-title compact">
                Live field overview
              </Typography>
              <Box className="snapshot-list">
                <Box className="snapshot-row">
                  <span>District</span>
                  <strong>{district}</strong>
                </Box>
                <Box className="snapshot-row">
                  <span>Crop focus</span>
                  <strong>{cropHint ? cropHint.toUpperCase() : 'AUTO'}</strong>
                </Box>
                <Box className="snapshot-row">
                  <span>Language</span>
                  <strong>{language}</strong>
                </Box>
                <Box className="snapshot-row">
                  <span>Weather gate</span>
                  <strong>{weather?.rain_risk ?? 'Awaiting'}</strong>
                </Box>
              </Box>
              <Box className="mini-badges compact-gap">
                <Chip label="PAU data" size="small" className="soft-pill" />
                <Chip label="Verified" size="small" className="soft-pill" />
              </Box>
            </Box>
          </Card>

          {/* Error alert (if any) */}
          {error && (
            <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
              <ErrorOutlined fontSize="inherit" />
              {error}
            </Alert>
          )}

          {/* Advisory result panel */}
          {response && (
            <Card elevation={3} sx={{ p: 4 }}>
              <Box className="panel-header panel-header-wrap">
                <Typography variant="h6" className="section-title compact">
                  📜 Advisory result
                </Typography>
                <Box className="badges-wrap">
                  <Tooltip title="Confidence level">
                    <Chip
                      label={getConfidenceLabel(response.confidence)}
                      color={getConfidenceColor(response.confidence)}
                      size="small"
                    />
                  </Tooltip>
                  {getCropBadge(response.detected_crop)}
                  <Tooltip title="Source documents">
                    <Chip label={`Sources: ${response.sources.length}`} color="default" size="small" />
                  </Tooltip>
                </Box>
              </Box>

              {/* Advice Card - Made more prominent */}
              <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="body1" className="advice-text" sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
                  {response.answer}
                </Typography>
              </Box>

              {response.sources.length > 0 && (
                <Box className="source-box">
                  <Typography variant="subtitle2" className="source-title">
                    📚 Reference sources
                  </Typography>
                  <Box className="chip-row" sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {response.sources.map((source, index) => (
                      <Chip key={index} label={source} size="small" color="info" />
                    ))}
                  </Box>
                </Box>
              )}
            </Card>
          )}

          {/* History panel */}
          {history.length > 0 && (
            <Card elevation={3} sx={{ p: 4 }}>
              <Box className="history-panel">
                <Box className="panel-header">
                  <Typography variant="h6" className="section-title compact">
                    🕘 Recent queries
                  </Typography>
                  <Button variant="text" size="small" onClick={clearForm} className="minor-button">
                    Clear
                  </Button>
                </Box>

                <Box className="history-list">
                  {history.map((item, index) => (
                    <Paper key={index} elevation={1} className="history-item">
                      <Box className="history-head">
                        <Typography variant="body2" className="history-query">
                          {truncateText(item.query, 50)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>

                      <Typography variant="body2" className="history-answer">
                        {truncateText(item.response.answer, 100)}
                      </Typography>

                      <Box className="chip-row compact-row">
                        <Tooltip title="Confidence">
                          <Chip
                            label={item.response.confidence.toUpperCase()}
                            color={getConfidenceColor(item.response.confidence)}
                            size="small"
                          />
                        </Tooltip>
                        {getCropBadge(item.response.detected_crop)}
                      </Box>
                    </Paper>
                  ))}
                </Box>
              </Box>
            </Card>
          )}
        </Stack>
      </Box>
    </Container>
  );
};

export default App;
