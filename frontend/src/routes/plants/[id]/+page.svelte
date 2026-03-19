<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { getPlant, waterPlant, deletePlant, updatePlant, updatePlantPhoto } from '$lib/api';
    import type { PlantDetail } from '$lib/types';

    let plant = $state<PlantDetail | null>(null);
    let loading = $state(true);
    let error = $state<string | null>(null);
    let watering = $state(false);
    let saving = $state(false);
    let retaking = $state(false);
    let photoInput: HTMLInputElement;
    let deleting = $state(false);
    let showDeleteConfirm = $state(false);
    let waterNotes = $state('');
    let showNotesInput = $state(false);
    let editName = $state('');
    let editLocation = $state<'indoor' | 'balcony'>('indoor');
    let saveMessage = $state<{ text: string; type: 'success' | 'error' } | null>(null);

    let id = $derived(Number($page.params.id));

    let hasChanges = $derived(
        plant != null && (editName !== plant.name || editLocation !== plant.location)
    );

    async function load() {
        try {
            loading = true;
            plant = await getPlant(id);
            editName = plant.name;
            editLocation = plant.location as 'indoor' | 'balcony';
        } catch {
            error = 'Failed to load plant';
        } finally {
            loading = false;
        }
    }

    async function handleSave() {
        if (!plant || !hasChanges || saving) return;
        saving = true;
        try {
            const updates: Record<string, string> = {};
            if (editName !== plant.name) updates.name = editName.trim();
            if (editLocation !== plant.location) updates.location = editLocation;
            await updatePlant(plant.id, updates);
            await load();
            saveMessage = { text: 'Saved', type: 'success' };
            setTimeout(() => { saveMessage = null; }, 2000);
        } catch {
            saveMessage = { text: 'Failed to save', type: 'error' };
            setTimeout(() => { saveMessage = null; }, 3000);
        } finally {
            saving = false;
        }
    }

    async function handleRetakePhoto(event: Event) {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file || !plant || retaking) return;
        retaking = true;
        try {
            await updatePlantPhoto(plant.id, file);
            await load();
            saveMessage = { text: 'Photo updated, checking health...', type: 'success' };
            setTimeout(() => { saveMessage = null; }, 3000);
        } catch {
            saveMessage = { text: 'Failed to update photo', type: 'error' };
            setTimeout(() => { saveMessage = null; }, 3000);
        } finally {
            retaking = false;
            input.value = '';
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
            error = 'Failed to log watering';
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
    <div class="loading-state">
        <div class="skeleton-hero"></div>
        <div class="skeleton-bar wide"></div>
        <div class="skeleton-bar narrow"></div>
    </div>
{:else if error || !plant}
    <div class="error-state">
        <p>{error ?? 'Plant not found'}</p>
        <a href="/" class="back-cta">Back to garden</a>
    </div>
{:else}
    <div class="detail">
        <div class="hero-section">
            <a href="/" class="back-btn" aria-label="Back to garden">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" class="back-icon">
                    <path d="M19 12H5M12 19l-7-7 7-7" />
                </svg>
            </a>
            <label class="retake-btn" aria-label="Retake photo">
                {#if retaking}
                    <span class="spinner-light"></span>
                {:else}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="retake-icon">
                        <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                        <circle cx="12" cy="13" r="4" />
                    </svg>
                {/if}
                <input
                    type="file"
                    accept="image/*"
                    onchange={handleRetakePhoto}
                    class="retake-input"
                    disabled={retaking}
                />
            </label>
            <img
                class="hero-photo"
                src={plant.photo_path}
                alt={plant.name}
            />
            <div class="hero-gradient"></div>
            <div class="hero-info">
                <h1 class="plant-name">{editName || plant.name}</h1>
                {#if plant.species}
                    <p class="plant-species">{plant.species}</p>
                {/if}
            </div>
        </div>

        <div class="content">
            <div class="edit-section">
                <div class="edit-field">
                    <label class="edit-label" for="edit-name">Name</label>
                    <input id="edit-name" type="text" bind:value={editName} class="edit-input" />
                </div>
                <div class="edit-field">
                    <span class="edit-label">Location</span>
                    <div class="toggle-group">
                        <button type="button" class="toggle-option" class:active={editLocation === 'indoor'} onclick={() => editLocation = 'indoor'}>Indoor</button>
                        <button type="button" class="toggle-option" class:active={editLocation === 'balcony'} onclick={() => editLocation = 'balcony'}>Balcony</button>
                    </div>
                </div>
                {#if hasChanges}
                    <button class="save-btn" onclick={handleSave} disabled={saving || !editName.trim()}>
                        {#if saving}
                            <span class="spinner"></span> Saving...
                        {:else}
                            Save Changes
                        {/if}
                    </button>
                {/if}
                {#if saveMessage}
                    <div class="save-toast {saveMessage.type}" style="animation: fadeIn 0.3s var(--ease-out)">{saveMessage.text}</div>
                {/if}
            </div>

            <div class="stats-row">
                <div class="stat">
                    <span class="stat-value">
                        {plant.interval_days != null ? `${Math.round(plant.interval_days)}` : '—'}
                    </span>
                    <span class="stat-unit">days</span>
                    <span class="stat-label">Interval</span>
                </div>
                <div class="stat-divider"></div>
                <div class="stat">
                    <span class="stat-value">
                        {plant.next_watering ? formatDate(plant.next_watering).split(',')[0] : '—'}
                    </span>
                    <span class="stat-label">Next water</span>
                </div>
                <div class="stat-divider"></div>
                <div class="stat">
                    <span class="stat-value">{plant.watering_logs.length}</span>
                    <span class="stat-label">Total waters</span>
                </div>
            </div>

            {#if plant.adjustment_reason}
                <div class="note-card">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="note-icon">
                        <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <p>{plant.adjustment_reason}</p>
                </div>
            {/if}

            <div class="water-section">
                {#if showNotesInput}
                    <input
                        type="text"
                        placeholder="Add a note (optional)"
                        bind:value={waterNotes}
                    />
                {/if}
                <div class="water-actions">
                    <button
                        class="water-btn"
                        onclick={handleWater}
                        disabled={watering}
                    >
                        {#if watering}
                            <span class="spinner"></span>
                            Watering...
                        {:else}
                            <svg viewBox="0 0 24 24" fill="currentColor" class="water-icon">
                                <path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0L12 2.69z" />
                            </svg>
                            Water Now
                        {/if}
                    </button>
                    <button
                        class="notes-toggle"
                        onclick={() => showNotesInput = !showNotesInput}
                        aria-label="Toggle notes"
                        class:active={showNotesInput}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toggle-icon">
                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                    </button>
                </div>
            </div>

            {#if plant.identification_details}
                {@const info = plant.identification_details}
                <div class="section">
                    <h2 class="section-title">Care Guide</h2>
                    <div class="care-card">
                        {#if info.care_summary}
                            <p class="care-summary">{info.care_summary}</p>
                        {/if}
                        <div class="care-grid">
                            {#if info.light_preference}
                                <div class="care-item">
                                    <span class="care-label">Light</span>
                                    <span class="care-value">{info.light_preference}</span>
                                </div>
                            {/if}
                            {#if info.overwatering_signs}
                                <div class="care-item">
                                    <span class="care-label">Overwatering</span>
                                    <span class="care-value">{info.overwatering_signs}</span>
                                </div>
                            {/if}
                            {#if info.underwatering_signs}
                                <div class="care-item">
                                    <span class="care-label">Underwatering</span>
                                    <span class="care-value">{info.underwatering_signs}</span>
                                </div>
                            {/if}
                        </div>
                    </div>
                </div>
            {/if}

            {#if plant.health_status}
                {@const health = plant.health_status}
                <div class="section">
                    <h2 class="section-title">Health Check</h2>
                    <div class="health-card {health.overall}">
                        <div class="health-header">
                            <span class="health-badge {health.overall}">
                                {#if health.overall === 'good'}&#x2705;{:else if health.overall === 'fair'}&#x26A0;&#xFE0F;{:else if health.overall === 'poor'}&#x1F7E0;{:else}&#x1F534;{/if}
                                {health.overall}
                            </span>
                        </div>
                        <p class="health-summary">{health.summary}</p>
                        {#if health.issues.length > 0}
                            <div class="health-list">
                                <span class="health-list-label">Issues</span>
                                {#each health.issues as issue}
                                    <span class="health-item issue">{issue}</span>
                                {/each}
                            </div>
                        {/if}
                        {#if health.recommendations.length > 0}
                            <div class="health-list">
                                <span class="health-list-label">Recommendations</span>
                                {#each health.recommendations as rec}
                                    <span class="health-item rec">{rec}</span>
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}

            {#if plant.watering_logs.length > 0}
                <div class="section">
                    <h2 class="section-title">History</h2>
                    <div class="log-list">
                        {#each plant.watering_logs.slice(0, 10) as log (log.id)}
                            <div class="log-item">
                                <div class="log-dot"></div>
                                <div class="log-body">
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
                    <div class="confirm-card">
                        <p class="confirm-msg">Delete <strong>{plant.name}</strong>?<br />This cannot be undone.</p>
                        <div class="confirm-actions">
                            <button class="cancel-btn" onclick={() => showDeleteConfirm = false}>Cancel</button>
                            <button class="delete-btn" onclick={handleDelete} disabled={deleting}>
                                {deleting ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                {:else}
                    <button class="delete-trigger" onclick={() => showDeleteConfirm = true}>
                        Remove Plant
                    </button>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    .detail { animation: fadeIn 0.35s var(--ease-out); }

    /* Loading */
    .loading-state { display: flex; flex-direction: column; gap: 1rem; }
    .skeleton-hero { aspect-ratio: 4/3; border-radius: var(--radius); background: var(--surface); animation: pulse 1.5s infinite; }
    .skeleton-bar { height: 20px; border-radius: var(--radius-xs); background: var(--surface); animation: pulse 1.5s infinite; }
    .skeleton-bar.wide { width: 60%; }
    .skeleton-bar.narrow { width: 40%; }

    .error-state { text-align: center; padding: 3rem 1rem; color: var(--text-secondary); }
    .back-cta { display: inline-block; margin-top: 1rem; color: var(--accent); text-decoration: none; }

    /* Hero */
    .hero-section {
        position: relative;
        margin: -1.25rem -1.25rem 0;
        aspect-ratio: 4/3;
        overflow: hidden;
    }

    .back-btn {
        position: absolute;
        top: calc(0.75rem + env(safe-area-inset-top, 0px));
        left: 0.75rem;
        z-index: 10;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(0,0,0,0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }

    .back-icon { width: 20px; height: 20px; }

    .retake-btn {
        position: absolute;
        top: calc(0.75rem + env(safe-area-inset-top, 0px));
        right: 0.75rem;
        z-index: 10;
        width: 40px; height: 40px; border-radius: 50%;
        background: rgba(0,0,0,0.4);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        color: white; display: flex; align-items: center; justify-content: center;
        cursor: pointer;
    }
    .retake-icon { width: 18px; height: 18px; }
    .retake-input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
    .spinner-light {
        width: 16px; height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white; border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    .hero-photo { width: 100%; height: 100%; object-fit: cover; }

    .hero-gradient {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60%;
        background: linear-gradient(transparent, var(--bg));
    }

    .hero-info {
        position: absolute;
        bottom: 1rem;
        left: 1.25rem;
        right: 1.25rem;
    }

    .plant-name {
        font-family: var(--font-display);
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .plant-species {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-style: italic;
        margin-top: 0.25rem;
    }

    /* Content */
    .content { display: flex; flex-direction: column; gap: 1.5rem; padding-top: 0.75rem; }

    /* Edit */
    .edit-section {
        display: flex; flex-direction: column; gap: 0.75rem;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 1rem;
    }
    .edit-field { display: flex; flex-direction: column; gap: 0.3rem; }
    .edit-label {
        font-size: 0.7rem; font-weight: 600; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .edit-input {
        font-size: 0.95rem; padding: 0.6rem 0.75rem;
        background: var(--bg); border: 1px solid var(--border);
        border-radius: var(--radius-sm); color: var(--text-primary);
    }
    .edit-input:focus { border-color: var(--accent); outline: none; }
    .toggle-group { display: flex; gap: 0.5rem; }
    .toggle-option {
        flex: 1; padding: 0.6rem; border-radius: var(--radius-sm);
        background: var(--bg); border: 1.5px solid var(--border);
        font-weight: 600; font-size: 0.8rem; color: var(--text-muted);
        transition: all 0.15s;
    }
    .toggle-option.active {
        border-color: var(--accent); color: var(--accent);
        background: var(--accent-dim);
    }
    .save-btn {
        padding: 0.75rem; background: var(--accent); color: var(--bg);
        border-radius: var(--radius-sm); font-weight: 700; font-size: 0.9rem;
        display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        min-height: 44px; transition: transform 0.15s var(--ease-spring);
        animation: fadeIn 0.2s var(--ease-out);
    }
    .save-btn:active { transform: scale(0.97); }
    .save-btn:disabled { opacity: 0.5; }
    .save-toast {
        padding: 0.5rem 0.75rem; border-radius: var(--radius-xs);
        font-size: 0.8rem; font-weight: 500; text-align: center;
    }
    .save-toast.success { background: var(--accent-dim); color: var(--accent); }
    .save-toast.error { background: var(--danger-dim); color: var(--danger); }

    /* Stats */
    .stats-row {
        display: flex;
        align-items: center;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem;
    }

    .stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 0.1rem; }
    .stat-value { font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; color: var(--accent); }
    .stat-unit { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: -0.15rem; }
    .stat-label { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .stat-divider { width: 1px; height: 32px; background: var(--border); }

    /* Note */
    .note-card {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        padding: 0.875rem 1rem;
        background: var(--info-dim);
        border: 1px solid rgba(123, 168, 201, 0.15);
        border-radius: var(--radius-sm);
        font-size: 0.85rem;
        color: var(--info);
        line-height: 1.5;
    }
    .note-icon { width: 18px; height: 18px; flex-shrink: 0; margin-top: 0.1rem; }

    /* Water */
    .water-section { display: flex; flex-direction: column; gap: 0.5rem; }
    .water-actions { display: flex; gap: 0.5rem; }

    .water-btn {
        flex: 1;
        padding: 0.875rem;
        background: var(--accent);
        color: var(--bg);
        border-radius: var(--radius-sm);
        font-weight: 700;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: transform 0.15s var(--ease-spring);
        min-height: 52px;
    }
    .water-btn:active { transform: scale(0.97); }
    .water-btn:disabled { opacity: 0.5; }

    .water-icon { width: 18px; height: 18px; }

    .notes-toggle {
        width: 52px;
        background: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-muted);
        transition: border-color 0.15s, color 0.15s;
    }
    .notes-toggle.active { border-color: var(--accent); color: var(--accent); }
    .toggle-icon { width: 20px; height: 20px; }

    .spinner {
        width: 1.1rem;
        height: 1.1rem;
        border: 2.5px solid rgba(0,0,0,0.15);
        border-top-color: var(--bg);
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    /* Sections */
    .section { display: flex; flex-direction: column; gap: 0.5rem; }

    .section-title {
        font-family: var(--font-display);
        font-size: 1.1rem;
        font-weight: 700;
    }

    .care-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .care-summary { font-size: 0.875rem; line-height: 1.6; color: var(--text-secondary); }
    .care-grid { display: flex; flex-direction: column; gap: 0.75rem; }
    .care-item { display: flex; flex-direction: column; gap: 0.15rem; }
    .care-label { font-size: 0.7rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .care-value { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; }

    /* Health */
    .health-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 1rem;
        display: flex; flex-direction: column; gap: 0.75rem;
    }
    .health-card.good { border-color: var(--accent-medium); }
    .health-card.fair { border-color: rgba(232, 168, 124, 0.3); }
    .health-card.poor { border-color: rgba(232, 168, 124, 0.5); }
    .health-card.critical { border-color: rgba(201, 123, 123, 0.4); }
    .health-header { display: flex; align-items: center; }
    .health-badge {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.05em; padding: 0.2rem 0.5rem;
        border-radius: 999px; display: inline-flex; align-items: center; gap: 0.3rem;
    }
    .health-badge.good { background: var(--accent-dim); color: var(--accent); }
    .health-badge.fair { background: rgba(232, 168, 124, 0.1); color: var(--alert); }
    .health-badge.poor { background: rgba(232, 168, 124, 0.15); color: var(--alert); }
    .health-badge.critical { background: var(--danger-dim); color: var(--danger); }
    .health-summary { font-size: 0.875rem; line-height: 1.6; color: var(--text-secondary); }
    .health-list { display: flex; flex-direction: column; gap: 0.3rem; }
    .health-list-label {
        font-size: 0.65rem; font-weight: 600; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .health-item {
        font-size: 0.8rem; line-height: 1.5; color: var(--text-secondary);
        padding-left: 0.75rem; position: relative;
    }
    .health-item::before {
        content: ''; position: absolute; left: 0; top: 0.55rem;
        width: 4px; height: 4px; border-radius: 50%;
    }
    .health-item.issue::before { background: var(--alert); }
    .health-item.rec::before { background: var(--accent); }

    /* History */
    .log-list { display: flex; flex-direction: column; position: relative; padding-left: 1rem; }
    .log-list::before {
        content: '';
        position: absolute;
        left: 3px;
        top: 8px;
        bottom: 8px;
        width: 1px;
        background: var(--border);
    }

    .log-item { display: flex; gap: 1rem; align-items: flex-start; padding: 0.5rem 0; position: relative; }
    .log-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--accent);
        border: 1.5px solid var(--bg);
        flex-shrink: 0;
        margin-top: 0.4rem;
        margin-left: -1rem;
        position: relative;
        z-index: 1;
    }
    .log-body { display: flex; flex-direction: column; gap: 0.1rem; }
    .log-date { font-size: 0.85rem; font-weight: 500; }
    .log-notes { font-size: 0.78rem; color: var(--text-muted); }

    /* Delete */
    .danger-zone { padding-top: 1.5rem; border-top: 1px solid var(--border); }

    .delete-trigger {
        color: var(--text-muted);
        background: none;
        font-size: 0.85rem;
        padding: 0.75rem;
        width: 100%;
        text-align: center;
        transition: color 0.15s;
    }
    .delete-trigger:active { color: var(--danger); }

    .confirm-card {
        background: var(--danger-dim);
        border: 1px solid rgba(201, 123, 123, 0.2);
        border-radius: var(--radius-sm);
        padding: 1.25rem;
        animation: fadeInScale 0.2s var(--ease-out);
    }
    .confirm-msg { font-size: 0.9rem; color: var(--danger); margin-bottom: 1rem; line-height: 1.5; }
    .confirm-actions { display: flex; gap: 0.75rem; }
    .cancel-btn {
        flex: 1;
        padding: 0.75rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-weight: 500;
        min-height: 48px;
    }
    .delete-btn {
        flex: 1;
        padding: 0.75rem;
        background: var(--danger);
        color: white;
        border-radius: var(--radius-sm);
        font-weight: 700;
        min-height: 48px;
    }
    .delete-btn:disabled { opacity: 0.5; }
</style>
