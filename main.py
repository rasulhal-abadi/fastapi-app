from typing import Optional

from fastapi import FastAPI

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient, errors
import asyncio
api_id = '26262567'
api_hash = '6d9ed43d1bd597c3d5ca81276f338148'
client = TelegramClient('session_name', api_id, api_hash)

app = FastAPI()

class LoginRequest(BaseModel):
    phone_number: str
    code: str = None
    password: str = None

class SendMessagesRequest(BaseModel):
    message: str
    interval: int
    groups: str

@app.post("/login")
async def login_telegram(request: LoginRequest):
    try:
        await client.connect()
        if not await client.is_user_authorized():
            if not request.code:
                await client.send_code_request(request.phone_number)
                return {"status": "Code Sent"}
            else:
                try:
                    await client.sign_in(request.phone_number, request.code)
                    if request.password:
                        try:
                            await client.sign_in(password=request.password)
                            return {"status": "Success"}
                        except errors.SessionPasswordNeededError:
                            return {"status": "Password Required"}
                        except errors.PasswordHashInvalidError:
                            return {"status": "Invalid Password"}
                    return {"status": "Success"}
                except errors.SessionPasswordNeededError:
                    return {"status": "Password Required"}
                except errors.PhoneCodeInvalidError:
                    return {"status": "Invalid Code"}
        return {"status": "Already Authorized"}
    except errors.FloodWaitError as e:
        return {"status": f"Please wait {e.seconds} seconds and try again."}
    except errors.PhoneNumberInvalidError:
        raise HTTPException(status_code=400, detail="Invalid Phone Number")
    except errors.PhoneCodeInvalidError:
        raise HTTPException(status_code=400, detail="Invalid Code")
    except errors.PhoneCodeExpiredError:
        raise HTTPException(status_code=400, detail="Code Expired")
    except errors.FloodError:
        raise HTTPException(status_code=400, detail="Too many attempts. Please try again later.")
    except errors.RpcCallFailError as e:
        raise HTTPException(status_code=500, detail=f"Telegram server error: {e.message}")
    except errors.AuthKeyDuplicatedError:
        raise HTTPException(status_code=400, detail="Duplicate authorization detected.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        await client.disconnect()

@app.post("/send_messages")
async def send_messages_periodically(request: SendMessagesRequest):
    try:
        await client.connect()
        groups = request.groups.split(',')
        interval = max(1, int(request.interval)) * 60  # Convert minutes to seconds
        for group_id in groups:
            try:
                while True:
                    await client.send_message(int(group_id), request.message)
                    await asyncio.sleep(interval)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"خطأ أثناء إرسال الرسالة إلى {group_id}: {str(e)}")
        return {"status": "Messages Sent"}
    finally:
        await client.disconnect()
