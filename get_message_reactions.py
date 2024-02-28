from utils import get_reaction_info
from pyrogram import errors
from pyrogram.raw.functions.messages import GetMessageReactionsList

def get_message_reactions(app, tpl_group_id, messages, namelist):
    """
    Get reactions for each message in the given list of messages.

    Args:
    app: The running telegram client, which is a Pyrogram application instance.
    input_peer: The input peer for the messages.
    messages: A list of Message objects.
    namelist: A dictionary mapping user IDs to usernames.

    Returns:
    list: A list of dictionaries, each containing information about the reactions to a message.
    """
    input_peer = app.resolve_peer(peer_id=tpl_group_id)
    reactions = []
    for message in messages:
            # get reaction objects from each
            try:
                message_reactions_list = app.invoke(
                    GetMessageReactionsList(
                        peer=input_peer,
                        id=message.id,
                        limit=30  
                    )
                )
        # extract reaction info for each message
                reactions_info = get_reaction_info(message_reactions_list, message)
                for reactor in reactions_info:
                    if reactor['user_id'] is not None:
                        try:
                            reactor['username'] = namelist[namelist['user_id'] == reactor['user_id']]['username'].item()
                            # reactor['username'] = namelist[reactor['user_id']]['username']
                            # reactor['full_name'] = namelist[reactor['user_id']]['full_name']
                        except KeyError:
                            # Handle members with no usernames aka KeyError
                            raise KeyError(f"User ID {reactor['user_id']} not found in namelist")
                reactions += reactions_info

            except errors.exceptions.bad_request_400.MsgIdInvalid as e:
                # Handle the MsgIdInvalid error when there are no reactions to the message
                print(e)

                continue

            except AttributeError as e:
                # Handle the AttributeError here
                print(e)

                continue       
            
    return reactions
