import React, { useState, useCallback } from 'react';
import { useMap } from 'react-leaflet';
import { Search, MapPin, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { geoApi } from '../../api/geo';
import type { Asset } from '../../types';
import L from 'leaflet';

interface NearbySearchProps {
  onResults: (assets: Asset[]) => void;
  onClear?: () => void;
}

export const NearbySearch: React.FC<NearbySearchProps> = ({ onResults, onClear }) => {
  const map = useMap();
  const [isOpen, setIsOpen] = useState(false);
  const [radius, setRadius] = useState<number>(500);
  const [isSearching, setIsSearching] = useState(false);
  const [searchMarker, setSearchMarker] = useState<L.Marker | null>(null);
  const [circleLayer, setCircleLayer] = useState<L.Circle | null>(null);

  const handleSearch = useCallback(async () => {
    const center = map.getCenter();
    const lat = center.lat;
    const lng = center.lng;

    setIsSearching(true);
    try {
      const results = await geoApi.findNearbyAssets({
        lat,
        lng,
        radius_meters: radius,
      });

      onResults(results);

      // Add marker at search center
      if (searchMarker) {
        map.removeLayer(searchMarker);
      }
      const marker = L.marker([lat, lng], {
        icon: L.divIcon({
          className: 'custom-search-marker',
          html: '<div class="w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg"></div>',
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        }),
      }).addTo(map);

      // Add circle to show search radius
      if (circleLayer) {
        map.removeLayer(circleLayer);
      }
      const circle = L.circle([lat, lng], {
        radius: radius,
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.1,
        weight: 2,
        dashArray: '5, 5',
      }).addTo(map);

      setSearchMarker(marker);
      setCircleLayer(circle);

      // Fit bounds to show all results
      if (results.length > 0) {
        const group = new L.FeatureGroup([marker, circle]);
        map.fitBounds(group.getBounds().pad(0.1));
      }
    } catch (error) {
      console.error('Nearby search failed:', error);
    } finally {
      setIsSearching(false);
    }
  }, [map, radius, onResults, searchMarker, circleLayer]);

  const handleClear = useCallback(() => {
    if (searchMarker) {
      map.removeLayer(searchMarker);
      setSearchMarker(null);
    }
    if (circleLayer) {
      map.removeLayer(circleLayer);
      setCircleLayer(null);
    }
    if (onClear) {
      onClear();
    }
    setIsOpen(false);
  }, [map, searchMarker, circleLayer, onClear]);

  return (
    <div className="relative bg-white rounded-lg shadow-lg border border-slate-200">
      {!isOpen ? (
        <Button
          onClick={() => setIsOpen(true)}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <Search size={16} />
          Nearby Search
        </Button>
      ) : (
        <div className="p-4 w-80">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm text-slate-900">Search Nearby</h3>
            <button
              onClick={handleClear}
              className="text-slate-400 hover:text-slate-600"
            >
              <X size={16} />
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <Label htmlFor="radius" className="text-xs text-slate-600">
                Search Radius (meters)
              </Label>
              <div className="flex items-center gap-2 mt-1">
                <Input
                  id="radius"
                  type="number"
                  min="100"
                  max="10000"
                  step="100"
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                  className="text-sm"
                />
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => setRadius((r) => Math.min(r + 100, 10000))}
                    className="text-xs px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded"
                  >
                    +
                  </button>
                  <button
                    onClick={() => setRadius((r) => Math.max(r - 100, 100))}
                    className="text-xs px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded"
                  >
                    −
                  </button>
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                {[500, 1000, 2000, 5000].map((r) => (
                  <button
                    key={r}
                    onClick={() => setRadius(r)}
                    className={`text-xs px-2 py-1 rounded ${
                      radius === r
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {r / 1000}km
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <Button
                onClick={handleSearch}
                disabled={isSearching}
                className="w-full"
                size="sm"
              >
                {isSearching ? (
                  'Searching...'
                ) : (
                  <>
                    <MapPin size={16} className="mr-2" />
                    Search from Map Center
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
