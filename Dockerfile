FROM python:3.11-slim

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=user bureaucratic_maze/ ./bureaucratic_maze/
COPY --chown=user server/ ./server/
COPY --chown=user openenv.yaml .
COPY --chown=user pyproject.toml .
COPY --chown=user setup.py .

# Install the package
RUN pip install --no-cache-dir -e .

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "bureaucratic_maze.server:app", "--host", "0.0.0.0", "--port", "7860"]
