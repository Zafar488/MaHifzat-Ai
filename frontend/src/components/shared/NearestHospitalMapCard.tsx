import { useState, useEffect } from 'react';
import {
  MapPin,
  Navigation,
  Phone,
  Building2,
  Ambulance,
  ExternalLink,
  ShieldAlert,
  Clock,
  Compass,
  Loader2,
  AlertTriangle,
  RefreshCw,
  Globe,
  CheckCircle2,
} from 'lucide-react';
import { api } from '@/lib/api-client';

interface HospitalFacility {
  facility_id: string;
  name: string;
  latitude: number;
  longitude: number;
  phone?: string;
  type?: string;
  source?: string;
  distance_km?: number;
  distance_m?: number;
  duration_min?: number;
  travel_time_minutes?: number;
  emergency?: string;
  directions_url?: string;
}

interface NearestHospitalMapCardProps {
  riskLevel: 'high' | 'mid' | 'low' | string;
  patientName?: string;
  initialLat?: number;
  initialLon?: number;
  title?: string;
}

const PAKISTAN_CITIES = [
  { name: 'Lahore (Punjab)', lat: 31.5204, lon: 74.3587 },
  { name: 'Karachi (Sindh)', lat: 24.8607, lon: 67.0011 },
  { name: 'Islamabad (Capital)', lat: 33.6844, lon: 73.0479 },
  { name: 'Rawalpindi (Punjab)', lat: 33.5989, lon: 73.0433 },
  { name: 'Peshawar (KPK)', lat: 34.0151, lon: 71.5249 },
  { name: 'Multan (Punjab)', lat: 30.1575, lon: 71.5249 },
  { name: 'Faisalabad (Punjab)', lat: 31.4504, lon: 73.1350 },
  { name: 'Quetta (Balochistan)', lat: 30.1798, lon: 66.9750 },
  { name: 'Swat / Saidu Sharif (KPK)', lat: 34.7500, lon: 72.3600 },
];

export function NearestHospitalMapCard({
  riskLevel,
  patientName,
  initialLat = 34.0151,
  initialLon = 71.5249,
  title,
}: NearestHospitalMapCardProps) {
  const normalizedRisk = String(riskLevel || '').toLowerCase();
  const isHighRisk = ['high', 'high risk', 'emergency', 'pathological', '1', 'severe'].some((k) =>
    normalizedRisk.includes(k)
  );
  const isMidRisk = ['mid', 'medium', 'moderate', 'suspect', 'warning'].some((k) =>
    normalizedRisk.includes(k)
  );

  const [location, setLocation] = useState<{ latitude: number; longitude: number }>({
    latitude: initialLat,
    longitude: initialLon,
  });

  const [locationMethod, setLocationMethod] = useState<string>('Detecting Current GPS...');
  const [selectedCityName, setSelectedCityName] = useState<string>('Detecting Location...');
  const [facilities, setFacilities] = useState<HospitalFacility[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<HospitalFacility | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [isAutoDetected, setIsAutoDetected] = useState<boolean>(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchNearbyHospitals = async (lat: number, lon: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.post('/facilities/nearby', {
        location: {
          latitude: lat,
          longitude: lon,
          share_for_discovery: true,
          share_for_routing: true,
        },
        radius_km: 35,
      });
      const facs: HospitalFacility[] = res.data?.facilities || [];
      setFacilities(facs);
      if (facs.length > 0) {
        setSelectedFacility(facs[0]);
      } else {
        setSelectedFacility(null);
      }
    } catch (err: any) {
      setError('Unable to discover nearby hospitals from OpenStreetMap.');
    } finally {
      setIsLoading(false);
    }
  };

  // Reverse geocodes coordinates to human-readable city/town name
  const reverseGeocodeCity = async (lat: number, lon: number): Promise<string> => {
    // 1. Check proximity to static Pakistan cities (~25km)
    for (const c of PAKISTAN_CITIES) {
      const dLat = Math.abs(c.lat - lat);
      const dLon = Math.abs(c.lon - lon);
      if (dLat < 0.22 && dLon < 0.22) {
        return c.name;
      }
    }

    // 2. OpenStreetMap Nominatim reverse geocode
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10`,
        {
          headers: { 'Accept-Language': 'en' },
          signal: controller.signal,
        }
      );
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        const addr = data.address || {};
        const city =
          addr.city ||
          addr.town ||
          addr.suburb ||
          addr.municipality ||
          addr.county ||
          addr.district ||
          addr.state;
        if (city) {
          const country = addr.country ? `, ${addr.country}` : '';
          return `${city}${country}`;
        }
      }
    } catch (e) {
      // ignore network/timeout error
    }

    return `GPS (${lat.toFixed(3)}, ${lon.toFixed(3)})`;
  };

  // IP Geolocation fallback across multiple providers
  const attemptIPGeolocation = async (): Promise<{ lat: number; lon: number; label: string; cityName: string } | null> => {
    // Provider A: ipapi.co
    try {
      const rA = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(3500) });
      if (rA.ok) {
        const d = await rA.json();
        if (d.latitude && d.longitude) {
          const cityStr = d.city ? `${d.city}, ${d.region_code || d.country_name || ''}` : 'IP Network';
          return {
            lat: Number(d.latitude),
            lon: Number(d.longitude),
            label: `IP Network (${cityStr})`,
            cityName: d.city || 'IP Detected City',
          };
        }
      }
    } catch (e) {}

    // Provider B: ip-api.com
    try {
      const rB = await fetch('http://ip-api.com/json/', { signal: AbortSignal.timeout(3500) });
      if (rB.ok) {
        const d = await rB.json();
        if (d.lat && d.lon) {
          const cityStr = d.city ? `${d.city}, ${d.country || ''}` : 'IP Location';
          return {
            lat: Number(d.lat),
            lon: Number(d.lon),
            label: `IP Network (${cityStr})`,
            cityName: d.city || 'IP Detected City',
          };
        }
      }
    } catch (e) {}

    return null;
  };

  // Robust location detection with high/low accuracy fallback
  const detectUserLocation = async (isManualClick = false) => {
    setIsLocating(true);
    setError(null);

    const getBrowserGPS = (highAcc: boolean): Promise<GeolocationPosition> => {
      return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('Browser Geolocation unavailable'));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: highAcc,
          timeout: highAcc ? 6000 : 10000,
          maximumAge: 60000,
        });
      });
    };

    let lat: number | null = null;
    let lon: number | null = null;
    let methodLabel = '';
    let resolvedCity = '';

    // Step 1: Try High Accuracy Browser Geolocation (GPS)
    try {
      const posHigh = await getBrowserGPS(true);
      lat = posHigh.coords.latitude;
      lon = posHigh.coords.longitude;
      methodLabel = 'Live Device GPS (High Precision)';
    } catch (errHigh) {
      // Step 2: Fall back to Low Accuracy Browser Geolocation (Wi-Fi/Cellular positioning)
      try {
        const posLow = await getBrowserGPS(false);
        lat = posLow.coords.latitude;
        lon = posLow.coords.longitude;
        methodLabel = 'Live Device Location (Network/Wi-Fi)';
      } catch (errLow) {
        // Step 3: Fall back to IP Geolocation
        const ipRes = await attemptIPGeolocation();
        if (ipRes) {
          lat = ipRes.lat;
          lon = ipRes.lon;
          methodLabel = ipRes.label;
          resolvedCity = ipRes.cityName;
        }
      }
    }

    if (lat !== null && lon !== null) {
      if (!resolvedCity) {
        resolvedCity = await reverseGeocodeCity(lat, lon);
      }

      const displayCityName =
        resolvedCity.startsWith('🎯') || resolvedCity.startsWith('📍')
          ? resolvedCity
          : `🎯 Current Location (${resolvedCity})`;

      setLocation({ latitude: lat, longitude: lon });
      setLocationMethod(methodLabel);
      setSelectedCityName(displayCityName);
      setIsAutoDetected(true);
      setIsLocating(false);

      if (isManualClick) {
        setSuccessNotice(`Detected Current Location: ${resolvedCity}`);
        setTimeout(() => setSuccessNotice(null), 4000);
      }

      // Save in sessionStorage so tab switching preserves current location
      try {
        sessionStorage.setItem(
          'maahifazat_user_location',
          JSON.stringify({
            lat,
            lon,
            selectedCityName: displayCityName,
            locationMethod: methodLabel,
          })
        );
      } catch (e) {}

      return true;
    } else {
      setIsLocating(false);
      // Fallback to initial Peshawar if nothing worked
      if (!isAutoDetected) {
        setLocation({ latitude: initialLat, longitude: initialLon });
        setSelectedCityName('Peshawar (KPK)');
        setLocationMethod('Regional Default (Peshawar)');
      }
      if (isManualClick) {
        setError('GPS permission denied or signal unavailable. Please pick your city from the dropdown below.');
      }
      return false;
    }
  };

  // Auto-detect user location on component mount or load cached location
  useEffect(() => {
    try {
      const cached = sessionStorage.getItem('maahifazat_user_location');
      if (cached) {
        const p = JSON.parse(cached);
        if (p.lat && p.lon) {
          setLocation({ latitude: p.lat, longitude: p.lon });
          setSelectedCityName(p.selectedCityName || 'Detected Location');
          setLocationMethod(p.locationMethod || 'Live Location');
          setIsAutoDetected(true);
          setIsLocating(false);
          // Refresh hospitals for cached location
          fetchNearbyHospitals(p.lat, p.lon);
          // Trigger silent background update
          detectUserLocation(false);
          return;
        }
      }
    } catch (e) {}

    detectUserLocation(false);
  }, []);

  useEffect(() => {
    if (location.latitude && location.longitude) {
      fetchNearbyHospitals(location.latitude, location.longitude);
    }
  }, [location.latitude, location.longitude]);

  const handleUseHardwareGPS = () => {
    detectUserLocation(true);
  };

  const handleSelectCity = async (cityName: string) => {
    if (!cityName) return;
    setSelectedCityName(cityName);
    const staticCity = PAKISTAN_CITIES.find((c) => c.name === cityName);
    if (staticCity) {
      setLocation({ latitude: staticCity.lat, longitude: staticCity.lon });
      setLocationMethod(`Selected Region: ${staticCity.name}`);
      setIsAutoDetected(true);
    } else if (cityName.includes('(')) {
      // User re-selected custom auto-detected location
      try {
        const cached = sessionStorage.getItem('maahifazat_user_location');
        if (cached) {
          const p = JSON.parse(cached);
          if (p.lat && p.lon) {
            setLocation({ latitude: p.lat, longitude: p.lon });
            setLocationMethod(p.locationMethod || 'Device GPS');
          }
        }
      } catch (e) {}
    }
  };

  if (!isHighRisk && !isMidRisk) {
    return null;
  }

  const mapLat = selectedFacility?.latitude || location.latitude;
  const mapLon = selectedFacility?.longitude || location.longitude;
  const osmEmbedUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${mapLon - 0.04}%2C${mapLat - 0.04}%2C${mapLon + 0.04}%2C${mapLat + 0.04}&layer=mapnik&marker=${mapLat}%2C${mapLon}`;
  const gmapsDirectionsUrl = selectedFacility
    ? `https://www.google.com/maps/dir/?api=1&origin=${location.latitude},${location.longitude}&destination=${selectedFacility.latitude},${selectedFacility.longitude}&travelmode=driving`
    : `https://www.google.com/maps/search/hospital/@${location.latitude},${location.longitude},13z`;

  return (
    <div
      className={`rounded-2xl border shadow-lg overflow-hidden transition-all ${
        isHighRisk
          ? 'bg-red-950/5 border-red-500/40 ring-1 ring-red-500/30'
          : 'bg-amber-950/5 border-amber-500/40 ring-1 ring-amber-500/30'
      }`}
    >
      {/* Header Banner */}
      <div
        className={`px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
          isHighRisk ? 'bg-red-700 text-white' : 'bg-amber-600 text-white'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
            {isHighRisk ? <Ambulance className="size-6 text-white animate-bounce" /> : <ShieldAlert className="size-6 text-white" />}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] uppercase font-mono font-bold tracking-widest px-2 py-0.5 rounded bg-black/20 text-white">
                {isHighRisk ? 'EMERGENCY FACILITY MAPPING' : 'URGENT CARE FACILITY MAPPING'}
              </span>
              <span className="text-xs font-semibold text-white/90">
                {isHighRisk ? '🔴 High Risk Verified' : '🟡 Moderate Risk Verified'}
              </span>
              {isAutoDetected && (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/90 text-white flex items-center gap-1 shadow-sm">
                  <MapPin className="size-3" /> {locationMethod}
                </span>
              )}
            </div>
            <h3 className="text-base font-extrabold tracking-tight mt-0.5">
              {title || (patientName ? `Nearest Emergency Hospital for ${patientName}` : `Nearest Emergency Maternity Hospital Routing`)}
            </h3>
          </div>
        </div>

        <button
          onClick={handleUseHardwareGPS}
          disabled={isLocating}
          className="self-start sm:self-center flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white text-gray-900 hover:bg-emerald-50 text-xs font-extrabold transition-all shadow-md active:scale-95 disabled:opacity-50 cursor-pointer border border-white/40 shrink-0"
        >
          {isLocating ? <Loader2 className="size-4 animate-spin text-teal-600" /> : <Compass className="size-4 text-teal-700" />}
          <span>{isLocating ? 'Detecting Location...' : 'Detect My Live Location'}</span>
        </button>
      </div>

      {/* Main Content Body */}
      <div className="p-6 space-y-6 bg-white">
        {/* Success Notice Banner */}
        {successNotice && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-bold flex items-center gap-2 shadow-sm animate-in fade-in duration-300">
            <CheckCircle2 className="size-4 text-emerald-600 shrink-0" />
            <span>{successNotice}</span>
          </div>
        )}

        {/* City & Manual Coordinates Selector Toolbar */}
        <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <Globe className="size-4 text-teal-600 shrink-0" />
            <label className="text-xs font-bold text-gray-800 whitespace-nowrap">Current Location / City:</label>
            <select
              value={selectedCityName}
              onChange={(e) => handleSelectCity(e.target.value)}
              className="w-full md:w-72 rounded-lg border border-teal-300 bg-white px-3 py-1.5 text-xs font-bold text-gray-900 shadow-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer"
            >
              <option value="">-- Select Patient City / Region --</option>
              {selectedCityName && !PAKISTAN_CITIES.some((c) => c.name === selectedCityName) && (
                <option value={selectedCityName}>
                  {selectedCityName.startsWith('🎯') ? selectedCityName : `🎯 ${selectedCityName}`} (Current Device Location)
                </option>
              )}
              {PAKISTAN_CITIES.map((c) => (
                <option key={c.name} value={c.name}>
                  📍 {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 text-xs text-gray-600 font-mono w-full md:w-auto justify-end flex-wrap">
            <span>Lat: <strong>{location.latitude.toFixed(4)}</strong></span>
            <span>Lon: <strong>{location.longitude.toFixed(4)}</strong></span>
            <span className="px-2.5 py-1 rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold font-sans flex items-center gap-1 border border-teal-200">
              <MapPin className="size-3 text-teal-600" />
              {locationMethod}
            </span>
          </div>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed">
          Based on the verified <strong>{isHighRisk ? 'High' : 'Moderate'} Risk Level</strong>, hospital referral and route mapping has been updated via OpenStreetMap to the nearest emergency tertiary maternity facility around <strong>{selectedCityName || locationMethod}</strong>.
        </p>

        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center bg-gray-50 rounded-xl border border-gray-200">
            <Loader2 className="size-8 animate-spin text-teal-600 mb-2" />
            <p className="text-xs font-semibold text-gray-600">Discovering nearest hospital emergency units around {selectedCityName}...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-red-500 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => fetchNearbyHospitals(location.latitude, location.longitude)}
              className="text-teal-700 font-bold underline flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className="size-3" /> Retry Search
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Map Column (Interactive OSM View) */}
            <div className="lg:col-span-7 space-y-3">
              <div className="relative rounded-xl overflow-hidden border border-gray-300 shadow-inner h-72 bg-gray-100">
                <iframe
                  title="Nearest Hospital Route Map"
                  width="100%"
                  height="100%"
                  frameBorder="0"
                  scrolling="no"
                  marginHeight={0}
                  marginWidth={0}
                  src={osmEmbedUrl}
                  className="w-full h-full"
                />

                <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm flex items-center gap-2 text-xs font-bold text-gray-800">
                  <MapPin className="size-4 text-red-600 animate-pulse" />
                  <span>{selectedFacility ? selectedFacility.name : 'Target Facility'}</span>
                </div>
              </div>

              {selectedFacility && (
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-gray-50 p-3 rounded-xl border border-gray-200">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1 font-bold text-gray-800">
                      <Navigation className="size-3.5 text-teal-600" />
                      Distance: {selectedFacility.distance_km ? `${selectedFacility.distance_km.toFixed(1)} km` : 'Near'}
                    </span>
                    <span className="flex items-center gap-1 font-bold text-gray-800">
                      <Clock className="size-3.5 text-amber-600" />
                      Travel Time: {selectedFacility.duration_min ? `${Math.round(selectedFacility.duration_min)} mins` : 'Est. ~10 mins'}
                    </span>
                  </div>

                  <a
                    href={gmapsDirectionsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 font-bold text-teal-700 hover:text-teal-900 underline"
                  >
                    <ExternalLink className="size-3.5" />
                    Open Google Maps Directions
                  </a>
                </div>
              )}
            </div>

            {/* Nearest Facilities List Column */}
            <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
              <div>
                <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Building2 className="size-4 text-teal-600" />
                  Nearest Mapped Emergency Facilities ({facilities.length})
                </h4>

                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {facilities.map((fac) => {
                    const isSelected = selectedFacility?.facility_id === fac.facility_id;
                    return (
                      <button
                        key={fac.facility_id}
                        onClick={() => setSelectedFacility(fac)}
                        className={`w-full text-left p-3 rounded-xl border transition-all flex items-start justify-between gap-2 cursor-pointer ${
                          isSelected
                            ? 'border-teal-600 bg-teal-50/80 ring-2 ring-teal-500/20 shadow-sm'
                            : 'border-gray-200 bg-white hover:bg-gray-50'
                        }`}
                      >
                        <div>
                          <h5 className="text-xs font-bold text-gray-900 line-clamp-1">{fac.name}</h5>
                          <div className="flex items-center gap-2 text-[11px] text-gray-500 mt-1">
                            <span>{fac.distance_km ? `${fac.distance_km.toFixed(1)} km away` : 'Mapped Hospital'}</span>
                            {fac.duration_min && <span>• ~{Math.round(fac.duration_min)} mins drive</span>}
                          </div>
                        </div>

                        {isSelected && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-600 text-white shrink-0">
                            Selected
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Action Buttons Panel */}
              <div className="pt-3 border-t border-gray-200 space-y-2">
                {selectedFacility?.phone && (
                  <a
                    href={`tel:${selectedFacility.phone}`}
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm transition-colors"
                  >
                    <Phone className="size-4" />
                    Call Hospital ({selectedFacility.phone})
                  </a>
                )}

                <a
                  href={gmapsDirectionsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow-sm transition-colors"
                >
                  <Navigation className="size-4" />
                  Map Driving Route to Hospital
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
