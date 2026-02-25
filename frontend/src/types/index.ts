// ── Camera ────────────────────────────────────────────────────────────────────

export type ConnectionType = "network" | "hardware";

export interface HardwareCameraInfo {
	index: number;
	name: string;
}

export interface CameraResponse {
	id: number;
	name: string;
	connection_type: ConnectionType;
	rtsp_url: string | null;
	device_index: number | null;
	enabled: boolean;
	created_at: string;
}

export interface CameraCreateRequest {
	name: string;
	connection_type: ConnectionType;
	rtsp_url?: string | null;
	device_index?: number | null;
	enabled?: boolean;
}

export interface CameraUpdateRequest {
	name?: string;
	connection_type?: ConnectionType;
	rtsp_url?: string | null;
	device_index?: number | null;
	enabled?: boolean;
}

export interface TestCaptureRequest {
	connection_type: ConnectionType;
	rtsp_url?: string | null;
	device_index?: number | null;
}

// ── Timelapse ─────────────────────────────────────────────────────────────────

export type TimelapseStatus = "pending" | "running" | "paused" | "completed";

export interface TimelapseResponse {
	id: number;
	camera_id: number;
	name: string;
	interval_seconds: number;
	status: TimelapseStatus;
	started_at: string | null;
	ended_at: string | null;
	created_at: string;
	last_frame_id: number | null;
	frame_count: number;
	size_bytes: number;
}

export interface TimelapseCreateRequest {
	camera_id: number;
	name: string;
	interval_seconds: number;
	status?: TimelapseStatus;
	started_at?: string | null;
	ended_at?: string | null;
}

export interface TimelapseUpdateRequest {
	name?: string;
	interval_seconds?: number;
	status?: TimelapseStatus;
	started_at?: string | null;
	ended_at?: string | null;
}

// ── Frame ─────────────────────────────────────────────────────────────────────

export interface FrameResponse {
	id: number;
	timelapse_id: number;
	file_path: string;
	captured_at: string;
}

export interface FrameCreateRequest {
	timelapse_id: number;
	file_path: string;
	captured_at?: string | null;
}

export interface FrameUpdateRequest {
	file_path?: string;
}

// ── Storage ────────────────────────────────────────────────────────────────────

export interface StorageStats {
	total_bytes: number;
	used_bytes: number;
	free_bytes: number;
}

// ── Settings ───────────────────────────────────────────────────────────────────

export type RtspTransport = "tcp" | "udp" | "http";
export type CaptureImageFormat = "webp" | "jpeg" | "png";

export interface AppSettingsResponse {
	id: number;
	timezone: string;
	storage_path: string;
	max_storage_gb: number | null;
	ffmpeg_timeout_seconds: number;
	ffmpeg_rtsp_transport: RtspTransport;
	capture_image_format: CaptureImageFormat;
	capture_image_quality: number;
	default_capture_interval_seconds: number;
	max_frames_per_timelapse: number | null;
	retention_days: number | null;
}

export interface AppSettingsUpdateRequest {
	timezone?: string;
	storage_path?: string;
	max_storage_gb?: number | null;
	ffmpeg_timeout_seconds?: number;
	ffmpeg_rtsp_transport?: RtspTransport;
	capture_image_format?: CaptureImageFormat;
	capture_image_quality?: number;
	default_capture_interval_seconds?: number;
	max_frames_per_timelapse?: number | null;
	retention_days?: number | null;
}

// ── Export ─────────────────────────────────────────────────────────────────────

export type ExportStatus     = "pending" | "running" | "completed" | "error"
export type OutputFormat     = "webm" | "mp4"
export type ExportResolution = "original" | "1920x1080" | "1280x720" | "640x360" | "custom"

export interface ExportRequest {
	output_format:      OutputFormat
	output_fps:         number
	resolution:         ExportResolution
	custom_resolution?: string | null
	crf:                number
}

export interface ExportJobResponse {
	id:            number
	timelapse_id:  number
	status:        ExportStatus
	output_format: OutputFormat
	output_fps:    number
	resolution:    string
	crf:           number
	total_frames:  number
	frames_done:   number
	progress_pct:  number
	output_file:   string | null
	error_message: string | null
	created_at:    string
	completed_at:  string | null
}
