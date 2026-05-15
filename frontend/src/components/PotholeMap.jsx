import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const userIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function LiveLocationMarker() {
  const [position, setPosition] = useState(null);
  const map = useMap();

  useEffect(() => {
    if (!navigator.geolocation) {
      console.error("Geolocation is not supported by your browser");
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const newPos = [latitude, longitude];
        setPosition(newPos);
        map.flyTo(newPos, map.getZoom());
      },
      (err) => {
        console.error("Error getting location:", err);
      },
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, [map]);

  return position === null ? null : (
    <Marker position={position} icon={userIcon}>
      <Popup>
        <div className="font-bold text-center">Live Vehicle Location</div>
        <div className="text-xs text-gray-500">{position[0].toFixed(5)}, {position[1].toFixed(5)}</div>
      </Popup>
    </Marker>
  );
}

export default function PotholeMap() {
  const [potholes, setPotholes] = useState([]);
  const defaultCenter = [11.0168, 76.9558]; // Default to Coimbatore, Tamil Nadu

  useEffect(() => {
    // Load potholes from local storage or use some initial dummy data
    const savedPotholes = localStorage.getItem('pothole_data_v2');
    if (savedPotholes) {
      setPotholes(JSON.parse(savedPotholes));
    } else {
      const initialPotholes = [
        { id: 1, lat: 11.0168, lng: 76.9558, status: 'active', reportedAt: new Date().toISOString() },
        { id: 2, lat: 11.0268, lng: 76.9658, status: 'active', reportedAt: new Date().toISOString() },
        { id: 3, lat: 11.0068, lng: 76.9458, status: 'active', reportedAt: new Date().toISOString() },
        { id: 4, lat: 11.0188, lng: 76.9578, status: 'active', reportedAt: new Date().toISOString() },
        { id: 5, lat: 11.0128, lng: 76.9508, status: 'active', reportedAt: new Date().toISOString() },
      ];
      setPotholes(initialPotholes);
      localStorage.setItem('pothole_data_v2', JSON.stringify(initialPotholes));
    }
  }, []);

  const markAsFixed = (id) => {
    // Completely remove the pothole from the list once fixed
    const updatedPotholes = potholes.filter(p => p.id !== id);
    setPotholes(updatedPotholes);
    localStorage.setItem('pothole_data_v2', JSON.stringify(updatedPotholes));
  };

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden border border-white/10 shadow-2xl relative">
      <div className="absolute top-4 left-4 z-[400] bg-black/60 px-4 py-2 rounded-full backdrop-blur-md border border-white/10 flex items-center gap-2">
         <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
         <span className="text-white font-mono text-xs tracking-widest uppercase">Live Tracking</span>
      </div>
      <MapContainer center={defaultCenter} zoom={14} style={{ height: '100%', width: '100%' }} zoomControl={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <LiveLocationMarker />
        {potholes.map(p => (
          <CircleMarker 
            key={p.id} 
            center={[p.lat, p.lng]} 
            radius={20}
            pathOptions={{ color: 'transparent', fillColor: '#ef4444', fillOpacity: 0.4 }}
          >
            {/* Inner hot spot */}
            <CircleMarker 
              center={[p.lat, p.lng]} 
              radius={4}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 1 }}
            />
            <Popup className="custom-popup">
              <div className="text-black p-2">
                <h3 className="font-bold text-lg mb-1">Hazard Zone #{p.id}</h3>
                <p className="text-sm mb-2 text-red-600 font-bold">POTHOLE CLUSTER</p>
                <p className="text-xs text-gray-500 mb-3">Detected: {new Date(p.reportedAt).toLocaleDateString()}</p>
                <button 
                  onClick={() => markAsFixed(p.id)}
                  className="w-full py-2 rounded text-white font-bold text-sm transition-colors bg-green-500 hover:bg-green-600"
                >
                  Mark as Fixed (Remove)
                </button>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <style>{`
        .leaflet-container {
          background: #0f172a;
          font-family: inherit;
        }
        .leaflet-popup-content-wrapper {
          border-radius: 12px;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
