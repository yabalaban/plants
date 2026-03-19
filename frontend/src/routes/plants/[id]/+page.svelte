<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { getPlant, waterPlant, deletePlant } from '$lib/api';
    import type { PlantDetail } from '$lib/types';

    let plant = $state<PlantDetail | null>(null);
    let loading = $state(true);
    let error = $state<string | null>(null);
    let watering = $state(false);
    let deleting = $state(false);
    let showDeleteConfirm = $state(false);
    let waterNotes = $state('');
    let showNotesInput = $state(false);

    let id = $derived(Number($page.params.id));

    async function load() {
        try {
            loading = true;
            plant = await getPlant(id);
        } catch {
            error = 'Failed to load plant';
        } finally {
            loading = false;
        }
    }

    async function handleWater() {
        if (watering || !plant) return;
        watering = true;
        try {
            await waterPlant(plant.id, waterNotes || undefined);
            waterNotes = '';
            showNotesInput = false;
            await load();
        } catch {
            // silently fail
        } finally {
            watering = false;
        }
    }

    async function handleDelete() {
        if (deleting || !plant) return;
        deleting = true;
        try {
            await deletePlant(plant.id);
            goto('/');
        } catch {
            deleting = false;
            showDeleteConfirm = false;
        }
    }

    function formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    }

    function formatDateTime(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }

    onMount(load);
</script>

{#if loading}
    <div class="state-box">Loading...</div>
{:else if error || !plant}
    <div class="state-box error">{error ?? 'Plant not found'}</div>
{:else}
    <div class="detail">
        <img
            class="hero-photo"
            src="/api/photos/{plant.photo_path.split('/').pop()}"
            alt={plant.name}
        />

        <div class="header">
            <h1 class="name">{plant.name}</h1>
            {#if plant.species}
                <p class="species">{plant.species}</p>
            {/if}
            <p class="added">Added {formatDate(plant.created_at)}</p>
        </div>

        <div class="stats-grid">
            <div class="stat">
                <span class="stat-label">Interval</span>
                <span class="stat-value">
                    {plant.interval_days != null ? `${plant.interval_days}d` : '—'}
                </span>
            </div>
            <div class="stat">
                <span class="stat-label">Next Watering</span>
                <span class="stat-value">
                    {plant.next_watering ? formatDate(plant.next_watering) : '—'}
                </span>
            </div>
        </div>

        {#if plant.adjustment_reason}
            <div class="note-box">
                <span class="note-icon">📊</span>
                <p>{plant.adjustment_reason}</p>
            </div>
        {/if}

        <div class="water-section">
            {#if showNotesInput}
                <input
                    type="text"
                    placeholder="Notes (optional)"
                    bind:value={waterNotes}
                />
            {/if}
            <div class="water-actions">
                <button
                    class="water-btn"
                    onclick={handleWater}
                    disabled={watering}
                >
                    {watering ? 'Watering...' : '💧 Mark as Watered'}
                </button>
                <button
                    class="notes-toggle"
                    onclick={() => showNotesInput = !showNotesInput}
                    title="Add notes"
                >
                    📝
                </button>
            </div>
        </div>

        {#if plant.identification_details}
            {@const info = plant.identification_details}
            <div class="care-section">
                <h2 class="section-title">Care Info</h2>
                <div class="care-card">
                    {#if info.care_summary}
                        <p class="care-summary">{info.care_summary}</p>
                    {/if}
                    <div class="care-rows">
                        {#if info.light_preference}
                            <div class="care-row">
                                <span class="care-key">Light</span>
                                <span>{info.light_preference}</span>
                            </div>
                        {/if}
                        {#if info.overwatering_signs}
                            <div class="care-row">
                                <span class="care-key">Overwatering</span>
                                <span>{info.overwatering_signs}</span>
                            </div>
                        {/if}
                        {#if info.underwatering_signs}
                            <div class="care-row">
                                <span class="care-key">Underwatering</span>
                                <span>{info.underwatering_signs}</span>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}

        {#if plant.watering_logs.length > 0}
            <div class="history-section">
                <h2 class="section-title">Watering History</h2>
                <div class="log-list">
                    {#each plant.watering_logs.slice(0, 10) as log (log.id)}
                        <div class="log-item">
                            <span class="log-icon">💧</span>
                            <div class="log-info">
                                <span class="log-date">{formatDateTime(log.watered_at)}</span>
                                {#if log.notes}
                                    <span class="log-notes">{log.notes}</span>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="danger-zone">
            {#if showDeleteConfirm}
                <p class="confirm-msg">Delete "{plant.name}"? This cannot be undone.</p>
                <div class="confirm-actions">
                    <button class="cancel-btn" onclick={() => showDeleteConfirm = false}>Cancel</button>
                    <button class="delete-btn" onclick={handleDelete} disabled={deleting}>
                        {deleting ? 'Deleting...' : 'Delete'}
                    </button>
                </div>
            {:else}
                <button class="delete-trigger" onclick={() => showDeleteConfirm = true}>
                    Delete Plant
                </button>
            {/if}
        </div>
    </div>
{/if}

<style>
    .state-box { padding: 2rem; text-align: center; color: var(--text-muted); background: var(--surface); border-radius: var(--radius); }
    .state-box.error { color: var(--red); }

    .detail { display: flex; flex-direction: column; gap: 1.25rem; }

    .hero-photo { width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: var(--radius); background: var(--surface); }

    .header { display: flex; flex-direction: column; gap: 0.25rem; }
    .name { font-size: 1.6rem; font-weight: 700; }
    .species { color: var(--text-muted); font-size: 0.9rem; font-style: italic; }
    .added { color: var(--text-muted); font-size: 0.8rem; }

    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .stat { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.875rem; display: flex; flex-direction: column; gap: 0.25rem; }
    .stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .stat-value { font-size: 1.1rem; font-weight: 600; color: var(--green); }

    .note-box { display: flex; gap: 0.75rem; padding: 0.875rem; background: var(--blue-bg); border: 1px solid rgba(96, 165, 250, 0.2); border-radius: var(--radius); font-size: 0.875rem; color: var(--blue); line-height: 1.5; }
    .note-icon { flex-shrink: 0; }

    .water-section { display: flex; flex-direction: column; gap: 0.5rem; }
    .water-actions { display: flex; gap: 0.5rem; }
    .water-btn { flex: 1; padding: 0.875rem; background: var(--green); color: #000; border-radius: var(--radius-sm); font-weight: 600; font-size: 1rem; transition: opacity 0.15s; }
    .water-btn:disabled { opacity: 0.5; }
    .notes-toggle { width: 48px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 1.1rem; }

    .section-title { font-size: 1rem; font-weight: 700; margin-bottom: 0.25rem; }

    .care-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
    .care-summary { font-size: 0.875rem; line-height: 1.6; color: var(--text-muted); }
    .care-rows { display: flex; flex-direction: column; gap: 0.5rem; }
    .care-row { display: flex; gap: 0.75rem; font-size: 0.875rem; }
    .care-key { font-weight: 600; min-width: 100px; color: var(--text-muted); }

    .log-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .log-item { display: flex; gap: 0.75rem; align-items: flex-start; padding: 0.75rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
    .log-icon { flex-shrink: 0; font-size: 1.1rem; }
    .log-info { display: flex; flex-direction: column; gap: 0.15rem; }
    .log-date { font-size: 0.875rem; font-weight: 500; }
    .log-notes { font-size: 0.8rem; color: var(--text-muted); }

    .danger-zone { padding-top: 1rem; border-top: 1px solid var(--border); }
    .delete-trigger { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-sm); padding: 0.75rem 1.25rem; font-weight: 500; width: 100%; }
    .confirm-msg { color: var(--red); font-size: 0.9rem; margin-bottom: 0.75rem; }
    .confirm-actions { display: flex; gap: 0.75rem; }
    .cancel-btn { flex: 1; padding: 0.75rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); }
    .delete-btn { flex: 1; padding: 0.75rem; background: var(--red); color: #fff; border-radius: var(--radius-sm); font-weight: 600; }
    .delete-btn:disabled { opacity: 0.5; }
</style>
