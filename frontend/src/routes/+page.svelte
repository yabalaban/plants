<script lang="ts">
    import { onMount } from 'svelte';
    import { getPlants, waterPlant } from '$lib/api';
    import type { Plant } from '$lib/types';

    let plants = $state<Plant[]>([]);
    let loading = $state(true);
    let error = $state<string | null>(null);
    let watering = $state<Set<number>>(new Set());

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    function getStatus(plant: Plant): 'overdue' | 'due' | 'upcoming' | 'unscheduled' {
        if (!plant.next_watering) return 'unscheduled';
        const next = new Date(plant.next_watering);
        next.setHours(0, 0, 0, 0);
        const diff = Math.floor((next.getTime() - today.getTime()) / 86400000);
        if (diff < 0) return 'overdue';
        if (diff === 0) return 'due';
        return 'upcoming';
    }

    function daysUntil(dateStr: string): string {
        const next = new Date(dateStr);
        next.setHours(0, 0, 0, 0);
        const diff = Math.floor((next.getTime() - today.getTime()) / 86400000);
        if (diff < -1) return `${Math.abs(diff)} days overdue`;
        if (diff === -1) return '1 day overdue';
        if (diff === 0) return 'Due today';
        if (diff === 1) return 'in 1 day';
        return `in ${diff} days`;
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
        today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
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
            // silently fail
        } finally {
            watering = new Set([...watering].filter(id => id !== plant.id));
        }
    }

    onMount(load);
</script>

<div class="dashboard">
    <div class="header">
        <p class="date">{todayStr}</p>
        <h1 class="title">My Plants</h1>
        {#if !loading && needsWaterCount > 0}
            <p class="needs-water">{needsWaterCount} plant{needsWaterCount > 1 ? 's' : ''} need water</p>
        {/if}
    </div>

    {#if loading}
        <div class="state-box">Loading plants...</div>
    {:else if error}
        <div class="state-box error">{error}</div>
    {:else if plants.length === 0}
        <div class="empty-state">
            <span class="empty-icon">🌱</span>
            <p>No plants yet</p>
            <a href="/add" class="add-link">Add your first plant</a>
        </div>
    {:else}
        <div class="plant-list">
            {#each sorted as plant (plant.id)}
                {@const status = getStatus(plant)}
                <a href="/plants/{plant.id}" class="plant-card {status}">
                    <img
                        class="photo"
                        src="/api/photos/{plant.photo_path.split('/').pop()}"
                        alt={plant.name}
                    />
                    <div class="info">
                        <p class="name">{plant.name}</p>
                        <p class="species">{plant.species ?? 'Identifying...'}</p>
                        {#if plant.next_watering}
                            <p class="watering-label {status}">{daysUntil(plant.next_watering)}</p>
                        {:else}
                            <p class="watering-label unscheduled">Not scheduled</p>
                        {/if}
                    </div>
                    {#if status === 'overdue' || status === 'due'}
                        <button
                            class="water-btn"
                            onclick={(e) => handleWater(plant, e)}
                            disabled={watering.has(plant.id)}
                        >
                            {watering.has(plant.id) ? '...' : '💧'}
                        </button>
                    {/if}
                </a>
            {/each}
        </div>
    {/if}
</div>

<style>
    .dashboard { display: flex; flex-direction: column; gap: 1.5rem; }

    .header { display: flex; flex-direction: column; gap: 0.25rem; }
    .date { color: var(--text-muted); font-size: 0.85rem; }
    .title { font-size: 1.6rem; font-weight: 700; }
    .needs-water { color: var(--yellow); font-size: 0.85rem; }

    .state-box { padding: 2rem; text-align: center; color: var(--text-muted); background: var(--surface); border-radius: var(--radius); }
    .state-box.error { color: var(--red); }

    .empty-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 3rem 1rem; }
    .empty-icon { font-size: 3rem; }
    .empty-state p { color: var(--text-muted); }
    .add-link { color: var(--green); text-decoration: none; font-weight: 600; }

    .plant-list { display: flex; flex-direction: column; gap: 0.75rem; }

    .plant-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem;
        background: var(--surface);
        border-radius: var(--radius);
        border: 1px solid var(--border);
        text-decoration: none;
        color: inherit;
        transition: border-color 0.15s;
    }
    .plant-card.overdue { border-color: rgba(239, 68, 68, 0.3); background: var(--red-bg); }
    .plant-card.due { border-color: rgba(250, 204, 21, 0.3); background: var(--yellow-bg); }

    .photo { width: 56px; height: 56px; border-radius: var(--radius-sm); object-fit: cover; flex-shrink: 0; background: var(--border); }

    .info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.2rem; }
    .name { font-weight: 600; font-size: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .species { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    .watering-label { font-size: 0.75rem; font-weight: 500; }
    .watering-label.overdue { color: var(--red); }
    .watering-label.due { color: var(--yellow); }
    .watering-label.upcoming { color: var(--green); }
    .watering-label.unscheduled { color: var(--text-muted); }

    .water-btn {
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--blue-bg);
        border: 1px solid var(--blue);
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.15s;
    }
    .water-btn:disabled { opacity: 0.5; }
</style>
