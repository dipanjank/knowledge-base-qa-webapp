import { auth } from './stores/auth';

let accessToken: string | null = null;

auth.subscribe((state) => {
	accessToken = state.accessToken;
});

export class ApiError extends Error {
	constructor(
		public status: number,
		public detail: string
	) {
		super(detail);
	}
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
	const headers: Record<string, string> = {
		...(options.headers as Record<string, string>)
	};

	if (accessToken) {
		headers['Authorization'] = `Bearer ${accessToken}`;
	}

	if (options.body && typeof options.body === 'string') {
		headers['Content-Type'] = 'application/json';
	}

	const res = await fetch(path, {
		...options,
		headers,
		credentials: 'include'
	});

	if (res.status === 401 && !path.includes('/api/auth/')) {
		const refreshed = await tryRefresh();
		if (refreshed) {
			headers['Authorization'] = `Bearer ${accessToken}`;
			const retry = await fetch(path, { ...options, headers, credentials: 'include' });
			if (!retry.ok) {
				const err = await retry.json().catch(() => ({ detail: retry.statusText }));
				throw new ApiError(retry.status, err.detail ?? retry.statusText);
			}
			return retry.json();
		}
		auth.logout();
		throw new ApiError(401, 'Session expired');
	}

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new ApiError(res.status, err.detail ?? res.statusText);
	}

	return res.json();
}

async function tryRefresh(): Promise<boolean> {
	try {
		const res = await fetch('/api/auth/refresh', {
			method: 'POST',
			credentials: 'include'
		});
		if (!res.ok) return false;
		const data = await res.json();
		auth.setToken(data.access_token, data.expires_in);
		return true;
	} catch {
		return false;
	}
}
