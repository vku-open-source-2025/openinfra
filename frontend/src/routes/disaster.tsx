import { createFileRoute } from '@tanstack/react-router';
import DisasterMap from '../pages/DisasterMap';

export const Route = createFileRoute('/disaster')({
  component: DisasterMap,
});
