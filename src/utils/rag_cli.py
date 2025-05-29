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
from src.core.services.conversation_service import create_conversation_service
from src.core.generation.rag import RAGToolsConfig

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


def create_rag_config(args) -> RAGToolsConfig:
    """Create RAG configuration from command line arguments."""
    return RAGToolsConfig(
        enable_retrieval=not getattr(args, 'disable_rag', False),
        max_retrieval_results=getattr(args, 'max_results', 5),
        min_similarity_score=getattr(args, 'min_similarity', 0.3),
        include_source_metadata=not getattr(args, 'no_metadata', False)
    )


def handle_ask(args) -> int:
    """Handle the ask command."""
    try:
        config = create_rag_config(args)
        service = create_conversation_service()
        
        if not args.quiet:
            print(f"Asking: {args.question}")
            if config.enable_retrieval and service.is_rag_enabled:
                print("Using retrieval-augmented generation...")
            else:
                print("Using standard generation (RAG disabled)...")
            print()
        
        # Add the user message to the conversation
        service.add_conversation_message('user', args.question)
        
        # Generate response with RAG enabled based on config
        rag_enabled = config.enable_retrieval and service.is_rag_enabled
        response, thinking, retrieval_result = service.generate_chat_response(rag_enabled=rag_enabled)
        
        # Add the response to the conversation
        service.add_conversation_message('assistant', response)
        
        if args.format == 'json':
            result = {
                "question": args.question,
                "response": response,
                "thinking": thinking if args.show_thinking else None,
                "retrieval_info": retrieval_result if args.show_retrieval else None
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
            
            if args.show_retrieval and retrieval_result:
                print("\nRetrieval Information:")
                print("-" * 50)
                print(f"Query: {retrieval_result.get('query', 'N/A')}")
                print(f"Total matches: {retrieval_result.get('total_matches', 0)}")
                print(f"Search time: {retrieval_result.get('search_time_ms', 0):.2f}ms")
                if 'matches' in retrieval_result:
                    print("\nRetrieved documents:")
                    for i, match in enumerate(retrieval_result['matches'], 1):
                        print(f"{i}. {match.get('filepath', 'Unknown')} (score: {match.get('similarity_score', 0):.3f})")
                        content_preview = match.get('content', '')[:100] + "..." if len(match.get('content', '')) > 100 else match.get('content', '')
                        print(f"   {content_preview}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in ask: {str(e)}")
        return 1


def handle_interactive(args) -> int:
    """Handle the interactive command."""
    try:
        config = create_rag_config(args)
        service = create_conversation_service()
        
        print("Alexandria RAG Interactive Session")
        print("=" * 40)
        if config.enable_retrieval and service.is_rag_enabled:
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
                        for key, value in stats.items():
                            print(f"  {key}: {value}")
                    else:
                        print("RAG not enabled")
                    continue
                elif not user_input:
                    continue
                
                # Add user message and generate response
                service.add_conversation_message('user', user_input)
                rag_enabled = config.enable_retrieval and service.is_rag_enabled
                response, thinking, retrieval_result = service.generate_chat_response(rag_enabled=rag_enabled)
                service.add_conversation_message('assistant', response)
                
                print(f"Assistant: {response}")
                
                if retrieval_result and config.enable_retrieval:
                    print(f"\n[Retrieved {retrieval_result.get('total_matches', 0)} documents]")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in interactive: {str(e)}")
        return 1


def handle_search(args) -> int:
    """Handle the search command."""
    try:
        config = create_rag_config(args)
        service = create_conversation_service()
        
        if not service.is_rag_enabled:
            print("Error: Document search requires RAG to be enabled")
            return 1
        
        print(f"Searching for: {args.query}")
        
        # Use the search_documents method directly
        result = service.search_documents(args.query, max_results=config.max_retrieval_results)
        
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"\nFound {result['total_matches']} matches in {result['search_time_ms']:.2f}ms")
            print()
            
            for i, match in enumerate(result['matches'], 1):
                print(f"{i}. [{match['filepath']}] Score: {match['similarity_score']:.3f}")
                content_preview = match['content'][:200] + "..." if len(match['content']) > 200 else match['content']
                print(f"   Content: {content_preview}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search: {str(e)}")
        return 1


def handle_stats(args) -> int:
    """Handle the stats command."""
    try:
        service = create_conversation_service()
        stats = service.get_rag_stats()
        
        if args.format == 'json':
            result = {
                "rag_enabled": service.is_rag_enabled,
                "stats": stats
            }
            print(json.dumps(result, indent=2))
        else:
            print("RAG System Status:")
            print("-" * 30)
            print(f"RAG Enabled: {service.is_rag_enabled}")
            
            if stats:
                print("Configuration:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                print("No additional statistics available")
        
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