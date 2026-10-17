Here you go. These ramp from core Python to ML-flavored. Solve them in order, paste your solutions back, and I'll review — correctness *and* whether it's idiomatic. Don't look anything up unless stuck; the point is recall.

**Core structures & comprehensions**

1. Given `text = "the cat sat on the mat the cat slept"`, return a dict of word → count. (Then do it again in one line.)

2. From `nums = [4, 7, 2, 7, 9, 2, 4, 1]`, return a list of the unique values, sorted descending.

3. Given `pairs = [("a", 1), ("b", 2), ("c", 3)]`, build a dict `{"a": 1, ...}` using a comprehension. Then invert it to `{1: "a", ...}`.

**Functions & unpacking**

4. Write `stats(*numbers)` that returns the min, max, and average as a tuple. Call it and unpack the result into three variables.

5. Write a function `chunk(lst, size)` that splits a list into sublists of length `size` (last one can be shorter). E.g. `chunk([1,2,3,4,5], 2)` → `[[1,2],[3,4],[5]]`. (This is literally text chunking for RAG.)

**Generators & iteration**

6. Write a generator `read_lines(n)` that yields strings `"line 0"`, `"line 1"`, ... up to `n`. Explain in one sentence why a generator is better than a list here for a huge file.

7. Given `a = ["q1", "q2", "q3"]` and `b = [0.9, 0.7, 0.4]`, print each as `"q1 -> 0.9"` using `zip`. Then get the same with the index number in front using `enumerate`.

**OOP**

8. Write a class `Document` with `__init__(self, text, metadata=None)` where `metadata` defaults to an empty dict (careful — there's a classic trap here). Add a `__repr__` that prints `Document(text='...', metadata=...)` with text truncated to 20 chars.

9. Add a method `word_count(self)` to that class returning the number of words in `text`.

**Practical / error handling / files**

10. Write `safe_divide(a, b)` that returns the result, or returns `None` and prints a message if dividing by zero — using try/except.

11. Given a JSON string `'{"model": "phi-1.5", "chunks": 42}'`, parse it, add a key `"status": "ok"`, and turn it back into a JSON string.

12. Using `pathlib`, write code that takes a filename and returns just the extension (e.g. `"doc.pdf"` → `"pdf"`).

**Slightly harder (type hints + real ML shape)**

13. Write a typed function `top_k(scores: dict[str, float], k: int) -> list[str]` that returns the `k` keys with the highest values, highest first. (This is retrieval — ranking chunks by similarity.)

14. Write `cosine_sim(a, b)` for two equal-length lists of floats, using only pure Python (no NumPy). Formula: dot(a,b) / (norm(a) * norm(b)).

Start whenever. You can send them in batches — even just 1–5 first if you want quicker feedback loops.