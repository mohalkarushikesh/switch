import faiss
import numpy as np

dimension = 128  # Dimension of the vectors

index = faiss.IndexFlatL2(dimension)  # Create a flat (brute-force) index

vectors = np.random.random((1000, dimension)).astype('float32')  # Generate random vectors

index.add(vectors)  # Add vectors to the index

# Perform a search for the nearest neighbors of a query vector
query_vector = np.random.random((1, dimension)).astype('float32')  # Generate

distance = np.random.random((1, dimension)).astype('float32')  # Generate a random query vector

# return the distances and indices of the nearest neighbors
distances, indices = index.search(query_vector, k=5)  # Search for 5 nearest neighbors

print("Query Vector:", query_vector)
print("Distances:", distances)  
print("Indices:", indices)


# recall@k calculation
def recall_at_k(true_indices, predicted_indices, k):
    """
    Calculate recall@k for a single query.

    Parameters:
    - true_indices: The ground truth indices of the nearest neighbors.
    - predicted_indices: The predicted indices of the nearest neighbors.
    - k: The number of nearest neighbors to consider.

    Returns:
    - recall: The recall@k value.
    """
    true_set = set(true_indices[:k])
    predicted_set = set(predicted_indices[:k])
    
    intersection = true_set.intersection(predicted_set)
    
    recall = len(intersection) / min(k, len(true_set)) if true_set else 0.0
    return recall

# Example usage of recall_at_k
true_indices = [1, 2, 3, 4, 5]
predicted_indices = indices[0]  # Get the predicted indices from the search result
k = 5
recall = recall_at_k(true_indices, predicted_indices, k)
print(f"Recall@{k}: {recall}")



