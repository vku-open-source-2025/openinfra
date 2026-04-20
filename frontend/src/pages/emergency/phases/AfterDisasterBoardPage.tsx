import React from 'react';

import PhaseBoardTemplate from '@/components/emergency/phase-board/PhaseBoardTemplate';

import { phaseBoardDefinitions } from './phaseBoardDefinitions';

const AfterDisasterBoardPage: React.FC = () => {
  return <PhaseBoardTemplate board={phaseBoardDefinitions.after} />;
};

export default AfterDisasterBoardPage;
