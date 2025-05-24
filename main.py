from dotenv import load_dotenv
import argparse
from prompt_toolkit.patch_stdout import patch_stdout
import src.logger as logger
from src.userland import application
from src.core.managers.rag_manager import RAGConfig

load_dotenv()

logger.configure_logger()



def parse_args():
    parser = argparse.ArgumentParser(description='Alexandria - Your AI Assistant with RAG')
    parser.add_argument('--conversation', '-c', type=int, 
                       help='Conversation ID to continue. If not provided, starts a new conversation.')
    
    # RAG configuration options
    rag_group = parser.add_argument_group('RAG Options', 'Configure retrieval-augmented generation')
    rag_group.add_argument('--disable-rag', action='store_true',
                          help='Disable retrieval-augmented generation')
    rag_group.add_argument('--max-results', type=int, default=5,
                          help='Maximum number of retrieval results (default: 5)')
    rag_group.add_argument('--min-similarity', type=float, default=0.3,
                          help='Minimum similarity score for results (default: 0.3)')
    rag_group.add_argument('--no-enhancement', action='store_true',
                          help='Disable query enhancement')
    rag_group.add_argument('--no-metadata', action='store_true',
                          help='Exclude source metadata from responses')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Configure RAG based on command line arguments
    if not args.disable_rag:
        rag_config = RAGConfig(
            enable_retrieval=True,
            max_retrieval_results=args.max_results,
            min_similarity_score=args.min_similarity,
            retrieval_query_enhancement=not args.no_enhancement,
            include_source_metadata=not args.no_metadata
        )
        application.configure_rag(enable_rag=True, rag_config=rag_config)
    else:
        application.configure_rag(enable_rag=False)
    
    with patch_stdout():
        application.run(conversation_id=args.conversation)

