import React from 'react';
import { INFRASTRUCTURE_TYPES } from '../../constants';

export const SidebarControls = ({ logic, children }) => {
    const handleDeleteLast = () => {
        if (logic.currentLinePoints.length > 0) logic.setCurrentLinePoints(logic.currentLinePoints.slice(0, -1));
        else if (logic.pendingFeatures.length > 0) logic.setPendingFeatures(logic.pendingFeatures.slice(0, -1));
    };

    return (
        <>
            <div className="section">
                <h3>1. Select Type</h3>
                <div className="toggle-container">
                    <label className="switch">
                        <input type="checkbox" checked={logic.showAllFeatures} onChange={(e) => logic.setShowAllFeatures(e.target.checked)} />
                        <span className="slider"></span>
                    </label>
                    <span>Show All Features</span>
                </div>
                <div className="type-selector">
                    {Object.keys(INFRASTRUCTURE_TYPES).map(type => (
                        <button key={type} className={`type-btn ${logic.selectedType === type ? 'active' : ''}`}
                            onClick={() => logic.setSelectedType(type)}
                            style={{ borderLeft: `5px solid ${INFRASTRUCTURE_TYPES[type].color}` }}>
                            {type}
                        </button>
                    ))}
                </div>
            </div>
            <div className="section">
                <h3>2. Properties</h3>
                {INFRASTRUCTURE_TYPES[logic.selectedType].props.map(prop => (
                    <div key={prop} className="form-group">
                        <label>{prop.replace(/_/g, ' ')}:</label>
                        <input type="text" name={prop} value={logic.featureProperties[prop] || ''}
                            onChange={(e) => logic.setFeatureProperties(prev => ({ ...prev, [e.target.name]: e.target.value }))}
                            placeholder={`Enter ${prop}...`} />
                    </div>
                ))}
            </div>
            <div className="section">
                <h3>3. Actions</h3>
                <div className="action-buttons">
                    {INFRASTRUCTURE_TYPES[logic.selectedType].type === "LineString" && (
                        <button onClick={logic.finishLine} disabled={logic.currentLinePoints.length < 2} className="btn btn-primary">Finish Line</button>
                    )}
                    <button onClick={handleDeleteLast} className="delete-btn">Delete Last</button>
                </div>
            </div>
            <div className="section footer-actions">
                {children}
            </div>
        </>
    );
};
