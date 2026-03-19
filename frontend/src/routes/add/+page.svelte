<script lang="ts">
    import { goto } from '$app/navigation';
    import { addPlant } from '$lib/api';

    let name = $state('');
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
            const plant = await addPlant(name.trim(), photo);
            goto(`/plants/${plant.id}`);
        } catch (e) {
            error = 'Failed to add plant. Please try again.';
            loading = false;
        }
    }
</script>

<div class="page">
    <h1 class="title">Add Plant</h1>

    <div class="info-box">
        <span class="info-icon">✨</span>
        <p>After adding, Claude will identify your plant and provide personalized care guidance including watering schedule.</p>
    </div>

    <form onsubmit={handleSubmit} class="form">
        <div class="section">
            <span class="section-label">Photo</span>
            <label class="photo-upload" class:has-preview={!!preview}>
                {#if preview}
                    <img src={preview} alt="Plant preview" class="preview-img" />
                    <div class="change-overlay">Change photo</div>
                {:else}
                    <div class="upload-prompt">
                        <span class="upload-icon">📷</span>
                        <p>Tap to take a photo or choose from library</p>
                    </div>
                {/if}
                <input
                    type="file"
                    accept="image/*"
                    onchange={handleFileChange}
                    class="file-input"
                />
            </label>
        </div>

        <div class="section">
            <label class="section-label" for="plant-name">Name</label>
            <input
                id="plant-name"
                type="text"
                placeholder="e.g. Living room fern"
                bind:value={name}
                disabled={loading}
            />
        </div>

        {#if error}
            <p class="error-msg">{error}</p>
        {/if}

        <button type="submit" class="submit-btn" disabled={!canSubmit}>
            {#if loading}
                <span class="spinner"></span>
                Identifying...
            {:else}
                Add & Identify Plant
            {/if}
        </button>
    </form>
</div>

<style>
    .page { display: flex; flex-direction: column; gap: 1.5rem; }
    .title { font-size: 1.6rem; font-weight: 700; }

    .info-box {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        padding: 1rem;
        background: var(--blue-bg);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: var(--radius);
        font-size: 0.875rem;
        color: var(--blue);
        line-height: 1.5;
    }
    .info-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 0.05rem; }

    .form { display: flex; flex-direction: column; gap: 1.25rem; }
    .section { display: flex; flex-direction: column; gap: 0.5rem; }
    .section-label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

    .photo-upload {
        position: relative;
        width: 100%;
        aspect-ratio: 4/3;
        border-radius: var(--radius);
        border: 2px dashed var(--border);
        overflow: hidden;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.15s;
    }
    .photo-upload:hover { border-color: var(--green); }
    .photo-upload.has-preview { border-style: solid; border-color: var(--border); }

    .upload-prompt { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; color: var(--text-muted); text-align: center; padding: 1rem; }
    .upload-icon { font-size: 2.5rem; }
    .upload-prompt p { font-size: 0.875rem; }

    .preview-img { width: 100%; height: 100%; object-fit: cover; }

    .change-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 0.5rem;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        text-align: center;
        font-size: 0.8rem;
    }

    .file-input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }

    .error-msg { color: var(--red); font-size: 0.875rem; }

    .submit-btn {
        padding: 0.875rem;
        background: var(--green);
        color: #000;
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: opacity 0.15s;
    }
    .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .spinner {
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(0, 0, 0, 0.2);
        border-top-color: #000;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
</style>
