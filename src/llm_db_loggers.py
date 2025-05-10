import os
from sqlalchemy import create_engine, inspect, update, select
from src.db_models import db_init, metadata as db_metadata
from src.logger import *


class DatabaseStorage:
    def __init__(self):

        db_user = os.getenv('DB_USER')
        db_host = os.getenv('DB_HOST')
        db_pass = os.getenv('DB_PASS')
        db = os.getenv('DATABASE')

        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}/{db}"

        self.engine = create_engine(db_url)
        self.metadata = db_metadata
        self.db_schema = self.metadata.schema

        self.conversations_table = self.metadata.tables[f"{self.db_schema}.conversations"]
        self.messages_table = self.metadata.tables[f"{self.db_schema}.messages"]

        self._validate_schema()

        return None


    def _validate_schema(self):

        inspector = inspect(self.engine)

        required_tables = [t for t in self.metadata.tables]
        existing_tables = [t for t in inspector.get_table_names(schema=self.db_schema)]

        if len(existing_tables) < len(required_tables): 
            db_init(self.engine, self.db_schema, self.metadata, existing_tables, required_tables)


    def insert_single_message(self,conversation_id: int , role: str, message: str, token_count: int):
        """
        Inserts a single message record into the database.

        Args:
            title: The title of the conversation.
            title_embedding: The vector embedding for the title (optional).
        """
        # Create an insert statement
        insert_stmt = self.messages_table.insert().values(
            conversation_id=conversation_id,
            role=role,
            message=message,
            total_token_count=token_count,
        )

        # Execute the insert statement
        with self.engine.connect() as connection:
            result = connection.execute(insert_stmt)
            connection.commit()

        return None


    def insert_single_conversation(self, conversation_id: int, message_count: int = 0, title: str = "", title_embedding: list[float] = None):
        """
        Inserts a single conversation record into the database.

        Args:
            title: The title of the conversation.
            title_embedding: The vector embedding for the title (optional).
        """
        # Create an insert statement

        insert_stmt = self.conversations_table.insert().values(
            message_count=message_count,
            title=title,
            title_embedding=title_embedding,
        )

        select_stmt = select(self.conversations_table).where(self.conversations_table.c.id==conversation_id)

        logger(select, "debug.log")
        # Execute the insert statement
        with self.engine.connect() as connection:
            recalled_conversation = connection.execute(select_stmt)

            logger(recalled_conversation,"debug.log")

            result = connection.execute(insert_stmt)
            connection.commit()

    def update_message_count(self, conversation_id: int):
        update_stmt = update(self.conversations_table).where(self.conversations_table.c.id == conversation_id).values(message_count = self.conversations_table.c.message_count + 1)
        

        # Execute the insert statement
        with self.engine.connect() as connection:
            result = connection.execute(update_stmt)
            connection.commit()