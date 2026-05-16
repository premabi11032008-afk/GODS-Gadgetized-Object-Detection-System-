import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import PotholeMap from '../components/PotholeMap';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [hazardWarning, setHazardWarning] = useState(null);
  const [showHazardPopup, setShowHazardPopup] = useState(false);
  const [lastDismissedAt, setLastDismissedAt] = useState(0);
  const navigate = useNavigate();

  // New states for feature additions
  const [mode, setMode] = useState('analysis'); // 'analysis' or 'drive'
  const [videoKey, setVideoKey] = useState(Date.now());
  const lastPotholeReportedAt = useRef(0);
  
  const [hazardData, setHazardData] = useState({
    distance: null,
    risk_score: 0,
    latest_log: "Awaiting feed..."
  });
  const [activityLogs, setActivityLogs] = useState([]);

  useEffect(() => {
    // Check auth status
    const checkAuth = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/status`, { withCredentials: true });
        if (!res.data.logged_in) {
          navigate('/login');
        }
      } catch (err) {
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, [navigate]);

  useEffect(() => {
    let intervalId;
    
    const checkHazard = async () => {
      // Don't poll if popup is already showing
      if (showHazardPopup) return;
      
      try {
        const res = await axios.get(`${API_URL}/api/hazard`);
        const data = res.data;
        
        setHazardData({
          distance: data.distance,
          risk_score: data.risk_score,
          latest_log: data.latest_log,
          hazard_action: data.hazard_action,
          hazard: data.hazard
        });

        // 🚨 Pothole Reporting Logic 🚨
        if (data.pothole_detected) {
          const now = Date.now();
          // 15 second cooldown so we don't spam the CSV for the same pothole
          if (now - lastPotholeReportedAt.current > 15000) {
            lastPotholeReportedAt.current = now;
            
            if ("geolocation" in navigator) {
              navigator.geolocation.getCurrentPosition(
                async (position) => {
                  try {
                    await axios.post(`${API_URL}/api/potholes`, {
                      lat: position.coords.latitude,
                      lng: position.coords.longitude
                    });
                    console.log("Pothole reported to backend CSV!");
                  } catch (e) {
                    console.error("Failed to post pothole", e);
                  }
                },
                (error) => console.error("Error getting location", error),
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
              );
            }
          }
        }

        setActivityLogs(prev => {
          if (!data.latest_log) return prev;
          if (prev.length === 0 || prev[0].log !== data.latest_log) {
            return [{ time: new Date().toLocaleTimeString('en-US', { hour12: false }), log: data.latest_log }, ...prev].slice(0, 5);
          }
          return prev;
        });

        if (data.hazard && !showHazardPopup && mode !== 'drive') {
          // Smart cooldown based on risk score
          const riskScore = data.risk_score || 50;
          let cooldownMs = 10000;
          if (riskScore > 90) cooldownMs = 3000;
          else if (riskScore > 75) cooldownMs = 6000;
          
          if (Date.now() - lastDismissedAt < cooldownMs) return;

          // Instead of API call, use local warnings for zero latency
          if (!hazardWarning) {
            if (data.hazard_action === 'slow_down') {
              setHazardWarning("ROAD DAMAGE AHEAD. SLOW DOWN.");
            } else {
              setHazardWarning("OBJECT IN ROADWAY. HIT THE BRAKE.");
            }
          }
          setShowHazardPopup(true);
        }
      } catch (err) {
        console.error("Error polling hazard state", err);
      }
    };

    if (!loading) {
      intervalId = setInterval(checkHazard, 3000); // Polling every 3 seconds to reduce API spam
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [loading, showHazardPopup, hazardWarning, lastDismissedAt, mode]);

  const handleLogout = async () => {
    try {
      await axios.post(`${API_URL}/api/logout`, {}, { withCredentials: true });
      navigate('/');
    } catch (err) {
      console.error("Logout failed");
    }
  };



  const handleRotate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/rotate`);
      setVideoKey(Date.now());
    } catch (err) {
      console.error("Failed to rotate camera", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-bg-base">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-primary font-mono tracking-widest text-sm animate-pulse">INITIALIZING NEURAL NET...</p>
      </div>
    );
  }

  const isDriveMode = mode === 'drive';

  return (
    <div className="min-h-screen p-4 md:p-8 bg-bg-base relative overflow-hidden font-sans flex flex-col">
      
      {/* HAZARD POPUP OVERLAY */}
      {showHazardPopup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-red-950/80 backdrop-blur-2xl animate-pulse" />
          
          <div className="relative z-10 bg-black/40 border border-red-500/50 p-8 md:p-12 rounded-3xl shadow-[0_0_100px_rgba(239,68,68,0.5)] max-w-3xl w-full text-center flex flex-col items-center">
            <div className="w-24 h-24 mb-6 text-red-500 animate-bounce">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-4xl md:text-6xl font-black text-white mb-4 tracking-tighter">
              CRITICAL <span className="text-red-500">HAZARD</span>
            </h2>
            <p className="text-xl md:text-3xl text-red-100 font-medium mb-10 leading-tight">
              {hazardWarning || "IMMINENT COLLISION DETECTED"}
            </p>
            <button 
              onClick={() => {
                setShowHazardPopup(false);
                setLastDismissedAt(Date.now());
              }}
              className="px-10 py-4 bg-red-600 hover:bg-red-500 text-white font-bold rounded-full text-xl transition-transform hover:scale-110 shadow-[0_0_30px_rgba(220,38,38,0.6)]"
            >
              DISMISS WARNING
            </button>
          </div>
        </div>
      )}

      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-1/2 h-1/2 bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-1/2 h-1/2 bg-secondary/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')] opacity-50 pointer-events-none"></div>

      {/* Header - Hidden in Drive Mode */}
      {!isDriveMode && (
        <header className="relative z-10 flex flex-wrap justify-between items-center gap-4 mb-6 border-b border-white/5 pb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-[0_0_20px_rgba(56,189,248,0.4)]">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-wide">
                SafeDrive <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Command Center</span>
              </h1>
              <p className="text-xs text-gray-400 font-mono tracking-widest mt-1">NODE: KAPPA-7 | ENCRYPTED LINK</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">

            <button 
              onClick={handleRotate}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 hover:text-white transition-all text-sm font-semibold tracking-wide backdrop-blur-md flex items-center gap-2"
              title="Rotate Camera 90 Degrees"
            >
              <span>↻ Rotate</span>
            </button>
            <button 
              onClick={handleLogout}
              className="px-6 py-2 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 hover:border-white/20 hover:text-accent transition-all text-sm font-semibold tracking-wide backdrop-blur-md"
            >
              DISCONNECT
            </button>
          </div>
        </header>
      )}

      {/* Mode Switcher */}
      <div className="relative z-20 flex justify-center mb-6">
        <div className="bg-black/40 p-1 rounded-full backdrop-blur-md border border-white/10 inline-flex shadow-lg">
          <button 
            onClick={() => setMode('analysis')}
            className={`px-6 py-2 rounded-full text-sm font-bold tracking-wide transition-all ${mode === 'analysis' ? 'bg-primary text-black' : 'text-gray-400 hover:text-white'}`}
          >
            ANALYSIS MODE
          </button>
          <button 
            onClick={() => setMode('drive')}
            className={`px-6 py-2 rounded-full text-sm font-bold tracking-wide transition-all ${mode === 'drive' ? 'bg-accent text-black shadow-[0_0_15px_rgba(244,63,94,0.5)]' : 'text-gray-400 hover:text-white'}`}
          >
            DRIVE MODE
          </button>
        </div>
      </div>

      <div className={`grid grid-cols-1 ${isDriveMode ? 'xl:grid-cols-1 flex-grow' : 'xl:grid-cols-4'} gap-8 relative z-10 ${isDriveMode ? 'h-full pb-8 flex-grow' : ''}`}>
        
        {/* Main Video Feed Area & Map */}
        <div className={`col-span-1 ${isDriveMode ? 'xl:col-span-1 h-full' : 'xl:col-span-3'} flex flex-col gap-6`}>
          <div className={`relative rounded-3xl overflow-hidden bg-black flex items-center justify-center shadow-[0_0_40px_rgba(0,0,0,0.8)] border ${isDriveMode ? 'border-accent/30 flex-grow' : 'border-white/10 aspect-video'} group`}>
            
            {/* HUD Elements */}
            <div className="absolute top-6 left-6 z-20 flex flex-col gap-2">
              <div className="flex items-center gap-3 bg-black/60 px-4 py-2 rounded-full backdrop-blur-md border border-white/10 w-max">
                <div className="relative flex h-3 w-3">
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isDriveMode ? 'bg-accent' : 'bg-primary'} opacity-75`}></span>
                  <span className={`relative inline-flex rounded-full h-3 w-3 ${isDriveMode ? 'bg-accent' : 'bg-primary'}`}></span>
                </div>
                <span className={`text-xs font-bold tracking-widest ${isDriveMode ? 'text-accent' : 'text-primary'} font-mono`}>LIVE INFERENCE</span>
              </div>
              
              {/* Overlay Metrics for Drive Mode */}
              {isDriveMode && (
                <div className="mt-4 space-y-3">
                  <div className="bg-black/60 px-4 py-3 rounded-2xl backdrop-blur-md border border-white/10 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full border-2 border-red-500/50 flex items-center justify-center text-red-400">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 font-mono tracking-widest uppercase">Risk Score</p>
                      <p className="text-2xl font-black text-white">{hazardData.risk_score} <span className="text-sm text-gray-500 font-medium">/ 100</span></p>
                    </div>
                  </div>
                  
                  <div className="bg-black/60 px-4 py-3 rounded-2xl backdrop-blur-md border border-white/10 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full border-2 border-blue-500/50 flex items-center justify-center text-blue-400">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 font-mono tracking-widest uppercase">Proximity</p>
                      <p className="text-2xl font-black text-white">{hazardData.distance !== null ? `${hazardData.distance}m` : '--'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="absolute bottom-6 right-6 z-20 bg-black/60 px-3 py-1.5 rounded-lg backdrop-blur-md border border-white/10">
               <span className="text-[10px] text-gray-400 font-mono tracking-widest">FPS: <span className="text-white">~30</span> | LATENCY: <span className="text-green-400">12ms</span></span>
            </div>

            {/* Corner Brackets */}
            <div className={`absolute top-4 left-4 w-12 h-12 border-t-2 border-l-2 ${isDriveMode ? 'border-accent/50' : 'border-primary/50'} rounded-tl-xl pointer-events-none z-10 transition-transform duration-500 group-hover:-translate-x-1 group-hover:-translate-y-1`}></div>
            <div className={`absolute top-4 right-4 w-12 h-12 border-t-2 border-r-2 ${isDriveMode ? 'border-accent/50' : 'border-primary/50'} rounded-tr-xl pointer-events-none z-10 transition-transform duration-500 group-hover:translate-x-1 group-hover:-translate-y-1`}></div>
            <div className={`absolute bottom-4 left-4 w-12 h-12 border-b-2 border-l-2 ${isDriveMode ? 'border-accent/50' : 'border-primary/50'} rounded-bl-xl pointer-events-none z-10 transition-transform duration-500 group-hover:-translate-x-1 group-hover:translate-y-1`}></div>
            <div className={`absolute bottom-4 right-4 w-12 h-12 border-b-2 border-r-2 ${isDriveMode ? 'border-accent/50' : 'border-primary/50'} rounded-br-xl pointer-events-none z-10 transition-transform duration-500 group-hover:translate-x-1 group-hover:translate-y-1`}></div>

            {/* Scanning Line Animation */}
            <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
                <div className={`w-full h-1 ${isDriveMode ? 'bg-accent/20 shadow-[0_0_15px_rgba(244,63,94,0.3)]' : 'bg-primary/30 shadow-[0_0_15px_rgba(56,189,248,0.5)]'} animate-[scan_4s_ease-in-out_infinite]`}></div>
            </div>

            {/* Drive Mode Simple Overlay Warning */}
            {isDriveMode && hazardData.hazard && (
              <div className={`absolute top-1/4 left-1/2 -translate-x-1/2 z-30 ${hazardData.hazard_action === 'slow_down' ? 'bg-yellow-600/90 border-yellow-400 shadow-[0_0_50px_rgba(234,179,8,0.8)]' : 'bg-red-600/90 border-red-400 shadow-[0_0_50px_rgba(220,38,38,0.8)]'} text-white px-8 py-4 rounded-xl backdrop-blur-md border animate-pulse flex items-center gap-4`}>
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-2xl font-black tracking-widest uppercase">
                  {hazardData.hazard_action === 'slow_down' ? 'SLOW DOWN' : 'HIT THE BRAKE'}
                </span>
              </div>
            )}

            {/* The video stream from Flask */}
            <img 
              src={`${API_URL}/video_feed?k=${videoKey}`}
              alt="Live Video Stream" 
              className={`w-full h-full object-cover filter ${isDriveMode ? 'contrast-125 brightness-100' : 'contrast-125 brightness-110'}`}
            />
          </div>
          
          {/* Bottom Data Ribbon - Hidden in Drive Mode */}
          {!isDriveMode && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-md flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Threat Level</p>
                  <p className={`text-lg font-bold ${hazardData.risk_score > 75 ? 'text-red-400' : (hazardData.risk_score > 40 ? 'text-yellow-400' : 'text-green-400')}`}>
                    {hazardData.risk_score > 75 ? 'CRITICAL' : (hazardData.risk_score > 40 ? 'WARNING' : 'NOMINAL')}
                  </p>
                </div>
                <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center ${hazardData.risk_score > 75 ? 'border-red-500/30' : (hazardData.risk_score > 40 ? 'border-yellow-500/30' : 'border-green-500/30')}`}>
                   <div className={`w-6 h-6 rounded-full ${hazardData.risk_score > 75 ? 'bg-red-500/50' : (hazardData.risk_score > 40 ? 'bg-yellow-500/50' : 'bg-green-500/20')}`}></div>
                </div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-md flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Risk Score</p>
                  <p className="text-lg font-bold text-white">{hazardData.risk_score} / 100</p>
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-accent/30 flex items-center justify-center">
                   <div className="w-6 h-6 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs font-bold">R</div>
                </div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-md flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Min Distance</p>
                  <p className="text-lg font-bold text-white">{hazardData.distance !== null ? `${hazardData.distance}m` : 'Clear'}</p>
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-primary/30 flex items-center justify-center">
                   <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-bold">D</div>
                </div>
              </div>
            </div>
          )}

          {/* Map Area under Video Feed in Analysis Mode */}
          {mode === 'analysis' && (
            <div className="h-96 w-full mt-4">
               <PotholeMap />
            </div>
          )}
        </div>

        {/* Right Side Panel - Hidden in Drive Mode */}
        {mode === 'analysis' && (
          <div className="col-span-1 flex flex-col gap-6">
            {/* Status Widget */}
            <div className="bg-gradient-to-br from-white/10 to-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden">
              <div className="absolute -right-10 -top-10 w-32 h-32 bg-primary/20 blur-2xl rounded-full"></div>
              <h3 className="text-gray-400 text-xs font-bold uppercase tracking-[0.2em] mb-4">Core Analytics</h3>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white">Detection Confidence</span>
                    <span className="text-primary font-mono">94%</span>
                  </div>
                  <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-secondary w-[94%] shadow-[0_0_10px_rgba(56,189,248,0.5)]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white">Current Risk Level</span>
                    <span className="text-accent font-mono">{hazardData.risk_score}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-accent to-red-600 shadow-[0_0_10px_rgba(244,63,94,0.5)] transition-all duration-300" style={{ width: `${Math.max(5, hazardData.risk_score)}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Real-time Log Widget */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-xl flex-grow flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-gray-400 text-xs font-bold uppercase tracking-[0.2em]">Activity Log</h3>
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></div>
              </div>
              
              <div className="flex-1 space-y-4 font-mono text-xs overflow-hidden relative">
                <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-[#0f172a] to-transparent z-10 pointer-events-none"></div>
                
                {activityLogs.map((logItem, index) => (
                  <div key={index} className={`flex gap-3 items-start ${index === 0 ? 'text-white bg-primary/10 p-2 rounded border border-primary/20' : 'text-gray-400 opacity-80'}`}>
                    <span className={`${index === 0 ? 'text-primary' : 'text-gray-500'} mt-0.5`}>►</span>
                    <p><span className={`${index === 0 ? 'text-primary/70' : 'text-gray-600'}`}>[{logItem.time}]</span> {logItem.log}</p>
                  </div>
                ))}
                
                {activityLogs.length === 0 && (
                  <div className="text-gray-500 italic">No activity logs recorded yet.</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Global Styles for Animations */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { transform: translateY(-100%); }
          50% { transform: translateY(800%); }
          100% { transform: translateY(-100%); }
        }
      `}} />
    </div>
  );
}
