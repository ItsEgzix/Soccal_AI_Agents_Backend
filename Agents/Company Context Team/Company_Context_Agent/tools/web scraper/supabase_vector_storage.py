"""
Supabase pgvector Storage for Website Scraped Content
Stores scraped website content in Supabase PostgreSQL with pgvector embeddings.
"""

import psycopg2
from psycopg2.extras import execute_values, Json
from typing import List, Dict, Optional
import uuid
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Load .env file (searches from current directory up to root)
env_path = find_dotenv()
if env_path:
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback: try AI_Backend directory explicitly
    env_path = Path(__file__).parent.parent.parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


class SupabaseVectorStorage:
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Supabase pgvector storage.
        
        Args:
            connection_string: PostgreSQL connection string (defaults to DATABASE_URL env var or individual parameters)
        """
        # Support both connection string and individual parameters
        if connection_string:
            self.connection_string = connection_string
        elif os.getenv("DATABASE_URL"):
            self.connection_string = os.getenv("DATABASE_URL")
        elif os.getenv("DB_HOST") and os.getenv("DB_USER") and os.getenv("DB_PASSWORD"):
            # Build connection string from individual parameters
            db_user = os.getenv("DB_USER") or os.getenv("user")
            db_password = os.getenv("DB_PASSWORD") or os.getenv("password")
            db_host = os.getenv("DB_HOST") or os.getenv("host")
            db_port = os.getenv("DB_PORT") or os.getenv("port") or "5432"
            db_name = os.getenv("DB_NAME") or os.getenv("dbname") or "postgres"
            self.connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            raise ValueError("Database connection not configured. Set either DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME in .env")
        
        # Initialize embedding model (all-MiniLM-L6-v2, 384 dimensions)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded!")
        
        # Test connection
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.close()
            print("Connected to Supabase PostgreSQL")
        except Exception as e:
            raise Exception(f"Could not connect to Supabase: {str(e)}")
    
    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def _chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - chunk_overlap
        
        return chunks
    
    def company_exists(self, company_id: str) -> bool:
        """
        Check if company data already exists.
        
        Args:
            company_id: Company identifier
        
        Returns:
            True if company exists, False otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM companies_vector_data WHERE company_id = %s",
                (company_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            conn.close()
    
    def find_company_by_url(self, base_url: str) -> Optional[str]:
        """
        Find company_id by URL.
        
        Args:
            base_url: Website URL to search for
        
        Returns:
            Company ID if found, None otherwise
        """
        # Normalize URL (remove trailing slash, convert to lowercase)
        normalized_url = base_url.rstrip('/').lower()
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Try exact match first
            cursor.execute(
                "SELECT DISTINCT company_id FROM companies_vector_data WHERE LOWER(base_url) = %s LIMIT 1",
                (normalized_url,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Try variations (with/without protocol, with/without trailing slash)
            url_variations = [
                normalized_url,
                normalized_url.replace('https://', '').replace('http://', ''),
                normalized_url + '/',
                'https://' + normalized_url.lstrip('https://').lstrip('http://'),
                'http://' + normalized_url.lstrip('https://').lstrip('http://')
            ]
            
            for url_variant in url_variations:
                if url_variant == normalized_url:
                    continue  # Already checked
                
                cursor.execute(
                    "SELECT DISTINCT company_id FROM companies_vector_data WHERE LOWER(base_url) = %s LIMIT 1",
                    (url_variant.lower(),)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
            
            return None
        finally:
            conn.close()
    
    def store_company_content(self, company_id: str, base_url: str, scraped_data: Dict, replace_existing: bool = False) -> int:
        """
        Store company website content in Supabase.
        
        Args:
            company_id: Unique identifier for the company
            base_url: Base URL of the company website
            scraped_data: Dictionary with scraped data (home, about, services)
            replace_existing: If True, delete existing data before storing (default: False - reuses existing data)
        
        Returns:
            Number of chunks stored
        """
        # Check if company already exists
        if self.company_exists(company_id):
            if replace_existing:
                print(f"Company {company_id} already exists. Deleting existing data...")
                self.delete_company(company_id)
            else:
                print(f"Company {company_id} already exists. Skipping storage.")
                return 0
        
        all_chunks = []
        all_metadatas = []
        
        # Process each page type
        for page_type in ['home', 'about', 'services']:
            page_data = scraped_data.get(page_type)
            if not page_data or not page_data.get('content'):
                continue
            
            content = page_data.get('content', '')
            url = page_data.get('url', base_url)
            meta = page_data.get('meta', {})
            
            # Chunk the content
            chunks = self._chunk_text(content, chunk_size=500, chunk_overlap=50)
            
            # Create metadata for each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    'company_id': company_id,
                    'base_url': base_url,
                    'page_type': page_type,
                    'url': url,
                    'title': meta.get('title', ''),
                    'description': meta.get('description', ''),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
        
        if not all_chunks:
            print("No content to store in Supabase")
            return 0
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self._generate_embeddings(all_chunks)
        
        # Store in database
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Prepare data for batch insert
            insert_data = []
            for i, (chunk, embedding, metadata) in enumerate(zip(all_chunks, embeddings, all_metadatas)):
                # Convert embedding list to string format for pgvector
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                insert_data.append((
                    str(uuid.uuid4()),  # id
                    company_id,
                    base_url,
                    metadata['page_type'],
                    metadata['chunk_index'],
                    chunk,  # content
                    embedding_str,  # embedding (as text, will be cast to vector)
                    Json(metadata)  # metadata as JSONB
                ))
            
            # Batch insert
            execute_values(
                cursor,
                """
                INSERT INTO companies_vector_data 
                (id, company_id, base_url, page_type, chunk_index, content, embedding, metadata)
                VALUES %s
                """,
                insert_data,
                template="""
                (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                """,
                page_size=100
            )
            
            conn.commit()
            print(f"Stored {len(all_chunks)} chunks in Supabase for company: {company_id}")
            return len(all_chunks)
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error storing content: {str(e)}")
        finally:
            conn.close()
    
    def query(self, query_text: str, company_id: Optional[str] = None, n_results: int = 5) -> List[Dict]:
        """
        Query the vector database using cosine similarity.
        
        Args:
            query_text: Query text to search for
            company_id: Optional company ID to filter results
            n_results: Number of results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embeddings([query_text])[0]
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            if company_id:
                # Query with company filter
                cursor.execute(
                    """
                    SELECT 
                        id,
                        content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM companies_vector_data
                    WHERE company_id = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding_str, company_id, embedding_str, n_results)
                )
            else:
                # Query without company filter
                cursor.execute(
                    """
                    SELECT 
                        id,
                        content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM companies_vector_data
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding_str, embedding_str, n_results)
                )
            
            results = cursor.fetchall()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row[0],
                    'text': row[1],
                    'metadata': row[2] if isinstance(row[2], dict) else row[2],
                    'distance': 1 - row[3] if row[3] is not None else None  # Convert similarity to distance
                })
            
            return formatted_results
        finally:
            conn.close()
    
    def get_company_content(self, company_id: str) -> List[Dict]:
        """
        Get all content for a specific company.
        
        Args:
            company_id: Company identifier
        
        Returns:
            List of all chunks for the company
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, metadata
                FROM companies_vector_data
                WHERE company_id = %s
                ORDER BY page_type, chunk_index
                """,
                (company_id,)
            )
            
            results = cursor.fetchall()
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row[0],
                    'text': row[1],
                    'metadata': row[2] if isinstance(row[2], dict) else row[2]
                })
            
            return formatted_results
        finally:
            conn.close()
    
    def delete_company(self, company_id: str) -> bool:
        """
        Delete all content for a specific company.
        
        Args:
            company_id: Company identifier
        
        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM companies_vector_data WHERE company_id = %s",
                (company_id,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"Deleted {deleted_count} chunks for company: {company_id}")
                return True
            else:
                print(f"No content found for company: {company_id}")
                return False
        except Exception as e:
            conn.rollback()
            print(f"Error deleting company: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_collection_info(self) -> Dict:
        """Get information about the storage."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM companies_vector_data")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT company_id) FROM companies_vector_data")
            company_count = cursor.fetchone()[0]
            
            return {
                'total_chunks': count,
                'total_companies': company_count,
                'storage_type': 'Supabase pgvector'
            }
        finally:
            conn.close()

