import { apiRequest } from './client'

export interface VersionInfo {
	git_hash: string
	git_hash_full: string
}

export const getVersion = () => apiRequest<VersionInfo>('/api/v1/version')
