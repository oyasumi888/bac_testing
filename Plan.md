I am planning to build a full-stack web application that calculates and tracks a user's Blood Alcohol Concentration (BAC) in real-time to help them understand their level of intoxication.
The core logic must strictly rely on the Widmark Formula for accuracy.

## Preferred Tech Stack:

Frontend: React.js
Backend: Python or Node.js
Database: PostgreSQL
Infrastructure: Docker

## Core Features:

User Onboarding: Collect essential biological data (weight in kg, biological sex) needed for the Widmark constant. This should be saved per session or user profile.
Drink Catalog: A pre-populated database table of common drinks with standard volumes (ml) and ABV (Alcohol by Volume) percentages, so users don't have to input these manually.
Real-Time Tracking: A UI where users can easily add a drink ("+1 Beer", "+1 Shot") with an automatic timestamp.
BAC Calculation & UI: A backend controller that calculates the current BAC using the accumulated drinks and time elapsed. The frontend should display a dynamic progress bar or color-coded thresholds (e.g., Green: <0.03, Yellow: 0.04-0.06, Red: >0.08) indicating their intoxication level.
Please provide a comprehensive project plan including:

## System Architecture Overview: 
How the frontend, backend, and database will communicate.

## Database Schema (PostgreSQL): 
Tables, columns, and relationships for Users, Drinks Catalog, and Consumption Logs.

## API Design: 
Key REST endpoints needed for the core loop.

## Step-by-Step Development Roadmap: 
Breaking down the project into logical phases (e.g., Phase 1: DB & Auth, Phase 2: Core Logic, etc.).