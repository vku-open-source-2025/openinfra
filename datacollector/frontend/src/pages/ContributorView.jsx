import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { useMapLogic } from '../hooks/useMapLogic';
import { SidebarControls } from '../components/UI/SidebarControls';
import { MapView } from '../components/Map/MapView';
import { API_URL } from '../config';

export function ContributorView() {
    const logic = useMapLogic();
    const [showContribModal, setShowContribModal] = useState(false);
    const [contributorName, setContributorName] = useState("");
    const [msv, setMsv] = useState("");
    const [unit, setUnit] = useState("VKU");

    const handleContribute = async () => {
        if (!contributorName || !msv) { alert("Please enter Name and MSV"); return; }
        try {
            await Promise.all(logic.pendingFeatures.map(feature => {
                // Remove id field as backend doesn't accept it
                const { id, ...featureWithoutId } = feature;
                return axios.post(`${API_URL}/api/contributions`, {
                    ...featureWithoutId,
                    contributor_name: contributorName,
                    msv: msv,
                    unit: unit
                });
            }));
            alert("Contribution submitted for review!");
            logic.setPendingFeatures([]);
            setShowContribModal(false);
        } catch (error) { 
            console.error("Error submitting contribution:", error);
            alert("Error submitting contribution"); 
        }
    };

    return (
        <div className="app-container">
            <div className="sidebar left-sidebar">
                <h2>OpenInfra GIS</h2>
                <SidebarControls logic={logic}>
                    <button onClick={() => logic.pendingFeatures.length > 0 ? setShowContribModal(true) : alert("Nothing to contribute")} className="save-btn">Contribute</button>
                    <Link to="/leaderboard" className="back-link">🏆 Leaderboard</Link>
                    <Link to="/admin" className="back-link">Admin Panel</Link>
                </SidebarControls>
            </div>

            <div className="map-wrapper">
                <MapView 
                    {...logic} 
                    dbFeatures={logic.features}
                    onZoomChange={logic.setCurrentZoom} 
                    onDeleteFeature={() => {}} 
                    isAdmin={false} 
                />
            </div>

            {/* Right Sidebar - Show Pending Features */}
            <div className="sidebar right-sidebar">
                <h3>Your Drafts</h3>
                {logic.pendingFeatures.length === 0 ? (
                    <p className="empty-msg">No pending features. Click on map to draw.</p>
                ) : (
                    <ul className="feature-list">
                        {logic.pendingFeatures.map((feature, idx) => (
                            <li key={idx} className="feature-item" onClick={() => logic.focusFeature(feature)} style={{cursor: 'pointer'}}>
                                <div className="feature-info">
                                    <strong>{feature.properties.feature_type}</strong>
                                    <span>{feature.geometry.type}</span>
                                </div>
                                <button className="delete-item-btn" onClick={(e) => {
                                    e.stopPropagation();
                                    const newFeatures = [...logic.pendingFeatures];
                                    newFeatures.splice(idx, 1);
                                    logic.setPendingFeatures(newFeatures);
                                }}>×</button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            
            {/* Contribution Modal */}
            {showContribModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>Submit Contribution</h3>
                        <div className="form-group">
                            <label>Name:</label>
                            <input type="text" value={contributorName} onChange={e => setContributorName(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>MSV (Student ID):</label>
                            <input type="text" value={msv} onChange={e => setMsv(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Unit (Đơn vị):</label>
                            <input type="text" value={unit} onChange={e => setUnit(e.target.value)} placeholder="VKU" />
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowContribModal(false)} className="cancel-btn">Cancel</button>
                            <button onClick={handleContribute} className="confirm-btn">Submit</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
