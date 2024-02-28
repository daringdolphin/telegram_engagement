from pyrogram import Client as telegram_client
from pyrogram.types import Message, User
import datetime as dt

def format_namelist(namelist: list) -> dict:
    """
    Format the namelist into a nested dictionary.

    Args:
    namelist (list): A list of dictionaries, each containing information about a member.

    Returns:
    dict: A nested dictionary, where the keys are user IDs and the values are dictionaries containing member information.
    """
    nested_dict = {}
    for member in namelist:
        user_id = member['user_id']
        user_info = {}
        for key, value in member.items():
            if key != 'user_id':
                user_info[key] = value
        nested_dict[user_id] = user_info
    return(nested_dict)


def get_chat_member_list(app: telegram_client, groupchat_id: int) -> tuple:
    """
    Get the list of members in a chat.

    Args:
    app (PyrogramClient): The Pyrogram client.
    groupchat_id (int): The ID of the chat.

    Returns:
    tuple: A tuple containing a dictionary that maps user IDs to usernames and a list of member info dictionaries.
    """
    members_info = []
    username_map = {}
    for member in app.get_chat_members(groupchat_id):
        member_info = {
                    'user_id': "user" + str(member.user.id),
                    'username': member.user.username,
                    'first_name': member.user.first_name if member.user.first_name else None,
                    'last_name': member.user.last_name if member.user.last_name else None,
        }
        members_info.append(member_info)
        username_map[member_info['user_id']] = member_info['username']
    return (username_map, members_info)

def get_new_member_info(message: Message, user: User) -> dict:
    """
    Get information about a new member.

    Args:
    message (Message): The message that describes the new member event.
    user (User): The new member.

    Returns:
    dict: A dictionary containing information about the new member.
    """
    return {
        'user_id': "user" + str(user.id),
        'username': user.username,
        'first_name': user.first_name if user.first_name else None,
        'last_name': user.last_name if user.last_name else None,
        'full_name': user.first_name if user.first_name else None + " " + user.last_name if user.last_name else None,
        'join_date': message.date.isoformat(),
        'is_mgmt': False,
        'is_kin': False,
        'left_the_group': False
    }

def get_message_info(message: Message) -> dict:
    """
    Get information about a chat message.

    Args:
    message (Message): The message to get info about.

    Returns:
    dict: A dictionary containing information about the message.
    """
    message_info = {
        'msg_id': message.id,
        'from': message.from_user.username if message.from_user else None,
        'from_id': "user" + str(message.from_user.id) if message.from_user else None,
        'datetime': message.date.isoformat(),
        'text': (message.text if message.text else "") + (message.caption if message.caption else ""),
        'reply_to_message_id': message.reply_to_message_id,
        'poll_question': message.poll.question if message.poll else None,
        'poll_total_voters': message.poll.total_voter_count  if message.poll else None,
        'media_type': message.media.value if message.media else None,
        'system_action': None,
    }
    if message_info['text'] == "" and all(value is None for value in (message_info['poll_question'], message_info['media_type'])):
        message_info['system_action'] = handle_other_system_messages(message)
    return message_info

def handle_other_system_messages(message):
    # todo
    return "other system actions performed"

def get_reaction_info(message_reactions_list: list, message: Message) -> list:
    """
    Get information about reactions to a message.

    Args:
    message_reactions_list (MessageReactionsList): The list of reactions to the message.
    message (Message): The message.

    Returns:
    list: A list of reaction dictionaries. Each dict contains information about the reaction.
    """
    list_of_reactions = []
    counter = len(message_reactions_list.reactions)
    for reaction in message_reactions_list.reactions:
        reaction_info = {
             "reaction_id": f"{str(message.id)}-{str(counter)}",
             "msg_id": message.id,
             "datetime": reaction.date,
             "reaction": reaction.reaction.emoticon,
             "user_id": ("user" + str(reaction.peer_id.user_id)) if reaction.peer_id.user_id else None
        }
        reaction_date = dt.datetime.fromtimestamp(reaction_info['datetime']).isoformat()
        reaction_info["datetime"] = reaction_date
        list_of_reactions.append(reaction_info)
        counter -= 1
    return list_of_reactions