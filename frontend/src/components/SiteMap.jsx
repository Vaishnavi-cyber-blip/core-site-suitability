import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix missing marker icons in Vite + Leaflet
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

export default function SiteMap({ sites }) {
  if (!sites || sites.length === 0) {
    return (
      <div className="text-sm text-slate-400">
        No sites to display on the map.
      </div>
    );
  }

  // Center map roughly at the average of all sites
  const avgLat = sites.reduce((sum, s) => sum + s.lat, 0) / sites.length;
  const avgLon = sites.reduce((sum, s) => sum + s.lon, 0) / sites.length;

  return (
    <MapContainer
      center={[avgLat, avgLon]}
      zoom={14}
      className="w-full h-[450px] rounded-xl overflow-hidden"
    >
      {/* Esri satellite basemap */}
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="&copy; Esri & contributors"
      />

      {sites.map((s) => (
        <Marker key={s.id} position={[s.lat, s.lon]}>
          <Popup>
            <div className="text-sm">
              <div className="font-semibold">
                {s.structure_type || "No structure type"}
              </div>
              <div className="text-xs mt-1">
                Lat: {s.lat.toFixed(6)} <br />
                Lon: {s.lon.toFixed(6)}
              </div>
              <div className="text-[10px] mt-1 break-all">
                ID: {s.id}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
