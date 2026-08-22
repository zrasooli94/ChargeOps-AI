# ChargeOps AI — Next.js frontend migration

This folder is a parallel replacement for the existing Streamlit `frontend/app.py`. Keep the Streamlit frontend running until the Next.js version reaches feature parity and passes production testing.

## Architecture

Browser -> Next.js (Vercel) -> Next.js server proxy -> existing FastAPI (Render) -> Neon PostgreSQL/pgvector

The Next.js proxy stores the FastAPI access token in an HttpOnly cookie, so the browser does not need to store the bearer token in localStorage and the browser does not call Render directly.

## Local setup

1. Copy this folder into the repository as `frontend-next/`.
2. Copy `.env.example` to `.env.local`.
3. Set:
   - `CHARGEOPS_API_URL=http://127.0.0.1:8000` for local FastAPI, or your Render API URL.
   - `CHARGEOPS_DEMO_EMAIL` and `CHARGEOPS_DEMO_PASSWORD` for the public viewer/demo account.
4. Run `npm install`.
5. Run `npm run dev`.
6. Open `http://localhost:3000`.

## Migrated feature flows

- FastAPI OAuth2 form login + `/auth/me`
- Stations and shared station context
- Agent run/resume, thread IDs, chat, protected approval flow
- Demand forecasting and details
- Incidents and operator/admin lifecycle updates
- Knowledge document list, semantic search, admin upload/delete
- Observability runs and inspector
- Admin users, role changes and activation/deactivation
- System/architecture and station inventory

## Vercel

Create a Vercel project from the same GitHub repository and set Root Directory to `frontend-next`.
Add the same three environment variables there. The FastAPI backend remains on Render and the database remains on Neon.

After Vercel is verified, update the LinkedIn project URL to the Vercel URL and then retire the Streamlit Render frontend if desired.
