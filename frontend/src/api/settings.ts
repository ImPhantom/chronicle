import type { AppSettingsResponse, AppSettingsUpdateRequest, StorageStats } from "@/types";
import { apiRequest } from "./client";

export const getSettings = (): Promise<AppSettingsResponse> =>
	apiRequest<AppSettingsResponse>("/api/v1/settings")

export const updateSettings = (settings: AppSettingsUpdateRequest): Promise<AppSettingsResponse> =>
	apiRequest<AppSettingsResponse>("/api/v1/settings", {
		method: "PATCH",
		body: JSON.stringify(settings),
	})

export const getStorageStats = (): Promise<StorageStats> =>
	apiRequest<StorageStats>("/api/v1/settings/storage")