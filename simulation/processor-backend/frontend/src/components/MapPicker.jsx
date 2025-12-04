import React from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";

function LocationMarker({ position, onChange }) {
    useMapEvents({
        click(e) {
            onChange({
                lat: e.latlng.lat,
                lng: e.latlng.lng,
            });
        },
    });

    return position ? (
        <Marker position={[position.lat, position.lng]} />
    ) : null;
}

export default function MapPicker({ position, onChange }) {
    const defaultCenter = position
        ? [position.lat, position.lng]
        : [21.03, 105.85]; // Hà Nội

    return (
        <MapContainer
            center={defaultCenter}
            zoom={13}
            style={{ height: "100%", width: "100%" }}
        >
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <LocationMarker position={position} onChange={onChange} />
        </MapContainer>
    );
}
