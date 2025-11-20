import React, { useState } from "react";
import axios from "axios";
import MapPicker from "./MapPicker";
import "../App.css";

export default function ReportForm() {
    const [description, setDescription] = useState("");
    const [reporterId, setReporterId] = useState(""); // Thêm reporterId
    const [files, setFiles] = useState([]);
    const [position, setPosition] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);

    // Lấy GPS từ trình duyệt
    const getLocation = () => {
        if (!navigator.geolocation) {
            alert("Trình duyệt không hỗ trợ GPS");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setPosition({
                    lat: pos.coords.latitude,
                    lng: pos.coords.longitude,
                });
            },
            () => alert("Không thể lấy vị trí")
        );
    };

    // Gửi form lên backend
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!description) return alert("Vui lòng nhập mô tả!");
        if (!reporterId) return alert("Vui lòng nhập Reporter ID!");

        setLoading(true);

        try {
            const form = new FormData();
            form.append("description", description);
            form.append("reporterId", reporterId);
            if (position) {
                form.append("latitude", position.lat);
                form.append("longitude", position.lng);
            }
            files.forEach((f) => form.append("images", f));

            const res = await axios.post(
                import.meta.env.VITE_API_BASE_URL + "/report",
                form
            );

            setStatus(res.data);
            alert("Đã gửi báo cáo!");
        } catch (e) {
            console.error(e);
            alert("Gửi thất bại.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <h2>Gửi Báo Cáo Hiện Trường</h2>

            <form onSubmit={handleSubmit}>
                <label>Reporter ID</label>
                <input
                    type="text"
                    value={reporterId}
                    onChange={(e) => setReporterId(e.target.value)}
                    required
                />

                <label>Mô tả</label>
                <textarea
                    rows="4"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />

                <label>Ảnh</label>
                <input
                    type="file"
                    multiple
                    onChange={(e) => setFiles(Array.from(e.target.files))}
                />

                {files.length > 0 && (
                    <div className="preview">
                        <p>Ảnh xem trước:</p>
                        <div style={{ display: "flex", gap: "10px" }}>
                            {files.map((f, i) => (
                                <img
                                    key={i}
                                    src={URL.createObjectURL(f)}
                                    alt="preview"
                                    width={100}
                                />
                            ))}
                        </div>
                    </div>
                )}

                <button type="button" onClick={getLocation}>
                    Lấy vị trí GPS
                </button>

                <div style={{ height: "300px", marginTop: "10px" }}>
                    <MapPicker position={position} onChange={setPosition} />
                </div>

                <button type="submit" disabled={loading}>
                    {loading ? "Đang gửi..." : "Gửi báo cáo"}
                </button>
            </form>

            {status && (
                <div className="status-box">
                    <p><strong>ID:</strong> {status.id}</p>
                    <p><strong>Trạng thái:</strong> {status.status}</p>
                    {status.image_urls && status.image_urls.length > 0 && (
                        <div>
                            <p><strong>Ảnh đã upload:</strong></p>
                            <div style={{ display: "flex", gap: "10px" }}>
                                {status.image_urls.map((url, i) => (
                                    <img key={i} src={url} alt="uploaded" width={100} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
