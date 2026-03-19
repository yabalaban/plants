import type { Plant, PlantDetail, Settings, SettingsUpdate } from './types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const resp = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        ...options,
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    if (resp.status === 204) return undefined as T;
    return resp.json();
}

export async function getPlants(): Promise<Plant[]> { return request('/plants'); }
export async function getPlant(id: number): Promise<PlantDetail> { return request(`/plants/${id}`); }

export async function addPlant(name: string, photo: File): Promise<Plant> {
    const form = new FormData();
    form.append('name', name);
    form.append('photo', photo);
    const resp = await fetch(`${BASE}/plants`, { method: 'POST', body: form });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}

export async function waterPlant(id: number, notes?: string): Promise<void> {
    await request(`/plants/${id}/water`, { method: 'POST', body: JSON.stringify({ notes: notes || null }) });
}

export async function deletePlant(id: number): Promise<void> {
    await request(`/plants/${id}`, { method: 'DELETE' });
}

export async function getSettings(): Promise<Settings> { return request('/settings'); }
export async function updateSettings(data: SettingsUpdate): Promise<Settings> {
    return request('/settings', { method: 'PUT', body: JSON.stringify(data) });
}
export async function testTelegram(): Promise<void> { await request('/settings/test-telegram', { method: 'POST' }); }
