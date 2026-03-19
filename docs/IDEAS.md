# Product Ideas & Feature Brainstorm

Captured 2026-03-19. Dogfooding first, then revisit.

## Deepen the core loop

- **Photo timeline** — every retake builds a visual history per plant. See growth/decline over time. Makes retake-photo a habit, not a chore.
- **Seasonal rhythms** — dormancy awareness. Proactive interval changes based on season, not just reactive weather adjustments.
- **Watering quality feedback** — after each cycle, quick "how does it look?" (thumbs up/down or photo). Closes the loop: did the interval work? System learns your specific environment over time.
- **Soil moisture sensors** — cheap Zigbee/BLE sensors as input alongside weather. Pi is always-on, could listen for sensor data and override schedules when soil is actually dry.

## Make the AI smarter

- **Diagnosis mode** — "something's wrong" flow with close-up photo + Claude follow-up questions for targeted diagnosis.
- **Care plan generation** — beyond watering: fertilizing schedule, repotting reminders, pruning guidance. Seasonal care calendar per plant.
- **Cross-plant intelligence** — "your balcony plants all needed more water this week, consider grouping watering days" or "peace lily and pothos have similar needs, water together."

## Personality & engagement

- **Plant personas** — notifications from the plant's perspective based on species personality.
- **Achievements/milestones** — "100 days streak", "first bloom", "survived winter". Light gamification for consistency.
- **Switchable reminder characters** — beyond Rick & Morty: zen master, passive-aggressive British butler, concerned grandma, etc.

## Social / sharing

- **Plant passport** — shareable card per plant with story, species, care history, health score.
- **Care tips exchange** — anonymized aggregate data: "people in your climate zone water this species every X days."
- **Gift mode** — send a care card with learned intervals when giving someone a cutting.

## Hardware & environment

- **Room/zone management** — rooms with light/humidity profiles. Recommendations per zone.
- **Light tracking** — measure actual lux levels, compare to species requirements.
- **Climate dashboard** — local microclimate trends over time.

## Product growth

- **Nursery/store scan** — scan a plant at the store, get "will it survive in your home?" assessment.
- **Plant journal export** — beautiful PDF/webpage of your collection with photos and timeline.
- **Beginner onboarding** — guided "first plant" flow, then expand.
- **Notification channels** — native PWA push, email digest, WhatsApp (beyond Telegram).
- **Integrations** — Home Assistant, Apple Shortcuts, IFTTT.

## Prioritization notes

Photo timeline is the highest-leverage feature: low effort, high emotional payoff, and turns retake-photo into a habit. Combined with seasonal awareness and watering feedback, creates a genuinely learning system.
