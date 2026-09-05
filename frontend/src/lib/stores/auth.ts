import { writable } from 'svelte/store';

interface AuthState {
	accessToken: string | null;
	role: string | null;
	isAuthenticated: boolean;
}

function parseJwt(token: string): Record<string, unknown> | null {
	try {
		const payload = token.split('.')[1];
		return JSON.parse(atob(payload));
	} catch {
		return null;
	}
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		accessToken: null,
		role: null,
		isAuthenticated: false
	});

	return {
		subscribe,
		setToken(token: string, _expiresIn: number) {
			const claims = parseJwt(token);
			set({
				accessToken: token,
				role: (claims?.role as string) ?? null,
				isAuthenticated: true
			});
		},
		logout() {
			set({ accessToken: null, role: null, isAuthenticated: false });
		}
	};
}

export const auth = createAuthStore();
