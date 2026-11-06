// SPDX-License-Identifier: Apache-2.0
// SPDX-FileCopyrightText: 2026 VKU.VIC
import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const LINKS = [
  { to: '/', label: 'Bản đồ' },
  { to: '/leaderboard', label: 'Bảng xếp hạng' },
  { to: '/admin', label: 'Quản trị' },
];

export function SiteHeader({ subtitle = 'Nền tảng đóng góp dữ liệu hạ tầng' }) {
  const { pathname } = useLocation();
  const isActive = (to) => (to === '/' ? pathname === '/' : pathname.startsWith(to));

  return (
    <header className="site-header">
      <Link to="/" className="site-brand">
        <span className="site-brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z" />
            <circle cx="12" cy="10" r="2.6" />
          </svg>
        </span>
        <span className="site-brand-copy">
          <span className="site-brand-name">OpenInfra GIS</span>
          <span className="site-brand-sub">SynapseCity · {subtitle}</span>
        </span>
      </Link>

      <nav className="site-nav" aria-label="Điều hướng chính">
        {LINKS.map((link) => (
          <Link key={link.to} to={link.to} className={`site-nav-link${isActive(link.to) ? ' active' : ''}`}>
            {link.label}
          </Link>
        ))}
      </nav>

      <div className="site-meta">
        <span className="site-pill">Dữ liệu mở · PDDL 1.0</span>
      </div>
    </header>
  );
}
