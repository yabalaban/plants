export interface PlantIdentification {
    species: string;
    confidence: string;
    care_summary: string;
    light_preference: string;
    base_watering_interval_days: number;
    overwatering_signs: string;
    underwatering_signs: string;
}

export interface PlantHealth {
    overall: string;
    summary: string;
    issues: string[];
    recommendations: string[];
}

export interface Plant {
    id: number;
    name: string;
    species: string | null;
    location: string;
    photo_path: string;
    identification_details: PlantIdentification | null;
    health_status: PlantHealth | null;
    base_watering_interval_days: number | null;
    created_at: string;
    interval_days: number | null;
    next_watering: string | null;
    adjustment_reason: string | null;
}

export interface PlantDetail extends Plant {
    watering_logs: WateringLog[];
}

export interface WateringLog {
    id: number;
    watered_at: string;
    notes: string | null;
}

export interface Settings {
    location_city: string;
    location_latitude: number;
    location_longitude: number;
    telegram_bot_token_set: boolean;
    telegram_chat_id: string;
    reminder_time: string;
}

export interface SettingsUpdate {
    location_city?: string;
    telegram_bot_token?: string;
    telegram_chat_id?: string;
    reminder_time?: string;
}

export interface WeatherEntry {
    date: string;
    temp_high: number | null;
    temp_low: number | null;
    humidity: number | null;
    precipitation_mm: number | null;
    fetched_at: string;
}

export interface ClaudeLog {
    id: number;
    task: string;
    prompt: string;
    response: string | null;
    error: string | null;
    duration_ms: number;
    created_at: string;
}
