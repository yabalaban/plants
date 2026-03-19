<script lang="ts">
    import { onMount } from 'svelte';
    import { getPlants, waterPlant } from '$lib/api';
    import type { Plant } from '$lib/types';

    let plants = $state<Plant[]>([]);
    let loading = $state(true);
    let error = $state<string | null>(null);
    let watering = $state<Set<number>>(new Set());

    function getToday(): Date {
        const d = new Date();
        d.setHours(0, 0, 0, 0);
        return d;
    }

    function getStatus(plant: Plant): 'overdue' | 'due' | 'upcoming' | 'unscheduled' {
        if (!plant.next_watering) return 'unscheduled';
        const today = getToday();
        const next = new Date(plant.next_watering);
        next.setHours(0, 0, 0, 0);
        const diff = Math.floor((next.getTime() - today.getTime()) / 86400000);
        if (diff < 0) return 'overdue';
        if (diff === 0) return 'due';
        return 'upcoming';
    }

    function daysUntil(dateStr: string): string {
        const today = getToday();
        const next = new Date(dateStr);
        next.setHours(0, 0, 0, 0);
        const diff = Math.floor((next.getTime() - today.getTime()) / 86400000);
        if (diff < -1) return `${Math.abs(diff)}d overdue`;
        if (diff === -1) return '1d overdue';
        if (diff === 0) return 'Today';
        if (diff === 1) return 'Tomorrow';
        return `${diff} days`;
    }

    function statusOrder(status: string): number {
        return { overdue: 0, due: 1, upcoming: 2, unscheduled: 3 }[status] ?? 3;
    }

    let sorted = $derived(
        [...plants].sort((a, b) => statusOrder(getStatus(a)) - statusOrder(getStatus(b)))
    );

    let needsWaterCount = $derived(
        plants.filter(p => ['overdue', 'due'].includes(getStatus(p))).length
    );

    let todayStr = $derived(
        getToday().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    );

    async function load() {
        try {
            loading = true;
            plants = await getPlants();
        } catch (e) {
            error = 'Failed to load plants';
        } finally {
            loading = false;
        }
    }

    async function handleWater(plant: Plant, event: Event) {
        event.preventDefault();
        event.stopPropagation();
        if (watering.has(plant.id)) return;
        watering = new Set([...watering, plant.id]);
        try {
            await waterPlant(plant.id);
            await load();
        } catch {
            error = 'Failed to log watering';
        } finally {
            watering = new Set([...watering].filter(id => id !== plant.id));
        }
    }

    onMount(load);
</script>

<div class="dashboard">
    <header class="hero">
        <p class="greeting">{todayStr}</p>
        <h1 class="title">Your Garden</h1>
        {#if !loading && needsWaterCount > 0}
            <div class="alert-pill">
                <span class="alert-dot"></span>
                {needsWaterCount} plant{needsWaterCount > 1 ? 's' : ''} need{needsWaterCount === 1 ? 's' : ''} water
            </div>
        {/if}
    </header>

    {#if loading}
        <div class="skeleton-list">
            {#each [1, 2, 3] as _}
                <div class="skeleton-card"></div>
            {/each}
        </div>
    {:else if error}
        <div class="message-box error">{error}</div>
    {:else if plants.length === 0}
        <div class="empty">
            <div class="empty-illustration">
                <svg viewBox="0 0 80 80" fill="none" class="empty-svg">
                    <circle cx="40" cy="60" rx="20" ry="6" fill="var(--accent-dim)" />
                    <path d="M40 55V35" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" />
                    <path d="M40 35c-8-12-20-8-18 0s18 8 18 0z" fill="var(--accent-dim)" stroke="var(--accent)" stroke-width="1.5" />
                    <path d="M40 42c8-14 22-10 18 0s-18 6-18 0z" fill="var(--accent-dim)" stroke="var(--accent)" stroke-width="1.5" />
                </svg>
            </div>
            <p class="empty-text">No plants yet</p>
            <a href="/add" class="empty-cta">Add your first plant</a>
        </div>
    {:else}
        <div class="plant-grid">
            {#each sorted as plant, i (plant.id)}
                {@const status = getStatus(plant)}
                <a
                    href="/plants/{plant.id}"
                    class="plant-card {status}"
                    style="animation-delay: {i * 60}ms"
                >
                    <div class="card-photo-wrap">
                        <img
                            class="card-photo"
                            src={plant.photo_path}
                            alt={plant.name}
                            loading="lazy"
                        />
                        {#if status === 'overdue' || status === 'due'}
                            <button
                                class="card-water-btn"
                                onclick={(e) => handleWater(plant, e)}
                                disabled={watering.has(plant.id)}
                                aria-label="Water {plant.name}"
                            >
                                {#if watering.has(plant.id)}
                                    <span class="btn-spinner"></span>
                                {:else}
                                    <svg viewBox="0 0 24 24" fill="currentColor" class="water-icon">
                                        <path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0L12 2.69z" />
                                    </svg>
                                {/if}
                            </button>
                        {/if}
                    </div>
                    <div class="card-body">
                        <p class="card-name">{plant.name}</p>
                        <p class="card-species">{plant.species ?? 'Identifying...'}</p>
                        <div class="card-status {status}">
                            {#if plant.next_watering}
                                <span class="status-dot"></span>
                                {daysUntil(plant.next_watering)}
                            {:else}
                                <span class="status-dot"></span>
                                Pending
                            {/if}
                        </div>
                    </div>
                </a>
            {/each}
        </div>
    {/if}
</div>

<style>
    .dashboard {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        animation: fadeIn 0.4s var(--ease-out);
    }

    .hero {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        padding-bottom: 0.5rem;
    }

    .greeting {
        font-family: var(--font-body);
        font-size: 0.8rem;
        color: var(--text-muted);
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-weight: 500;
    }

    .title {
        font-family: var(--font-display);
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text);
    }

    .alert-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.35rem;
        padding: 0.4rem 0.85rem;
        background: var(--alert-dim);
        border: 1px solid rgba(232, 168, 124, 0.2);
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--alert);
        width: fit-content;
    }

    .alert-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--alert);
        animation: pulse 2s ease-in-out infinite;
    }

    /* Skeleton */
    .skeleton-list { display: flex; flex-direction: column; gap: 0.75rem; }
    .skeleton-card {
        height: 88px;
        border-radius: var(--radius);
        background: var(--surface);
        animation: pulse 1.5s ease-in-out infinite;
    }

    .message-box {
        padding: 1rem 1.25rem;
        border-radius: var(--radius-sm);
        font-size: 0.875rem;
        text-align: center;
    }
    .message-box.error {
        background: var(--danger-dim);
        color: var(--danger);
        border: 1px solid rgba(201, 123, 123, 0.2);
    }

    /* Empty */
    .empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        padding: 4rem 1rem 2rem;
        animation: fadeInScale 0.5s var(--ease-out);
    }

    .empty-svg { width: 80px; height: 80px; }
    .empty-text { color: var(--text-secondary); font-size: 0.95rem; }
    .empty-cta {
        display: inline-flex;
        align-items: center;
        padding: 0.7rem 1.5rem;
        background: var(--accent-dim);
        color: var(--accent);
        border: 1px solid var(--accent-medium);
        border-radius: 999px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.875rem;
        transition: background 0.2s;
    }

    /* Plant Grid */
    .plant-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .plant-card {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 0.75rem;
        background: var(--surface);
        border-radius: var(--radius);
        border: 1px solid var(--border);
        text-decoration: none;
        color: inherit;
        transition: transform 0.2s var(--ease-out), border-color 0.2s, background 0.2s;
        animation: fadeIn 0.4s var(--ease-out) both;
    }

    .plant-card:active {
        transform: scale(0.98);
    }

    .plant-card.overdue {
        border-color: rgba(201, 123, 123, 0.25);
        background: var(--danger-dim);
    }
    .plant-card.due {
        border-color: rgba(232, 168, 124, 0.25);
        background: var(--alert-dim);
    }

    .card-photo-wrap {
        position: relative;
        flex-shrink: 0;
    }

    .card-photo {
        width: 64px;
        height: 64px;
        border-radius: var(--radius-sm);
        object-fit: cover;
        background: var(--surface-raised);
    }

    .card-water-btn {
        position: absolute;
        bottom: -4px;
        right: -4px;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--accent);
        color: var(--bg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: transform 0.15s var(--ease-spring);
    }

    .card-water-btn:active { transform: scale(0.85); }
    .card-water-btn:disabled { opacity: 0.6; }

    .water-icon { width: 16px; height: 16px; }

    .btn-spinner {
        width: 14px;
        height: 14px;
        border: 2px solid rgba(0,0,0,0.15);
        border-top-color: var(--bg);
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    .card-body {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }

    .card-name {
        font-family: var(--font-display);
        font-weight: 600;
        font-size: 1.05rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .card-species {
        font-size: 0.78rem;
        color: var(--text-muted);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-style: italic;
    }

    .card-status {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-top: 0.2rem;
    }

    .status-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: currentColor;
    }

    .card-status.overdue { color: var(--danger); }
    .card-status.due { color: var(--alert); }
    .card-status.upcoming { color: var(--accent); }
    .card-status.unscheduled { color: var(--text-muted); }
</style>
