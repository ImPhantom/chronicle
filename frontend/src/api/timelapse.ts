import type { TimelapseCreateRequest, TimelapseResponse, TimelapseUpdateRequest } from "@/types"
import { apiRequest } from "./client"

export const getTimelapses = (): Promise<TimelapseResponse[]> =>
	apiRequest<TimelapseResponse[]>("/api/v1/timelapses")

export const getTimelapse = (id: number): Promise<TimelapseResponse> =>
	apiRequest<TimelapseResponse>(`/api/v1/timelapses/${id}`)

export const createTimelapse = (data: TimelapseCreateRequest): Promise<TimelapseResponse> =>
	apiRequest<TimelapseResponse>("/api/v1/timelapses", {
		method: "POST",
		body: JSON.stringify(data),
	})

export const updateTimelapse = (id: number, data: TimelapseUpdateRequest): Promise<TimelapseResponse> =>
	apiRequest<TimelapseResponse>(`/api/v1/timelapses/${id}`, {
		method: "PATCH",
		body: JSON.stringify(data),
	})

export const deleteTimelapse = (id: number): Promise<void> =>
	apiRequest<void>(`/api/v1/timelapses/${id}`, {
		method: "DELETE",
	})