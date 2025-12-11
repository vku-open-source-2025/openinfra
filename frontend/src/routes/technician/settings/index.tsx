import { createFileRoute } from "@tanstack/react-router";
import ProfileSettings from "@/pages/settings/ProfileSettings";

export const Route = createFileRoute("/technician/settings/")({
    component: ProfileSettings,
});


