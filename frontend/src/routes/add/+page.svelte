<script lang="ts">
    import { goto } from '$app/navigation';
    import { addPlant } from '$lib/api';

    let name = $state('');
    let location = $state<'indoor' | 'balcony'>('indoor');
    let photo = $state<File | null>(null);
    let preview = $state<string | null>(null);
    let loading = $state(false);
    let error = $state<string | null>(null);

    let canSubmit = $derived(!loading && name.trim().length > 0 && photo !== null);

    function handleFileChange(event: Event) {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;
        photo = file;
        const reader = new FileReader();
        reader.onload = (e) => { preview = e.target?.result as string; };
        reader.readAsDataURL(file);
    }

    async function handleSubmit(event: Event) {
        event.preventDefault();
        if (!canSubmit || !photo) return;
        loading = true;
        error = null;
        try {
            const plant = await addPlant(name.trim(), photo, location);
            goto(`/plants/${plant.id}`);
        } catch (e) {
            error = 'Failed to add plant. Please try again.';
            loading = false;
        }
    }
</script>

<div class="page">
    <header class="page-header">
        <a href="/" class="back-link" aria-label="Back to garden">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="back-icon">
                <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
        </a>
        <h1 class="page-title">New Plant</h1>
    </header>

    <form onsubmit={handleSubmit} class="form">
        <label class="photo-upload" class:has-preview={!!preview}>
            {#if preview}
                <img src={preview} alt="Plant preview" class="preview-img" />
                <div class="photo-overlay">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="overlay-icon">
                        <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                        <circle cx="12" cy="13" r="4" />
                    </svg>
                    <span>Change photo</span>
                </div>
            {:else}
                <div class="upload-prompt">
                    <div class="upload-ring">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="upload-camera">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                            <circle cx="12" cy="13" r="4" />
                        </svg>
                    </div>
                    <p class="upload-text">Take or choose a photo</p>
                    <p class="upload-hint">We'll identify the species for you</p>
                </div>
            {/if}
            <input
                type="file"
                accept="image/*"
                onchange={handleFileChange}
                class="file-input"
            />
        </label>

        <div class="field">
            <label class="field-label" for="plant-name">Plant Name</label>
            <input
                id="plant-name"
                type="text"
                placeholder="e.g. Living room fern"
                bind:value={name}
                disabled={loading}
            />
        </div>

        <div class="field">
            <span class="field-label">Location</span>
            <div class="toggle-group">
                <button type="button" class="toggle-option" class:active={location === 'indoor'} onclick={() => location = 'indoor'} disabled={loading}>
                    Indoor
                </button>
                <button type="button" class="toggle-option" class:active={location === 'balcony'} onclick={() => location = 'balcony'} disabled={loading}>
                    Balcony
                </button>
            </div>
        </div>

        {#if error}
            <div class="error-msg">{error}</div>
        {/if}

        <button type="submit" class="submit-btn" disabled={!canSubmit}>
            {#if loading}
                <span class="spinner"></span>
                Identifying...
            {:else}
                Add & Identify
            {/if}
        </button>
    </form>
</div>

<style>
    .page {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        animation: fadeIn 0.4s var(--ease-out);
    }

    .page-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .back-link {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--surface);
        color: var(--text-secondary);
        text-decoration: none;
        transition: background 0.15s;
    }

    .back-icon { width: 20px; height: 20px; }

    .page-title {
        font-family: var(--font-display);
        font-size: 1.5rem;
        font-weight: 700;
    }

    .form { display: flex; flex-direction: column; gap: 1.25rem; }

    .photo-upload {
        position: relative;
        width: 100%;
        aspect-ratio: 4/3;
        border-radius: var(--radius);
        border: 2px dashed var(--border-hover);
        overflow: hidden;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.25s var(--ease-out);
        background: var(--surface);
    }
    .photo-upload:hover, .photo-upload:focus-within { border-color: var(--accent); }
    .photo-upload.has-preview { border-style: solid; border-color: transparent; }

    .upload-prompt {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        color: var(--text-secondary);
    }

    .upload-ring {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: var(--accent-dim);
        border: 1.5px solid var(--accent-medium);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .upload-camera { width: 28px; height: 28px; color: var(--accent); }

    .upload-text { font-weight: 600; font-size: 0.95rem; }
    .upload-hint { font-size: 0.8rem; color: var(--text-muted); }

    .preview-img { width: 100%; height: 100%; object-fit: cover; }

    .photo-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 0.75rem;
        background: linear-gradient(transparent, rgba(0,0,0,0.7));
        color: white;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .overlay-icon { width: 18px; height: 18px; }

    .file-input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }

    .field { display: flex; flex-direction: column; gap: 0.4rem; }
    .field-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .toggle-group {
        display: flex; gap: 0.5rem;
    }
    .toggle-option {
        flex: 1; padding: 0.7rem; border-radius: var(--radius-sm);
        background: var(--surface); border: 1.5px solid var(--border);
        font-weight: 600; font-size: 0.875rem; color: var(--text-muted);
        transition: all 0.15s;
    }
    .toggle-option.active {
        border-color: var(--accent); color: var(--accent);
        background: var(--accent-dim);
    }

    .error-msg {
        padding: 0.75rem 1rem;
        background: var(--danger-dim);
        border: 1px solid rgba(201, 123, 123, 0.2);
        border-radius: var(--radius-sm);
        color: var(--danger);
        font-size: 0.875rem;
    }

    .submit-btn {
        padding: 1rem;
        background: var(--accent);
        color: var(--bg);
        border-radius: var(--radius-sm);
        font-weight: 700;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: opacity 0.15s, transform 0.15s var(--ease-spring);
        min-height: 52px;
    }
    .submit-btn:active { transform: scale(0.97); }
    .submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

    .spinner {
        width: 1.1rem;
        height: 1.1rem;
        border: 2.5px solid rgba(0, 0, 0, 0.15);
        border-top-color: var(--bg);
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }
</style>
