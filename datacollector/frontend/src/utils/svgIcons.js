// Custom SVG icons for infrastructure types
export const SVG_ICONS = {
  // Trạm điện - Power Station
  tram_dien: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(7, 7)">
        <!-- Building structure -->
        <rect x="2" y="6" width="12" height="10" fill="white" stroke="#333" stroke-width="0.8"/>
        <!-- Roof -->
        <path d="M 1 6 L 8 2 L 15 6 Z" fill="#FFD700" stroke="#333" stroke-width="0.8"/>
        <!-- Lightning bolt -->
        <path d="M 8 4 L 6 9 L 8.5 9 L 6.5 13 L 10 8 L 7.5 8 Z" fill="#FFD700" stroke="#333" stroke-width="0.5"/>
        <!-- Windows -->
        <rect x="4" y="8" width="2" height="2" fill="#87CEEB"/>
        <rect x="10" y="8" width="2" height="2" fill="#87CEEB"/>
        <rect x="4" y="12" width="2" height="2" fill="#87CEEB"/>
        <rect x="10" y="12" width="2" height="2" fill="#87CEEB"/>
      </g>
    </svg>
  `,
  
  // Cột điện - Electric Pole
  cot_dien: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(7, 5)">
        <!-- Main pole -->
        <rect x="6.5" y="2" width="1.5" height="16" fill="#8B4513" stroke="#333" stroke-width="0.5"/>
        <!-- Cross arm -->
        <rect x="1" y="4" width="14" height="1.2" fill="#8B4513" stroke="#333" stroke-width="0.5"/>
        <!-- Insulators -->
        <circle cx="2.5" cy="3.5" r="1" fill="#4682B4" stroke="#333" stroke-width="0.5"/>
        <circle cx="7.5" cy="3.5" r="1" fill="#4682B4" stroke="#333" stroke-width="0.5"/>
        <circle cx="12.5" cy="3.5" r="1" fill="#4682B4" stroke="#333" stroke-width="0.5"/>
        <!-- Power lines -->
        <path d="M 2.5 2.5 Q 5 1.5 7.5 2.5" stroke="#333" stroke-width="0.8" fill="none"/>
        <path d="M 7.5 2.5 Q 10 1.5 12.5 2.5" stroke="#333" stroke-width="0.8" fill="none"/>
      </g>
    </svg>
  `,
  
  // Đèn đường - Street Light
  den_duong: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(9, 4)">
        <!-- Pole -->
        <rect x="5" y="4" width="1.5" height="15" fill="#666" stroke="#333" stroke-width="0.5"/>
        <!-- Lamp head -->
        <path d="M 3 3 L 3 5 L 9 5 L 9 3 Q 6 1 3 3 Z" fill="#FFD700" stroke="#333" stroke-width="0.8"/>
        <!-- Light glow -->
        <ellipse cx="6" cy="6" rx="5" ry="2" fill="#FFFF99" opacity="0.6"/>
        <!-- Base -->
        <rect x="4" y="18" width="3.5" height="1.5" fill="#666" stroke="#333" stroke-width="0.5"/>
      </g>
    </svg>
  `,
  
  // Đèn giao thông - Traffic Light
  den_giao_thong: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(8, 3)">
        <!-- Pole -->
        <rect x="6" y="10" width="1.5" height="12" fill="#444" stroke="#333" stroke-width="0.5"/>
        <!-- Traffic light housing -->
        <rect x="3" y="2" width="8" height="10" rx="1" fill="#333" stroke="#222" stroke-width="0.8"/>
        <!-- Red light -->
        <circle cx="7" cy="4" r="1.8" fill="#FF4444" stroke="#222" stroke-width="0.5"/>
        <!-- Yellow light -->
        <circle cx="7" cy="7" r="1.8" fill="#FFD700" stroke="#222" stroke-width="0.5"/>
        <!-- Green light -->
        <circle cx="7" cy="10" r="1.8" fill="#44FF44" stroke="#222" stroke-width="0.5"/>
        <!-- Base -->
        <rect x="5.5" y="21" width="2.5" height="1" fill="#444"/>
      </g>
    </svg>
  `,
  
  // Cống thoát nước - Drainage pipe (for LineString, shown as waypoint)
  cong_thoat_nuoc: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(6, 8)">
        <!-- Manhole cover -->
        <circle cx="9" cy="7" r="7.5" fill="#555" stroke="#333" stroke-width="1"/>
        <circle cx="9" cy="7" r="6" fill="none" stroke="#777" stroke-width="0.8"/>
        <circle cx="9" cy="7" r="4" fill="none" stroke="#777" stroke-width="0.8"/>
        <!-- Grid pattern -->
        <line x1="9" y1="1" x2="9" y2="13" stroke="#777" stroke-width="0.5"/>
        <line x1="3" y1="7" x2="15" y2="7" stroke="#777" stroke-width="0.5"/>
      </g>
    </svg>
  `,
  
  // Ống dẫn nước - Water pipe (for LineString, shown as waypoint)
  ong_dan_nuoc: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(6, 8)">
        <!-- Water valve -->
        <circle cx="9" cy="7" r="7" fill="#4169E1" stroke="#333" stroke-width="1"/>
        <!-- Valve wheel -->
        <circle cx="9" cy="7" r="5" fill="none" stroke="white" stroke-width="1.2"/>
        <line x1="9" y1="2" x2="9" y2="12" stroke="white" stroke-width="1.2"/>
        <line x1="4" y1="7" x2="14" y2="7" stroke="white" stroke-width="1.2"/>
        <line x1="6" y1="4" x2="12" y2="10" stroke="white" stroke-width="1.2"/>
        <line x1="6" y1="10" x2="12" y2="4" stroke="white" stroke-width="1.2"/>
      </g>
    </svg>
  `,
  
  // Trụ chữa cháy - Fire Hydrant
  tru_chua_chay: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(8, 5)">
        <!-- Main body -->
        <rect x="4" y="8" width="6" height="8" rx="1" fill="#DC143C" stroke="#8B0000" stroke-width="0.8"/>
        <!-- Top cap -->
        <ellipse cx="7" cy="8" rx="3.5" ry="1.5" fill="#FF6347" stroke="#8B0000" stroke-width="0.8"/>
        <!-- Side outlets -->
        <rect x="1" y="11" width="3" height="2" rx="0.5" fill="#FFD700" stroke="#8B0000" stroke-width="0.5"/>
        <rect x="10" y="11" width="3" height="2" rx="0.5" fill="#FFD700" stroke="#8B0000" stroke-width="0.5"/>
        <!-- Base -->
        <rect x="3" y="16" width="8" height="2" rx="0.5" fill="#8B0000" stroke="#8B0000" stroke-width="0.5"/>
        <!-- Valve details -->
        <circle cx="7" cy="10" r="0.8" fill="#FFD700"/>
        <circle cx="7" cy="13" r="0.8" fill="#FFD700"/>
      </g>
    </svg>
  `,
  
  // Trạm sạc - Charging Station
  tram_sac: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(7, 4)">
        <!-- Charging station body -->
        <rect x="3" y="3" width="10" height="14" rx="1" fill="white" stroke="#333" stroke-width="1"/>
        <!-- Screen -->
        <rect x="4" y="4" width="8" height="6" fill="#4CAF50" stroke="#333" stroke-width="0.5"/>
        <!-- Lightning bolt (charging symbol) -->
        <path d="M 8 5 L 6 8.5 L 7.5 8.5 L 6 11.5 L 9 8 L 7.5 8 Z" fill="#FFD700" stroke="#333" stroke-width="0.5"/>
        <!-- Cable connector -->
        <rect x="5" y="11" width="6" height="2" rx="0.5" fill="#333"/>
        <path d="M 8 13 Q 6 15 7 18" stroke="#333" stroke-width="1.5" fill="none"/>
        <circle cx="7" cy="18" r="1" fill="#333"/>
        <!-- Plug icon -->
        <rect x="10" y="14" width="2" height="1" fill="#666"/>
      </g>
    </svg>
  `,
  
  // Đường ống điện - Electrical conduit (for LineString, shown as waypoint)
  duong_ong_dien: `
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="14" fill="COLOR" stroke="white" stroke-width="2"/>
      <g transform="translate(6, 8)">
        <!-- Conduit junction box -->
        <rect x="4" y="3" width="10" height="8" rx="0.5" fill="#FFD700" stroke="#333" stroke-width="1"/>
        <!-- Warning symbol -->
        <path d="M 9 4.5 L 6 9.5 L 12 9.5 Z" fill="#FF0000" stroke="#333" stroke-width="0.5"/>
        <text x="9" y="9" font-size="4" text-anchor="middle" fill="white" font-weight="bold">!</text>
        <!-- Screws -->
        <circle cx="5.5" cy="4.5" r="0.5" fill="#666"/>
        <circle cx="12.5" cy="4.5" r="0.5" fill="#666"/>
        <circle cx="5.5" cy="9.5" r="0.5" fill="#666"/>
        <circle cx="12.5" cy="9.5" r="0.5" fill="#666"/>
      </g>
    </svg>
  `
};

// Function to get SVG icon with custom color
export const getSVGIcon = (featureCode, color) => {
  const iconTemplate = SVG_ICONS[featureCode];
  if (!iconTemplate) {
    // Fallback to a default icon
    return SVG_ICONS.tram_dien.replace(/COLOR/g, color);
  }
  return iconTemplate.replace(/COLOR/g, color);
};
