import type { FrameCreateRequest, FrameResponse, FrameUpdateRequest } from "@/types";
import { apiRequest } from "./client";

export const getFrames = (timelapseId?: number): Promise<FrameResponse[]> =>
	apiRequest<FrameResponse[]>(`/api/v1/frames${timelapseId ? `/${timelapseId}` : ''}`)

export const getFrameImage = (id: number): Promise<Blob> =>
	apiRequest<Blob>(`/api/v1/frames/${id}/image`)

export const getFrame = (id: number): Promise<FrameResponse> =>
	apiRequest<FrameResponse>(`/api/v1/frames/${id}`)

export const createFrame = (data: FrameCreateRequest): Promise<FrameResponse> =>
	apiRequest<FrameResponse>("/api/v1/frames", {
		method: "POST",
		body: JSON.stringify(data),
	})

export const updateFrame = (id: number, data: FrameUpdateRequest): Promise<FrameResponse> =>
	apiRequest<FrameResponse>(`/api/v1/frames/${id}`, {
		method: "PATCH",
		body: JSON.stringify(data),
	})

export const deleteFrame = (id: number): Promise<void> =>
	apiRequest<void>(`/api/v1/frames/${id}`, {
		method: "DELETE",
	})
