"""Flask service implementing FAISS similarity search with request queue."""
import time
from queue import Queue
from threading import Lock, Thread

import numpy as np
from flask import Flask, jsonify, request

from query_service.db import get_user_id_from_api_key
from query_service.embedding_client import EmbeddingClient
from query_service.faiss_index import FaissIndex

app = Flask(__name__)

# Global variables
request_queue = Queue()
processing_lock = Lock()
embedding_client = EmbeddingClient()


def process_queue():
    """Process requests from the queue."""
    while True:
        if not request_queue.empty():
            with processing_lock:
                query_data, response_queue = request_queue.get()
                try:
                    query_vector = np.array(
                        embedding_client.get_embeddings([query_data["query"]])[0],
                        dtype=np.float32,
                    ).reshape(1, -1)

                    faiss_index = FaissIndex(query_data["userId"])

                    results = faiss_index.search(query_vector, query_data.get("k", 30))

                    response_queue.put({"status": "success", "results": results})
                except Exception as e:
                    response_queue.put({"status": "error", "message": str(e)})

                request_queue.task_done()

        time.sleep(0.01)  # Small delay to prevent CPU spinning


@app.before_first_request
def startup():
    """Initialize the service."""
    # Start queue processing thread
    worker_thread = Thread(target=process_queue, daemon=True)
    worker_thread.start()


@app.route("/search", methods=["POST"])
def search():
    """Handle search requests."""
    # Check for API key in headers
    api_key = request.headers.get("Authorization")
    if not api_key:
        return jsonify({"error": "Authorization header is required"}), 401

    # Authenticate API key
    user_id = get_user_id_from_api_key(api_key)
    if not user_id:
        return jsonify({"error": "Invalid API key"}), 401

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "query is required"}), 400

    # Add authenticated user ID to the request data
    data["userId"] = user_id

    # Create response queue for this request
    response_queue = Queue()

    # Add request to queue
    request_queue.put((data, response_queue))

    # Wait for response
    response = response_queue.get()

    if response["status"] == "error":
        return jsonify({"error": response["message"]}), 500

    return jsonify(response["results"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
