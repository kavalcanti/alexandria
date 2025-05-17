from dotenv import load_dotenv
import argparse
from prompt_toolkit.patch_stdout import patch_stdout
import src.logger as logger
from src.userland import application

load_dotenv()

logger.configure_logger()



def parse_args():
    parser = argparse.ArgumentParser(description='Alexandria - Your AI Assistant')
    parser.add_argument('--conversation', '-c', type=int, 
                       help='Conversation ID to continue. If not provided, starts a new conversation.')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    with patch_stdout():
        application.run(conversation_id=args.conversation)

