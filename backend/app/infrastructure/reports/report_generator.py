"""Report generation service."""
from typing import Dict, Any, Optional
from datetime import datetime
from app.domain.models.report import Report, ReportType, ReportFormat
from app.infrastructure.database.mongodb import get_database
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Report generator service."""

    async def generate_report(self, report: Report) -> str:
        """Generate report file and return file URL."""
        try:
            if report.type == ReportType.MAINTENANCE_SUMMARY:
                return await self._generate_maintenance_summary(report)
            elif report.type == ReportType.ASSET_INVENTORY:
                return await self._generate_asset_inventory(report)
            elif report.type == ReportType.INCIDENT_REPORT:
                return await self._generate_incident_report(report)
            elif report.type == ReportType.BUDGET_UTILIZATION:
                return await self._generate_budget_utilization(report)
            elif report.type == ReportType.IOT_SENSOR_DATA:
                return await self._generate_iot_sensor_data(report)
            else:
                raise ValueError(f"Unknown report type: {report.type}")
        except Exception as e:
            logger.error(f"Error generating report {report.report_code}: {e}")
            raise

    async def _generate_maintenance_summary(self, report: Report) -> str:
        """Generate maintenance summary report."""
        db = await get_database()
        collection = db["maintenance_records"]

        # Build query from parameters
        query = report.parameters.get("filters", {})
        if "from_date" in report.parameters:
            query["created_at"] = {"$gte": report.parameters["from_date"]}
        if "to_date" in report.parameters:
            if "created_at" in query:
                query["created_at"]["$lte"] = report.parameters["to_date"]
            else:
                query["created_at"] = {"$lte": report.parameters["to_date"]}

        # Aggregate data
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_cost": {"$sum": "$cost"}
                }
            }
        ]

        results = []
        async for doc in collection.aggregate(pipeline):
            results.append(doc)

        # Generate file based on format
        if report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, {"summary": results})
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(report, {"summary": results})
        elif report.format == ReportFormat.CSV:
            return await self._generate_csv(report, {"summary": results})
        else:
            return await self._generate_json(report, {"summary": results})

    async def _generate_asset_inventory(self, report: Report) -> str:
        """Generate asset inventory report."""
        db = await get_database()
        collection = db["assets"]

        query = report.parameters.get("filters", {})

        # Get assets
        cursor = collection.find(query)
        assets = []
        async for asset in cursor:
            assets.append(asset)

        if report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, {"assets": assets})
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(report, {"assets": assets})
        elif report.format == ReportFormat.CSV:
            return await self._generate_csv(report, {"assets": assets})
        else:
            return await self._generate_json(report, {"assets": assets})

    async def _generate_incident_report(self, report: Report) -> str:
        """Generate incident report."""
        db = await get_database()
        collection = db["incidents"]

        query = report.parameters.get("filters", {})

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time_minutes"}
                }
            }
        ]

        results = []
        async for doc in collection.aggregate(pipeline):
            results.append(doc)

        if report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, {"incidents": results})
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(report, {"incidents": results})
        elif report.format == ReportFormat.CSV:
            return await self._generate_csv(report, {"incidents": results})
        else:
            return await self._generate_json(report, {"incidents": results})

    async def _generate_budget_utilization(self, report: Report) -> str:
        """Generate budget utilization report."""
        db = await get_database()
        budgets_collection = db["budgets"]
        transactions_collection = db["budget_transactions"]

        query = report.parameters.get("filters", {})

        budgets = []
        async for budget in budgets_collection.find(query):
            # Calculate utilization
            totals = await transactions_collection.aggregate([
                {"$match": {"budget_id": str(budget["_id"])}},
                {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}}
            ]).to_list(None)

            budget["utilization"] = totals
            budgets.append(budget)

        if report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, {"budgets": budgets})
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(report, {"budgets": budgets})
        elif report.format == ReportFormat.CSV:
            return await self._generate_csv(report, {"budgets": budgets})
        else:
            return await self._generate_json(report, {"budgets": budgets})

    async def _generate_iot_sensor_data(self, report: Report) -> str:
        """Generate IoT sensor data report."""
        db = await get_database()
        collection = db["sensor_data"]

        query = report.parameters.get("filters", {})

        # Aggregate sensor data
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$sensor_id",
                    "avg_value": {"$avg": "$value"},
                    "min_value": {"$min": "$value"},
                    "max_value": {"$max": "$value"},
                    "count": {"$sum": 1}
                }
            }
        ]

        results = []
        async for doc in collection.aggregate(pipeline):
            results.append(doc)

        if report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, {"sensor_data": results})
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(report, {"sensor_data": results})
        elif report.format == ReportFormat.CSV:
            return await self._generate_csv(report, {"sensor_data": results})
        else:
            return await self._generate_json(report, {"sensor_data": results})

    async def _generate_pdf(self, report: Report, data: Dict[str, Any]) -> str:
        """Generate PDF report."""
        # In production, use libraries like reportlab or weasyprint
        # For now, return placeholder
        logger.info(f"Generating PDF report: {report.report_code}")
        # TODO: Implement PDF generation
        return f"/reports/{report.report_code}.pdf"

    async def _generate_excel(self, report: Report, data: Dict[str, Any]) -> str:
        """Generate Excel report."""
        import pandas as pd
        from app.infrastructure.storage.local_storage import LocalStorageService

        # Convert data to DataFrame
        df = pd.DataFrame(data.get("summary", data.get("assets", [])))

        # Save to Excel
        storage = LocalStorageService()
        file_path = f"reports/{report.report_code}.xlsx"

        # In production, save to storage service
        # For now, just return path
        logger.info(f"Generating Excel report: {report.report_code}")
        return file_path

    async def _generate_csv(self, report: Report, data: Dict[str, Any]) -> str:
        """Generate CSV report."""
        import pandas as pd

        # Convert data to DataFrame
        df = pd.DataFrame(data.get("summary", data.get("assets", [])))

        file_path = f"reports/{report.report_code}.csv"
        logger.info(f"Generating CSV report: {report.report_code}")
        return file_path

    async def _generate_json(self, report: Report, data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        import json

        file_path = f"reports/{report.report_code}.json"
        logger.info(f"Generating JSON report: {report.report_code}")
        return file_path
