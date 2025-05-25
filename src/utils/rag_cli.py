"""
Command-line interface for RAG (Retrieval-Augmented Generation) testing and interaction.

This tool provides a convenient way to test and interact with the integrated
RAG capabilities, allowing users to ask questions and see how the system
retrieves and uses document context.
"""

import argparse
import sys
import json
from typing import Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

from src.logger import get_module_logger
from src.core.services.conversation_service import create_rag_conversation_service
from src.core.managers.rag_manager import RAGConfig

load_dotenv()

logger = get_module_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Alexandria RAG Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ask a question using RAG
  python -m src.utils.rag_cli ask "What is machine learning?"
  
  # Interactive RAG session
  python -m src.utils.rag_cli interactive
  
  # Search documents without generation
  python -m src.utils.rag_cli search "neural networks"
  
  # Test with custom RAG configuration
  python -m src.utils.rag_cli ask "Tell me about AI" --max-results 10 --min-similarity 0.5
  
  # Get RAG system statistics
  python -m src.utils.rag_cli stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ask command for single questions
    ask_parser = subparsers.add_parser('ask', help='Ask a single question using RAG')
    ask_parser.add_argument('question', type=str, help='Question to ask')
    add_rag_args(ask_parser)
    add_output_args(ask_parser)
    
    # Interactive command for conversation mode
    interactive_parser = subparsers.add_parser('interactive', help='Start interactive RAG session')
    add_rag_args(interactive_parser)
    
    # Search command for document search only
    search_parser = subparsers.add_parser('search', help='Search documents without generation')
    search_parser.add_argument('query', type=str, help='Search query')
    add_rag_args(search_parser)
    add_output_args(search_parser)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show RAG system statistics')
    add_output_args(stats_parser)
    
    return parser


def add_rag_args(parser: argparse.ArgumentParser) -> None:
    """Add RAG configuration arguments to a parser."""
    parser.add_argument('--max-results', type=int, default=5,
                       help='Maximum number of retrieval results (default: 5)')
    parser.add_argument('--min-similarity', type=float, default=0.3,
                       help='Minimum similarity score for results (default: 0.3)')
    parser.add_argument('--no-enhancement', action='store_true',
                       help='Disable query enhancement')
    parser.add_argument('--no-metadata', action='store_true', 
                       help='Exclude source metadata from responses')
    parser.add_argument('--disable-rag', action='store_true',
                       help='Disable retrieval for this session')


def add_output_args(parser: argparse.ArgumentParser) -> None:
    """Add output formatting arguments to a parser."""
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--show-thinking', action='store_true',
                       help='Show model thinking process')
    parser.add_argument('--show-retrieval', action='store_true',
                       help='Show retrieval details')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress non-essential output')


def create_rag_config(args) -> RAGConfig:
    """Create RAG configuration from command line arguments."""
    return RAGConfig(
        enable_retrieval=not getattr(args, 'disable_rag', False),
        max_retrieval_results=getattr(args, 'max_results', 5),
        min_similarity_score=getattr(args, 'min_similarity', 0.3),
        retrieval_query_enhancement=not getattr(args, 'no_enhancement', False),
        include_source_metadata=not getattr(args, 'no_metadata', False)
    )


def handle_ask(args) -> int:
    """Handle the ask command."""
    try:
        config = create_rag_config(args)
        service = create_rag_conversation_service(rag_config=config)
        
        if not args.quiet:
            print(f"Asking: {args.question}")
            if config.enable_retrieval:
                print("Using retrieval-augmented generation...")
            else:
                print("Using standard generation (RAG disabled)...")
            print()
        
        if config.enable_retrieval and service.is_rag_enabled:
            response, thinking, retrieval_info = service.generate_rag_response(args.question)
        else:
            service.manage_context_window('user', args.question)
            response_tuple = service.generate_chat_response()
            response = response_tuple[0] if isinstance(response_tuple, tuple) else response_tuple
            thinking = response_tuple[1] if isinstance(response_tuple, tuple) and len(response_tuple) > 1 else ""
            retrieval_info = None
        
        if args.format == 'json':
            result = {
                "question": args.question,
                "response": response,
                "thinking": thinking if args.show_thinking else None,
                "retrieval_info": retrieval_info if args.show_retrieval else None
            }
            print(json.dumps(result, indent=2))
        else:
            print("Response:")
            print("-" * 50)
            print(response)
            
            if args.show_thinking and thinking:
                print("\nThinking Process:")
                print("-" * 50)
                print(thinking)
            
            if args.show_retrieval and retrieval_info:
                print("\nRetrieval Information:")
                print("-" * 50)
                print(f"Query: {retrieval_info['query']}")
                print(f"Total matches: {retrieval_info['total_matches']}")
                print(f"Search time: {retrieval_info['search_time_ms']:.2f}ms")
                print("\nRetrieved documents:")
                for i, match in enumerate(retrieval_info['matches'], 1):
                    print(f"{i}. {match['filepath']} (score: {match['similarity_score']:.3f})")
                    print(f"   {match['content_preview']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in ask: {str(e)}")
        return 1


def handle_interactive(args) -> int:
    """Handle the interactive command."""
    try:
        config = create_rag_config(args)
        service = create_rag_conversation_service(rag_config=config)
        
        print("Alexandria RAG Interactive Session")
        print("=" * 40)
        if config.enable_retrieval:
            print("RAG enabled - responses will use document retrieval")
        else:
            print("RAG disabled - using standard generation")
        print("Type 'quit' to exit, 'help' for commands\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                elif user_input.lower() == 'stats':
                    stats = service.get_rag_stats()
                    if stats:
                        print("RAG Configuration:")
                        for key, value in stats['config'].items():
                            print(f"  {key}: {value}")
                    else:
                        print("RAG not enabled")
                    continue
                elif not user_input:
                    continue
                
                print("\nAssistant: ", end="", flush=True)
                
                if config.enable_retrieval and service.is_rag_enabled:
                    response, thinking, retrieval_info = service.generate_rag_response(user_input)
                    
                    print(response)
                    
                    if retrieval_info and retrieval_info['total_matches'] > 0:
                        print(f"\n[Used {retrieval_info['total_matches']} document(s) from knowledge base]")
                else:
                    service.manage_context_window('user', user_input)
                    response_tuple = service.generate_chat_response()
                    response = response_tuple[0] if isinstance(response_tuple, tuple) else response_tuple
                    print(response)
                
                print()
                
            except KeyboardInterrupt:
                print("\nSession interrupted.")
                break
            except EOFError:
                break
        
        print("Goodbye!")
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in interactive: {str(e)}")
        return 1


def handle_search(args) -> int:
    """Handle the search command."""
    try:
        config = create_rag_config(args)
        service = create_rag_conversation_service(rag_config=config)
        
        if not service.is_rag_enabled:
            print("Error: RAG not enabled, cannot search documents")
            return 1
        
        if not args.quiet:
            print(f"Searching for: {args.query}")
            print()
        
        result = service.search_documents(args.query, max_results=args.max_results)
        
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"Found {result['total_matches']} matches in {result['search_time_ms']:.2f}ms:")
            print()
            
            for i, match in enumerate(result['matches'], 1):
                print(f"{i}. [{match['filepath']}] Score: {match['similarity_score']:.3f}")
                content_preview = match['content'][:200] + "..." if len(match['content']) > 200 else match['content']
                print(f"   {content_preview}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search: {str(e)}")
        return 1


def handle_stats(args) -> int:
    """Handle the stats command."""
    try:
        service = create_rag_conversation_service()
        stats = service.get_rag_stats()
        
        if args.format == 'json':
            print(json.dumps(stats or {}, indent=2))
        else:
            if stats:
                print("RAG System Statistics:")
                print("=" * 25)
                print(f"Retrieval enabled: {stats['config']['enable_retrieval']}")
                print(f"Max results: {stats['config']['max_results']}")
                print(f"Min similarity: {stats['config']['min_similarity']}")
                print(f"Query enhancement: {stats['config']['query_enhancement']}")
                print(f"Include metadata: {stats['config']['include_metadata']}")
            else:
                print("RAG system not available")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in stats: {str(e)}")
        return 1


def print_help():
    """Print interactive session help."""
    print("""
Available commands:
  help    - Show this help message
  stats   - Show RAG configuration and statistics
  quit    - Exit the session (or Ctrl+C)

Ask any question and the system will:
1. Search for relevant documents in the knowledge base
2. Use the retrieved context to provide informed responses
3. Indicate when knowledge base information was used
    """)


def main() -> int:
    """Main entry point for the RAG CLI tool."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'ask':
        return handle_ask(args)
    elif args.command == 'interactive':
        return handle_interactive(args)
    elif args.command == 'search':
        return handle_search(args)
    elif args.command == 'stats':
        return handle_stats(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main()) 