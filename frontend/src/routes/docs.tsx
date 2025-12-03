import { createFileRoute } from "@tanstack/react-router";
import ApiDocsPage from "../pages/ApiDocsPage";

export const Route = createFileRoute("/docs")({
    component: ApiDocsPage,
});


