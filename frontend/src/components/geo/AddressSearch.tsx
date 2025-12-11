import React, { useState, useCallback, useRef, useEffect } from "react";
import { Search, MapPin, X, Loader2 } from "lucide-react";
import { Input } from "../ui/input";
import { geoApi } from "../../api/geo";
import type { AddressSuggestion } from "../../types";
import L from "leaflet";
import { useDebounce } from "../../hooks/useDebounce";

interface AddressSearchProps {
    map: L.Map;
    onLocationSelect?: (lat: number, lng: number, address: string) => void;
    onClear?: () => void;
}

export const AddressSearch: React.FC<AddressSearchProps> = ({
    map,
    onLocationSelect,
    onClear,
}) => {
    const [query, setQuery] = useState("");
    const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedMarker, setSelectedMarker] = useState<L.Marker | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const debouncedQuery = useDebounce(query, 300);

    useEffect(() => {
        if (debouncedQuery.length < 3) {
            setSuggestions([]);
            return;
        }

        const fetchSuggestions = async () => {
            setIsLoading(true);
            try {
                const results = await geoApi.searchAddress(debouncedQuery, 5);
                setSuggestions(results);
            } catch (error) {
                console.error("Address search failed:", error);
                setSuggestions([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchSuggestions();
    }, [debouncedQuery]);

    const handleSelect = useCallback(
        async (suggestion: AddressSuggestion) => {
            const { latitude, longitude } = suggestion.coordinates;

            // Fly to location
            map.flyTo([latitude, longitude], 15, {
                animate: true,
                duration: 1.5,
            });

            // Add marker
            if (selectedMarker) {
                map.removeLayer(selectedMarker);
            }
            const marker = L.marker([latitude, longitude], {
                icon: L.divIcon({
                    className: "custom-address-marker",
                    html: '<div class="w-5 h-5 bg-green-600 rounded-full border-2 border-white shadow-lg"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10],
                }),
            })
                .addTo(map)
                .bindPopup(
                    `<div class="text-sm font-medium">${suggestion.address}</div>`
                )
                .openPopup();

            setSelectedMarker(marker);
            setQuery(suggestion.address);
            setSuggestions([]);
            setIsOpen(false);

            if (onLocationSelect) {
                onLocationSelect(latitude, longitude, suggestion.address);
            }
        },
        [map, selectedMarker, onLocationSelect]
    );

    const handleClear = useCallback(() => {
        setQuery("");
        setSuggestions([]);
        setIsOpen(false);
        if (selectedMarker) {
            map.removeLayer(selectedMarker);
            setSelectedMarker(null);
        }
        if (onClear) {
            onClear();
        }
        if (inputRef.current) {
            inputRef.current.blur();
        }
    }, [map, selectedMarker, onClear]);

    const handleGeocode = useCallback(async () => {
        if (query.length < 3) return;

        setIsLoading(true);
        try {
            const result = await geoApi.geocode({ address: query });
            const { latitude, longitude } = result.coordinates;

            map.flyTo([latitude, longitude], 15, {
                animate: true,
                duration: 1.5,
            });

            if (selectedMarker) {
                map.removeLayer(selectedMarker);
            }
            const marker = L.marker([latitude, longitude], {
                icon: L.divIcon({
                    className: "custom-address-marker",
                    html: '<div class="w-5 h-5 bg-green-600 rounded-full border-2 border-white shadow-lg"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10],
                }),
            })
                .addTo(map)
                .bindPopup(`<div class="text-sm font-medium">${query}</div>`)
                .openPopup();

            setSelectedMarker(marker);
            setSuggestions([]);
            setIsOpen(false);

            if (onLocationSelect) {
                onLocationSelect(latitude, longitude, query);
            }
        } catch (error) {
            console.error("Geocoding failed:", error);
        } finally {
            setIsLoading(false);
        }
    }, [query, map, selectedMarker, onLocationSelect]);

    // Close suggestions when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                containerRef.current &&
                !containerRef.current.contains(event.target as Node)
            ) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div
            ref={containerRef}
            className="relative bg-white rounded-lg shadow-lg border border-slate-200 w-96"
        >
            <div className="relative">
                <div className="flex items-center gap-2 p-2">
                    <Search size={18} className="text-slate-400 shrink-0" />
                    <Input
                        ref={inputRef}
                        type="text"
                        placeholder="Tìm kiếm địa chỉ..."
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            setIsOpen(true);
                        }}
                        onFocus={() => setIsOpen(true)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                e.preventDefault();
                                handleGeocode();
                            }
                        }}
                        className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                    />
                    {query && (
                        <button
                            onClick={handleClear}
                            className="text-slate-400 hover:text-slate-600 shrink-0"
                        >
                            <X size={16} />
                        </button>
                    )}
                </div>

                {isOpen && (suggestions.length > 0 || isLoading) && (
                    <div className="absolute top-full left-0 right-0 bg-white border-t border-slate-200 rounded-b-lg shadow-lg max-h-64 overflow-y-auto z-10">
                        {isLoading ? (
                            <div className="p-4 flex items-center justify-center">
                                <Loader2
                                    size={20}
                                    className="animate-spin text-slate-400"
                                />
                            </div>
                        ) : (
                            <ul className="py-1">
                                {suggestions.map((suggestion, index) => (
                                    <li
                                        key={index}
                                        onClick={() => handleSelect(suggestion)}
                                        className="px-4 py-2 hover:bg-slate-50 cursor-pointer flex items-start gap-2"
                                    >
                                        <MapPin
                                            size={16}
                                            className="text-slate-400 mt-0.5 shrink-0"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-medium text-slate-900 truncate">
                                                {suggestion.address}
                                            </div>
                                            {(() => {
                                                const getStringValue = (
                                                    value: unknown
                                                ): string => {
                                                    if (
                                                        typeof value ===
                                                        "string"
                                                    )
                                                        return value;
                                                    if (
                                                        typeof value ===
                                                            "object" &&
                                                        value !== null
                                                    ) {
                                                        const obj =
                                                            value as Record<
                                                                string,
                                                                unknown
                                                            >;
                                                        return String(
                                                            obj.city ||
                                                                obj.country ||
                                                                obj.name ||
                                                                ""
                                                        );
                                                    }
                                                    return "";
                                                };

                                                const cityStr = getStringValue(
                                                    suggestion.city
                                                );
                                                const countryStr =
                                                    getStringValue(
                                                        suggestion.country
                                                    );

                                                return cityStr || countryStr ? (
                                                    <div className="text-xs text-slate-500 truncate">
                                                        {[cityStr, countryStr]
                                                            .filter(Boolean)
                                                            .join(", ")}
                                                    </div>
                                                ) : null;
                                            })()}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
