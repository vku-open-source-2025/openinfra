import { httpClient } from '../lib/httpClient';

export interface CSVIngestResponse {
  message: string;
}

export const ingestApi = {
  /**
   * Upload CSV file for asset ingestion
   * POST /ingest/csv
   *
   * @param file - CSV file to upload
   * @returns Response with ingestion message
   */
  uploadCSV: async (file: File): Promise<CSVIngestResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await httpClient.post<CSVIngestResponse>('/ingest/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },
};
