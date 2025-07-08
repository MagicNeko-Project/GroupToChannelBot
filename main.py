import configparser
import os
from telethon import TelegramClient, events, errors

# --- Configuration Loading ---
config = configparser.ConfigParser()
config.read('config.ini')

API_ID = os.getenv('TELEGRAM_API_ID', config['telegram']['api_id'])
API_HASH = os.getenv('TELEGRAM_API_HASH', config['telegram']['api_hash'])
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER', config['telegram']['phone_number'])
SOURCE_GROUP_ID = int(os.getenv('TELEGRAM_SOURCE_GROUP_ID', config['telegram']['source_group_id']))
TARGET_CHANNEL_ID = int(os.getenv('TELEGRAM_TARGET_CHANNEL_ID', config['telegram']['target_channel_id']))
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', config['bot_settings']['command_prefix'])

# --- Basic Client Setup ---
# Initialize the client
# Using a file for the session is recommended for userbots
client = TelegramClient('userbot_session', API_ID, API_HASH)

async def main():
    """Main function to connect and run the userbot."""
    # Connect to Telegram
    await client.connect()

    if not await client.is_user_authorized():
        print("User is not authorized. Please run the script interactively to authorize.")
        await client.send_code_request(PHONE_NUMBER)
        code_ok = False
        try:
            code = input('Enter the code sent to Telegram: ')
            await client.sign_in(phone=PHONE_NUMBER, code=code)
            code_ok = True
        except errors.SessionPasswordNeededError:
            # This error means that 2FA is enabled.
            # Prompt for the password.
            password = input('Two-factor authentication is enabled. Please enter your password: ')
            try:
                await client.sign_in(password=password)
                code_ok = True
            except errors.PhoneCodeInvalidError:
                print("Invalid code entered. Please try again.")
            except errors.PasswordHashInvalidError:
                 print("Invalid password entered. Please try again.")
            except Exception as e_pass:
                print(f"Error during password entry: {e_pass}")
        except errors.PhoneCodeInvalidError:
            print("Invalid code entered. Please try again.")
        except errors.PhoneNumberUnoccupiedError:
            print(f"The phone number {PHONE_NUMBER} is not registered on Telegram.")
        except Exception as e:
            print(f"Sign in failed: {e}")

        if not code_ok:
            return # Exit if sign-in was not successful

        print("Signed in successfully!")

    print("Userbot started...")
    print(f"Listening for command '{COMMAND_PREFIX}' in group {SOURCE_GROUP_ID}")
    print(f"Forwarding to channel {TARGET_CHANNEL_ID}")

    # --- Event Handler for New Messages ---
    @client.on(events.NewMessage(chats=SOURCE_GROUP_ID))
    async def handler(event):
        message_text = event.message.message
        sender = await event.get_sender()
        sender_username = getattr(sender, 'username', 'N/A')
        print(f"Received message in group {SOURCE_GROUP_ID} from {sender_username}: '{message_text}'")

        if message_text.startswith(COMMAND_PREFIX):
            content_to_forward = message_text[len(COMMAND_PREFIX):].strip()
            if content_to_forward:
                try:
                    print(f"Command '{COMMAND_PREFIX}' detected. Content to forward: '{content_to_forward}'")
                    # We use send_message to send the content as the userbot.
                    # If you want to forward the message *as if the original sender sent it*
                    # (preserving sender name, etc.), you would use:
                    # await client.forward_messages(TARGET_CHANNEL_ID, event.message)
                    # However, the request implies the userbot posts the content.
                    await client.send_message(TARGET_CHANNEL_ID, content_to_forward)
                    print(f"Message successfully forwarded to channel {TARGET_CHANNEL_ID} by user {sender_username}")
                    # Optionally, send a confirmation back to the group (can be noisy)
                    # await event.reply(f"Message forwarded to channel {TARGET_CHANNEL_ID}!")
                except ValueError as ve:
                    print(f"Configuration Error: Ensure SOURCE_GROUP_ID and TARGET_CHANNEL_ID are valid integers. {ve}")
                    # Optionally, notify user in chat about config issues if desired, though console is safer for credentials
                except errors.ChatWriteForbiddenError:
                    print(f"Error: Bot does not have permission to write to the target channel {TARGET_CHANNEL_ID}.")
                    # Optionally, send a message to the source group or user
                    # await event.reply("Error: I don't have permission to send messages to the target channel.")
                except errors.UserIsBlockedError:
                    print(f"Error: The bot is blocked by the user or in the target channel {TARGET_CHANNEL_ID}.")
                except errors.RPCError as rpc_e:
                    print(f"Telegram API RPCError while forwarding message: {rpc_e}")
                except Exception as e:
                    print(f"An unexpected error occurred while forwarding message: {e}")
            else:
                print(f"Command '{COMMAND_PREFIX}' received from {sender_username}, but no content to forward.")
                # Optionally, inform the user about correct usage
                # await event.reply(f"Usage: {COMMAND_PREFIX} <your message>")
        else:
            # Optional: Log messages that don't match the command
            # print(f"Message does not start with command prefix: '{message_text}'")
            pass

    # Keep the script running.
    print("Listening for messages...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    # Ensure API_ID and API_HASH are not placeholders
    if 'YOUR_API_ID' in API_ID or 'YOUR_API_HASH' in API_HASH:
        print("ERROR: Please replace YOUR_API_ID and YOUR_API_HASH in config.ini or environment variables.")
    elif 'YOUR_PHONE_NUMBER' in PHONE_NUMBER:
        print("ERROR: Please replace YOUR_PHONE_NUMBER in config.ini or environment variables.")
    elif 'YOUR_SOURCE_GROUP_ID' in str(SOURCE_GROUP_ID) or SOURCE_GROUP_ID == 0: # Assuming 0 is an invalid ID
        print("ERROR: Please replace YOUR_SOURCE_GROUP_ID in config.ini or environment variables with a valid group ID.")
    elif 'YOUR_TARGET_CHANNEL_ID' in str(TARGET_CHANNEL_ID) or TARGET_CHANNEL_ID == 0: # Assuming 0 is an invalid ID
        print("ERROR: Please replace YOUR_TARGET_CHANNEL_ID in config.ini or environment variables with a valid channel ID.")
    else:
        asyncio.run(main())
