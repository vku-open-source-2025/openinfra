import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../services/apiClient';

export function Leaderboard() {
    const [leaders, setLeaders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLeaderboard = async () => {
            try {
                const response = await apiClient.get('/api/leaderboard');
                setLeaders(response.data);
            } catch (error) {
                console.error("Error fetching leaderboard:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchLeaderboard();
    }, []);

    const getRankIcon = (rank) => {
        switch(rank) {
            case 1: return "🥇";
            case 2: return "🥈";
            case 3: return "🥉";
            default: return rank;
        }
    };

    return (
        <div className="app-container" style={{background: '#f0f2f5'}}>
            <div className="leaderboard-content">
                <div className="leaderboard-header">
                    <Link to="/" className="back-btn">← Back to Map</Link>
                    <h1>🏆 Top Contributors</h1>
                    <p>
                        Cảm ơn rất nhiều vì các bạn đã bỏ thời gian công sức quý báu ra để đóng góp dữ liệu cho dự án <br/>
                        

                    </p>
                </div>

                {loading ? (
                    <div className="loading-spinner">Loading...</div>
                ) : (
                    <div className="leaderboard-card">
                        {leaders.length === 0 ? (
                            <div className="empty-state">
                                <p>No contributions yet. Be the first!</p>
                                <Link to="/" className="contribute-btn">Start Mapping</Link>
                            </div>
                        ) : (
                            <table className="leaderboard-table">
                                <thead>
                                    <tr>
                                        <th style={{width: '100px', textAlign: 'center'}}>Rank</th>
                                        <th>Contributor</th>
                                        <th style={{textAlign: 'right'}}>Points</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {leaders.map((leader, index) => (
                                        <tr key={index} className={`rank-row rank-${index + 1}`}>
                                            <td className="rank-cell">
                                                <span className={`rank-badge rank-${index + 1}`}>
                                                    {getRankIcon(index + 1)}
                                                </span>
                                            </td>
                                            <td className="name-cell">
                                                <div className="contributor-info">
                                                    <span className="name">{leader.contributor_name}</span>
                                                    <span className="msv">{leader.msv}</span>
                                                    <span className="unit">{leader.unit || "VKU"}</span>
                                                </div>
                                            </td>
                                            <td className="count-cell">{leader.count}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
