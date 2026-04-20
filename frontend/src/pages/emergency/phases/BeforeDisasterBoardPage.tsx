import React from 'react';

import PhaseBoardTemplate from '@/components/emergency/phase-board/PhaseBoardTemplate';

import { phaseBoardDefinitions } from './phaseBoardDefinitions';

const BeforeDisasterBoardPage: React.FC = () => {
  return <PhaseBoardTemplate board={phaseBoardDefinitions.before} />;
};

export default BeforeDisasterBoardPage;
