export async function apiRequest<T>(
  	url: string,
	options?: RequestInit
): Promise<T> {
	const response = await fetch(url, {
		headers: {
			"Content-Type": "application/json",
			...(options?.headers ?? {}),
		},
		...options,
	})
	if (!response.ok) {
		const body = await response.json().catch(() => null)
		throw new Error(body?.detail ?? `HTTP ${response.status}: ${response.statusText}`)
	}

	const contentType = response.headers.get("Content-Type") || ""
	if (!contentType.includes("application/json")) {
		return (await response.blob()) as T
	}

	return (await response.json()) as T
}