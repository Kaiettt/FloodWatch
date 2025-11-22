import React, { useState } from "react";
import axios from "axios";
import MapPicker from "./MapPicker";
import "../App.css";

export default function ReportForm() {
    const [description, setDescription] = useState("");
    const [files, setFiles] = useState([]);
    const [position, setPosition] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [waterHeight, setWaterHeight] = useState("");
    const [notification, setNotification] = useState(null); // new state

    // Get GPS location
    const getLocation = () => {
        if (!navigator.geolocation) return alert("Trình duyệt không hỗ trợ GPS");
        navigator.geolocation.getCurrentPosition(
            (pos) => setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
            () => alert("Không thể lấy vị trí")
        );
    };

    // Drag and drop files
    const handleDrop = (e) => {
        e.preventDefault();
        const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("image/"));
        setFiles(prev => [...prev, ...droppedFiles]);
    };

    const handleDragOver = (e) => e.preventDefault();

    // Submit form
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!description) return alert("Vui lòng nhập mô tả!");
        setLoading(true);
        setNotification(null); // reset notification

        try {
            const form = new FormData();
            form.append("description", description);
            if (position) {
                form.append("latitude", position.lat);
                form.append("longitude", position.lng);
            }
            if (waterHeight) form.append("water_height", parseFloat(waterHeight));
            files.forEach(f => form.append("images", f));

            const res = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/report`, form);
            setStatus(res.data);
            setNotification({ type: "success", message: "Gửi báo cáo thành công!" });
        } catch (err) {
            console.error(err);
            setNotification({ type: "error", message: "Gửi báo cáo thất bại." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container-full">
            <div className="container">
                <h2>📢 Báo Cáo Hiện Trường Lũ Lụt</h2>

                {/* Notification */}
                {notification && (
                    <div
                        className={`notification ${notification.type}`}
                        style={{
                            padding: "15px",
                            borderRadius: "12px",
                            marginBottom: "20px",
                            color: "#fff",
                            backgroundColor: notification.type === "success" ? "#198754" : "#dc3545"
                        }}
                    >
                        {notification.message}
                    </div>
                )}

                {/* Description */}
                <div className="card">
                    <label>Mô tả</label>
                    <textarea
                        rows="5"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Mô tả tình hình lũ lụt..."
                    />
                </div>

                {/* Image Upload */}
                <div className="card dropzone" onDrop={handleDrop} onDragOver={handleDragOver}>
                    <label>Ảnh minh họa</label>
                    <input
                        type="file"
                        multiple
                        accept="image/*"
                        onChange={(e) => setFiles(Array.from(e.target.files))}
                    />
                    <p className="drop-text">Kéo thả ảnh vào đây hoặc click để chọn</p>
                    {files.length > 0 && (
                        <div className="preview-grid">
                            {files.map((f, i) => (
                                <div key={i} className="preview-item">
                                    <img src={URL.createObjectURL(f)} alt="preview" />
                                    <span className="preview-label">{f.name}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* GPS */}
                <div className="card">
                    <label>Vị trí GPS</label>
                    <button type="button" className="secondary" onClick={getLocation}>
                        Lấy vị trí hiện tại
                    </button>
                    {position && <p>Lat: {position.lat}, Lng: {position.lng}</p>}
                </div>

                {/* Water Height */}
                <div className="card">
                    <label>Độ cao nước (mét)</label>
                    <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={waterHeight}
                        onChange={(e) => setWaterHeight(e.target.value)}
                        placeholder="Nhập độ cao nước"
                    />
                </div>

                {/* Map */}
                <div className="card map-card">
                    <MapPicker position={position} onChange={setPosition} />
                </div>

                {/* Submit */}
                <button type="submit" className="primary" onClick={handleSubmit} disabled={loading}>
                    {loading ? "Đang gửi..." : "Gửi báo cáo"}
                </button>

                {/* Status */}
                {status && (
                    <div className="status-box">
                        <p><strong>ID:</strong> {status.id}</p>
                        <p><strong>Trạng thái:</strong> {status.status}</p>
                        {status.image_urls && status.image_urls.length > 0 && (
                            <div className="preview-grid">
                                {status.image_urls.map((url, i) => (
                                    <img key={i} src={url} alt="uploaded" width={100} />
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
