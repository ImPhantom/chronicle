export function formatBytes(bytes: number, decimals = 2): string {
	if (bytes === 0) return '0 Bytes'

	const k = 1024
	const dm = decimals < 0 ? 0 : decimals
	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
	const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function formatInterval(seconds: number, short: boolean = true): string {
	if (seconds < 60) return `${seconds}${short ? 's' : ' second' + (seconds !== 1 ? 's' : '')}`
	if (seconds < 3600) return `${Math.round(seconds / 60)}${short ? 'm' : ' minute' + (Math.round(seconds / 60) !== 1 ? 's' : '')}`
	const h = Math.floor(seconds / 3600)
	const m = Math.round((seconds % 3600) / 60)
	return m > 0 
		? `${h}${short ? 'h' : ' hour' + (h !== 1 ? 's' : '')} ${m}${short ? 'm' : ' minute' + (Math.round(seconds / 60) !== 1 ? 's' : '')}` 
		: `${h}${short ? 'h' : ' hour' + (h !== 1 ? 's' : '')}`
}