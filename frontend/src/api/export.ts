import { apiRequest } from "./client"
import type { ExportJobResponse, ExportRequest } from "@/types"

export const startExport = (id: number, data: ExportRequest) =>
	apiRequest<ExportJobResponse>(`/api/v1/exports/timelapses/${id}`, {
		method: "POST",
		body: JSON.stringify(data),
	})

export const getExportsForTimelapse = (timelapseId: number) =>
	apiRequest<ExportJobResponse[]>(`/api/v1/exports/list/${timelapseId}`)

export const getExportStatus = (jobId: number) =>
	apiRequest<ExportJobResponse>(`/api/v1/exports/${jobId}/status`)

export const downloadExport = (jobId: number) =>
	apiRequest<Blob>(`/api/v1/exports/${jobId}/download`)
