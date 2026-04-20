import React from 'react';

import PhaseBoardTemplate from '@/components/emergency/phase-board/PhaseBoardTemplate';

import { phaseBoardDefinitions } from './phaseBoardDefinitions';

const DuringDisasterBoardPage: React.FC = () => {
  return <PhaseBoardTemplate board={phaseBoardDefinitions.during} />;
};

export default DuringDisasterBoardPage;
