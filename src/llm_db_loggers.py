from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from src.db_models import db_init, metadata as db_metadata



class DatabaseStorage:
    def __init__(self):

        db_user = os.getenv('DB_USER')
        db_host = os.getenv('DB_HOST')
        db_pass = os.getenv('DB_PASS')
        db = os.getenv('DATABASE')

        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}/{db}"

        self.engine = create_engine(db_url)
        self.metadata = db_metadata

        try:
            db_schema = self.metadata.schema
            self.conversations_table = self.metadata.tables[f"{db_schema}.conversations"]
            self.messages_table = self.metadata.tables[f"{db_schema}.messages"]
        except KeyError as e:
            print(f"Error: Table {e} not found in imported metadata. Ensure tables are defined in src.db_models with schema='{db_schema}'.")
            raise
        # self.messages_table = messages_table
        # self.conversations_table = conversations_table

        db_init(self.engine, db_schema, self.metadata, [self.messages_table, self.conversations_table])
        return None


class ChatsStorage(DatabaseStorage):
    def __init__(self):
        ### NO RECURSIVE DEPENDENCIES
        ### need to implement titling without calling model_calls
        # Chat CRUD to db

        return None

    def insert_single_conversation(self, title, title_embedding: list[float] = None):
        """
        Inserts a single conversation record into the database.

        Args:
            title: The title of the conversation.
            title_embedding: The vector embedding for the title (optional).
        """
        # Create an insert statement

        insert_stmt = conversations_table.insert().values(
            title=title,
            # uuid, created_at, updated_at, and message_count have defaults and don't need to be explicitly provided
            # unless you want to override the default.
            title_embedding=title_embedding
        )

        # Execute the insert statement
        with self.engine.connect() as connection:
            result = connection.execute(insert_stmt)
            connection.commit()

class MessagesStorage(DatabaseStorage):
    def __init__(self):
        ### Message CRUD to db
        return None

    def insert_single_message(self, title, title_embedding: list[float] = None):
        """
        Inserts a single conversation record into the database.

        Args:
            title: The title of the conversation.
            title_embedding: The vector embedding for the title (optional).
        """
        # Create an insert statement
        insert_stmt = messages_table.insert().values(
            role=role,
            message=message,
            token_count=token_count,
        )

        # Execute the insert statement
        with self.engine.connect() as connection:
            result = connection.execute(insert_stmt)
            connection.commit()