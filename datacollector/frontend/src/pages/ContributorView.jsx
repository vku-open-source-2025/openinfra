import React, { useState } from 'react';
import axios from 'axios';
import { useMapLogic } from '../hooks/useMapLogic';
import { SidebarControls } from '../components/UI/SidebarControls';
import { MapView } from '../components/Map/MapView';
import { API_URL } from '../config';
import { SiteHeader } from '../components/UI/SiteHeader';

const IDENTITY_KEY = 'openinfra.contributor.v1';
const EMPTY_IDENTITY = { name: '', msv: '', unit: 'VKU' };

function readSavedIdentity() {
    try {
        const raw = window.localStorage.getItem(IDENTITY_KEY);
        if (!raw) return { ...EMPTY_IDENTITY };
        const parsed = JSON.parse(raw);
        return {
            name: typeof parsed?.name === 'string' ? parsed.name : '',
            msv: typeof parsed?.msv === 'string' ? parsed.msv : '',
            unit: typeof parsed?.unit === 'string' && parsed.unit ? parsed.unit : 'VKU',
        };
    } catch {
        return { ...EMPTY_IDENTITY };
    }
}

function persistIdentity(identity) {
    try {
        window.localStorage.setItem(IDENTITY_KEY, JSON.stringify(identity));
    } catch {
        // Private mode / storage full: the form still works for this session.
    }
}

function forgetIdentity() {
    try {
        window.localStorage.removeItem(IDENTITY_KEY);
    } catch {
        // ignore storage errors
    }
}

export function ContributorView() {
    const logic = useMapLogic();
    const [showContribModal, setShowContribModal] = useState(false);
    const [savedIdentity, setSavedIdentity] = useState(readSavedIdentity);
    const [form, setForm] = useState(readSavedIdentity);
    const [submitting, setSubmitting] = useState(false);

    const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

    const openContribution = () => {
        if (logic.pendingFeatures.length === 0) {
            alert('Chưa có dữ liệu nào để đóng góp. Hãy vẽ trên bản đồ trước.');
            return;
        }
        setForm(savedIdentity.name || savedIdentity.msv ? savedIdentity : form);
        setShowContribModal(true);
    };

    const submitContribution = async (anonymous) => {
        if (logic.pendingFeatures.length === 0) return;
        const name = form.name.trim();
        const msv = form.msv.trim();
        const unit = form.unit.trim() || 'VKU';

        if (!anonymous && (!name || !msv)) {
            alert('Vui lòng nhập họ tên và MSSV, hoặc chọn "Đóng góp ẩn danh".');
            return;
        }

        setSubmitting(true);
        try {
            await Promise.all(logic.pendingFeatures.map((feature) => {
                // Remove id field as backend doesn't accept it
                const { id, ...featureWithoutId } = feature;
                return axios.post(`${API_URL}/api/contributions`, {
                    ...featureWithoutId,
                    ...(anonymous
                        ? { anonymous: true }
                        : { contributor_name: name, msv, unit }),
                });
            }));

            if (!anonymous) {
                const identity = { name, msv, unit };
                setSavedIdentity(identity);
                persistIdentity(identity);
            }

            alert(anonymous ? 'Đã gửi đóng góp ẩn danh!' : 'Đã gửi đóng góp để duyệt!');
            logic.setPendingFeatures([]);
            setShowContribModal(false);
        } catch (error) {
            console.error('Error submitting contribution:', error);
            alert('Không gửi được đóng góp. Vui lòng thử lại.');
        } finally {
            setSubmitting(false);
        }
    };

    const hasSavedIdentity = Boolean(savedIdentity.name || savedIdentity.msv);

    return (
        <div className="page">
            <SiteHeader />
            <div className="app-container">
            <div className="sidebar left-sidebar">
                <SidebarControls logic={logic}>
                    <button onClick={openContribution} className="save-btn">
                        Đóng góp dữ liệu
                    </button>
                </SidebarControls>

                {hasSavedIdentity ? (
                    <div className="identity-card">
                        <span className="identity-avatar" aria-hidden="true">
                            {(savedIdentity.name || '?').trim().charAt(0).toUpperCase()}
                        </span>
                        <div className="identity-copy">
                            <strong>{savedIdentity.name || 'Ẩn danh'}</strong>
                            <span>
                                {savedIdentity.msv}
                                {savedIdentity.unit ? ` · ${savedIdentity.unit}` : ''}
                            </span>
                            <small>Tự động điền cho lần đóng góp sau</small>
                        </div>
                        <button
                            type="button"
                            className="identity-clear"
                            onClick={() => {
                                forgetIdentity();
                                setSavedIdentity({ ...EMPTY_IDENTITY });
                                setForm({ ...EMPTY_IDENTITY });
                            }}
                            aria-label="Xóa danh tính đã lưu"
                            title="Xóa danh tính đã lưu"
                        >
                            ×
                        </button>
                    </div>
                ) : (
                    <p className="identity-hint">
                        Điền họ tên một lần, các lần sau sẽ tự điền. Bạn cũng có thể
                        gửi đóng góp ẩn danh mà không cần thông tin.
                    </p>
                )}
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
                <div className="modal-overlay" role="presentation" onClick={() => !submitting && setShowContribModal(false)}>
                    <div className="modal-content" role="dialog" aria-modal="true" aria-labelledby="contribution-title" onClick={(e) => e.stopPropagation()}>
                        <h3 id="contribution-title">Gửi đóng góp</h3>
                        <p>
                            Thông tin chỉ dùng để ghi nhận đóng góp và được lưu trên
                            thiết bị này để tự điền lần sau.
                        </p>
                        <div className="form-group">
                            <label htmlFor="contributor-name">Họ và tên:</label>
                            <input
                                id="contributor-name"
                                type="text"
                                autoComplete="name"
                                value={form.name}
                                onChange={(e) => updateField('name', e.target.value)}
                                placeholder="Nguyễn Văn A"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="contributor-msv">MSSV / Mã cán bộ:</label>
                            <input
                                id="contributor-msv"
                                type="text"
                                autoComplete="username"
                                value={form.msv}
                                onChange={(e) => updateField('msv', e.target.value)}
                                placeholder="2212345"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="contributor-unit">Đơn vị:</label>
                            <input
                                id="contributor-unit"
                                type="text"
                                autoComplete="organization"
                                value={form.unit}
                                onChange={(e) => updateField('unit', e.target.value)}
                                placeholder="VKU"
                            />
                        </div>
                        {hasSavedIdentity && (
                            <p className="form-hint">
                                Đã điền từ danh tính lưu trên thiết bị. Bấm “×” ở thẻ
                                danh tính để xóa.
                            </p>
                        )}
                        <div className="modal-footer">
                            <button type="button" onClick={() => setShowContribModal(false)} className="cancel-btn" disabled={submitting}>
                                Hủy
                            </button>
                            <button type="button" onClick={() => submitContribution(true)} className="anon-btn" disabled={submitting}>
                                Đóng góp ẩn danh
                            </button>
                            <button type="button" onClick={() => submitContribution(false)} className="confirm-btn" disabled={submitting}>
                                {submitting ? 'Đang gửi…' : 'Gửi đóng góp'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            </div>
        </div>
    );
}
