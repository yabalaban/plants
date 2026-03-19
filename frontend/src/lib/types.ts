export interface PlantIdentification {
    species: string;
    confidence: string;
    care_summary: string;
    light_preference: string;
    base_watering_interval_days: number;
    overwatering_signs: string;
    underwatering_signs: string;
}

export interface Plant {
    id: number;
    name: string;
    species: string | null;
    photo_path: string;
    identification_details: PlantIdentification | null;
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
