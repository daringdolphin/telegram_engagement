# How This Program Works

## Overview

This is a **Telegram Group Engagement Tracker** that automatically monitors a Telegram group chat and captures all activity into a database. Think of it as a data collection system that records:
- All messages sent in the group
- Who joins the group
- Reactions (emojis) people add to messages

The data is stored in Supabase (a cloud database) where it can be analyzed to understand group engagement patterns, active members, popular topics, etc.

---

## The Big Picture: What Happens When The Program Runs

1. **Connect to Telegram**: The program logs into Telegram using credentials (like logging into your account)
2. **Check What's New**: It looks at the database to find the most recent message ID it previously saved
3. **Fetch New Messages**: It pulls all new messages from Telegram since the last run (up to 2,000 messages)
4. **Process & Categorize**: It sorts through messages to separate regular chat messages from system events (like "John joined the group")
5. **Save to Database**: It uploads the new messages and member joins to Supabase
6. **Capture Reactions**: It goes through each new message and collects any reactions (👍, ❤️, etc.)
7. **Save Reactions**: It uploads all reactions to the database
8. **Disconnect**: It safely closes the Telegram connection

---

## Technology Stack

- **Python**: The programming language used
- **Pyrogram**: A library that lets Python talk to Telegram's servers
- **Supabase**: A cloud database (like Google Sheets but for apps) that stores all the data
- **Environment Variables**: Secure storage for passwords and API keys (kept in a `.env` file that's not shared publicly)

---

## File-by-File Breakdown

### `main.py` - The Orchestra Conductor

This is the entry point that coordinates everything. When you run the program, this file executes.

**What it does:**
1. Loads secret credentials (API keys, database connection info)
2. Connects to Supabase database and finds the last message ID that was saved
3. Connects to Telegram using Pyrogram
4. Fetches up to 2,000 recent messages from the group (stops when it hits an old message already in the database)
5. Calls `process_messages()` to categorize and extract data from messages
6. Uploads new messages and new member joins to Supabase
7. Fetches the updated member list from the database
8. Calls `get_message_reactions()` to collect reactions for all new messages
9. Uploads reactions to Supabase
10. Disconnects from Telegram

**Key Logic:**
- It only processes messages newer than the latest one in the database (incremental updates, not full re-sync)
- It handles three separate data types: messages, member joins, and reactions

---

### `process_messages.py` - The Message Classifier

This file takes raw Telegram message objects and categorizes them.

**What it does:**
- Takes a list of new messages
- Separates them into two categories:
  1. **Chat Messages**: Regular messages people sent (text, media, polls)
  2. **New Members**: System notifications when someone joins the group
- Extracts relevant information from each message using helper functions from `utils.py`
- Filters out edge cases like pinned messages, topic creation, group title changes

**Why this matters:**
Telegram has many types of "messages" - some are actual chat messages, others are system notifications. This file ensures we only save the data we care about in the right format.

---

### `get_message_reactions.py` - The Reaction Collector

This file fetches all the reactions (emoji responses) for messages.

**What it does:**
- Takes a list of messages and loops through each one
- Uses Telegram's API to fetch the list of reactions for each message (limit: 30 reactions per message)
- Extracts details about each reaction: which emoji, who reacted, when they reacted
- Matches the reactor's user ID to their username using the member list
- Handles errors gracefully (e.g., if a message has no reactions or if the API call fails)

**Why this is tricky:**
Reactions require a separate API call per message. The program has to handle cases where:
- A message has no reactions (error handling)
- A user who reacted isn't in the member list (error handling)
- Telegram rate limits the requests (limit of 30 reactions fetched per message)

---

### `utils.py` - The Helper Functions Toolbox

This file contains reusable functions that extract and format data.

**Key Functions:**

1. **`format_namelist()`**: Converts the member list from a flat list into a nested dictionary for fast lookups (so you can quickly find a username by user ID)

2. **`get_chat_member_list()`**: Fetches all members currently in the Telegram group (not currently used in main flow, but available for full member syncs)

3. **`get_new_member_info()`**: When someone joins the group, this extracts their info:
   - User ID, username, first name, last name
   - Join date
   - Flags like `is_mgmt` (is management), `is_kin`, `left_the_group` (defaulting to False)

4. **`get_message_info()`**: Extracts structured data from a chat message:
   - Message ID, sender username/ID, timestamp
   - Text content (including captions from media)
   - Whether it's a reply (and to which message)
   - Poll questions (if it's a poll)
   - Media type (photo, video, document, etc.)
   - System actions (if it's a system message)

5. **`get_reaction_info()`**: Converts Telegram reaction objects into clean dictionaries:
   - Unique reaction ID (message ID + counter)
   - Message ID, timestamp, emoji, user ID

6. **`handle_other_system_messages()`**: Placeholder for handling edge-case system messages (pinned messages, topic creation, etc.)

---

## Data Flow Diagram

```
┌─────────────────────────┐
│   Telegram Group        │
│   (Source of Data)      │
└──────────┬──────────────┘
           │
           │ Pyrogram Library
           │ (Fetches messages)
           ▼
┌─────────────────────────┐
│   main.py               │
│   - Gets new messages   │
│   - Orchestrates flow   │
└──────────┬──────────────┘
           │
           ├─────────────────────────┐
           │                         │
           ▼                         ▼
┌──────────────────────┐   ┌─────────────────────┐
│ process_messages.py  │   │ get_message_        │
│ - Classifies msgs    │   │   reactions.py      │
│ - Extracts data      │   │ - Fetches reactions │
└──────────┬───────────┘   └─────────┬───────────┘
           │                         │
           │    (uses utils.py)      │
           │                         │
           └─────────┬───────────────┘
                     │
                     ▼
           ┌─────────────────────┐
           │   Supabase Database │
           │   - chat_messages   │
           │   - member_list     │
           │   - chat_reactions  │
           └─────────────────────┘
```

---

## Database Schema (What Gets Saved)

### `chat_messages` Table
- `msg_id`: Unique message ID from Telegram
- `from`: Username of the sender
- `from_id`: User ID of the sender
- `datetime`: When the message was sent
- `text`: Message content
- `reply_to_message_id`: If it's a reply, which message it replies to
- `poll_question`: If it's a poll, the question text
- `poll_total_voters`: Number of people who voted
- `media_type`: Type of media (photo, video, document, etc.)
- `system_action`: Description of system actions (e.g., "pinned message")

### `member_list` Table
- `user_id`: Unique Telegram user ID (prefixed with "user")
- `username`: Telegram username
- `first_name`, `last_name`, `full_name`: User's name
- `join_date`: When they joined the group
- `is_mgmt`: Whether they're management (manually set)
- `is_kin`: Custom flag (manually set)
- `left_the_group`: Whether they've left

### `chat_reactions` Table
- `reaction_id`: Unique ID (message ID + counter)
- `msg_id`: Which message was reacted to
- `datetime`: When the reaction was added
- `reaction`: The emoji used
- `user_id`: Who reacted
- `username`: Username of reactor
- `full_name`: Full name of reactor

---

## How to Run This Program

1. **Set up credentials** in a `.env` file:
   - Telegram API ID and hash
   - Telegram session string (for login)
   - Telegram group ID
   - Supabase URL and key

2. **Run the main script**:
   ```
   python main.py
   ```

3. The program runs once and then stops. To run it continuously, you'd set up a scheduled task (cron job on Linux, Task Scheduler on Windows) to run it every hour/day.

---

## Limitations & Design Choices

- **2,000 Message Limit**: Each run fetches up to 2,000 messages. If the group is very active and you run it infrequently, you might miss messages.
- **30 Reaction Limit**: Only the first 30 reactions per message are captured.
- **No Real-Time**: This isn't a live monitor - it's a periodic batch job that catches up on new activity.
- **Incremental Updates**: It doesn't re-process old messages. Once saved to the database, messages are never updated (even if edited in Telegram).

---

## Use Cases

This data collection enables analytics like:
- **Engagement metrics**: Who's most active? What times are busiest?
- **Member growth**: Track when members join and if they leave
- **Content analysis**: What topics get the most reactions?
- **Response patterns**: Who replies to whom? Are there conversation clusters?
- **Polls & voting**: Track poll participation rates

---

## Security Notes

- All credentials are stored in a `.env` file (never committed to version control)
- The Telegram session string is essentially a login token - keep it secret
- Supabase keys have database access - protect them carefully
- This program requires permission to access the Telegram group's full history
