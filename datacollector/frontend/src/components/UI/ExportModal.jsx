import React from 'react';
import { INFRASTRUCTURE_TYPES } from '../../constants';

export const ExportModal = ({ logic }) => {
    if (!logic.showExportModal) return null;
    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h3>Export Options</h3>
                <p>Select infrastructure types to export:</p>
                <div className="modal-actions">
                    <button onClick={logic.selectAllExportTypes} className="small-btn">Select All</button>
                    <button onClick={logic.deselectAllExportTypes} className="small-btn">Deselect All</button>
                </div>
                <div className="checkbox-list">
                    {Object.entries(INFRASTRUCTURE_TYPES).map(([label, config]) => (
                        <label key={config.code} className="checkbox-item">
                            <input type="checkbox" checked={logic.selectedExportTypes.includes(config.code)} onChange={() => logic.toggleExportType(config.code)} />
                            {label}
                        </label>
                    ))}
                </div>
                <div className="modal-footer">
                    <button onClick={() => logic.setShowExportModal(false)} className="cancel-btn">Cancel</button>
                    <button onClick={logic.handleExportCsv} className="confirm-btn">Export CSV</button>
                </div>
            </div>
        </div>
    );
};
