import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { SidebarControls } from '../components/UI/SidebarControls';
import { ExportModal } from '../components/UI/ExportModal';
import { MapView } from '../components/Map/MapView';
import { useMapLogic } from '../hooks/useMapLogic';
import AuthService from '../services/authService';
import apiClient from '../services/apiClient';
import { groupContributionsByBatch } from '../utils/mapUtils';
import { INFRASTRUCTURE_TYPES } from '../constants';

export function AdminView() {
    const logic = useMapLogic();
    const [isAuthenticated, setIsAuthenticated] = useState(AuthService.isAuthenticated());
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [contributions, setContributions] = useState([]);
    const [batches, setBatches] = useState([]);
    const [selectedBatch, setSelectedBatch] = useState(null);
    const [activeTab, setActiveTab] = useState('contributions'); // 'contributions' or 'features'
    
    // Export modal states
    const [showExportModal, setShowExportModal] = useState(false);
    const [selectedExportTypes, setSelectedExportTypes] = useState(
        Object.values(INFRASTRUCTURE_TYPES).map(config => config.code)
    );

    // Filter text states
    const [filterWords, setFilterWords] = useState([]);
    const [showFilterModal, setShowFilterModal] = useState(false);
    const [filterWordsText, setFilterWordsText] = useState('');

    // Load filter words from file on mount
    useEffect(() => {
        fetch('/filter_text.txt')
            .then(res => res.text())
            .then(text => {
                const words = text.split('\n').map(w => w.trim().toLowerCase()).filter(w => w);
                setFilterWords(words);
                setFilterWordsText(words.join('\n'));
            })
            .catch(err => {
                console.error('Failed to load filter words:', err);
                // Default filter words
                const defaultWords = ['hacker', 'lỏ', 'test', 'spam', 'cặc', 'lồn', 'địt', 'đụ'];
                setFilterWords(defaultWords);
                setFilterWordsText(defaultWords.join('\n'));
            });
    }, []);

    useEffect(() => {
        if (isAuthenticated) {
            fetchContributions();
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (contributions.length > 0) {
            const grouped = groupContributionsByBatch(contributions);
            setBatches(grouped);
        } else {
            setBatches([]);
        }
    }, [contributions]);

    // Filter batches based on filter words
    const containsFilterWord = (text) => {
        if (!text) return false;
        const lowerText = text.toLowerCase();
        return filterWords.some(word => lowerText.includes(word));
    };

    const batchContainsFilterWord = (batch) => {
        // Check contributor name, msv
        if (containsFilterWord(batch.contributor_name)) return true;
        if (containsFilterWord(batch.msv)) return true;
        
        // Check all features in batch
        for (const feature of batch.features) {
            if (feature.properties) {
                const propsStr = JSON.stringify(feature.properties);
                if (containsFilterWord(propsStr)) return true;
            }
            if (containsFilterWord(feature.contributor_name)) return true;
            if (containsFilterWord(feature.msv)) return true;
        }
        return false;
    };

    const filteredBatches = batches.filter(batch => batchContainsFilterWord(batch));

    // Update filter words from modal
    const handleSaveFilterWords = () => {
        const words = filterWordsText.split('\n').map(w => w.trim().toLowerCase()).filter(w => w);
        setFilterWords(words);
        setShowFilterModal(false);
    };

    // Reject all filtered batches
    const handleRejectAllFiltered = async () => {
        if (filteredBatches.length === 0) {
            alert('No contributions match the filter criteria');
            return;
        }
        
        if (!window.confirm(`Reject ALL ${filteredBatches.length} batches (${filteredBatches.reduce((sum, b) => sum + b.count, 0)} items) containing filtered words?`)) return;
        
        try {
            // Collect all features from all filtered batches
            const allFilteredFeatures = filteredBatches.flatMap(batch => batch.features);
            
            await Promise.all(allFilteredFeatures.map(f => apiClient.delete(`/api/contributions/${f._id}`)));
            
            const remainingContributions = contributions.filter(
                c => !allFilteredFeatures.find(f => f._id === c._id)
            );
            setContributions(remainingContributions);
            
            setSelectedBatch(null);
            alert(`Rejected ${filteredBatches.length} batches (${allFilteredFeatures.length} contributions)!`);
        } catch (err) {
            console.error("Error rejecting filtered batches", err);
            alert("Failed to reject some contributions");
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            await AuthService.login(username, password);
            setIsAuthenticated(true);
            setError("");
        } catch (err) {
            setError("Invalid credentials");
            console.error("Login failed", err);
        }
    };

    const handleLogout = () => {
        AuthService.logout();
        setIsAuthenticated(false);
        setContributions([]);
        setBatches([]);
        setSelectedBatch(null);
    };

    const fetchContributions = async () => {
        try {
            const res = await apiClient.get('/api/contributions');
            setContributions(res.data);
        } catch (err) {
            console.error("Failed to fetch contributions", err);
            if (err.response && err.response.status === 401) {
                handleLogout();
            }
        }
    };

    const handleApproveBatch = async (batch) => {
        try {
            await Promise.all(batch.features.map(f => apiClient.post(`/api/contributions/${f._id}/approve`)));
            
            const remaining = contributions.filter(c => !batch.features.find(f => f._id === c._id));
            setContributions(remaining);
            
            logic.fetchFeatures();
            setSelectedBatch(null);
            alert(`Approved ${batch.count} contributions!`);
        } catch (err) {
            console.error("Error approving batch", err);
            alert("Failed to approve batch");
        }
    };

    const handleRejectBatch = async (batch) => {
        if (!window.confirm(`Reject all ${batch.count} contributions in this batch?`)) return;
        
        try {
            await Promise.all(batch.features.map(f => apiClient.delete(`/api/contributions/${f._id}`)));
            
            const remaining = contributions.filter(c => !batch.features.find(f => f._id === c._id));
            setContributions(remaining);
            
            setSelectedBatch(null);
            alert("Batch rejected");
        } catch (err) {
            console.error("Error rejecting batch", err);
            alert("Failed to reject batch");
        }
    };

    const handleDeleteFeature = async (featureId) => {
        if (!window.confirm("Delete this feature?")) return;
        try {
            await apiClient.delete(`/api/features/${featureId}`);
            logic.fetchFeatures();
            alert("Feature deleted");
        } catch (err) {
            console.error("Error deleting feature", err);
            alert("Failed to delete feature");
        }
    };

    const visualizeBatch = (batch) => {
        setSelectedBatch(batch);
        if (batch.features.length > 0) {
            logic.focusFeature(batch.features[0]);
        }
    };

    // Export handlers
    const toggleExportType = (code) => {
        setSelectedExportTypes(prev =>
            prev.includes(code)
                ? prev.filter(c => c !== code)
                : [...prev, code]
        );
    };

    const selectAllExportTypes = () => {
        setSelectedExportTypes(Object.values(INFRASTRUCTURE_TYPES).map(config => config.code));
    };

    const deselectAllExportTypes = () => {
        setSelectedExportTypes([]);
    };

    const handleExportCsv = async () => {
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const types = selectedExportTypes.join(',');
        const url = `${API_BASE_URL}/api/export_csv${types ? `?types=${types}` : ''}`;
        
        try {
            // Fetch the CSV file as blob
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error('Export failed');
            }
            
            // Get the blob data
            const blob = await response.blob();
            
            // Create a temporary URL for the blob
            const blobUrl = window.URL.createObjectURL(blob);
            
            // Create a temporary link and trigger download
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = 'infrastructure_export.csv';
            document.body.appendChild(link);
            link.click();
            
            // Cleanup
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
            
            setShowExportModal(false);
            alert('File exported successfully!');
        } catch (err) {
            console.error('Export error:', err);
            alert('Failed to export data');
        }
    };


    if (!isAuthenticated) {
        return (
            <div className="login-container">
                <form onSubmit={handleLogin} className="login-form">
                    <h2>Admin Login</h2>
                    <div className="form-group">
                        <label>Username:</label>
                        <input 
                            type="text" 
                            value={username} 
                            onChange={e => setUsername(e.target.value)} 
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <label>Password:</label>
                        <input 
                            type="password" 
                            value={password} 
                            onChange={e => setPassword(e.target.value)} 
                            className="form-control"
                        />
                    </div>
                    {error && <p style={{ color: 'red' }}>{error}</p>}
                    <button type="submit" className="save-btn" style={{width: '100%'}}>Login</button>
                    <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                        <Link to="/" className="back-link">Back to Map</Link>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="app-container">
            <div className="sidebar left-sidebar">
                <h2>Admin Panel</h2>
                <div className="admin-controls">
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                        <button onClick={handleLogout} className="logout-btn" style={{ flex: 1 }}>Logout</button>
                        <button onClick={() => setShowExportModal(true)} className="save-btn" style={{ flex: 1 }}>Export CSV</button>
                    </div>
                    <div className="tab-controls" style={{ margin: '1rem 0' }}>
                        <button 
                            onClick={() => setActiveTab('contributions')}
                            className={activeTab === 'contributions' ? 'active' : ''}
                        >
                            Contributions ({contributions.length})
                        </button>
                        <button 
                            onClick={() => setActiveTab('features')}
                            className={activeTab === 'features' ? 'active' : ''}
                        >
                            Manage Features
                        </button>
                    </div>
                </div>
                
                <SidebarControls logic={logic}>
                    <Link to="/" className="back-link">View as User</Link>
                </SidebarControls>

                {activeTab === 'contributions' && (
                    <div className="contributions-list">
                        {/* Filter Reject Section */}
                        <div style={{ 
                            padding: '0.75rem', 
                            marginBottom: '1rem', 
                            backgroundColor: '#fff3cd', 
                            borderRadius: '8px',
                            border: '1px solid #ffc107'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>🔍 Filter & Reject Spam</span>
                                <button 
                                    onClick={() => setShowFilterModal(true)} 
                                    className="btn"
                                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                    title="Edit filter words"
                                >
                                    ⚙️ Edit
                                </button>
                            </div>
                            <small style={{ display: 'block', color: '#856404', marginBottom: '0.5rem' }}>
                                Found {filteredBatches.length} batch(es) with: {filterWords.slice(0, 5).join(', ')}{filterWords.length > 5 ? '...' : ''}
                            </small>
                            <button 
                                onClick={handleRejectAllFiltered}
                                className="reject-btn"
                                style={{ width: '100%' }}
                                disabled={filteredBatches.length === 0}
                            >
                                🗑️ Reject All Filtered ({filteredBatches.length} batches)
                            </button>
                        </div>

                        <h3>Pending Batches ({batches.length})</h3>
                        {batches.length === 0 ? <p>No pending contributions</p> : (
                            <div className="batch-list">
                                {batches.map(batch => (
                                    <div key={batch.batchId} className="batch-item">
                                        <div className="batch-header" onClick={() => visualizeBatch(batch)}>
                                            <div className="batch-info">
                                                <strong>{batch.contributor_name}</strong>
                                                <small>{batch.count} items • {new Date(batch.timestamp).toLocaleTimeString()}</small>
                                                <small>MSV: {batch.msv}</small>
                                            </div>
                                            <div className="batch-actions">
                                                <button onClick={(e) => { e.stopPropagation(); handleApproveBatch(batch); }} className="approve-btn">✓</button>
                                                <button onClick={(e) => { e.stopPropagation(); handleRejectBatch(batch); }} className="reject-btn">✗</button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="map-wrapper">
                {console.log("AdminView features:", logic.features)}
                <MapView 
                    {...logic} 
                    dbFeatures={logic.features}
                    onZoomChange={logic.setCurrentZoom} 
                    onDeleteFeature={handleDeleteFeature}
                    isAdmin={true}
                    // Pass pending features for visualization
                    reviewFeatures={selectedBatch ? selectedBatch.features : []}
                />
            </div>

            {selectedBatch && activeTab === 'contributions' && (
                <div className="sidebar right-sidebar">
                    <h3>Batch Details</h3>
                    <div className="batch-info-panel">
                        <p><strong>Contributor:</strong> {selectedBatch.contributor_name}</p>
                        <p><strong>MSV:</strong> {selectedBatch.msv}</p>
                        <p><strong>Time:</strong> {new Date(selectedBatch.timestamp).toLocaleString()}</p>
                        <p><strong>Count:</strong> {selectedBatch.count}</p>
                        
                        <div className="batch-footer-actions">
                            <button onClick={() => handleApproveBatch(selectedBatch)} className="approve-btn">Approve All</button>
                            <button onClick={() => handleRejectBatch(selectedBatch)} className="reject-btn">Reject All</button>
                        </div>
                    </div>

                    <h4>Features in Batch</h4>
                    <ul className="feature-list">
                        {selectedBatch.features.map((f, idx) => (
                            <li key={f._id || idx} className="feature-item" onClick={() => logic.focusFeature(f)}>
                                <div className="feature-info">
                                    <strong>{f?.properties?.feature_type || 'Unknown Type'}</strong>
                                    <span>{f?.properties ? JSON.stringify(f.properties).slice(0, 30) : ''}...</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                    
                    <button onClick={() => setSelectedBatch(null)} className="btn" style={{marginTop: '20px', width: '100%'}}>Close Preview</button>
                </div>
            )}

            {/* Show Drafts in Right Sidebar if no batch selected but drafts exist */}
            {!selectedBatch && logic.pendingFeatures.length > 0 && (
                <div className="sidebar right-sidebar">
                    <h3>Admin Drafts ({logic.pendingFeatures.length})</h3>
                    <ul className="feature-list">
                        {logic.pendingFeatures.map((feature, idx) => (
                            <li key={idx} className="feature-item" onClick={() => logic.focusFeature(feature)}>
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
                    <div style={{marginTop: '20px'}}>
                        <button 
                            onClick={async () => {
                                try {
                                    await Promise.all(logic.pendingFeatures.map(feature => {
                                        const { id, ...featureWithoutId } = feature;
                                        return apiClient.post('/api/features', featureWithoutId);
                                    }));
                                    alert(`Saved ${logic.pendingFeatures.length} features!`);
                                    logic.setPendingFeatures([]);
                                    logic.fetchFeatures();
                                } catch (err) {
                                    console.error("Error saving", err);
                                    alert("Failed to save");
                                }
                            }} 
                            className="save-btn"
                            style={{width: '100%'}}
                        >
                            Save All Drafts
                        </button>
                        <button 
                            onClick={() => logic.setPendingFeatures([])} 
                            className="reject-btn"
                            style={{width: '100%', marginTop: '10px'}}
                        >
                            Clear All
                        </button>
                    </div>
                </div>
            )}

            {/* Export Modal */}
            <ExportModal 
                logic={{
                    showExportModal,
                    setShowExportModal,
                    selectedExportTypes,
                    toggleExportType,
                    selectAllExportTypes,
                    deselectAllExportTypes,
                    handleExportCsv
                }}
            />

            {/* Filter Words Modal */}
            {showFilterModal && (
                <div className="modal-overlay" onClick={() => setShowFilterModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3>Edit Filter Words</h3>
                        <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '1rem' }}>
                            Enter words to filter (one per line). Contributions containing these words (case-insensitive) will be shown when filter is enabled.
                        </p>
                        <textarea
                            value={filterWordsText}
                            onChange={e => setFilterWordsText(e.target.value)}
                            style={{
                                width: '100%',
                                height: '200px',
                                padding: '0.5rem',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                fontFamily: 'monospace',
                                fontSize: '0.9rem',
                                resize: 'vertical'
                            }}
                            placeholder="Enter filter words, one per line..."
                        />
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', justifyContent: 'flex-end' }}>
                            <button onClick={() => setShowFilterModal(false)} className="btn">Cancel</button>
                            <button onClick={handleSaveFilterWords} className="save-btn">Save</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
