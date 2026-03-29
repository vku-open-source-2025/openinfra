import L from 'leaflet';
import { getSVGIcon } from './svgIcons';

export const createCustomIcon = (color, isPreview = false, isReview = false, featureCode = null) => {
  let className = 'custom-marker';
  if (isPreview) className += ' preview-feature';
  if (isReview) className += ' review-feature'; 

  // Use SVG icon if feature code is provided, otherwise fallback to simple marker
  let iconHtml;
  if (featureCode) {
    iconHtml = getSVGIcon(featureCode, color);
  } else {
    // Fallback to simple colored marker
    iconHtml = `<div style="background-color: ${color}" class="marker-pin"></div>`;
  }

  return L.divIcon({
    className: className,
    html: iconHtml,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  });
};

export const groupContributionsByBatch = (contributions) => {
  if (!contributions || contributions.length === 0) return [];
  
  const batches = [];
  const sorted = [...contributions].sort((a, b) => 
    new Date(a.timestamp) - new Date(b.timestamp)
  );
  
  for (const contrib of sorted) {
    const lastBatch = batches[batches.length - 1];
    const timeDiff = lastBatch ? 
      new Date(contrib.timestamp) - new Date(lastBatch.timestamp) : Infinity;
    
    // Group if same contributor, MSV, and within 5 seconds
    if (lastBatch && 
        lastBatch.contributor_name === contrib.contributor_name &&
        lastBatch.msv === contrib.msv &&
        timeDiff < 5000) {
      lastBatch.features.push(contrib);
      lastBatch.count++;
    } else {
      batches.push({
        batchId: `batch-${contrib.id || Date.now()}-${Math.random()}`,
        contributor_name: contrib.contributor_name,
        msv: contrib.msv,
        timestamp: contrib.timestamp,
        features: [contrib],
        count: 1
      });
    }
  }
  
  return batches;
};
