import os
import datetime as dt
import pandas as pd
from dotenv import load_dotenv
from pyrogram import Client as telegram_client
from process_messages import process_messages
from get_message_reactions import get_message_reactions
from supabase import create_client
from utils import format_namelist

def main():

    # getting keyss and secrets 
    load_dotenv()
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_string = os.getenv('TELEGRAM_SESSION_STRING')
    tpl_group_id = int(os.getenv('TPL_GROUP_ID'))
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')


    # initialise supabase connection
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    all_messages = (supabase.table('chat_messages')
                    .select('msg_id')
                    .execute()
                    )
    latest_message_id = max(row['msg_id'] for row in all_messages.data)
    
    app = telegram_client(
        name="telegram_session",
        session_string=session_string,
        api_id=api_id,
        api_hash=api_hash
        )

    app.start()

    # get all new messages since the last export
    # most recent messages are fetched first. Stop once an old message is found (<= latest_message_id)
    all_new_messages = []
    for message in app.get_chat_history(tpl_group_id, limit=2000):
        if message.id > latest_message_id:
            all_new_messages.append(message)
        else:
            break

    # classifies each new message as either a chat message or new member joining (system message), processes the message to extract all relevant info
    new_chat_messages, new_members_joined = process_messages(all_new_messages)

    # uploads the new messages and new members
    if new_chat_messages:
        upload_messages = supabase.table("chat_messages").insert(new_chat_messages).execute()

    if new_members_joined:
        upload_members = supabase.table("member_list").insert(new_members_joined).execute()

    # get updated list of new members
    all_members = (supabase.table('member_list')
                .select('*')
                .execute()
                )
    tpl_namelist = format_namelist(all_members.data)

    # Get reactions and process them
    reactions = get_message_reactions(app, tpl_group_id, all_new_messages, tpl_namelist)
    
    # upload reactions to table
    if reactions:
        upload_reactions = supabase.table("chat_reactions").insert(reactions).execute()

    app.stop()


if __name__ == "__main__":
    main()
