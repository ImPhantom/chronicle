import { type CameraResponse, type CameraCreateRequest, type CameraUpdateRequest, type TestCaptureRequest, type HardwareCameraInfo } from "@/types";
import { apiRequest } from "./client";

export const getCameras = (): Promise<CameraResponse[]> =>
	apiRequest<CameraResponse[]>("/api/v1/cameras")

export const getCamera = (id: number): Promise<CameraResponse> =>
	apiRequest<CameraResponse>(`/api/v1/cameras/${id}`)

export const createCamera = (data: CameraCreateRequest): Promise<CameraResponse> =>
	apiRequest<CameraResponse>("/api/v1/cameras", {
		method: "POST",
		body: JSON.stringify(data),
	})

export const updateCamera = (id: number, data: CameraUpdateRequest): Promise<CameraResponse> =>
	apiRequest<CameraResponse>(`/api/v1/cameras/${id}`, {
		method: "PATCH",
		body: JSON.stringify(data),
	})

export const deleteCamera = (id: number): Promise<void> =>
	apiRequest<void>(`/api/v1/cameras/${id}`, {
		method: "DELETE",
	})

export const getHardwareCameras = (): Promise<HardwareCameraInfo[]> =>
	apiRequest<HardwareCameraInfo[]>("/api/v1/cameras/hardware")

export const testCamera = (data: TestCaptureRequest): Promise<Blob> =>
	apiRequest<Blob>("/api/v1/cameras/test-capture", {
		method: "POST",
		body: JSON.stringify(data),
	})