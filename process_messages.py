from utils import get_new_member_info, get_message_info, handle_other_system_messages

def process_messages(new_messages):

    """
    Processes all new telegram messages, classifies them into either chat messages or new members joining (system service messages)

    Args:
    new_messages (list): A list of Message objects

    Returns:
    tuple: A tuple containing a list of new_chat_messages and a list of new_chat_members
    """

    # classify all messages into either chat messages, or new members joining (system service messages)
    chat_messages = []
    new_members = []

    for message in new_messages:
        
        # If message indicates new member joining, add it to new_members list and move on
        if message.new_chat_members:
            for new_member in message.new_chat_members:
                member_info = get_new_member_info(message, new_member)
                new_members.append(member_info)
            continue 

        # extract all relevant fields for chat messages
        message_info = get_message_info(message)
                    
        # filter out edge cases (pinned msgs, group title, creating topics etc.)
        if message_info['text'] == "" and all(value is None for value in (message_info['poll_question'], message_info['media_type'])):
            # print(f"other system message: message ID {message.id}")
            message_info['system_action'] = handle_other_system_messages(message)

        chat_messages.append(message_info)

    return chat_messages, new_members