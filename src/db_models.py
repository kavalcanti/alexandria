import uuid
import datetime
import os
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Sequence,
    inspect,
    text
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, VARCHAR
from pgvector.sqlalchemy import Vector

db_user = os.getenv('DB_USER')
db_host = os.getenv('DB_HOST')
db_pass = os.getenv('DB_PASS')
db = os.getenv('DATABASE')

db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}/{db}"

engine = create_engine(db_url)

db_schema = 'exp'

# Metadata with schema
metadata = MetaData(schema=db_schema)

# Conversations definition. Holds groups of messages.
conversations_table = Table(
    "conversations",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('conversations_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
    ),
    Column("title", VARCHAR(256), nullable=False),
    Column(
        "created_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
    ),
    Column(
        "updated_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    Column("message_count", Integer, nullable=False, default=0),
    Column("title_embedding", Vector(384), nullable=True),
)

# Define the 'messages' table
messages_table = Table(
    "messages",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('conversations_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
    ),
    Column(
        "conversation_id",
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
    ),
    Column(
        "timestamp",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
    ),
    Column("role", VARCHAR(24), nullable=False), # e.g., 'system', 'user', 'assistant'
    Column("message", Text, nullable=False),
    Column("total_token_count", Integer, nullable=False, default=0),
)


target_tables = [conversations_table, messages_table]

def db_init(engine, db_schema, metadata, target_tables):
    """Checks if tables exist and creates them if they don't.
       Currently performs DESTRUCTIVE operation to sync schema changes while in development.
       Backup your data!
    """
    try:
        inspector = inspect(engine)

        existing_tables = inspector.get_table_names(schema=db_schema)
        print(target_tables)
        print(existing_tables)

        table_checker = []
        for t in target_tables:
            table_checker.append(t in existing_tables)
        print(table_checker)
        if False in table_checker:

        # if not conversations_exist or not messages_exist:
            print(f"Schema '{db_schema}' does not match expected tables.")
            print("DESTRUCTIVELY RECONSTRUCTING.")
            try:
                with engine.connect() as connection:
                    # Create the schema if it doesn't exist
                    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {db_schema}"))
                    # Install the vector extension if not already done
                    # Note: This requires superuser privileges or appropriate database permissions
                    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

                # Create tables within the schema
                metadata.drop_all(engine)
                metadata.create_all(engine)
                # print(f"Schema '{DB_SCHEMA}' and tables created successfully.")
            except Exception as e:
                print(f"An error occurred during schema and table creation: {e}")
                print("Please ensure the database is running, the user has necessary permissions, and the 'vector' extension is installed.")
                # sys.exit(1) # Exit if table creation fails
        else:
            print(f"Schema '{db_schema}' and tables already exist.")

    except Exception as e:
        print(f"An error occurred while trying to connect to the database or inspect tables: {e}")
        print("Please check your database connection string and ensure the database server is accessible.")
        # sys.exit(1) # Exit if inspection fails