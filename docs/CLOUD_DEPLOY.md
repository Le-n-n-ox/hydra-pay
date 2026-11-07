# Running Hydra Pay in the cloud (Rumpty)

The dashboard, M-Pesa, WhatsApp, SMS and USSD run on a cloud server. The card reader stays on the laptop's USB:
`bridge.py` reads each tap and sends it to the server over HTTPS.

```
ESP32 reader --USB--> laptop: bridge.py --HTTPS--> cloud: dashboard.py --> M-Pesa, WhatsApp, SMS, USSD
                                                        ^
                                       dashboard in any browser, callbacks from Safaricom / ThriveVAS / UltraMsg
```

The laptop no longer needs ngrok or `start.bat`. It only needs internet and `start_bridge.bat`.

## 1. Create the deployment on Rumpty

New deployment → GitHub → repository `hydra-pay`, branch `main`, then set:

| Setting | Value |
|---|---|
| Application type | **Web Service/Backend** |
| Build method | **Dockerfile** (don't leave it on Auto: the repo also has a frontend) |
| Root directory | empty (the `Dockerfile` is at the repo root) |
| Port | leave the default; Rumpty passes it in as `PORT` |
| Readiness/health check path | `/` |
| Persistent storage | tick **Add persistent storage**, mount path **`/data`**, size **1 GiB** |

Without persistent storage the database (cards, payments, history) is wiped on every deploy.

Deploy once to get the app's address (`https://…`). It is fine if M-Pesa etc. are off on this first run.

## 2. Add the environment variables

On the laptop, in the project folder:

```
python cloud_env.py https://YOUR-APP-ADDRESS
```

This writes `.env.cloud` with every variable the server needs (keys from `.env`, the M-Pesa settings, the admin PIN,
a new bridge token and the public address). Nothing secret is printed. It also adds `CLOUD_URL` and `BRIDGE_TOKEN`
to `.env` for the bridge.

Open `.env.cloud`, add each line in Rumpty's **Env** tab, redeploy, then delete `.env.cloud`.

| Variable | What it is |
|---|---|
| `PUBLIC_URL` | the app's address; M-Pesa, WhatsApp, SMS and USSD callbacks go here |
| `BRIDGE_TOKEN` | shared secret between the server and the laptop bridge |
| `ADMIN_PIN` | admin PIN (not 1234), needed for every change |
| `MPESA_CONFIG_JSON` | contents of `mpesa_config.json` |
| `READER=bridge`, `DATA_DIR=/data` | already set in the Dockerfile; included for clarity |
| `ULTRAMSG_*`, `GEMINI_*`, `ELEVENLABS_*`, `SMS_PROVIDER`, `THRIVEVAS_*`, `TELCO_*` | same as in `.env` |

## 3. Start the bridge on the laptop

Plug in the ESP32 and double-click **`start_bridge.bat`**. Keep the window open. Within a few seconds the dashboard's
reader chip turns green ("Connected on COMx (laptop bridge)"). If it says **Laptop bridge offline**, the bridge isn't
running or can't reach the server.

- A tap that can't reach the server within 20 seconds is dropped, so nobody gets a late M-Pesa prompt.
- Each tap is sent with an id; the server ignores repeats if the bridge retries.

## 4. Point the providers at the cloud

- **M-Pesa:** nothing to do; each prompt carries `PUBLIC_URL/mpesa/callback`.
- **WhatsApp (UltraMsg):** the server sets the webhook to `PUBLIC_URL/webhook` when it starts.
- **SMS / USSD:** the server log and the dashboard's **SMS & USSD** page show the callback URLs to paste into the
  provider portal.

**Don't run `start.bat` on the laptop at the same time.** The laptop dashboard would point the WhatsApp webhook back at
ngrok and keep its own separate database.

## Going back to laptop-only

Stop the bridge and run `start.bat` as before. The laptop keeps its own `rfid.db`; the cloud database stays on Rumpty.

## Test the image locally (optional)

```
docker build -t hydra-pay-cloud .
docker run -p 8000:8000 -e BRIDGE_TOKEN=test -e ADMIN_PIN=9876 -e SMS_PROVIDER=none hydra-pay-cloud
```
